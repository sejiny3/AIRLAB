"""Bridge smoke test: waves both arms and opens/closes the grippers via /joint_commands."""

import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

ELBOW = math.pi / 2


class ArmDemo(Node):
    def __init__(self):
        super().__init__('arm_demo')
        self.declare_parameter('duration', 10.0)
        self.duration = self.get_parameter('duration').value
        self.pub = self.create_publisher(JointState, '/joint_commands', 10)
        self.start = None
        self.timer = self.create_timer(0.02, self._tick)

    def _tick(self):
        now = self.get_clock().now().nanoseconds * 1e-9
        if self.start is None:
            self.start = now
        t = now - self.start
        s = math.sin(2 * math.pi * 0.25 * t)
        grip = 0.5 * (1 + math.sin(2 * math.pi * 0.5 * t))  # 0 (closed) .. 1 (open)

        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        # Mirror-symmetric motion: joint1/joint2/finger ranges are mirrored between arms.
        msg.name = [
            'openarm_left_joint1', 'openarm_left_joint2', 'openarm_left_joint4', 'openarm_left_finger_joint1',
            'openarm_right_joint1', 'openarm_right_joint2', 'openarm_right_joint4', 'openarm_right_finger_joint1',
        ]
        msg.position = [
            -0.6 * (1 + s), -0.3, ELBOW + 0.4 * s, 0.7 * grip,
            0.6 * (1 + s), 0.3, ELBOW + 0.4 * s, -0.7 * grip,
        ]
        self.pub.publish(msg)

        if t > self.duration:
            msg.position = [0.0, 0.0, ELBOW, 0.0, 0.0, 0.0, ELBOW, 0.0]
            self.pub.publish(msg)
            self.get_logger().info('demo finished, arms back to home')
            raise SystemExit


def main():
    rclpy.init()
    node = ArmDemo()
    try:
        rclpy.spin(node)
    except (SystemExit, KeyboardInterrupt):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
