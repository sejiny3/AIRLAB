#!/usr/bin/env python3
"""Render the MuJoCo pictures used in the lecture slides (no ROS needed).

  python3 workshop/slides/src/render_assets.py [out_dir]

Writes robot / room / head-camera images. Head-camera views get the same ArUco
overlay as the aruco_detector node (OpenCV 4.5 API, DICT_4X4_50).
"""

import math
import os
import sys

import cv2
import mujoco
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), 'assets')
W, H = 1280, 720


def place_base(m, d, x, y, yaw):
    adr = m.joint('base_free').qposadr[0]
    d.qpos[adr:adr + 3] = (x, y, 0.08)
    d.qpos[adr + 3:adr + 7] = (math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2))


def arms(m, d, joint4):
    for side in ('left', 'right'):
        d.qpos[m.joint(f'openarm_{side}_joint4').qposadr[0]] = joint4


def free_cam(lookat, distance, azimuth, elevation):
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.lookat[:] = lookat
    cam.distance, cam.azimuth, cam.elevation = distance, azimuth, elevation
    return cam


def aruco_overlay(rgb):
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
    corners, ids, _ = cv2.aruco.detectMarkers(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), dictionary,
                                              parameters=cv2.aruco.DetectorParameters_create())
    if ids is not None:
        cv2.aruco.drawDetectedMarkers(bgr, corners, ids, borderColor=(0, 255, 0))
    return bgr, [] if ids is None else sorted(int(i) for i in ids.ravel())


def room_layout(top_png, out_png):
    """The top view with names and the staging poses (the 'top' camera: 11 m up, fovy 45, centred on x = 1.5)."""
    img = cv2.imread(top_png)
    ppm = (H / 2) / (11.0 * math.tan(math.radians(22.5)))  # pixels per metre on the floor
    px = lambda x, y: (int(W / 2 + (x - 1.5) * ppm), int(H / 2 - y * ppm))
    font = cv2.FONT_HERSHEY_SIMPLEX

    def label(text, x, y, color=(30, 30, 30), scale=0.55):
        (w, h), _ = cv2.getTextSize(text, font, scale, 1)
        cx, cy = px(x, y)
        cv2.rectangle(img, (cx - w // 2 - 4, cy - h - 4), (cx + w // 2 + 4, cy + 5), (255, 255, 255), -1)
        cv2.putText(img, text, (cx - w // 2, cy), font, scale, color, 1, cv2.LINE_AA)

    for name, x, y in [('supply_1 (red)', 1.45, -3.75), ('supply_2 (green)', 3.45, 3.65),
                       ('supply_3 (blue)', -2.35, 3.75), ('work_table (spots 1-3)', 4.8, -0.95),
                       ('home (0, 0)', 0.0, -0.55), ('door', -1.2, 1.25)]:
        label(name, x, y)
    for x, y, yaw in [(0.0, -2.8, -math.pi / 2), (2.0, 2.8, math.pi / 2), (-2.05, 2.6, math.pi), (3.8, 0.0, 0.0)]:
        a, b = px(x, y), px(x + 0.35 * math.cos(yaw), y + 0.35 * math.sin(yaw))
        cv2.circle(img, a, 6, (0, 140, 255), -1)
        cv2.arrowedLine(img, a, b, (0, 140, 255), 2, tipLength=0.35)
    for v in range(-3, 7):  # metre ticks along the south wall and the west wall
        cv2.putText(img, f'{v}', (px(v, -4.25)[0] - 5, px(v, -4.25)[1] + 18), font, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
    for v in range(-4, 5):
        cv2.putText(img, f'{v}', (px(-3.5, v)[0] - 26, px(-3.5, v)[1] + 4), font, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.imwrite(out_png, img)


def main():
    os.makedirs(OUT, exist_ok=True)
    m = mujoco.MjModel.from_xml_path(os.path.join(ROOT, 'models', 'scene.xml'))
    d = mujoco.MjData(m)
    r = mujoco.Renderer(m, H, W)

    def shot(name, camera, overlay=False):
        mujoco.mj_forward(m, d)
        r.update_scene(d, camera=camera)
        rgb = r.render()
        if overlay:
            bgr, ids = aruco_overlay(rgb)
            print(f'{name}: markers {ids}')
        else:
            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        cv2.imwrite(os.path.join(OUT, name), bgr)

    # robot at the start, arms hanging (home)
    mujoco.mj_resetData(m, d)
    arms(m, d, math.pi / 2)
    shot('robot_front.png', free_cam((0.0, 0.0, 0.55), 2.3, 150, -12))
    shot('robot_side.png', free_cam((0.0, 0.0, 0.55), 2.1, 90, -8))
    side = cv2.imread(os.path.join(OUT, 'robot_side.png'))
    cv2.imwrite(os.path.join(OUT, 'robot_side_crop.png'), side[160:660, 430:930])  # robot only, 500x500
    shot('room_top.png', 'top')
    shot('room_overview.png', 'overview')
    room_layout(os.path.join(OUT, 'room_top.png'), os.path.join(OUT, 'room_layout.png'))

    # at supply table 1 (red box), arms tucked: the view before a pick (staging pose of task_planner_core)
    arms(m, d, 2.3)
    place_base(m, d, 0.0, -2.8, -math.pi / 2)
    shot('at_supply_table.png', free_cam((0.0, -3.25, 0.55), 2.1, 255, -30))
    shot('headcam_supply.png', 'head_camera', overlay=True)

    # at the work table, facing its three place spots
    place_base(m, d, 3.8, 0.0, 0.0)
    shot('headcam_work.png', 'head_camera', overlay=True)
    shot('at_work_table.png', free_cam((4.3, 0.0, 0.55), 2.4, 90, -25))
    r.close()


if __name__ == '__main__':
    main()
