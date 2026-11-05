"""ROS 2 node that picks with the learned policy: ros2 run airlab_vla vla_pick

Subscribed:
  /vla/pick                std_msgs/String       instruction, e.g. "pick up the red box": start a pick with
                                                 the right arm; or JSON {"instruction": ..., "arm": "left"}
  /vla/cancel              std_msgs/Empty        stop the pick (the arm holds where it is)
  /camera/image_raw        sensor_msgs/Image     head camera (1280x720, area-resized to the policy's size)
  /wrist_camera/image_raw  sensor_msgs/Image     right wrist camera (bridge wrist_camera_rate > 0)
  /wrist_camera_left/image_raw sensor_msgs/Image left wrist camera
  /joint_states            sensor_msgs/JointState
Published:
  /joint_commands          sensor_msgs/JointState  arm + finger targets of the picking arm, CONTROL_HZ
  /vla/result              std_msgs/String         JSON {ok, steps, finger, reason} when a pick ends
  /vla/status              std_msgs/String         JSON per step {step, done, finger, latency} (for the dashboard)
  /vla/head_input          sensor_msgs/Image       the head image the policy was given at each step
                                                   (no marker overlay: the policy never sees marker poses)
  /vla/wrist_input         sensor_msgs/Image       the wrist image it was given

The policy runs only the pick itself; the robot must already stand in front of the object
with it roughly at GRASP_XY of the picking arm (the task planner's line-up does that).

The policy was trained on the right arm. A left-arm pick runs it through the mirror
(mirror.MirroredRunner): images flipped left-right, joints mapped with sim.MIRROR, the words
left and right swapped. /vla/head_input and /vla/wrist_input then show the flipped images.

With the parameter server set, the policy is π0.5 on that server (remote.py) instead of the
small policy here: head 224x126, wrist 224x224 (bridge wrist_camera_size).
"""

import array
import json
import os

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, JointState
from std_msgs.msg import Empty, String

