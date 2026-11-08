"""Closed-loop picks under visual changes the demonstrations never had (plan: paper/실험계획_1-2단계.md, stage 1):

  python3 perturb.py run    cnn|pi05 V3 out.jsonl [episodes] [server]
  python3 perturb.py expert V6 out.jsonl [episodes]     the expert on the same scenes (can it be done at all?)
  python3 perturb.py frame  small|pi05 V3 out.png      episode 0's head and wrist views

One condition per process: two scenes' renderers in one process spoil each other's images.
Same scenes and success check as `ros2 run airlab_vla evaluate` (seeds from 100000 on).
"""
import json
import math
import os
import sys
import time

import mujoco
import numpy as np

import airlab_vla.sim as sim
from airlab_vla.evaluate import DONE_STEPS, MAX_STEPS, side_by_side

CONDITIONS = {
    'V0': 'baseline',
    'V1': 'dim light (x0.4)',
    'V2': 'warm light colour',
    'V3': 'light from the side',
    'V4': 'dark brown table tops',
    'V5': 'fine green checker floor',
    'V6': 'unseen objects on the table (can, ball)',
    'V7': 'unseen box colour (yellow), named in the instruction',
    'V8': 'head camera tilted 3 deg further down',
}
YELLOW = (0.95, 0.85, 0.1, 1.0)
TABLE_Z = 0.65
PROPS = {  # name: (type, size, rgba, height of the centre above the table)
    'prop_can': (mujoco.mjtGeom.mjGEOM_CYLINDER, [0.033, 0.06, 0], [0.85, 0.85, 0.8, 1], 0.06),
    'prop_ball': (mujoco.mjtGeom.mjGEOM_SPHERE, [0.035, 0, 0], [1.0, 0.5, 0.0, 1], 0.035),
}


def load_with_props(path, gravity_compensation=True):
    """sim.load_model (the bridge's), plus the props as static world geoms parked far away."""
    spec = mujoco.MjSpec.from_file(path)
    if gravity_compensation:
        arm_joints = {a.target for a in spec.actuators if a.name not in ('left_wheel_vel', 'right_wheel_vel')}
        for joint in spec.joints:
            if joint.name in arm_joints:
                joint.actgravcomp = 1
                for body in [joint.parent] + list(joint.parent.find_all(mujoco.mjtObj.mjOBJ_BODY)):
                    body.gravcomp = 1.0
    for name, (kind, size, rgba, _) in PROPS.items():
        g = spec.worldbody.add_geom()
        g.name, g.type, g.size, g.rgba = name, kind, size, rgba
        g.pos = [40.0, 40.0, 1.0]
    return spec.compile()


def make_scene(cond, cameras):
    if cond == 'V6':
        sim.load_model = load_with_props
    scene = sim.PickScene(cameras=cameras)
    m = scene.model
    hl = m.vis.headlight
    if cond == 'V1':
        m.light_diffuse[:] *= 0.4
        m.light_ambient[:] *= 0.4
        hl.diffuse[:] = np.array(hl.diffuse) * 0.4
        hl.ambient[:] = np.array(hl.ambient) * 0.4
    elif cond == 'V2':
        warm = np.array([1.0, 0.75, 0.5])
        m.light_diffuse[:] *= warm
        hl.diffuse[:] = np.array(hl.diffuse) * warm
        hl.ambient[:] = np.array(hl.ambient) * warm
    elif cond == 'V3':
        d = np.array([1.0, 0.4, -0.3])
        m.light_dir[0] = d / np.linalg.norm(d)
    elif cond == 'V4':
        for g in range(m.ngeom):
            if m.geom(g).name.endswith('_top'):
                m.geom_rgba[g] = [0.35, 0.22, 0.12, 1]
    elif cond == 'V5':
        mat = m.material('groundplane').id
        m.mat_rgba[mat] = [0.45, 0.9, 0.45, 1]
        m.mat_texrepeat[mat] = [20, 20]
    elif cond == 'V8':
        cam = m.camera('head_camera').id
        a = math.radians(-3.0) / 2  # about the camera's own x axis; negative turns the view down
        q = np.empty(4)
        mujoco.mju_mulQuat(q, m.cam_quat[cam].copy(), np.array([math.cos(a), math.sin(a), 0, 0]))
        m.cam_quat[cam] = q
    return scene


