"""Fig. 2: what each policy receives for the first test scene (seed 100000). One process per camera
preset: two sets of MuJoCo renderers in one process overwrite each other's GL buffers."""
import os
import subprocess
import sys

import numpy as np
from PIL import Image

P = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) > 1:
    from airlab_vla.sim import PickScene, pad_square
    cameras = sys.argv[1]
    scene = PickScene(cameras=cameras)
    scene.rng = np.random.default_rng(100000)
    o = scene.reset()
    head = pad_square(o['head']) if cameras == 'pi05' else o['head']
    np.savez(os.path.join(P, f'view_{cameras}.npz'), head=head, wrist=o['wrist'])
    print(cameras, head.shape, o['wrist'].shape, scene.table, scene.color)
    sys.exit()

for cameras in ('small', 'pi05'):
    subprocess.run([sys.executable, __file__, cameras], check=True)
GAP, H = 12, 300


def fit(img, height):
    w = int(round(img.shape[1] * height / img.shape[0]))
    return np.asarray(Image.fromarray(img).resize((w, height), Image.NEAREST))


lines = []
for cameras in ('small', 'pi05'):
    z = np.load(os.path.join(P, f'view_{cameras}.npz'))
    a, b = fit(z['head'], H), fit(z['wrist'], H)
    lines.append(np.concatenate([a, np.full((H, GAP, 3), 255, np.uint8), b], axis=1))
width = max(line.shape[1] for line in lines)
pad = lambda line: np.concatenate([line, np.full((H, width - line.shape[1], 3), 255, np.uint8)], axis=1)
out = np.concatenate([pad(lines[0]), np.full((GAP, width, 3), 255, np.uint8), pad(lines[1])])
Image.fromarray(out).save(os.path.join(P, 'fig_views.png'))
print('saved', out.shape)
