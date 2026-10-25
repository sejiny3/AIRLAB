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

    # at the supply table, arms tucked: the view before a pick
    arms(m, d, 2.3)
    place_base(m, d, -0.15, -1.55, -math.pi / 2)
    shot('at_supply_table.png', free_cam((-0.15, -2.0, 0.55), 2.1, 255, -30))
    shot('headcam_supply.png', 'head_camera', overlay=True)

    # at the work table, facing the place pad
    place_base(m, d, 1.20, 0.0, 0.0)
    shot('headcam_work.png', 'head_camera', overlay=True)
    shot('at_work_table.png', free_cam((1.7, 0.0, 0.55), 2.4, 90, -25))
    r.close()


if __name__ == '__main__':
    main()
