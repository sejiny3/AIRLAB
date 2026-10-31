"""Closed-loop test of the fine-tuned π0.5 in the pick scene, on the small policy's test setups:

  .venv/bin/python ../AIRLAB/pi05/evaluate_pi05.py --checkpoint /path/to/checkpoints/pi05_airlab/run1/15000

The same episodes and the same success check as `ros2 run airlab_vla evaluate` (seeds from 100000
on), so the two policies' numbers compare directly. --ask-other is the language check there.
"""

import argparse
import pathlib
import sys
import time

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'ros2_ws/src/airlab_vla'))

from airlab_vla.evaluate import ask_other, run_policy, side_by_side  # noqa: E402
from airlab_vla.sim import PickScene  # noqa: E402
import airlab_policy  # noqa: E402
from openpi.policies import policy_config  # noqa: E402

REPLAN = 5  # steps of each 10-step chunk to play before asking the model again
SIZE = 224


def pad_square(head):
    """The head image as in the dataset: centred between black bars (convert_to_lerobot.py)."""
    out = np.zeros((SIZE, SIZE, 3), np.uint8)
    top = (SIZE - head.shape[0]) // 2
    out[top:top + head.shape[0]] = head
    return out


class Pi05Runner:
    """PolicyRunner's interface (airlab_vla/runner.py) around an openpi policy."""

    def __init__(self, policy, replan=REPLAN):
        self.policy, self.replan = policy, replan
        self.reset('pick up the red box')

    def reset(self, instruction):
        self.prompt, self.chunk, self.t = instruction, None, 0

    def act(self, head, wrist, state):
        """Joint targets for now (8,) and the done value (about 0 or 1)."""
        if self.chunk is None or self.t >= self.replan:
            self.chunk = self.policy.infer({
                'observation/image': pad_square(head),
                'observation/wrist_image': wrist,
                'observation/state': state,
                'prompt': self.prompt,
            })['actions']
            self.t = 0
        step = self.chunk[self.t]
        self.t += 1
        return step[:8], float(step[8])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--checkpoint', required=True, help='a step folder, e.g. .../pi05_airlab/run1/15000')
    ap.add_argument('--episodes', type=int, default=100)
    ap.add_argument('--instruction', default='pick up the {} box', help='{} = the colour of the box to pick')
    ap.add_argument('--replan', type=int, default=REPLAN)
    ap.add_argument('--video', default='', help='GIF path for the first 3 episodes')
    ap.add_argument('--ask-other', action='store_true',
                    help='language check: name the box on the next spot instead of the lined-up one')
    a = ap.parse_args()

    policy = policy_config.create_trained_policy(airlab_policy.CONFIG, a.checkpoint)
    runner = Pi05Runner(policy, a.replan)
    scene = PickScene(cameras='pi05')
    if a.ask_other:
        return ask_other(scene, runner, a.episodes)
    wins, frames, t0 = 0, [] if a.video else None, time.time()
    for k in range(a.episodes):
        scene.rng = np.random.default_rng(100000 + k)
        ok, steps = run_policy(scene, runner, a.instruction, frames=frames if k < 3 else None)
        wins += ok
        pair = 'with 2nd box' if scene.distractor else 'alone'
        print(f'episode {k:3d}  {scene.table:10s} {scene.color:5s} {pair:12s}  '
              f'{"lifted" if ok else "FAILED"} in {steps:3d} steps', flush=True)
    print(f'π0.5 {wins}/{a.episodes} ({100 * wins / a.episodes:.0f}%)   {time.time() - t0:.0f} s')
    if frames:
        from PIL import Image
        Image.fromarray(frames[0]).save(a.video, save_all=True, duration=100, loop=0,
                                        append_images=[Image.fromarray(f) for f in frames[1:]])
        print(f'video: {a.video}')


if __name__ == '__main__':
    main()
