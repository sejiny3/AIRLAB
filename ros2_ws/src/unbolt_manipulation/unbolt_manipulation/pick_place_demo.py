"""End-to-end demo: take the red box from the supply table to the place pad on the work table.

  ros2 launch unbolt_manipulation bringup.launch.py
  ros2 run unbolt_manipulation pick_place_demo --ros-args -p use_sim_time:=true

Sequence: tuck arms -> Nav2 to the supply table -> servo on marker 7 -> pick ->
back off -> Nav2 to the work table -> servo on marker 3 -> place -> back off.
At the end the box's true pose (from the simulator) is compared with the pad.
"""

import math
import time

import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry

from unbolt_manipulation.skills import GRASP_XY, RobotSkills

BOX_MARKER, PAD_MARKER = 7, 3
SUPPLY_STAGING = (-0.15, -1.55, -math.pi / 2)  # facing the supply table, box ~0.8 m ahead
WORK_STAGING = (1.20, 0.0, 0.0)                # facing the work table, pad ~0.8 m ahead
PAD_WORLD = (2.0, -0.15)                       # place pad centre (models/scene.xml)


def main():
    rclpy.init()
    s = RobotSkills()
    box, robot = {}, {}
    s.node.create_subscription(PoseStamped, '/ground_truth/red_box', lambda m: box.update(p=m.pose.position), 10)
    s.node.create_subscription(Odometry, '/ground_truth/odom', lambda m: robot.update(p=m.pose.pose), 10)
    t0 = time.time()
    steps = []

    def step(name, ok):
        steps.append((name, ok, time.time() - t0))
        where = ''
        if 'p' in robot:  # ground truth, for the log only (the skills never use it)
            p = robot['p']
            where = f'  [robot at ({p.position.x:.2f}, {p.position.y:.2f}, ' \
                    f'{math.degrees(2 * math.atan2(p.orientation.z, p.orientation.w)):.0f} deg)]'
        s.log.info(f'[{time.time() - t0:6.1f} s] {name}: {"OK" if ok else "FAILED"}{where}')
        return ok

    try:
        s.wait_ready()
        ok = (step('arms tuck', s.move_arms('tuck'))
              and step('navigate to supply table', s.navigate(*SUPPLY_STAGING)))
        if ok:
            first = s.marker_in_base(BOX_MARKER, samples=3)
            arm = 'left' if first is not None and first[0][1] > 0 else 'right'
            ok = (step(f'servo to box marker ({arm} arm)', s.servo_to_marker(BOX_MARKER, GRASP_XY[arm]))
                  and step('pick red box', s.pick(BOX_MARKER))
                  and step('back off', s.drive_straight(-0.35))
                  and step('navigate to work table', s.navigate(*WORK_STAGING))
                  and step('servo to place pad', s.servo_to_marker(PAD_MARKER, GRASP_XY[s.holding]))
                  and step('place red box', s.place(PAD_MARKER))
                  and step('back off', s.drive_straight(-0.35)))
        time.sleep(1.0)
        if 'p' in box:
            p = box['p']
            err = math.hypot(p.x - PAD_WORLD[0], p.y - PAD_WORLD[1])
            s.log.info(f'red box ends at ({p.x:.3f}, {p.y:.3f}, {p.z:.3f}); '
                       f'{err * 100:.1f} cm from the pad centre, {"on" if p.z > 0.66 else "NOT on"} the table')
        s.log.info(f'demo {"SUCCEEDED" if ok else "FAILED"} in {time.time() - t0:.0f} s wall')
    finally:
        s.shutdown()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
