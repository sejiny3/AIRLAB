#!/usr/bin/env python3
"""Drive the robot through a fixed tour of the room so slam_toolbox can build a map.

This is a mapping helper, not a navigator: it steers with /ground_truth/odom
(turn in place toward the next waypoint, then drive with heading correction)
along hand-picked waypoints that avoid the obstacles in models/scene.xml.
"""

import math

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node

# World-frame waypoints: east room loop, then through the partition doorway
# (y in [-0.4, 0.8]) into the west room and back to the start.
TOUR = [
    (1.2, 1.2), (3.2, 1.2), (3.2, -1.3), (1.6, -0.9), (0.0, -1.2),
    (-0.5, 0.2), (-1.85, 0.2), (-1.85, 1.9), (-1.85, -1.5), (-1.85, 0.2),
    (-0.3, 0.2), (0.0, 0.0),
]
MAX_V, MAX_W = 0.3, 0.8
REACHED = 0.12      # m
ALIGNED = 0.15      # rad: start driving once heading error is below this


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


class Explorer(Node):
    def __init__(self):
        super().__init__('explore_waypoints')
        self.pose = None
        self.idx = 0
        self.create_subscription(Odometry, '/ground_truth/odom', self._on_odom, 10)
        self.cmd = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_timer(0.05, self._tick)

    def _on_odom(self, msg):
        q = msg.pose.pose.orientation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        self.pose = (msg.pose.pose.position.x, msg.pose.pose.position.y, yaw)

    def _tick(self):
        if self.pose is None:
            return
        twist = Twist()
        if self.idx >= len(TOUR):
            self.cmd.publish(twist)
            self.get_logger().info('tour finished')
            raise SystemExit
        x, y, yaw = self.pose
        gx, gy = TOUR[self.idx]
        dist = math.hypot(gx - x, gy - y)
        if dist < REACHED:
            self.get_logger().info(f'reached waypoint {self.idx + 1}/{len(TOUR)} ({gx:.2f}, {gy:.2f})')
            self.idx += 1
            self.cmd.publish(twist)
            return
        err = wrap(math.atan2(gy - y, gx - x) - yaw)
        twist.angular.z = max(-MAX_W, min(MAX_W, 2.0 * err))
        if abs(err) < ALIGNED:
            twist.linear.x = min(MAX_V, 0.6 * dist)
        self.cmd.publish(twist)


def main():
    rclpy.init()
    node = Explorer()
    try:
        rclpy.spin(node)
    except (SystemExit, KeyboardInterrupt):
        pass
    finally:
        node.cmd.publish(Twist())
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
