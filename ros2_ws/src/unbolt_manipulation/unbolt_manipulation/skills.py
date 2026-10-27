"""Mobile manipulation skills for UNBOLT: navigate, servo to a marker, pick, place.

Each skill blocks until done and returns True/False (and logs why). They are meant
to be chained by a task script (pick_place_demo.py) or by the LLM task planner.

Geometry the skills rely on (all in base_footprint unless noted):
  - grasps approach forward, pitched GRASP_PITCH down, fingers closing along base y;
    the arms reach this best around GRASP_XY (from MoveIt IK probing).
  - tables are 0.65 m high; the arms are kept in 'tuck' while driving near them.
  - markers come from aruco_detector as TF frames aruco_<id> (z out of the face).
"""

import json
import math
import threading
import time

import numpy as np
import rclpy
from geometry_msgs.msg import Pose, PoseStamped, Twist
from moveit_msgs.action import ExecuteTrajectory, MoveGroup
from moveit_msgs.msg import (CollisionObject, Constraints, JointConstraint, MoveItErrorCodes,
                             OrientationConstraint, PlanningScene, PositionConstraint)
from moveit_msgs.srv import ApplyPlanningScene, GetCartesianPath
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from rclpy.time import Time
from sensor_msgs.msg import JointState
from shape_msgs.msg import SolidPrimitive
from std_msgs.msg import Empty, String
from std_srvs.srv import Trigger
import tf2_ros

BASE = 'base_footprint'
GRASP_PITCH = math.radians(15)        # approach axis pitched down
GRASP_HEIGHT = 0.015                  # grasp this far above the box centre: the hand's collision
                                      # model needs it to clear the table top (MoveIt IK probe)
GRASP_XY = {'left': (0.38, 0.15), 'right': (0.38, -0.15)}   # where the object should be, per arm
PRE_GRASP_BACK = 0.10                 # pre-grasp offset along -approach [m]
PRE_GRASP_UP = 0.04                   # and this much higher: MuJoCo's convex-hull hand is fatter than
                                      # MoveIt's mesh hand and could catch the table edge
GRASP_DEPTH = 0.01                    # fingertips (grasp frame) go this far past the box centre [m]
LIFT = 0.08                           # lift after grasping / height above the place spot [m]
BOX_HALF = 0.025                      # red box half size [m]
FINGER_OPEN = {'left': 0.6, 'right': -0.6}
HOLDING_MIN = 0.06                    # |finger angle| above this after closing = something is held

ARM_JOINTS = {s: [f'openarm_{s}_joint{i}' for i in range(1, 8)] for s in ('left', 'right')}
NAMED = {
    'home': {'joint4': 1.5708},
    'tuck': {'joint4': 2.3},
}


def quat_from_matrix(R):
    w = math.sqrt(max(0.0, 1.0 + R[0, 0] + R[1, 1] + R[2, 2])) / 2.0
    x = math.copysign(math.sqrt(max(0.0, 1.0 + R[0, 0] - R[1, 1] - R[2, 2])) / 2.0, R[2, 1] - R[1, 2])
    y = math.copysign(math.sqrt(max(0.0, 1.0 - R[0, 0] + R[1, 1] - R[2, 2])) / 2.0, R[0, 2] - R[2, 0])
    z = math.copysign(math.sqrt(max(0.0, 1.0 - R[0, 0] - R[1, 1] + R[2, 2])) / 2.0, R[1, 0] - R[0, 1])
    return x, y, z, w


def matrix_from_quat(q):
    x, y, z, w = q.x, q.y, q.z, q.w
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def grasp_rotation(yaw):
    """Grasp frame: x = approach (forward, pitched down), y = finger closing axis, rotated by yaw about z."""
    c, s = math.cos(GRASP_PITCH), math.sin(GRASP_PITCH)
    ry = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    cz, sz = math.cos(yaw), math.sin(yaw)
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


