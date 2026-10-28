"""ROS 2 node that picks with the learned policy: ros2 run airlab_vla vla_pick

Subscribed:
  /vla/pick                std_msgs/String       instruction, e.g. "pick up the red box": start a pick
  /vla/cancel              std_msgs/Empty        stop the pick (the arm holds where it is)
  /camera/image_raw        sensor_msgs/Image     head camera (1280x720, area-resized to 128x72)
  /wrist_camera/image_raw  sensor_msgs/Image     right wrist camera (96x96; bridge wrist_camera_rate > 0)
  /joint_states            sensor_msgs/JointState
Published:
  /joint_commands          sensor_msgs/JointState  right arm + finger targets, CONTROL_HZ
  /vla/result              std_msgs/String         JSON {ok, steps, finger, reason} when a pick ends
  /vla/status              std_msgs/String         JSON per step {step, done, finger} (for the dashboard)

The policy runs only the pick itself; the robot must already stand in front of the object
with it roughly at GRASP_XY['right'] (the task planner's line-up does that).
"""

import json
import os

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, JointState
from std_msgs.msg import Empty, String

from airlab_vla.sim import CONTROL_HZ, HEAD_SIZE, JOINTS, WRIST_SIZE

HOLDING_MIN = 0.06  # |finger| above this after closing = something is in the hand (skills.py)
CLOSING = -0.15     # finger target above this = the policy is closing the hand (open is -0.6, closed 0)


def image_array(msg):
    return np.frombuffer(msg.data, np.uint8).reshape(msg.height, msg.width, 3)


class VlaPick(Node):
    def __init__(self):
        super().__init__('vla_pick')
        self.declare_parameter('policy', os.path.expanduser('~/airlab_vla/policy.pt'))
        self.declare_parameter('timeout', 15.0)   # [s] of simulated time
        self.declare_parameter('done_steps', 3)   # "done" this many steps in a row ends the pick
        self.declare_parameter('threads', 4)
        p = lambda n: self.get_parameter(n).value
        self.timeout, self.done_steps = p('timeout'), p('done_steps')
        self.runner = None
        try:
            from airlab_vla.runner import PolicyRunner  # torch import takes a few seconds
            self.runner = PolicyRunner(p('policy'), threads=p('threads'))
            self.get_logger().info(f'policy loaded from {p("policy")}')
        except FileNotFoundError:
            self.get_logger().error(f'no trained policy at {p("policy")}: run "ros2 run airlab_vla record" and '
                                    '"ros2 run airlab_vla train" first')
        self.head = self.wrist = None
        self.joints = {}
        self.create_subscription(Image, '/camera/image_raw', self._on_head, 2)
        self.create_subscription(Image, '/wrist_camera/image_raw', self._on_wrist, 2)
        self.create_subscription(JointState, '/joint_states', lambda m: self.joints.update(zip(m.name, m.position)), 10)
        self.create_subscription(String, '/vla/pick', self._on_pick, 10)
        self.create_subscription(Empty, '/vla/cancel', lambda _: self._finish(False, 'cancelled'), 10)
        self.cmd_pub = self.create_publisher(JointState, '/joint_commands', 10)
        self.result_pub = self.create_publisher(String, '/vla/result', 10)
        self.status_pub = self.create_publisher(String, '/vla/status', 10)
        self.active = False
        self.create_timer(1.0 / CONTROL_HZ, self._tick)

    def _on_head(self, msg):
        self.head = cv2.resize(image_array(msg), HEAD_SIZE, interpolation=cv2.INTER_AREA)

    def _on_wrist(self, msg):
        img = image_array(msg)
        if img.shape[:2] != (WRIST_SIZE[1], WRIST_SIZE[0]):
            img = cv2.resize(img, WRIST_SIZE, interpolation=cv2.INTER_AREA)
        self.wrist = img

    def _on_pick(self, msg):
        if self.active:
            self.get_logger().warn('a pick is already running')
            return
        if self.runner is None:
            self._publish(self.result_pub, ok=False, steps=0, finger=0.0, reason='no trained policy')
            return
        missing = [n for n, v in (('head camera', self.head), ('wrist camera', self.wrist)) if v is None]
        missing += ['joint states'] if any(j not in self.joints for j in JOINTS) else []
        if missing:
            self._publish(self.result_pub, ok=False, steps=0, finger=0.0, reason='no ' + ', '.join(missing))
            return
        self.runner.reset(msg.data)
        self.step, self.streak = 0, 0
        self.finger_target = -1.0
        self.t0 = self.get_clock().now()
        self.active = True
        self.get_logger().info(f'VLA pick: "{msg.data}"')

    def _tick(self):
        if not self.active:
            return
        state = np.array([self.joints[j] for j in JOINTS], np.float32)
        action, done = self.runner.act(self.head, self.wrist, state)
        cmd = JointState(name=list(JOINTS), position=[float(a) for a in action])
        cmd.header.stamp = self.get_clock().now().to_msg()
        self.cmd_pub.publish(cmd)
        self.finger_target = float(action[-1])
        self.step += 1
        self.streak = self.streak + 1 if done > 0.5 else 0
        self._publish(self.status_pub, step=self.step, done=round(done, 3), finger=round(float(state[-1]), 3))
        if self.streak >= self.done_steps:
            self._finish(True, 'policy finished')
        elif (self.get_clock().now() - self.t0).nanoseconds * 1e-9 > self.timeout:
            self._finish(False, 'timeout')

    def _finish(self, policy_done, reason):
        if not self.active:
            return
        self.active = False
        # Held = the hand was told to close but stopped short of closed. An open hand also has a
        # large |finger|, so the commanded target matters (the policy can say "done" too early).
        finger = abs(self.joints.get(JOINTS[-1], 0.0))
        closing = self.finger_target > CLOSING
        ok = policy_done and closing and finger > HOLDING_MIN
        if policy_done and not closing:
            reason = f'policy said done without closing the hand (target {self.finger_target:.2f})'
        elif policy_done and not ok:
            reason = f'gripper closed on nothing (finger {finger:.3f})'
        self._publish(self.result_pub, ok=ok, steps=self.step, finger=round(finger, 3), reason=reason)
        self.get_logger().info(f'VLA pick {"succeeded" if ok else "FAILED"} after {self.step} steps: {reason}')

    @staticmethod
    def _publish(pub, **fields):
        pub.publish(String(data=json.dumps(fields)))


def main():
    rclpy.init()
    node = VlaPick()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
