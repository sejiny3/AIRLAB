"""Closed-loop test of a trained policy in the pick scene: ros2 run unbolt_vla evaluate

Runs the policy on setups it never saw (seeds from 100000 on) and the scripted expert on the
same setups, and reports how often each lifts the box. --video saves the first episodes'
head and wrist views as an animated GIF.
"""

import argparse
import os
import time

import numpy as np

from unbolt_vla.expert import Expert
from unbolt_vla.runner import DEFAULT_POLICY, PolicyRunner
from unbolt_vla.sim import PickScene

MAX_STEPS = 120   # 12 s; the expert needs 7.7 s
DONE_STEPS = 3    # stop once the policy says "done" this many steps in a row


def run_policy(scene, runner, instruction, table=None, frames=None):
    obs = scene.reset(table)
    runner.reset(instruction)
    streak = 0
    for t in range(MAX_STEPS):
        action, done = runner.act(obs['head'], obs['wrist'], obs['state'])
        if frames is not None:
            frames.append(side_by_side(obs['head'], obs['wrist']))
        streak = streak + 1 if done > 0.5 else 0
        if streak >= DONE_STEPS:
            break
        obs = scene.step(action)
    return scene.lifted(), t + 1


def run_expert(scene, expert, table=None):
    scene.reset(table)
    for a in expert.plan():
        scene.step(a)
    return scene.lifted()


def side_by_side(head, wrist):
    h = max(head.shape[0], wrist.shape[0])
    canvas = np.full((h, head.shape[1] + wrist.shape[1], 3), 255, np.uint8)
    canvas[:head.shape[0], :head.shape[1]] = head
    canvas[:wrist.shape[0], head.shape[1]:] = wrist
    return canvas


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--policy', default=DEFAULT_POLICY)
    ap.add_argument('--episodes', type=int, default=50)
    ap.add_argument('--instruction', default='pick up the red box')
    ap.add_argument('--table', choices=['both', 'supply', 'work'], default='both',
                    help='which table the box is on (both: random per episode)')
    ap.add_argument('--video', default='', help='GIF path for the first 3 episodes')
    a = ap.parse_args()
    scene = PickScene()
    runner = PolicyRunner(a.policy)
    expert = Expert(scene)
    table = None if a.table == 'both' else a.table
    tally = {}  # table -> [episodes, policy wins, expert wins]
    frames = [] if a.video else None
    t0 = time.time()
    for k in range(a.episodes):
        seed = 100000 + k
        scene.rng = np.random.default_rng(seed)
        ok, steps = run_policy(scene, runner, a.instruction, table, frames if k < 3 else None)
        where = scene.table
        scene.rng = np.random.default_rng(seed)
        ok_expert = run_expert(scene, expert, table)
        t = tally.setdefault(where, [0, 0, 0])
        t[0] += 1
        t[1] += ok
        t[2] += ok_expert
        print(f'episode {k:3d}  {where:6s}  policy {"lifted" if ok else "FAILED"} in {steps:3d} steps   '
              f'expert {"lifted" if ok_expert else "FAILED"}', flush=True)
    rate = lambda w, n: f'{w}/{n} ({100 * w / n:.0f}%)'
    for where, (n, p, e) in sorted(tally.items()):
        print(f'{where:6s}  policy {rate(p, n)}   expert {rate(e, n)}')
    n, p, e = (sum(v) for v in zip(*tally.values()))
    print(f'policy {rate(p, n)}   expert {rate(e, n)}   {time.time() - t0:.0f} s')
    if frames:
        from PIL import Image
        imgs = [Image.fromarray(f).resize((f.shape[1] * 2, f.shape[0] * 2)) for f in frames]
        imgs[0].save(a.video, save_all=True, append_images=imgs[1:], duration=100, loop=0)
        print(f'video: {a.video}')


if __name__ == '__main__':
    main()
