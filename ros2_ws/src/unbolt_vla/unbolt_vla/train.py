"""Train the pick policy on recorded demos (CPU): ros2 run unbolt_vla train

Behaviour cloning: for every recorded step, predict the expert's next CHUNK joint targets
(L1 loss, in normalised units) and whether the pick is done (cross-entropy). Images get small
random shifts and brightness/contrast changes, the joint state a little noise, so the policy
does not depend on pixel-exact renders or exact joint readings.
"""

import argparse
import glob
import os
import time

import numpy as np
import torch
import torch.nn.functional as F

from unbolt_vla.model import CHUNK, PickPolicy, to_float, word_batch


def load(demo_dir):
    files = sorted(glob.glob(os.path.join(demo_dir, 'ep_*.npz')))
    if not files:
        raise SystemExit(f'no demos in {demo_dir} (run: ros2 run unbolt_vla record)')
    eps = []
    for f in files:
        z = np.load(f)
        eps.append({k: z[k] for k in ('head', 'wrist', 'state', 'action', 'done')} | {'instruction': str(z['instruction'])})
    return eps


class Frames:
    """All steps of a set of episodes, with the CHUNK future actions of each step."""

    def __init__(self, eps):
        self.head = np.concatenate([e['head'] for e in eps])
        self.wrist = np.concatenate([e['wrist'] for e in eps])
        self.state = np.concatenate([e['state'] for e in eps]).astype(np.float32)
        self.done = np.concatenate([e['done'] for e in eps]).astype(np.float32)
        self.text = [e['instruction'] for e in eps for _ in range(len(e['action']))]
        chunks = []
        for e in eps:  # pad past the end with the last target: the arm holds still
            a = np.concatenate([e['action'], np.repeat(e['action'][-1:], CHUNK, 0)])
            chunks.append(np.stack([a[t:t + CHUNK] for t in range(len(e['action']))]))
        self.chunk = np.concatenate(chunks).astype(np.float32)

    def __len__(self):
        return len(self.state)

    def batch(self, idx, augment):
        head, wrist = to_float(self.head[idx]), to_float(self.wrist[idx])
        state = torch.from_numpy(self.state[idx])
        if augment:
            head, wrist = jitter(shift(head, 4)), jitter(shift(wrist, 4))
            state = state + 0.01 * torch.randn_like(state)
        words, offsets = word_batch([self.text[i] for i in idx])
        return head, wrist, words, offsets, state, torch.from_numpy(self.chunk[idx]), torch.from_numpy(self.done[idx])


def shift(x, pad):
    """Random translation by up to `pad` pixels (edge-replicated), per image."""
    n, c, h, w = x.shape
    x = F.pad(x, (pad, pad, pad, pad), mode='replicate')
    dx, dy = torch.randint(0, 2 * pad + 1, (2, n))
    return torch.stack([x[i, :, dy[i]:dy[i] + h, dx[i]:dx[i] + w] for i in range(n)])


def jitter(x):
    n = x.shape[0]
    b = 1 + 0.2 * (torch.rand(n, 1, 1, 1) - 0.5)
    c = 1 + 0.2 * (torch.rand(n, 1, 1, 1) - 0.5)
    m = x.mean(dim=(1, 2, 3), keepdim=True)
    return ((x - m) * c + m * b).clamp(0, 1)


def losses(policy, batch):
    head, wrist, words, offsets, state, chunk, done = batch
    pred, done_logit = policy(head, wrist, words, offsets, state)
    target = (chunk - policy.mean) / policy.std
    return F.l1_loss(pred, target), F.binary_cross_entropy_with_logits(done_logit, done)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--demos', default=os.path.expanduser('~/unbolt_vla/demos'))
    ap.add_argument('--out', default=os.path.expanduser('~/unbolt_vla/policy.pt'))
    ap.add_argument('--steps', type=int, default=20000)
    ap.add_argument('--batch', type=int, default=64)
    ap.add_argument('--lr', type=float, default=1e-3)
    ap.add_argument('--threads', type=int, default=os.cpu_count())
    ap.add_argument('--val', type=float, default=0.1, help='fraction of episodes held out')
    a = ap.parse_args()
    torch.set_num_threads(a.threads)
    torch.manual_seed(0)

    eps = load(a.demos)
    n_val = max(1, int(len(eps) * a.val))
    order = np.random.default_rng(0).permutation(len(eps))  # held-out episodes from every table
    train, val = Frames([eps[i] for i in order[n_val:]]), Frames([eps[i] for i in order[:n_val]])
    print(f'{len(eps) - n_val} training episodes ({len(train)} steps), {n_val} validation episodes')

    policy = PickPolicy()
    policy.mean.copy_(torch.from_numpy(train.chunk.reshape(-1, 8).mean(0)))
    policy.std.copy_(torch.from_numpy(train.chunk.reshape(-1, 8).std(0)).clamp(min=0.01))
    opt = torch.optim.AdamW(policy.parameters(), lr=a.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, a.lr, total_steps=a.steps, pct_start=0.05)
    rng = np.random.default_rng(0)
    t0, best = time.time(), float('inf')
    for step in range(1, a.steps + 1):
        policy.train()
        l_act, l_done = losses(policy, train.batch(rng.integers(0, len(train), a.batch), augment=True))
        opt.zero_grad()
        (l_act + 0.1 * l_done).backward()
        opt.step()
        sched.step()
        if step % 500 == 0 or step == a.steps:
            policy.eval()
            with torch.no_grad():
                idx = np.arange(0, len(val), max(1, len(val) // 1024))
                v_act, v_done = (sum(x) / len(x) for x in zip(*[
                    losses(policy, val.batch(idx[i:i + 256], augment=False)) for i in range(0, len(idx), 256)]))
            print(f'step {step:6d}  train {l_act.item():.4f}  val {v_act.item():.4f}  done {v_done.item():.3f}  '
                  f'{time.time() - t0:.0f} s', flush=True)
            if v_act.item() < best:
                best = v_act.item()
                os.makedirs(os.path.dirname(a.out), exist_ok=True)
                torch.save({'state_dict': policy.state_dict(), 'val_l1': best, 'step': step}, a.out)
    print(f'best validation L1 {best:.4f}, saved {a.out}')


if __name__ == '__main__':
    main()
