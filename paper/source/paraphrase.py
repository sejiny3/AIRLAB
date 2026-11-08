"""Closed-loop picks with instructions the demonstrations never used, for both policies:

  python3 paraphrase.py cnn  out.jsonl [episodes]
  python3 paraphrase.py pi05 out.jsonl [episodes] https://<server>

Same scenes and success check as `ros2 run airlab_vla evaluate` (seeds from 100000 on). The
demonstrations' sentences are the 7 English templates in airlab_vla/record.py; each set here
keeps the colour word's meaning but changes what is around it. The CNN policy hashes [a-z]+
words, so the Korean sentence reaches it as the empty instruction.
"""
import json
import sys
import time

import numpy as np

from airlab_vla.evaluate import DONE_STEPS, MAX_STEPS
from airlab_vla.sim import PickScene

KO = {'red': '빨간', 'green': '초록', 'blue': '파란'}
SETS = {
    'seen': lambda c: f'pick up the {c} box',
    'unseen_words': lambda c: f'could you please fetch me that {c} block',
    'distracting': lambda c: f'the weather is lovely today and my coffee is cold, anyway {c} box, pick it up for me',
    'korean': lambda c: f'{KO[c]} 상자를 집어 줘',
}

which, out = sys.argv[1], sys.argv[2]
episodes = int(sys.argv[3]) if len(sys.argv) > 3 else 50
if which == 'cnn':
    from airlab_vla.runner import DEFAULT_POLICY, PolicyRunner
    runner, scene = PolicyRunner(DEFAULT_POLICY), PickScene()
else:
    from airlab_vla.remote import RemoteRunner
    runner, scene = RemoteRunner(sys.argv[4]), PickScene(cameras='pi05')

log = open(out, 'a', encoding='utf8')
for name, make in SETS.items():
    wins, t0 = 0, time.time()
    for k in range(episodes):
        scene.rng = np.random.default_rng(100000 + k)
        obs = scene.reset(None)
        text = make(scene.color)
        runner.reset(text)
        streak, steps = 0, 0
        for steps in range(1, MAX_STEPS + 1):
            got = runner.act(obs['head'], obs['wrist'], obs['state'])
            while got is None:  # a remote policy: the sim waits, as the arm holds in the ROS node
                time.sleep(0.005)
                got = runner.act(obs['head'], obs['wrist'], obs['state'])
            action, done = got
            streak = streak + 1 if done > 0.5 else 0
            if streak >= DONE_STEPS:
                break
            obs = scene.step(action)
        ok, other = bool(scene.lifted()), bool(scene.lifted_other())
        wins += ok
        log.write(json.dumps({'policy': which, 'set': name, 'episode': k, 'instruction': text, 'ok': ok,
                              'other': other, 'steps': steps}, ensure_ascii=False) + '\n')
        log.flush()
    print(f'{which} {name:13s} {wins}/{episodes}  {time.time() - t0:.0f} s', flush=True)