from airlab_vla.mirror import MirroredRunner
from airlab_vla.sim import CAMERAS, CONTROL_HZ, MIRROR, arm_joints

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
        self.declare_parameter('server', '')      # π0.5 policy server (pi05/serve_pi05.py); empty = the small policy
        p = lambda n: self.get_parameter(n).value
        self.timeout, self.done_steps = p('timeout'), p('done_steps')
        self.cams = CAMERAS['pi05' if p('server') else 'small']
        self.runner, self.no_runner = None, 'no trained policy'
        if p('server'):
            try:
                from airlab_vla.remote import RemoteRunner
                self.runner = RemoteRunner(p('server'))
                self.get_logger().info(f'picking with the π0.5 server at {p("server")}')
            except ImportError as e:
                self.no_runner = f'{e.name} is missing: pip3 install --user websockets msgpack'
                self.get_logger().error(self.no_runner)
        else:
            try:
                from airlab_vla.runner import PolicyRunner  # torch import takes a few seconds
                self.runner = PolicyRunner(p('policy'), threads=p('threads'))
                self.get_logger().info(f'policy loaded from {p("policy")}')
            except FileNotFoundError:
                self.get_logger().error(f'no trained policy at {p("policy")}: run "ros2 run airlab_vla record" and '
                                        '"ros2 run airlab_vla train" first')
        self.head = None
        self.wrists = {'right': None, 'left': None}
        self.arm, self.joint_names, self.policy = 'right', arm_joints('right'), self.runner
        self.joints = {}
        self.create_subscription(Image, '/camera/image_raw', self._on_head, 2)
        self.create_subscription(Image, '/wrist_camera/image_raw', lambda m: self._on_wrist('right', m), 2)
        self.create_subscription(Image, '/wrist_camera_left/image_raw', lambda m: self._on_wrist('left', m), 2)
        self.create_subscription(JointState, '/joint_states', lambda m: self.joints.update(zip(m.name, m.position)), 10)
        self.create_subscription(String, '/vla/pick', self._on_pick, 10)
        self.create_subscription(Empty, '/vla/cancel', lambda _: self._finish(False, 'cancelled'), 10)
        self.cmd_pub = self.create_publisher(JointState, '/joint_commands', 10)
        self.result_pub = self.create_publisher(String, '/vla/result', 10)
        self.status_pub = self.create_publisher(String, '/vla/status', 10)
        self.head_input_pub = self.create_publisher(Image, '/vla/head_input', 2)
        self.wrist_input_pub = self.create_publisher(Image, '/vla/wrist_input', 2)
        self.active = False
        self.create_timer(1.0 / CONTROL_HZ, self._tick)

    def _on_head(self, msg):
        self.head = cv2.resize(image_array(msg), self.cams['head'], interpolation=cv2.INTER_AREA)

    def _on_wrist(self, arm, msg):
        img = image_array(msg)
        width, height = self.cams['wrist']
        if img.shape[:2] != (height, width):
            img = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
        self.wrists[arm] = img

    def _on_pick(self, msg):
        if self.active:
            self.get_logger().warn('a pick is already running')
            return
        if self.runner is None:
            self._publish(self.result_pub, ok=False, steps=0, finger=0.0, reason=self.no_runner)
            return
        instruction, arm = msg.data, 'right'
        if msg.data.lstrip().startswith('{'):
            try:
                req = json.loads(msg.data)
                instruction, arm = str(req['instruction']), str(req.get('arm', 'right'))
            except (ValueError, KeyError) as e:
                self._publish(self.result_pub, ok=False, steps=0, finger=0.0, reason=f'bad request: {e}')
                return
        if arm not in ('right', 'left'):
            self._publish(self.result_pub, ok=False, steps=0, finger=0.0, reason=f'unknown arm {arm!r}')
            return
        missing = [n for n, v in (('head camera', self.head), (f'{arm} wrist camera', self.wrists[arm])) if v is None]
        missing += ['joint states'] if any(j not in self.joints for j in arm_joints(arm)) else []
        if missing:
            self._publish(self.result_pub, ok=False, steps=0, finger=0.0, reason='no ' + ', '.join(missing))
            return
        self.arm, self.joint_names = arm, arm_joints(arm)
        # the policy only knows the right arm: the left one sees and moves through the mirror
        self.policy = self.runner if arm == 'right' else MirroredRunner(self.runner)
        self.policy.reset(instruction)
        self.step, self.streak = 0, 0
        self.finger_target = -1.0
        self.t0 = self.get_clock().now()
        self.active = True
        self.get_logger().info(f'VLA pick with the {arm} arm: "{instruction}"')

    def _tick(self):
        if not self.active:
            return
        state = np.array([self.joints[j] for j in self.joint_names], np.float32)
        head, wrist = self.head, self.wrists[self.arm]
        try:
            target = self.policy.act(head, wrist, state)
        except RuntimeError as e:  # a remote policy that stopped answering
            self._finish(False, f'policy server: {e}')
            return
        if target is None:  # waiting for the server: the arm holds its last target
            if self._timed_out():
                self._finish(False, 'timeout')
            return
        action, done = target
        mirrored = self.arm == 'left'
        self._publish_image(self.head_input_pub, head[:, ::-1] if mirrored else head)
        self._publish_image(self.wrist_input_pub, wrist[:, ::-1] if mirrored else wrist)
        cmd = JointState(name=list(self.joint_names), position=[float(a) for a in action])
        cmd.header.stamp = self.get_clock().now().to_msg()
        self.cmd_pub.publish(cmd)
        self.finger_target = float(action[-1]) * (float(MIRROR[-1]) if mirrored else 1.0)  # as for the right hand
        self.step += 1
        self.streak = self.streak + 1 if done > 0.5 else 0
        self._publish(self.status_pub, step=self.step, done=round(done, 3), finger=round(float(state[-1]), 3),
                      latency=self.policy.latency)
        if self.streak >= self.done_steps:
            self._finish(True, 'policy finished')
        elif self._timed_out():
            self._finish(False, 'timeout')

    def _timed_out(self):
        return (self.get_clock().now() - self.t0).nanoseconds * 1e-9 > self.timeout

    def _finish(self, policy_done, reason):
        if not self.active:
            return
        self.active = False
        # Held = the hand was told to close but stopped short of closed. An open hand also has a
        # large |finger|, so the commanded target matters (the policy can say "done" too early).
        finger = abs(self.joints.get(self.joint_names[-1], 0.0))
        closing = self.finger_target > CLOSING
        ok = policy_done and closing and finger > HOLDING_MIN
        if policy_done and not closing:
            reason = f'policy said done without closing the hand (target {self.finger_target:.2f})'
        elif policy_done and not ok:
            reason = f'gripper closed on nothing (finger {finger:.3f})'
        self._publish(self.result_pub, ok=ok, steps=self.step, finger=round(finger, 3), reason=reason, arm=self.arm)
        self.get_logger().info(f'VLA pick ({self.arm} arm) {"succeeded" if ok else "FAILED"} after {self.step} steps: {reason}')

    def _publish_image(self, pub, img):
        img = np.ascontiguousarray(img)
        msg = Image(height=img.shape[0], width=img.shape[1], encoding='rgb8', step=img.shape[1] * 3)
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.data = array.array('B', img.tobytes())  # bytes would be validated element by element
        pub.publish(msg)

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