class RobotSkills:
    def __init__(self):
        self.node = rclpy.create_node('unbolt_skills', parameter_overrides=[
            rclpy.parameter.Parameter('use_sim_time', value=True)])
        self.log = self.node.get_logger()
        self.tf = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf, self.node)
        self.cmd_vel = self.node.create_publisher(Twist, '/cmd_vel', 10)
        self.joints = {}
        self.node.create_subscription(JointState, '/joint_states',
                                      lambda m: self.joints.update(zip(m.name, m.position)), 10)
        self.move_group = ActionClient(self.node, MoveGroup, '/move_action')
        self.execute = ActionClient(self.node, ExecuteTrajectory, '/execute_trajectory')
        self.cartesian = self.node.create_client(GetCartesianPath, '/compute_cartesian_path')
        self.scene = self.node.create_client(ApplyPlanningScene, '/apply_planning_scene')
        self.sim_reset = self.node.create_client(Trigger, '/mujoco_bridge/reset')
        # learned pick (unbolt_vla's vla_pick node), used by the task planner in VLA mode
        self.vla_pick_pub = self.node.create_publisher(String, '/vla/pick', 10)
        self.vla_cancel_pub = self.node.create_publisher(Empty, '/vla/cancel', 10)
        self.vla_result = None
        self.vla_done = threading.Event()
        self.node.create_subscription(String, '/vla/result', self._on_vla_result, 10)
        self.executor = MultiThreadedExecutor(num_threads=4)
        self.executor.add_node(self.node)
        threading.Thread(target=self.executor.spin, daemon=True).start()
        self.nav = BasicNavigator(node_name='unbolt_skills_navigator')
        self.holding = None  # arm currently holding an object
        self.last_marker_error = ''
        self.marker_memory = {}  # marker id -> (position, rotation, stamp ns) in odom
        self.held_marker = None  # marker of the object in the gripper
        self.cancel_event = threading.Event()  # set to stop base motions (navigate / servo / drive)

    # ------------------------------------------------------------- utilities
    def wait_ready(self, timeout=60.0):
        ok = self.move_group.wait_for_server(timeout_sec=timeout) and \
            self.execute.wait_for_server(timeout_sec=timeout) and \
            self.cartesian.wait_for_service(timeout_sec=timeout) and \
            self.scene.wait_for_service(timeout_sec=timeout)
        self.nav.waitUntilNav2Active()
        return ok

    @staticmethod
    def _wait(future, timeout=60.0):
        end = time.time() + timeout
        while not future.done():
            if time.time() > end:
                return None
            time.sleep(0.01)
        return future.result()

    def now(self):
        return self.node.get_clock().now()

    def base_pose_in(self, frame='odom'):
        t = self.tf.lookup_transform(frame, BASE, Time()).transform
        yaw = math.atan2(2 * (t.rotation.w * t.rotation.z + t.rotation.x * t.rotation.y),
                         1 - 2 * (t.rotation.y ** 2 + t.rotation.z ** 2))
        return t.translation.x, t.translation.y, yaw

    # ------------------------------------------------------------ perception
    def _remember_marker(self, marker_id):
        """Store the newest detection of a marker in the odom frame.

        Markers on tables and resting objects are static, so their last detection carried by
        odometry stays valid. The marker of the object in the gripper is not static: its
        detections show the hand, so it is never remembered (and its memory is dropped
        whenever the object is picked or placed)."""
        if marker_id == self.held_marker:
            return
        try:
            t = self.tf.lookup_transform('odom', f'aruco_{marker_id}', Time())  # at the detection's stamp
        except tf2_ros.TransformException:
            return
        stamp = Time.from_msg(t.header.stamp).nanoseconds
        if marker_id in self.marker_memory and self.marker_memory[marker_id][2] >= stamp:
            return
        tr = t.transform.translation
        self.marker_memory[marker_id] = (np.array([tr.x, tr.y, tr.z]), matrix_from_quat(t.transform.rotation), stamp)

    def forget_marker(self, marker_id):
        self.marker_memory.pop(marker_id, None)

    def remembered_marker_in_base(self, marker_id):
        """Last remembered marker pose re-expressed in the current base frame (odometry-corrected)."""
        self._remember_marker(marker_id)  # absorb a detection that is too old to count as "in view"
        if marker_id not in self.marker_memory:
            return None
        p_odom, R_odom, _ = self.marker_memory[marker_id]
        t = self.tf.lookup_transform(BASE, 'odom', Time()).transform
        R = matrix_from_quat(t.rotation)
        return R @ p_odom + np.array([t.translation.x, t.translation.y, t.translation.z]), R @ R_odom

    def marker_in_base(self, marker_id, max_age=0.6, samples=1, timeout=3.0, use_memory=False):
        """Mean marker pose in base_footprint over `samples` distinct detections, or None.

        With use_memory, fall back to the last detection carried along by odometry when the
        marker is currently out of view (e.g. hidden by the object in the gripper up close)."""
        m = self._marker_in_base(marker_id, max_age, samples, timeout)
        if m is not None:
            self._remember_marker(marker_id)
            return m
        if use_memory:
            m = self.remembered_marker_in_base(marker_id)
            if m is not None:
                self.log.info(f'marker {marker_id} not in view ({self.last_marker_error}); using odometry-tracked pose',
                              throttle_duration_sec=2.0)
            return m
        return None

    def _marker_in_base(self, marker_id, max_age, samples, timeout):
        frame = f'aruco_{marker_id}'
        seen, positions, rotations = set(), [], []
        end = time.time() + timeout
        self.last_marker_error = 'timeout'
        while len(positions) < samples and time.time() < end:
            try:
                t = self.tf.lookup_transform(BASE, frame, Time())
            except tf2_ros.TransformException as e:
                self.last_marker_error = f'{type(e).__name__}: {e}'
                time.sleep(0.05)
                continue
            stamp = Time.from_msg(t.header.stamp)
            age = (self.now() - stamp).nanoseconds * 1e-9
            if age > max_age:
                self.last_marker_error = f'stale detection ({age:.2f} s old)'
            if age <= max_age and stamp.nanoseconds not in seen:
                seen.add(stamp.nanoseconds)
                tr = t.transform.translation
                positions.append((tr.x, tr.y, tr.z))
                rotations.append(matrix_from_quat(t.transform.rotation))
            time.sleep(0.05)
        if not positions:
            return None
        return np.mean(positions, axis=0), rotations[-1]

    # ------------------------------------------------------------ base motion
    def navigate(self, x, y, yaw, timeout=120.0):
        goal = PoseStamped()
        goal.header.frame_id = 'map'
        goal.header.stamp = self.nav.get_clock().now().to_msg()
        goal.pose.position.x, goal.pose.position.y = float(x), float(y)
        goal.pose.orientation.z, goal.pose.orientation.w = math.sin(yaw / 2), math.cos(yaw / 2)
        self.log.info(f'navigate to ({x:.2f}, {y:.2f}, {math.degrees(yaw):.0f} deg)')
        self.nav.goToPose(goal)
        start = time.time()
        while not self.nav.isTaskComplete():
            if self.cancel_event.is_set():
                self.nav.cancelTask()
                self.log.warn('navigation cancelled')
                return False
            if time.time() - start > timeout:
                self.nav.cancelTask()
                self.log.error('navigation timed out')
                return False
            time.sleep(0.1)
        ok = self.nav.getResult() == TaskResult.SUCCEEDED
        if not ok:
            self.log.error(f'navigation failed: {self.nav.getResult()}')
        return ok

    def stop(self):
        self.cmd_vel.publish(Twist())

    def reset_world(self, timeout=10.0):
        """Put the robot, its arms and the objects back where the simulation starts.

        Besides the simulator reset, everything that remembers the old world is cleared:
        AMCL is re-initialised at the map origin (where the robot spawns), the costmaps
        drop obstacles seen from the old pose, and marker memory / held object are forgotten."""
        self.stop()
        if not self.sim_reset.wait_for_service(timeout_sec=timeout):
            self.log.error('reset: /mujoco_bridge/reset not available')
            return False
        res = self._wait(self.sim_reset.call_async(Trigger.Request()), timeout)
        if res is None or not res.success:
            self.log.error('reset: simulator reset failed')
            return False
        self.holding = None
        self.held_marker = None
        self.marker_memory.clear()
        self.set_support_surface(None)
        time.sleep(0.5)  # the bridge applies the reset on its next cycle; odometry restarts at 0
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.now().to_msg()
        pose.pose.orientation.w = 1.0
        self.nav.setInitialPose(pose)
        time.sleep(1.0)  # let AMCL take the new pose before the costmaps refill
        self.nav.clearAllCostmaps()
        self.log.info('world reset: robot at home, objects at their start')
        return True

    def drive_straight(self, distance, speed=0.12):
        """Drive forward (distance > 0) or back up (< 0) using odometry."""
        x0, y0, _ = self.base_pose_in()
        twist = Twist()
        twist.linear.x = math.copysign(speed, distance)
        while not self.cancel_event.is_set():
            x, y, _ = self.base_pose_in()
            if math.hypot(x - x0, y - y0) >= abs(distance):
                break
            self.cmd_vel.publish(twist)
            time.sleep(0.05)
        self.stop()
        time.sleep(0.3)
        return True

    def servo_to_marker(self, marker_id, target_xy, tol=0.01, timeout=60.0):
        """Visual servoing with the diff-drive base until the marker sits at target_xy (base frame).

        A diff drive controls distance and bearing to a point, which together fix the
        point's (x, y) in the base frame: v drives the range error, w the bearing error.
        """
        rd, phid = math.hypot(*target_xy), math.atan2(target_xy[1], target_xy[0])
        settled, misses, start = 0, 0, time.time()
        self.log.info(f'servo marker {marker_id} to base ({target_xy[0]:.2f}, {target_xy[1]:.2f})')
        while time.time() - start < timeout:
            if self.cancel_event.is_set():
                self.stop()
                self.log.warn('servo cancelled')
                return False
            m = self.marker_in_base(marker_id, max_age=0.5, timeout=0.5, use_memory=True)
            if m is None:
                self.stop()
                misses += 1
                if misses > 10:
                    self.log.error(f'lost marker {marker_id}: {self.last_marker_error}')
                    return False
                continue
            misses = 0
            x, y = m[0][0], m[0][1]
            r, phi = math.hypot(x, y), math.atan2(y, x)
            ex, ey = x - target_xy[0], y - target_xy[1]
            if abs(ex) < tol and abs(ey) < tol:
                settled += 1
                self.stop()
                if settled >= 3:
                    self.log.info(f'servo done: marker at ({x:.3f}, {y:.3f}), error ({ex * 1000:+.0f}, {ey * 1000:+.0f}) mm')
                    return True
                time.sleep(0.2)
                continue
            settled = 0
            twist = Twist()
            twist.angular.z = float(np.clip(1.2 * wrap(phi - phid), -0.3, 0.3))
            # drive only when roughly facing the right bearing, so the range loop doesn't fight the turn
            twist.linear.x = float(np.clip(0.8 * (r - rd), -0.08, 0.08)) if abs(wrap(phi - phid)) < 0.15 else 0.0
            self.cmd_vel.publish(twist)
            time.sleep(0.1)
        self.stop()
        self.log.error('servo timed out')
        return False

    # ------------------------------------------------------------ arm motion
    def _move_group(self, group, constraints, label, scaling=0.5):
        goal = MoveGroup.Goal()
        req = goal.request
        req.group_name = group
        req.num_planning_attempts = 5
        req.allowed_planning_time = 5.0
        req.max_velocity_scaling_factor = scaling
        req.max_acceleration_scaling_factor = scaling
        req.start_state.is_diff = True
        req.goal_constraints = [constraints]
        goal.planning_options.planning_scene_diff.is_diff = True
        goal.planning_options.planning_scene_diff.robot_state.is_diff = True
        goal.planning_options.replan = True
        goal.planning_options.replan_attempts = 2
        handle = self._wait(self.move_group.send_goal_async(goal))
        if handle is None or not handle.accepted:
            self.log.error(f'{label}: goal rejected')
            return False
        res = self._wait(handle.get_result_async(), timeout=90.0)
        code = res.result.error_code.val if res else None
        if code != MoveItErrorCodes.SUCCESS:
            self.log.error(f'{label}: MoveIt error {code}')
            return False
        return True

    def move_arms(self, name, arms=('left', 'right')):
        """Move arms to a named posture ('home' | 'tuck'); joints not listed are 0."""
        c = Constraints()
        for s in arms:
            for j in ARM_JOINTS[s]:
                short = j.split('_')[-1]
                c.joint_constraints.append(JointConstraint(joint_name=j, position=NAMED[name].get(short, 0.0),
                                                           tolerance_above=0.005, tolerance_below=0.005, weight=1.0))
        group = 'both_arms' if len(arms) == 2 else f'{arms[0]}_arm'
        self.log.info(f'arms -> {name}')
        return self._move_group(group, c, f'arms -> {name}')

    def set_gripper(self, arm, position):
        c = Constraints()
        c.joint_constraints.append(JointConstraint(joint_name=f'openarm_{arm}_finger_joint1', position=float(position),
                                                   tolerance_above=0.01, tolerance_below=0.01, weight=1.0))
        ok = self._move_group(f'{arm}_gripper', c, f'{arm} gripper -> {position:.2f}', scaling=1.0)
        time.sleep(0.5)
        return ok

    def move_to_pose(self, arm, position, rotation, label):
        ps = PoseStamped()
        ps.header.frame_id = BASE
        ps.pose.position.x, ps.pose.position.y, ps.pose.position.z = map(float, position)
        q = quat_from_matrix(rotation)
        ps.pose.orientation.x, ps.pose.orientation.y, ps.pose.orientation.z, ps.pose.orientation.w = q
        link = f'openarm_{arm}_grasp_frame'
        c = Constraints()
        pc = PositionConstraint(header=ps.header, link_name=link, weight=1.0)
        pc.constraint_region.primitives.append(SolidPrimitive(type=SolidPrimitive.SPHERE, dimensions=[0.005]))
        pc.constraint_region.primitive_poses.append(ps.pose)
        oc = OrientationConstraint(header=ps.header, link_name=link, orientation=ps.pose.orientation,
                                   absolute_x_axis_tolerance=0.03, absolute_y_axis_tolerance=0.03,
                                   absolute_z_axis_tolerance=0.03, weight=1.0)
        c.position_constraints.append(pc)
        c.orientation_constraints.append(oc)
        return self._move_group(f'{arm}_arm', c, label)

    def move_linear(self, arm, offset, label, avoid_collisions=True):
        """Straight-line move of the grasp frame by `offset` (base frame), keeping orientation."""
        link = f'openarm_{arm}_grasp_frame'
        t = self.tf.lookup_transform(BASE, link, Time()).transform
        target = Pose()
        target.position.x = t.translation.x + offset[0]
        target.position.y = t.translation.y + offset[1]
        target.position.z = t.translation.z + offset[2]
        target.orientation = t.rotation
        req = GetCartesianPath.Request()
        req.header.frame_id = BASE
        req.start_state.is_diff = True
        req.group_name = f'{arm}_arm'
        req.link_name = link
        req.waypoints = [target]
        req.max_step = 0.005
        req.jump_threshold = 0.0
        req.avoid_collisions = avoid_collisions
        res = self._wait(self.cartesian.call_async(req))
        if res is None or res.fraction < 0.98:
            self.log.error(f'{label}: cartesian path only {0 if res is None else res.fraction:.0%} feasible')
            return False
        goal = ExecuteTrajectory.Goal(trajectory=res.solution)
        handle = self._wait(self.execute.send_goal_async(goal))
        result = self._wait(handle.get_result_async(), timeout=60.0) if handle and handle.accepted else None
        if result is None or result.result.error_code.val != MoveItErrorCodes.SUCCESS:
            self.log.error(f'{label}: execution failed')
            return False
        return True

    def lower_until_contact(self, arm, depth, min_travel=0.03):
        """Lower the grasp frame by `depth`; stopping early counts as reaching the surface.

        The place height comes from the marker estimate, which can be centimetres off when the
        pad was last seen from afar (up close, the held object hides it). If the straight move
        is blocked after descending at least `min_travel`, the held object is resting on the
        table, as with a guarded move on a real arm."""
        link = f'openarm_{arm}_grasp_frame'
        z0 = self.tf.lookup_transform(BASE, link, Time()).transform.translation.z
        if self.move_linear(arm, (0.0, 0.0, -depth), 'lower', avoid_collisions=False):
            return True
        time.sleep(0.3)
        travelled = z0 - self.tf.lookup_transform(BASE, link, Time()).transform.translation.z
        if travelled >= min_travel:
            self.log.warn(f'lower: stopped {(depth - travelled) * 100:.1f} cm above the target on contact; releasing here')
            return True
        self.log.error(f'lower: blocked after only {travelled * 100:.1f} cm')
        return False

    def set_support_surface(self, top_z=None, center_xy=None):
        """Add (or with top_z=None remove) a table-top slab to the planning scene, in the base frame."""
        obj = CollisionObject()
        obj.header.frame_id = BASE
        obj.id = 'support_surface'
        if top_z is None:
            obj.operation = CollisionObject.REMOVE
        else:
            obj.operation = CollisionObject.ADD
            obj.primitives.append(SolidPrimitive(type=SolidPrimitive.BOX, dimensions=[0.5, 0.8, 0.04]))
            pose = Pose()
            pose.position.x, pose.position.y, pose.position.z = center_xy[0] + 0.12, center_xy[1], top_z - 0.02
            pose.orientation.w = 1.0
            obj.primitive_poses.append(pose)
        scene = PlanningScene(is_diff=True)
        scene.world.collision_objects.append(obj)
        res = self._wait(self.scene.call_async(ApplyPlanningScene.Request(scene=scene)))
        return bool(res and res.success)

    def finger(self, arm):
        return abs(self.joints.get(f'openarm_{arm}_finger_joint1', 0.0))

    # ------------------------------------------------------------ pick & place
    def _grasp_yaw(self, R_marker):
        """Rotate the grasp about z so the fingers close on a pair of box faces (within +-45 deg)."""
        ax = R_marker[:, 0]
        yaw = math.atan2(ax[1], ax[0])
        return (yaw + math.pi / 4) % (math.pi / 2) - math.pi / 4

    def pick(self, marker_id):
        m = self.marker_in_base(marker_id, samples=5, use_memory=True)
        if m is None:
            self.log.error(f'pick: marker {marker_id} not visible')
            return False
        p_marker, R = m
        center = p_marker - BOX_HALF * R[:, 2]  # marker is on the top face; its z axis points up
        arm = 'left' if center[1] > 0 else 'right'
        yaw = self._grasp_yaw(R)
        Rg = grasp_rotation(yaw)
        approach = Rg[:, 0]
        self.log.info(f'pick marker {marker_id} with {arm} arm: box at ({center[0]:.3f}, {center[1]:.3f}, '
                      f'{center[2]:.3f}), grasp yaw {math.degrees(yaw):+.1f} deg')

        grasp = center + GRASP_DEPTH * approach + np.array([0.0, 0.0, GRASP_HEIGHT])
        self.set_support_surface(center[2] - BOX_HALF, center[:2])
        pre_offset = PRE_GRASP_BACK * approach - np.array([0.0, 0.0, PRE_GRASP_UP])
        ok = (self.set_gripper(arm, FINGER_OPEN[arm])
              and self.move_to_pose(arm, grasp - pre_offset, Rg, 'pre-grasp')
              and self.move_linear(arm, pre_offset, 'approach')
              and self.set_gripper(arm, 0.0))
        if ok:
            if self.finger(arm) < HOLDING_MIN:
                self.log.error(f'pick: gripper closed on nothing (finger {self.finger(arm):.3f})')
                ok = False
            else:
                self.holding = arm
                self.held_marker = marker_id  # the box moves with the hand from now on
                self.forget_marker(marker_id)
                ok = self.move_linear(arm, (0.0, 0.0, LIFT), 'lift', avoid_collisions=False)
        if not ok:
            self.set_gripper(arm, FINGER_OPEN[arm])
        self.move_arms('tuck', (arm,))
        if not ok:
            self.set_gripper(arm, 0.0)  # open fingers in 'tuck' hide the table from the head camera
        self.set_support_surface(None)
        self.log.info(f'pick {"succeeded" if ok else "FAILED"} (finger {self.finger(arm):.3f})')
        return ok

    def _on_vla_result(self, msg):
        self.vla_result = json.loads(msg.data)
        self.vla_done.set()

    def vla_pick(self, marker_id, instruction, timeout=40.0):
        """Pick with the learned policy instead of MoveIt: the vla_pick node reaches, grasps and
        lifts with the right arm from camera images alone. The object must already be lined up
        at GRASP_XY['right']. Afterwards the arm is tucked here, as in pick()."""
        self.vla_done.clear()
        self.vla_result = None
        self.log.info(f'VLA pick: "{instruction}"')
        self.vla_pick_pub.publish(String(data=instruction))
        end = time.time() + timeout
        while not self.vla_done.wait(0.1):
            if self.cancel_event.is_set() or time.time() > end:
                self.vla_cancel_pub.publish(Empty())
                self.vla_done.wait(2.0)
                break
        r = self.vla_result or {'ok': False, 'reason': 'no answer from the vla_pick node (is it running?)'}
        ok = bool(r.get('ok'))
        if ok:
            self.holding = 'right'
            self.held_marker = marker_id
            self.forget_marker(marker_id)
        else:
            self.log.error(f'VLA pick failed: {r.get("reason")}')
            self.set_gripper('right', FINGER_OPEN['right'])
        self.move_arms('tuck', ('right',))
        if not ok:
            self.set_gripper('right', 0.0)  # open fingers in 'tuck' hide the table from the head camera
        self.log.info(f'VLA pick {"succeeded" if ok else "FAILED"} ({r.get("reason")}, {r.get("steps", 0)} steps)')
        return ok

    def place(self, marker_id):
        arm = self.holding
        if arm is None:
            self.log.error('place: not holding anything')
            return False
        m = self.marker_in_base(marker_id, samples=5, use_memory=True)
        if m is None:
            self.log.error(f'place: marker {marker_id} not visible')
            return False
        p_pad, R = m
        Rg = grasp_rotation(self._grasp_yaw(R))
        # grasp frame target: box centre just above the pad, plus the depth used when picking
        target = p_pad + np.array([0.0, 0.0, BOX_HALF + 0.005 + GRASP_HEIGHT]) + GRASP_DEPTH * Rg[:, 0]
        self.log.info(f'place on marker {marker_id} with {arm} arm at ({target[0]:.3f}, {target[1]:.3f}, {target[2]:.3f})')

        self.set_support_surface(p_pad[2], p_pad[:2])
        ok = (self.move_to_pose(arm, target + np.array([0.0, 0.0, LIFT]), Rg, 'pre-place')
              and self.lower_until_contact(arm, LIFT)
              and self.set_gripper(arm, FINGER_OPEN[arm]))
        if ok:
            # The object is down and released, so the place succeeded; a failed straight
            # retreat is only a warning because the planned move to 'tuck' below clears the hand.
            self.holding = None
            self.forget_marker(self.held_marker)  # it rests somewhere new: re-detect before trusting it
            self.held_marker = None
            # lift clear of the box top first: backing out along the pitched approach drags the open fingers over it
            if not (self.move_linear(arm, (0.0, 0.0, 0.04), 'release lift', avoid_collisions=False)
                    and self.move_linear(arm, tuple(-PRE_GRASP_BACK * Rg[:, 0]), 'retreat', avoid_collisions=False)):
                self.log.warn('place: straight retreat failed, retreating with a planned move instead')
        self.move_arms('tuck', (arm,))
        if self.holding is None:
            self.set_gripper(arm, 0.0)  # open fingers in 'tuck' hide the table from the head camera
        self.set_support_surface(None)
        self.log.info(f'place {"succeeded" if ok else "FAILED"}')
        return ok

    def shutdown(self):
        try:
            self.stop()
        except Exception:  # the ROS context is already gone when the launch shuts us down
            pass
        self.executor.shutdown()
        self.nav.destroy_node()
        self.node.destroy_node()
