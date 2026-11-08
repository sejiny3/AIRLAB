"""Stage 2 tests: choosing one of three boxes by the instruction (plan: paper/실험계획_1-2단계.md).

  python3 language.py run    cnn|minilm|pi05 L1 out.jsonl [episodes] [server]
  python3 language.py expert L1 out.jsonl [episodes]     can the expert lift the asked-for box at all?

  L1  colour, a colour-slot combination the demos had
  L2  colour, the red box in the right slot (never named by colour in the demos)
  L3  position, "on the left" / "on the right"
  L4  position, "in the middle" (never in the demos)
  L5  unseen wording: English with new words (even episodes) or Korean (odd episodes)
  L6  relation, "the box to the left of the green box" (zero-shot)

Scenes are the row layout of record --task row (sim.reset_row) with seeds from 100000 on; the
condition's colours, slot and sentence come from their own seed, so every policy and the
expert get the same episodes. Success: the asked-for box lifted and no other box.
One condition per process (two scenes' renderers in one process spoil each other's images).
"""
import json
import os
import sys
import time

import numpy as np

import airlab_vla.sim as sim
from airlab_vla.evaluate import DONE_STEPS, MAX_STEPS
from airlab_vla.record import INSTRUCTIONS, PLACE, POSITION_INSTRUCTIONS, held_out

CONDITIONS = ('L1', 'L2', 'L3', 'L4', 'L5', 'L6')
UNSEEN_EN = ['could you please fetch me that {} block', 'i need the {} one, lift it up', 'grab that {} thing for me']
KOREAN = {'red': '빨간 상자를 집어 줘', 'green': '초록 상자를 집어 줘', 'blue': '파란 상자를 집어 줘'}
POLICIES = {'cnn': '~/airlab_vla/policy_row.pt', 'minilm': '~/airlab_vla/policy_row_minilm.pt'}


def episode(cond, k):
    """(colour order left to right, target slot, instruction) of episode k of a condition."""
    rng = np.random.default_rng([CONDITIONS.index(cond), k])
    while True:
        order = tuple(str(c) for c in rng.permutation(sorted(sim.BOXES)))
        slots = dict(zip(sim.SLOTS, order))
        if cond == 'L2':
            if slots['right'] == 'red':
                return order, 'right', str(rng.choice(INSTRUCTIONS)).format('red')
        elif cond in ('L1', 'L5'):  # seen combinations only, so L5 tests the wording alone
            target = str(rng.choice(sim.SLOTS))
            if held_out('colour', order, target):
                continue
            c = slots[target]
            if cond == 'L1':
                return order, target, str(rng.choice(INSTRUCTIONS)).format(c)
            return order, target, KOREAN[c] if k % 2 else str(rng.choice(UNSEEN_EN)).format(c)
        elif cond == 'L3':
            target = str(rng.choice(['left', 'right']))
            return order, target, str(rng.choice(POSITION_INSTRUCTIONS)).format(PLACE[target])
        elif cond == 'L4':
            return order, 'middle', str(rng.choice(POSITION_INSTRUCTIONS)).format(PLACE['middle'])
        else:  # L6: name the target by its neighbour
            side = str(rng.choice(['left', 'right']))
            i = int(rng.integers(2)) + (0 if side == 'left' else 1)  # target slot index
            ref = sim.SLOTS[i + 1 if side == 'left' else i - 1]
            return order, sim.SLOTS[i], f'pick up the box to the {side} of the {slots[ref]} box'


def lifted_slot(scene):
    z = {slot: scene.data.xpos[scene.box_bodies[c]][2] for slot, c in scene.slots.items()}
    up = [slot for slot, h in z.items() if h > 0.705]
    return up[0] if len(up) == 1 else ('none' if not up else '+'.join(up))


def run(which, cond, out, episodes, server=None):
    if which == 'pi05':
        from airlab_vla.remote import RemoteRunner
        runner, scene = RemoteRunner(server), sim.PickScene(cameras='pi05')
    else:
        from airlab_vla.runner import PolicyRunner
        runner, scene = PolicyRunner(os.path.expanduser(POLICIES[which])), sim.PickScene(cameras='small')
    log, wins, t0 = open(out, 'a', encoding='utf8'), 0, time.time()
    for k in range(episodes):
        order, target, text = episode(cond, k)
        scene.rng = np.random.default_rng(100000 + k)
        obs = scene.reset_row(order, target)
        runner.reset(text)
        streak = 0
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
        got = lifted_slot(scene)
        ok = got == target
        wins += ok
        log.write(json.dumps({'policy': which, 'cond': cond, 'episode': k, 'instruction': text, 'order': order,
                              'target': target, 'lifted': got, 'ok': ok, 'steps': steps}, ensure_ascii=False) + '\n')
        log.flush()
    print(f'{which} {cond} {wins}/{episodes}  {time.time() - t0:.0f} s', flush=True)


def expert(cond, out, episodes):
    from airlab_vla.expert import Expert
    scene = sim.PickScene(render=False)
    exp, wins = Expert(scene), 0
    log = open(out, 'a', encoding='utf8')
    for k in range(episodes):
        order, target, text = episode(cond, k)
        scene.rng = np.random.default_rng(100000 + k)
        scene.reset_row(order, target)
        for a in exp.plan():
            scene.step(a)
        ok = lifted_slot(scene) == target
        wins += ok
        log.write(json.dumps({'policy': 'expert', 'cond': cond, 'episode': k, 'target': target, 'ok': ok}) + '\n')
    print(f'expert {cond} {wins}/{episodes}', flush=True)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'run':
        run(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]) if len(sys.argv) > 5 else 50,
            sys.argv[6] if len(sys.argv) > 6 else None)
    elif mode == 'expert':
        expert(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 50)
    else:  # list: print the episodes of every condition
        for cond in CONDITIONS:
            for k in range(int(sys.argv[2]) if len(sys.argv) > 2 else 4):
                print(cond, k, *episode(cond, k))
