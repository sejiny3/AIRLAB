"""The VLA policy: two camera images + an instruction + the arm joints -> the next joint targets.

Small enough to train on a laptop CPU in a few minutes:

  head image  (72x128) --conv--> spatial softmax --> 64 keypoints (x, y) --+
  wrist image (96x96)  --conv--> spatial softmax --> 64 keypoints (x, y) --+
  instruction words --hashed--> mean of word embeddings (32) -------------+--> MLP --> CHUNK x 8 joint targets
  arm joints + finger (8, normalised) -------------------------------------+         + "done" logit

Spatial softmax turns each feature map into the image position where it fires most, which
is what a pick needs (where the box is, where the fingers are). Predicting a chunk of future
targets rather than one (as ACT does) gives smoother motion and fewer compounding errors;
at run time the overlapping chunks are averaged (temporal ensembling).
Words are hashed into a fixed table, so any sentence (for example from the LLM planner) maps
to an embedding; unknown words just land in buckets the policy learned little about.
"""

import re
import zlib

import torch
from torch import nn
import torch.nn.functional as F

CHUNK = 10           # future steps predicted at once (1 s at 10 Hz)
WORD_BUCKETS = 512
STATE_DIM = ACTION_DIM = 8


def tokenize(text):
    """Word ids for an instruction (crc32 hash: stable across runs, unlike Python's hash())."""
    words = re.findall(r'[a-z]+', text.lower()) or ['<empty>']
    return [zlib.crc32(w.encode()) % WORD_BUCKETS for w in words]


class SpatialSoftmax(nn.Module):
    def forward(self, x):
        n, c, h, w = x.shape
        p = F.softmax(x.flatten(2), dim=-1).view(n, c, h, w)
        ys = torch.linspace(-1, 1, h, device=x.device)
        xs = torch.linspace(-1, 1, w, device=x.device)
        return torch.cat([(p.sum(2) * xs).sum(-1), (p.sum(3) * ys).sum(-1)], dim=1)  # (n, 2c)


def encoder(keypoints=64):
    def block(i, o, k, s):
        return [nn.Conv2d(i, o, k, s, k // 2), nn.GroupNorm(8, o), nn.ReLU(inplace=True)]
    return nn.Sequential(*block(3, 32, 5, 2), *block(32, 64, 3, 2), *block(64, 64, 3, 1),
                         nn.Conv2d(64, keypoints, 1), SpatialSoftmax())


class PickPolicy(nn.Module):
    def __init__(self, hidden=512):
        super().__init__()
        self.head_enc = encoder()
        self.wrist_enc = encoder()
        self.words = nn.EmbeddingBag(WORD_BUCKETS, 32, mode='mean')
        self.trunk = nn.Sequential(
            nn.Linear(128 + 128 + 32 + STATE_DIM, hidden), nn.ReLU(inplace=True),
            nn.Linear(hidden, hidden), nn.ReLU(inplace=True),
            nn.Linear(hidden, CHUNK * ACTION_DIM + 1))
        # normalisation of state/actions, filled in from the training data
        self.register_buffer('mean', torch.zeros(STATE_DIM))
        self.register_buffer('std', torch.ones(STATE_DIM))

    def forward(self, head, wrist, words, offsets, state):
        """head/wrist: float images (n, 3, h, w) in [0, 1]; words/offsets: EmbeddingBag input;
        state: raw joint angles (n, 8). Returns normalised action chunks (n, CHUNK, 8), done logits (n,)."""
        z = torch.cat([self.head_enc(head - 0.5), self.wrist_enc(wrist - 0.5),
                       self.words(words, offsets), (state - self.mean) / self.std], dim=1)
        out = self.trunk(z)
        return out[:, :-1].view(-1, CHUNK, ACTION_DIM), out[:, -1]

    def unnormalise(self, actions):
        return actions * self.std + self.mean


def word_batch(texts):
    ids = [tokenize(t) for t in texts]
    offsets = torch.tensor([0] + [len(i) for i in ids[:-1]]).cumsum(0)
    return torch.tensor([w for i in ids for w in i]), offsets


def to_float(images):
    """uint8 (n, h, w, 3) -> float (n, 3, h, w) in [0, 1]."""
    return torch.as_tensor(images).permute(0, 3, 1, 2).float() / 255.0
