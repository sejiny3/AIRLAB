#!/usr/bin/env python3
"""Send Nav2 goals one after another and report the final error against the simulator's ground truth.

  ros2 run unbolt_navigation nav_goal_test.py --ros-args -p use_sim_time:=true
"""

import math
import time

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from nav_msgs.msg import Odometry

# (x, y, yaw) in the map frame. The SLAM map frame coincides with the world
# frame because the robot starts at the world origin facing +x.
GOALS = [
    (3.0, -1.4, -math.pi / 2),   # east side, past the table and the pillar
    (-1.9, 1.6, math.pi / 2),    # west room, through the doorway
    (0.0, 0.0, 0.0),             # back home
]


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def main():
    rclpy.init()
    nav = BasicNavigator()
    truth = {}
    nav.create_subscription(Odometry, '/ground_truth/odom', lambda m: truth.update(pose=m.pose.pose), 10)

    nav.waitUntilNav2Active()
    ok = 0
    for gx, gy, gyaw in GOALS:
        goal = PoseStamped()
        goal.header.frame_id = 'map'
        goal.header.stamp = nav.get_clock().now().to_msg()
        goal.pose.position.x, goal.pose.position.y = gx, gy
        goal.pose.orientation.z, goal.pose.orientation.w = math.sin(gyaw / 2), math.cos(gyaw / 2)

        start = time.time()
        nav.goToPose(goal)
        while not nav.isTaskComplete():
            rclpy.spin_once(nav, timeout_sec=0.1)
        result = nav.getResult()
        for _ in range(10):
            rclpy.spin_once(nav, timeout_sec=0.05)

        p = truth['pose']
        err = math.hypot(p.position.x - gx, p.position.y - gy)
        yerr = math.degrees(abs(math.atan2(math.sin(yaw_of(p.orientation) - gyaw), math.cos(yaw_of(p.orientation) - gyaw))))
        status = {TaskResult.SUCCEEDED: 'SUCCEEDED', TaskResult.CANCELED: 'CANCELED', TaskResult.FAILED: 'FAILED'}.get(result, str(result))
        nav.get_logger().info(
            f'goal ({gx:+.2f}, {gy:+.2f}): {status} in {time.time() - start:.1f} s wall, '
            f'true position error {err * 100:.1f} cm, heading error {yerr:.1f} deg')
        ok += result == TaskResult.SUCCEEDED

    nav.get_logger().info(f'{ok}/{len(GOALS)} goals succeeded')
    nav.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