def start_episode(scene, cond, k, instruction='pick up the {} box'):
    """Reset to scene k, apply the per-episode part of the condition, return (obs, instruction)."""
    m, d = scene.model, scene.data
    scene.rng = np.random.default_rng(100000 + k)
    obs = scene.reset(None)
    word = scene.color
    if cond == 'V6':
        box = d.xpos[scene.box_body][:2]
        _, R = scene.base_pose()
        fwd, left = R[:2, 0], R[:2, 1]
        spots = {'prop_can': box + 0.13 * left, 'prop_ball': box + 0.13 * fwd - 0.05 * left}
        for name, xy in spots.items():
            m.geom_pos[m.geom(name).id] = [xy[0], xy[1], TABLE_Z + PROPS[name][3]]
        mujoco.mj_forward(m, d)
        obs = scene.observe()
    elif cond == 'V7':
        for color, body in sim.BOXES.items():
            g = m.geom(body).id
            m.geom_rgba[g] = YELLOW if color == scene.color else ORIGINAL_RGBA[color]
        word = 'yellow'
        obs = scene.observe()
    return obs, instruction.format(word)


def run(which, cond, out, episodes, server=None):
    if which in ('cnn', 'cnn_aug'):  # cnn_aug: trained with openpi's image augmentation (train --augment openpi)
        from airlab_vla.runner import DEFAULT_POLICY, PolicyRunner
        path = DEFAULT_POLICY if which == 'cnn' else os.path.expanduser('~/airlab_vla/policy_aug.pt')
        runner, scene = PolicyRunner(path), make_scene(cond, 'small')
    else:
        from airlab_vla.remote import RemoteRunner
        runner, scene = RemoteRunner(server), make_scene(cond, 'pi05')
    remember_colours(scene)
    log, wins, t0 = open(out, 'a', encoding='utf8'), 0, time.time()
    for k in range(episodes):
        obs, text = start_episode(scene, cond, k)
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
        ok, other = bool(scene.lifted()), bool(scene.lifted_other())
        wins += ok
        log.write(json.dumps({'policy': which, 'cond': cond, 'episode': k, 'instruction': text, 'ok': ok,
                              'other': other, 'steps': steps}) + '\n')
        log.flush()
    print(f'{which} {cond} {CONDITIONS[cond]:52s} {wins}/{episodes}  {time.time() - t0:.0f} s', flush=True)


def expert(cond, out, episodes):
    from airlab_vla.expert import Expert
    scene = make_scene(cond, 'small')
    remember_colours(scene)
    exp, wins = Expert(scene), 0
    log = open(out, 'a', encoding='utf8')
    for k in range(episodes):
        start_episode(scene, cond, k)
        for a in exp.plan():
            scene.step(a)
        ok = bool(scene.lifted())
        wins += ok
        log.write(json.dumps({'policy': 'expert', 'cond': cond, 'episode': k, 'ok': ok}) + '\n')
    print(f'expert {cond} {CONDITIONS[cond]:52s} {wins}/{episodes}', flush=True)


def frame(cameras, cond, out):
    from PIL import Image
    scene = make_scene(cond, cameras)
    remember_colours(scene)
    obs, text = start_episode(scene, cond, 0)
    head = sim.pad_square(obs['head']) if cameras == 'pi05' else obs['head']
    Image.fromarray(side_by_side(head, obs['wrist'])).save(out)
    print(out, text)


ORIGINAL_RGBA = {}


def remember_colours(scene):
    for color, body in sim.BOXES.items():
        ORIGINAL_RGBA[color] = scene.model.geom_rgba[scene.model.geom(body).id].copy()


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'run':
        run(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]) if len(sys.argv) > 5 else 50,
            sys.argv[6] if len(sys.argv) > 6 else None)
    elif mode == 'expert':
        expert(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 50)
    else:
        frame(sys.argv[2], sys.argv[3], sys.argv[4])
