"""Can the expert lift the *named* (not lined-up) box in the ask-other scenes? Seeds 200000+k as in evaluate.ask_other."""
import numpy as np

from airlab_vla.expert import Expert
from airlab_vla.sim import PickScene

scene = PickScene(render=False)
expert = Expert(scene)
ok_lined = ok_named = 0
for k in range(20):
    scene.rng = np.random.default_rng(200000 + k)
    scene.reset(None, distractor=True)
    lined = scene.color
    named = next(c for c, b in scene.box_bodies.items() if c != lined and scene.data.xpos[b][2] > 0.5)
    state = scene.data.qpos.copy(), scene.data.qvel.copy()
    pos_named = None
    for target in (lined, named):
        scene.data.qpos[:], scene.data.qvel[:] = state
        scene.color, scene.box_body = target, scene.box_bodies[target]
        scene.box_z0 = scene.data.xpos[scene.box_body][2]
        if target == named:
            pos_named = scene.box_in_base()[0]
        for a in expert.plan():
            scene.step(a)
        got = bool(scene.lifted())
        if target == lined:
            ok_lined += got
        else:
            ok_named += got
            print(f'{k:2d} {scene.table:10s} named box at base x={pos_named[0]:.2f} y={pos_named[1]:.2f}  '
                  f'expert lifted it: {got}  ik_error {expert.ik_error:.3f}', flush=True)
print(f'expert lifted lined-up {ok_lined}/20, named {ok_named}/20')
