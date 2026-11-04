"""Record expert pick demonstrations: ros2 run airlab_vla record --episodes 1200

Each episode is one .npz in --out (default ~/airlab_vla/demos, ~/airlab_vla/demos_pi05 with
--cameras pi05):
  head    (T, 72, 128, 3) uint8   head camera (T, 126, 224, 3) with --cameras pi05
  wrist   (T, 96, 96, 3)  uint8   right wrist camera (T, 224, 224, 3) with --cameras pi05
  state   (T, 8)  float32         right arm joints 1-7 + finger, measured
  action  (T, 8)  float32         joint targets the expert commands at that step
  done    (T,)    float32         1 on the final hold steps (the pick is finished)
  instruction                     the sentence the episode was recorded with (names the box's colour)
  table, color, distractor        which table and box, and whether another box stood on the table
  task, kind, order, target       --task row only: 'row', 'colour' or 'position' instruction, the
                                  colours from the robot's left to right, and the slot picked
Only successful episodes (box lifted, every IK waypoint reached) are kept.

--task row puts all three boxes side by side in front of the robot (sim.reset_row) and names
the box by its colour or by where it stands. Two things never appear in these demos, so that a
test can ask for them (paper/실험계획_1-2단계.md, stage 2): the colour instruction for a red box
in the right slot, and the words "in the middle".

In half of the episodes the executed targets get a slowly drifting offset while the stored
labels stay the expert's own targets, so the policy also sees states a little off the
expert's path, labelled with the way back (the DART trick against compounding errors).
"""

import argparse
import multiprocessing as mp
import os
import time

import numpy as np

from airlab_vla.sim import BOXES, CAMERAS, SLOTS, TABLES

INSTRUCTIONS = [  # {} = the colour of the box to pick
    'pick up the {} box',
    'pick the {} box',
    'grab the {} box',
    'grasp the {} box and lift it',
    'take the {} box',
    'lift the {} cube',
    'pick up the {} cube from the table',
]
POSITION_INSTRUCTIONS = [  # {} = where the box stands: 'on the left', 'in the middle', 'on the right'
    'pick up the box {}',
    'grab the box {}',
    'take the box {}',
    'lift the cube {}',
    'pick up the cube {} from the table',
]
PLACE = {'left': 'on the left', 'middle': 'in the middle', 'right': 'on the right'}


def held_out(kind, order, target):
    """The combinations the row demos leave out: red named by colour in the right slot, and "in the middle"."""
    slots = dict(zip(SLOTS, order))
    return (kind == 'colour' and target == 'right' and slots['right'] == 'red') or (kind == 'position' and target == 'middle')


def row_setup(rng):
    """Colour order, instruction kind and target slot of a row demo, drawn until it is not held out."""
    while True:
        order = tuple(str(c) for c in rng.permutation(sorted(BOXES)))
        kind = 'colour' if rng.random() < 0.5 else 'position'
        target = str(rng.choice(SLOTS))
        if not held_out(kind, order, target):
            return order, kind, target


def record_episode(scene, expert, rng, noisy, table=None, task='pick'):
    if task == 'row':
        order, kind, target = row_setup(rng)
        obs = scene.reset_row(order, target, table)
    else:
        obs = scene.reset(table)
    plan = expert.plan()
    n_hold = int(round(0.5 * 10))
    frames = {k: [] for k in ('head', 'wrist', 'state', 'action', 'done')}
    drift = np.zeros(8)
    for t, a in enumerate(plan):
        for k in ('head', 'wrist', 'state'):
            frames[k].append(obs[k])
        frames['action'].append(a)
        frames['done'].append(1.0 if t >= len(plan) - n_hold else 0.0)
        if noisy:
            drift[:7] = 0.85 * drift[:7] + rng.normal(0, 0.012, 7)
        obs = scene.step(a + drift)
    ok = scene.lifted() and expert.ik_error < 0.005  # a plan that missed a waypoint is a bad example
    ep = {k: np.array(v) for k, v in frames.items()}
    if task == 'row' and kind == 'position':
        ep['instruction'] = rng.choice(POSITION_INSTRUCTIONS).format(PLACE[target])
    else:
        ep['instruction'] = rng.choice(INSTRUCTIONS).format(scene.color)
    ep['table'], ep['color'], ep['distractor'] = scene.table, scene.color, scene.distractor
    if task == 'row':
        ep['task'], ep['kind'], ep['order'], ep['target'] = task, kind, np.array(order), target
    return ep, ok


def worker(args):
    wid, seeds, out, table, cameras, task = args
    from airlab_vla.expert import Expert
    from airlab_vla.sim import PickScene
    kept = 0
    for seed in seeds:
        scene = getattr(worker, 'scene', None)
        if scene is None:
            scene = worker.scene = PickScene(seed=seed, cameras=cameras)
            worker.expert = Expert(scene)
        scene.rng = np.random.default_rng(seed)
        rng = np.random.default_rng(seed + 1_000_000)
        ep, ok = record_episode(scene, worker.expert, rng, noisy=seed % 2 == 1, table=table, task=task)
        if ok:
            np.savez_compressed(os.path.join(out, f'ep_{seed:05d}.npz'), **ep)
            kept += 1
    return len(seeds), kept


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--episodes', type=int, default=1200)
    ap.add_argument('--start', type=int, default=0, help='first episode seed (to add more later)')
    ap.add_argument('--workers', type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument('--table', choices=['all', *TABLES], default='all',
                    help='which table the box is on (all: random per episode)')
    ap.add_argument('--cameras', choices=sorted(CAMERAS), default='small',
                    help="image sizes: small (this package's policy) or pi05 (224 wide, for openpi)")
    ap.add_argument('--task', choices=['pick', 'row'], default='pick',
                    help='pick: one box lined up (maybe a second one nearby); row: three boxes, choose by the instruction')
    ap.add_argument('--out', help='default ~/airlab_vla/demos[_row][_pi05]')
    a = ap.parse_args()
    a.out = a.out or os.path.expanduser('~/airlab_vla/demos' + ('_row' if a.task == 'row' else '')
                                        + ('' if a.cameras == 'small' else '_' + a.cameras))
    os.makedirs(a.out, exist_ok=True)
    seeds = list(range(a.start, a.start + a.episodes))
    table = None if a.table == 'all' else a.table
    jobs = [(w, seeds[w::a.workers], a.out, table, a.cameras, a.task) for w in range(a.workers)]
    t0 = time.time()
    with mp.get_context('spawn').Pool(a.workers) as pool:
        results = pool.map(worker, jobs)
    tried, kept = map(sum, zip(*results))
    print(f'{kept}/{tried} episodes kept in {a.out} ({time.time() - t0:.0f} s)')


if __name__ == '__main__':
    main()
