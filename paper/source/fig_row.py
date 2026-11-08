"""Fig. 3: what the π0.5 policy sees in the first scene of the choosing task (L1, episode 0, seed 100000,
the same scene and instruction as row/language.py gives every policy). Head view without the black bands,
wrist view beside it, both at the policy's own resolution."""
import os
import sys

import numpy as np
from PIL import Image

P = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(P, 'row'))
from language import episode  # noqa: E402

import airlab_vla.sim as sim  # noqa: E402

GAP, H = 12, 300
order, target, text = episode('L1', 0)
scene = sim.PickScene(cameras='pi05')
scene.rng = np.random.default_rng(100000)
o = scene.reset_row(order, target)
print('order', order, 'target', target, 'instruction', text, 'table', scene.table, o['head'].shape, o['wrist'].shape)


def fit(img, height):
    w = int(round(img.shape[1] * height / img.shape[0]))
    return np.asarray(Image.fromarray(img).resize((w, height), Image.NEAREST))


a, b = fit(o['head'], H), fit(o['wrist'], H)
out = np.concatenate([a, np.full((H, GAP, 3), 255, np.uint8), b], axis=1)
Image.fromarray(out).save(os.path.join(P, 'fig_row.png'))
open(os.path.join(P, 'fig_row.txt'), 'w', encoding='utf8').write(f'{order} {target} {text}\n')
print('saved', out.shape)
