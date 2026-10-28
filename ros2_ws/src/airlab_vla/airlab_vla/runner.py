"""Run a trained policy step by step (used by evaluate.py and by the ROS node).

Every control step the policy predicts the next CHUNK targets. The target sent to the arm is
a weighted average of what all recent chunks said about *this* step (ACT's temporal
ensembling, older predictions weighted a little more), which smooths out jitter between
consecutive predictions.
"""

import collections
import os

import numpy as np
import torch

from airlab_vla.model import CHUNK, PickPolicy, to_float, word_batch

DEFAULT_POLICY = os.path.expanduser('~/airlab_vla/policy.pt')


class PolicyRunner:
    def __init__(self, path=DEFAULT_POLICY, threads=4, ensemble_decay=0.1):
        torch.set_num_threads(threads)
        ckpt = torch.load(path, map_location='cpu')
        self.policy = PickPolicy()
        self.policy.load_state_dict(ckpt['state_dict'])
        self.policy.eval()
        self.weights = np.exp(-ensemble_decay * np.arange(CHUNK))
        self.reset('pick up the red box')

    def reset(self, instruction):
        self.words = word_batch([instruction])
        self.chunks = collections.deque(maxlen=CHUNK)  # newest last; each has CHUNK future targets

    @torch.no_grad()
    def act(self, head, wrist, state):
        """head (72, 128, 3) and wrist (96, 96, 3) uint8 images, state (8,) joint angles.
        Returns the joint targets for now (8,) and the probability that the pick is done."""
        pred, done = self.policy(to_float(head[None]), to_float(wrist[None]), *self.words,
                                 torch.as_tensor(state, dtype=torch.float32)[None])
        self.chunks.append(self.policy.unnormalise(pred[0]).numpy())
        # chunk i (0 = oldest) was predicted len-1-i steps ago, so its entry for now is that index
        n = len(self.chunks)
        now = np.array([c[n - 1 - i] for i, c in enumerate(self.chunks)])
        w = self.weights[:n]
        return (w[:, None] * now).sum(0) / w.sum(), torch.sigmoid(done[0]).item()
