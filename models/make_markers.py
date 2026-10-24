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
# 7 = red box, 3 = place pad on the work table, 5 = place pad on the supply table (under the box)
MARKERS = {7: 'aruco_7.png', 3: 'aruco_3.png', 5: 'aruco_5.png'}
CELL = 32

os.makedirs(os.path.join(HERE, 'textures'), exist_ok=True)
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
for marker_id, name in MARKERS.items():
    marker = cv2.aruco.drawMarker(dictionary, marker_id, 6 * CELL)
    img = np.full((8 * CELL, 8 * CELL), 255, np.uint8)
    img[CELL:7 * CELL, CELL:7 * CELL] = marker
    cv2.imwrite(os.path.join(HERE, 'textures', name), cv2.cvtColor(img, cv2.COLOR_GRAY2RGB))
    print('wrote', name)
