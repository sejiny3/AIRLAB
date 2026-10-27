"""Generate the ArUco marker textures used in scene.xml (DICT_4X4_50).

  python3 models/make_markers.py

Each PNG is the marker (6x6 cells incl. its black border) plus a one-cell white
quiet zone, so the marker fills 6/8 of the image: a texture of side S shows a
marker of side 0.75 * S.
"""

import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
# boxes: 7 red, 8 green, 9 blue. Place pads: 1-3 on the work table, N1 / N2 on supply table N.
MARKERS = {i: f'aruco_{i}.png' for i in (1, 2, 3, 7, 8, 9, 11, 12, 21, 22, 31, 32)}
CELL = 32

os.makedirs(os.path.join(HERE, 'textures'), exist_ok=True)
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
for marker_id, name in MARKERS.items():
    marker = cv2.aruco.drawMarker(dictionary, marker_id, 6 * CELL)
    img = np.full((8 * CELL, 8 * CELL), 255, np.uint8)
    img[CELL:7 * CELL, CELL:7 * CELL] = marker
    cv2.imwrite(os.path.join(HERE, 'textures', name), cv2.cvtColor(img, cv2.COLOR_GRAY2RGB))
    print('wrote', name)
