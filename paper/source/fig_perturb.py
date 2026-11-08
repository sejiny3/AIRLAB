"""Fig. 4: the head view of the first test scene under each visual condition (frames/ from perturb.py frame)."""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

P = os.path.dirname(os.path.abspath(__file__))
NAMES = ['V0 Baseline', 'V1 Dim light', 'V2 Warm light', 'V3 Side light', 'V4 Brown table',
         'V5 Green floor', 'V6 Can and ball', 'V7 Yellow box', 'V8 Camera −3°']
SCALE, GAP, LABEL = 2, 10, 34
font = ImageFont.truetype('arial.ttf', 26)

tiles = []
for i, name in enumerate(NAMES):
    frame = np.asarray(Image.open(os.path.join(P, 'frames', f'V{i}_pi05.png')).convert('RGB'))
    head = frame[:, :224]
    rows = np.where(head.reshape(224, -1).max(axis=1) > 0)[0]  # drop the black bands of the square pad
    head = Image.fromarray(head[rows[0]:rows[-1] + 1])
    head = head.resize((head.width * SCALE, head.height * SCALE), Image.LANCZOS)
    tile = Image.new('RGB', (head.width, head.height + LABEL), 'white')
    tile.paste(head, (0, LABEL))
    ImageDraw.Draw(tile).text((2, 2), name, fill='black', font=font)
    tiles.append(tile)

w, h = tiles[0].size
out = Image.new('RGB', (3 * w + 2 * GAP, 3 * h + 2 * GAP), 'white')
for i, tile in enumerate(tiles):
    out.paste(tile, ((i % 3) * (w + GAP), (i // 3) * (h + GAP)))
out.save(os.path.join(P, 'fig_perturb.png'))
print('saved', out.size, 'head rows', rows[0], rows[-1])
