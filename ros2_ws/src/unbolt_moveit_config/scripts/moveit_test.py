#!/usr/bin/env python3
"""Exercise MoveIt end to end through the MuJoCo bridge and measure accuracy.

Steps: both arms -> 'ready', left grasp frame -> two Cartesian pose goals, left gripper
open/close, both arms -> 'home'. Every motion is planned AND executed by move_group;
reached poses are read back from TF (driven by the simulator's /joint_states).

  ros2 run unbolt_moveit_config moveit_test.py --ros-args -p use_sim_time:=true
"""

import math
import time

import rclpy
from geometry_msgs.msg import PoseStamped
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, JointConstraint, MoveItErrorCodes, OrientationConstraint, PositionConstraint
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import JointState
from shape_msgs.msg import SolidPrimitive
import tf2_ros

READY = {'openarm_left_joint1': -0.6, 'openarm_left_joint2': -0.1, 'openarm_left_joint4': 1.2,
         'openarm_right_joint1': 0.6, 'openarm_right_joint2': 0.1, 'openarm_right_joint4': 1.2}
HOME = {f'openarm_{s}_joint{i}': (1.5708 if i == 4 else 0.0) for s in ('left', 'right') for i in range(1, 8)}
ERR = {v: k for k, v in MoveItErrorCodes.__dict__.items() if isinstance(v, int) and k.isupper()}


class MoveItTest(Node):
    def __init__(self):
        super().__init__('moveit_test')
        self.client = ActionClient(self, MoveGroup, '/move_action')
        self.tf = tf2_ros.Buffer()
        self.tfl = tf2_ros.TransformListener(self.tf, self)
        self.joints = {}
        self.create_subscription(JointState, '/joint_states',
                                 lambda m: self.joints.update(zip(m.name, m.position)), 10)

    def wait(self, sec):
        end = time.time() + sec
        while time.time() < end:
            rclpy.spin_once(self, timeout_sec=0.02)

    def move(self, group, constraints, label):
        goal = MoveGroup.Goal()
        req = goal.request
        req.group_name = group
        req.num_planning_attempts = 5
        req.allowed_planning_time = 5.0
        req.max_velocity_scaling_factor = 0.5
        req.max_acceleration_scaling_factor = 0.5
        req.start_state.is_diff = True
        req.goal_constraints = [constraints]
        goal.planning_options.planning_scene_diff.is_diff = True
        goal.planning_options.planning_scene_diff.robot_state.is_diff = True
        goal.planning_options.plan_only = False
        goal.planning_options.replan = True
        goal.planning_options.replan_attempts = 2

        t0 = time.time()
        send = self.client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send)
        handle = send.result()
        if not handle.accepted:
            self.get_logger().error(f'{label}: goal rejected')
            return False
        res = handle.get_result_async()
        rclpy.spin_until_future_complete(self, res)
        result = res.result().result
        code = result.error_code.val
        self.wait(0.5)
        self.get_logger().info(
            f'{label}: {ERR.get(code, code)} (planning {result.planning_time:.2f} s, total {time.time() - t0:.1f} s wall)')
        return code == MoveItErrorCodes.SUCCESS

    @staticmethod
    def joint_goal(targets, tol=0.002):
        c = Constraints()
        for name, pos in targets.items():
            c.joint_constraints.append(JointConstraint(joint_name=name, position=pos, tolerance_above=tol,
                                                       tolerance_below=tol, weight=1.0))
        return c

    @staticmethod
    def pose_goal(link, pose: PoseStamped, pos_tol=0.005, rot_tol=0.02):
        c = Constraints()
        box = SolidPrimitive(type=SolidPrimitive.SPHERE, dimensions=[pos_tol])
        pc = PositionConstraint(header=pose.header, link_name=link, weight=1.0)
        pc.constraint_region.primitives.append(box)
        pc.constraint_region.primitive_poses.append(pose.pose)
        oc = OrientationConstraint(header=pose.header, link_name=link, orientation=pose.pose.orientation,
                                   absolute_x_axis_tolerance=rot_tol, absolute_y_axis_tolerance=rot_tol,
                                   absolute_z_axis_tolerance=rot_tol, weight=1.0)
        c.position_constraints.append(pc)
        c.orientation_constraints.append(oc)
        return c

    def link_pose(self, link):
        return self.tf.lookup_transform('base_footprint', link, Time()).transform

    def joint_error(self, targets):
        return max(abs(self.joints[n] - v) for n, v in targets.items())


def main():
    rclpy.init()
    t = MoveItTest()
    t.client.wait_for_server()
    t.wait(2.0)
    ok = 0

    ready = dict(HOME, **READY)
    ok += t.move('both_arms', t.joint_goal(ready), 'both_arms -> ready')
    t.get_logger().info(f'   max joint error vs target: {t.joint_error(ready):.4f} rad')

    # Cartesian goals for the left grasp frame relative to 'ready', keeping its orientation.
    # (From 'ready' the hand can only reach ~6 cm further forward at this orientation.)
    start = t.link_pose('openarm_left_grasp_frame')
    for dx, dz in ((0.05, -0.05), (-0.05, -0.08)):
        target = PoseStamped()
        target.header.frame_id = 'base_footprint'
        target.pose.position.x = start.translation.x + dx
        target.pose.position.y = start.translation.y
        target.pose.position.z = start.translation.z + dz
        target.pose.orientation = start.rotation
        ok += t.move('left_arm', t.pose_goal('openarm_left_grasp_frame', target),
                     f'left_arm -> pose goal (dx {dx * 100:+.0f} cm, dz {dz * 100:+.0f} cm)')
        reached = t.link_pose('openarm_left_grasp_frame')
        dp = math.dist((reached.translation.x, reached.translation.y, reached.translation.z),
                       (target.pose.position.x, target.pose.position.y, target.pose.position.z))
        q1, q2 = reached.rotation, target.pose.orientation
        dot = abs(q1.x * q2.x + q1.y * q2.y + q1.z * q2.z + q1.w * q2.w)
        t.get_logger().info(f'   grasp frame error: position {dp * 1000:.1f} mm, '
                            f'orientation {math.degrees(2 * math.acos(min(1.0, dot))):.2f} deg')

    ok += t.move('left_gripper', t.joint_goal({'openarm_left_finger_joint1': 0.6}, 0.02), 'left_gripper -> open')
    t.get_logger().info(f'   finger: {t.joints["openarm_left_finger_joint1"]:.3f} (target 0.6)')
    ok += t.move('left_gripper', t.joint_goal({'openarm_left_finger_joint1': 0.0}, 0.02), 'left_gripper -> closed')
    t.get_logger().info(f'   finger: {t.joints["openarm_left_finger_joint1"]:.3f} (target 0.0)')

    ok += t.move('both_arms', t.joint_goal(HOME), 'both_arms -> home')
    t.get_logger().info(f'   max joint error vs target: {t.joint_error(HOME):.4f} rad')

    t.get_logger().info(f'{ok}/6 motions succeeded')
    t.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
