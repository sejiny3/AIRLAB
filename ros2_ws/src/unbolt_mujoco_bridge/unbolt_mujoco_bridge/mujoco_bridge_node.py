"""MuJoCo <-> ROS 2 bridge for the UNBOLT mobile bimanual robot.

Physics runs in the main thread, paced to wall-clock time (scaled by
``real_time_factor``); rclpy spins in a background thread. Subscriber callbacks
only store the latest command, and the step loop applies it, so MjData is
written from a single thread.

Published:
  /clock               rosgraph_msgs/Clock      simulation time
  /joint_states        sensor_msgs/JointState   arms, grippers, wheels
  /odom                nav_msgs/Odometry        wheel odometry (odom -> base_footprint)
  /ground_truth/odom   nav_msgs/Odometry        true pose from the simulator (world frame)
  /imu                 sensor_msgs/Imu
  /scan                sensor_msgs/LaserScan    2D LiDAR (ray casting, world geoms only)
  /camera/image_raw    sensor_msgs/Image        head camera (rgb8, rendered with mujoco.Renderer)
  /camera/camera_info  sensor_msgs/CameraInfo   pinhole intrinsics from the MJCF fovy
  /ground_truth/<body> geometry_msgs/PoseStamped true pose of each tracked free body (world frame)
  TF                   odom -> base_footprint

Subscribed:
  /cmd_vel             geometry_msgs/Twist      diff-drive base velocity
  /joint_commands      sensor_msgs/JointState   position targets by joint name

Services:
  ~/reset              std_srvs/Trigger         reset the world to the home pose

Actions (control_msgs/FollowJointTrajectory, used by MoveIt):
  /left_arm_controller/follow_joint_trajectory      openarm_left_joint1..7
  /right_arm_controller/follow_joint_trajectory     openarm_right_joint1..7
  /left_gripper_controller/follow_joint_trajectory  openarm_left_finger_joint1
  /right_gripper_controller/follow_joint_trajectory openarm_right_finger_joint1
"""

import array
import math
import threading
import time

import mujoco
import mujoco.viewer
import numpy as np
import rclpy
from builtin_interfaces.msg import Time
from geometry_msgs.msg import PoseStamped, TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import CameraInfo, Image, Imu, JointState, LaserScan
from std_srvs.srv import Trigger
from tf2_ros import TransformBroadcaster

from unbolt_mujoco_bridge.trajectory_server import TrajectoryServer

# Arm pose the simulation starts in (same "home" as the OpenArm scenes: elbows at 90 deg).
HOME_POSE = {
    'openarm_left_joint4': math.pi / 2,
    'openarm_right_joint4': math.pi / 2,
}
WHEEL_JOINTS = ('left_wheel_joint', 'right_wheel_joint')
WHEEL_ACTUATORS = ('left_wheel_vel', 'right_wheel_vel')
# controller name -> (joints, goal tolerance [rad]). Grippers get a loose tolerance
# because a grasped object legitimately stops the fingers short of the target.
TRAJECTORY_CONTROLLERS = {
    'left_arm_controller': ([f'openarm_left_joint{i}' for i in range(1, 8)], 0.02),
    'right_arm_controller': ([f'openarm_right_joint{i}' for i in range(1, 8)], 0.02),
    'left_gripper_controller': (['openarm_left_finger_joint1'], 1.0),
    'right_gripper_controller': (['openarm_right_finger_joint1'], 1.0),
}
# The LiDAR only sees geom groups 0-1 (world); the robot's own geoms are in groups 2-3.
LIDAR_GEOMGROUP = np.array([1, 1, 0, 0, 0, 0], dtype=np.uint8)


def load_model(path: str, arm_gravity_compensation: bool) -> mujoco.MjModel:
    """Compile the scene; optionally cancel gravity on the arms through their actuators
    (like a real arm's gravity feed-forward) so position targets are reached without sag.
    gravcomp must be set before compiling: MuJoCo skips it when the compiled ngravcomp is 0."""
    spec = mujoco.MjSpec.from_file(path)
    if arm_gravity_compensation:
        arm_joints = {a.target for a in spec.actuators if a.name not in WHEEL_ACTUATORS}
        for joint in spec.joints:
            if joint.name in arm_joints:
                joint.actgravcomp = 1
                for body in [joint.parent] + list(joint.parent.find_all(mujoco.mjtObj.mjOBJ_BODY)):
                    body.gravcomp = 1.0
    return spec.compile()


def to_time_msg(t: float) -> Time:
    sec = int(t)
    return Time(sec=sec, nanosec=int((t - sec) * 1e9))


def yaw_to_quat(yaw: float):
    return (0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0))


class MujocoBridge(Node):
    def __init__(self):
        super().__init__('mujoco_bridge')
        self.declare_parameter('model_path', '')
        self.declare_parameter('use_viewer', True)
        self.declare_parameter('viewer_track_robot', True)
        self.declare_parameter('real_time_factor', 1.0)
        self.declare_parameter('clock_rate', 250.0)
        self.declare_parameter('joint_state_rate', 100.0)
        self.declare_parameter('odom_rate', 50.0)
        self.declare_parameter('cmd_vel_timeout', 0.5)
        self.declare_parameter('wheel_radius', 0.08)
        self.declare_parameter('wheel_separation', 0.45)
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_footprint')
        self.declare_parameter('world_frame', 'world')
        self.declare_parameter('lidar_frame', 'lidar_link')
        self.declare_parameter('lidar_rate', 10.0)
        self.declare_parameter('lidar_samples', 360)
        self.declare_parameter('lidar_range_min', 0.12)
        self.declare_parameter('lidar_range_max', 12.0)
        self.declare_parameter('lidar_noise_std', 0.01)
        self.declare_parameter('arm_gravity_compensation', True)
        self.declare_parameter('camera_name', 'head_camera')
        self.declare_parameter('camera_frame', 'camera_optical_frame')
        self.declare_parameter('camera_rate', 5.0)  # 0 disables rendering
        self.declare_parameter('tracked_bodies', ['red_box'])
        self.declare_parameter('ground_truth_rate', 10.0)

        p = lambda name: self.get_parameter(name).value
        model_path = p('model_path')
        if not model_path:
            raise RuntimeError('parameter "model_path" is required')
        self.use_viewer = p('use_viewer')
        self.track_robot = p('viewer_track_robot')
        self.rtf = p('real_time_factor')
        self.clock_dt = 1.0 / p('clock_rate')
        self.js_dt = 1.0 / p('joint_state_rate')
        self.odom_dt = 1.0 / p('odom_rate')
        self.cmd_vel_timeout = p('cmd_vel_timeout')
        self.wheel_radius = p('wheel_radius')
        self.wheel_sep = p('wheel_separation')
        self.odom_frame = p('odom_frame')
        self.base_frame = p('base_frame')
        self.world_frame = p('world_frame')
        self.lidar_frame = p('lidar_frame')
        self.lidar_dt = 1.0 / p('lidar_rate')
        self.lidar_n = p('lidar_samples')
        self.lidar_min = p('lidar_range_min')
        self.lidar_max = p('lidar_range_max')
        self.lidar_noise = p('lidar_noise_std')
        self.camera_name = p('camera_name')
        self.camera_frame = p('camera_frame')
        self.camera_dt = 1.0 / p('camera_rate') if p('camera_rate') > 0 else None
        self.tracked_names = list(p('tracked_bodies'))
        self.gt_objects_dt = 1.0 / p('ground_truth_rate')
        self.rng = np.random.default_rng()

        self.model = load_model(model_path, p('arm_gravity_compensation'))
        self.data = mujoco.MjData(self.model)
        m = self.model
        self.get_logger().info(
            f'loaded {model_path}: nq={m.nq} nv={m.nv} nu={m.nu} dt={m.opt.timestep}')

        self._index_model()
        self._reset_world()

        # Latest commands, written by callbacks and consumed by the step loop.
        self._lock = threading.Lock()
        self._cmd_vel = (0.0, 0.0)
        self._cmd_vel_wall = 0.0
        self._joint_targets = {}
        self._reset_requested = False

        reliable = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        self.clock_pub = self.create_publisher(Clock, '/clock', reliable)
        self.js_pub = self.create_publisher(JointState, '/joint_states', reliable)
        self.odom_pub = self.create_publisher(Odometry, '/odom', reliable)
        self.gt_pub = self.create_publisher(Odometry, '/ground_truth/odom', reliable)
        self.imu_pub = self.create_publisher(Imu, '/imu', reliable)
        self.scan_pub = self.create_publisher(LaserScan, '/scan', reliable)
        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 2)
        self.camera_info_pub = self.create_publisher(CameraInfo, '/camera/camera_info', 2)
        self.object_pubs = {name: self.create_publisher(PoseStamped, f'/ground_truth/{name}', reliable)
                            for name in self.tracked_bodies}
        self.tf_broadcaster = TransformBroadcaster(self)

        self.create_subscription(Twist, '/cmd_vel', self._on_cmd_vel, 10)
        self.create_subscription(JointState, '/joint_commands', self._on_joint_commands, 10)
        self.create_service(Trigger, '~/reset', self._on_reset)
        self.trajectory_servers = [
            TrajectoryServer(self, name, joints, tolerance)
            for name, (joints, tolerance) in TRAJECTORY_CONTROLLERS.items()
        ]

        self.get_logger().info(
            f'{len(self.js_names)} joints on /joint_states, '
            f'{len(self.pos_actuators)} position-controlled joints on /joint_commands')

    # ------------------------------------------------------------------ model
    def _index_model(self):
        m = self.model
        # Every 1-DoF joint (arms, fingers, wheels); free joints (base, objects) are excluded.
        one_dof = (int(mujoco.mjtJoint.mjJNT_HINGE), int(mujoco.mjtJoint.mjJNT_SLIDE))
        self.js_names, self.js_qpos, self.js_dof = [], [], []
        for j in range(m.njnt):
            if int(m.jnt_type[j]) in one_dof:
                self.js_names.append(m.joint(j).name)
                self.js_qpos.append(m.jnt_qposadr[j])
                self.js_dof.append(m.jnt_dofadr[j])
        self.qpos_of = dict(zip(self.js_names, self.js_qpos))
        self.js_qpos = np.array(self.js_qpos, dtype=int)
        self.js_dof = np.array(self.js_dof, dtype=int)

        self.wheel_act = [m.actuator(a).id for a in WHEEL_ACTUATORS]
        self.wheel_qpos = [m.jnt_qposadr[m.joint(j).id] for j in WHEEL_JOINTS]

        # joint name -> actuator id for every joint-driven actuator except the wheels.
        self.pos_actuators = {}
        for a in range(m.nu):
            if a in self.wheel_act or m.actuator_trntype[a] != mujoco.mjtTrn.mjTRN_JOINT:
                continue
            self.pos_actuators[m.joint(m.actuator_trnid[a, 0]).name] = a

        base_joint = m.joint('base_free')
        self.base_qpos = m.jnt_qposadr[base_joint.id]
        self.base_dof = m.jnt_dofadr[base_joint.id]
        self.base_body = m.body('base_link').id
        self.footprint_site = m.site('base_footprint').id

        # LiDAR: beams in the lidar site's xy-plane, counter-clockwise from -pi.
        self.lidar_site = m.site('lidar_link').id
        self.lidar_angles = -math.pi + np.arange(self.lidar_n) * (2 * math.pi / self.lidar_n)
        self.lidar_dirs = np.stack([np.cos(self.lidar_angles), np.sin(self.lidar_angles),
                                    np.zeros(self.lidar_n)], axis=1)
        self.lidar_geomid = np.zeros(self.lidar_n, dtype=np.int32)
        self.lidar_dist = np.zeros(self.lidar_n, dtype=np.float64)

        sens = lambda name: slice(m.sensor(name).adr[0], m.sensor(name).adr[0] + m.sensor(name).dim[0])
        self.s_gyro, self.s_accel, self.s_quat = sens('imu_gyro'), sens('imu_accel'), sens('imu_quat')

        # Head camera: pinhole intrinsics from the vertical field of view.
        self.camera_id = m.camera(self.camera_name).id if self.camera_dt else -1
        if self.camera_id >= 0:
            self.cam_w, self.cam_h = (int(v) for v in m.cam_resolution[self.camera_id])
            f = (self.cam_h / 2.0) / math.tan(math.radians(m.cam_fovy[self.camera_id]) / 2.0)
            self.cam_k = [f, 0.0, self.cam_w / 2.0, 0.0, f, self.cam_h / 2.0, 0.0, 0.0, 1.0]

        # Free bodies whose true pose is published for evaluation (missing names are skipped).
        names = [b.name for b in (m.body(i) for i in range(m.nbody))]
        self.tracked_bodies = {n: m.body(n).id for n in self.tracked_names if n in names}

    def _reset_world(self):
        m, d = self.model, self.data
        # Keep the simulation clock running: mj_resetData sets time to 0, and /clock jumping
        # back makes every ROS node clear its TF buffer (Nav2, AMCL and MoveIt lose their state).
        t = d.time
        mujoco.mj_resetData(m, d)
        d.time = t
        for name, q in HOME_POSE.items():
            d.qpos[m.joint(name).qposadr[0]] = q
        for name, a in self.pos_actuators.items():
            d.ctrl[a] = d.qpos[m.joint(name).qposadr[0]]
        mujoco.mj_forward(m, d)
        self.odom_pose = [0.0, 0.0, 0.0]  # x, y, yaw in odom frame
        self.odom_twist = (0.0, 0.0)
        self.prev_wheel = [d.qpos[a] for a in self.wheel_qpos]
        self.next_clock = self.next_js = self.next_odom = self.next_scan = 0.0
        self.next_camera = self.next_objects = 0.0
        self.camera_due = False
        self.last_odom_time = d.time

    # ------------------------------------------- interface for TrajectoryServer
    def sim_time(self) -> float:
        return self.data.time

    def joint_positions(self, names):
        return [float(self.data.qpos[self.qpos_of[n]]) for n in names]

    def set_joint_targets(self, targets):
        with self._lock:
            self._joint_targets.update(targets)

    # -------------------------------------------------------------- callbacks
    def _on_cmd_vel(self, msg: Twist):
        with self._lock:
            self._cmd_vel = (msg.linear.x, msg.angular.z)
            self._cmd_vel_wall = time.monotonic()

    def _on_joint_commands(self, msg: JointState):
        unknown = [n for n in msg.name if n not in self.pos_actuators]
        if unknown:
            self.get_logger().warn(f'ignoring unknown joints: {unknown}', throttle_duration_sec=2.0)
        with self._lock:
            for name, pos in zip(msg.name, msg.position):
                if name in self.pos_actuators:
                    self._joint_targets[name] = pos

    def _on_reset(self, request, response):
        with self._lock:
            self._reset_requested = True
            self._joint_targets.clear()
            self._cmd_vel = (0.0, 0.0)
        response.success = True
        response.message = 'world reset to home pose'
        return response

    def _apply_commands(self):
        d = self.data
        with self._lock:
            if self._reset_requested:
                self._reset_requested = False
                self._reset_world()
            v, w = self._cmd_vel
            if time.monotonic() - self._cmd_vel_wall > self.cmd_vel_timeout:
                v = w = 0.0
            targets, self._joint_targets = self._joint_targets, {}
        # Differential drive inverse kinematics: +y wheel is the left one.
        d.ctrl[self.wheel_act[0]] = (v - w * self.wheel_sep / 2.0) / self.wheel_radius
        d.ctrl[self.wheel_act[1]] = (v + w * self.wheel_sep / 2.0) / self.wheel_radius
        for name, pos in targets.items():
            d.ctrl[self.pos_actuators[name]] = pos  # ctrlrange clamps in MuJoCo

    # ------------------------------------------------------------ publishing
    def _publish_due(self):
        t = self.data.time
        if t >= self.next_clock:
            self.next_clock = t + self.clock_dt
            self.clock_pub.publish(Clock(clock=to_time_msg(t)))
        if t >= self.next_js:
            self.next_js = t + self.js_dt
            self._publish_joint_states()
        if t >= self.next_odom:
            self.next_odom = t + self.odom_dt
            self._update_odometry()
            self._publish_odometry()
            self._publish_ground_truth()
            self._publish_imu()
        if t >= self.next_scan:
            self.next_scan = t + self.lidar_dt
            self._publish_scan()
        if t >= self.next_objects:
            self.next_objects = t + self.gt_objects_dt
            self._publish_objects()
        if self.camera_id >= 0 and t >= self.next_camera:
            self.next_camera = t + self.camera_dt
            self.camera_due = True  # rendered by run() after this batch of steps

    def _publish_joint_states(self):
        d = self.data
        msg = JointState()
        msg.header.stamp = to_time_msg(d.time)
        msg.name = self.js_names
        msg.position = d.qpos[self.js_qpos].tolist()
        msg.velocity = d.qvel[self.js_dof].tolist()
        msg.effort = d.qfrc_actuator[self.js_dof].tolist()
        self.js_pub.publish(msg)

    def _update_odometry(self):
        """Integrate wheel encoder deltas (exact arc integration)."""
        d = self.data
        wheel = [d.qpos[a] for a in self.wheel_qpos]
        dl = (wheel[0] - self.prev_wheel[0]) * self.wheel_radius
        dr = (wheel[1] - self.prev_wheel[1]) * self.wheel_radius
        self.prev_wheel = wheel
        ds = (dl + dr) / 2.0
        dyaw = (dr - dl) / self.wheel_sep
        x, y, yaw = self.odom_pose
        mid = yaw + dyaw / 2.0
        self.odom_pose = [x + ds * math.cos(mid), y + ds * math.sin(mid), yaw + dyaw]
        dt = d.time - self.last_odom_time
        self.last_odom_time = d.time
        self.odom_twist = (ds / dt, dyaw / dt) if dt > 0 else (0.0, 0.0)

    def _publish_odometry(self):
        stamp = to_time_msg(self.data.time)
        x, y, yaw = self.odom_pose
        q = yaw_to_quat(yaw)

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose.position.x, odom.pose.pose.position.y = x, y
        (odom.pose.pose.orientation.x, odom.pose.pose.orientation.y,
         odom.pose.pose.orientation.z, odom.pose.pose.orientation.w) = q
        odom.twist.twist.linear.x, odom.twist.twist.angular.z = self.odom_twist
        self.odom_pub.publish(odom)

        tf = TransformStamped()
        tf.header.stamp = stamp
        tf.header.frame_id = self.odom_frame
        tf.child_frame_id = self.base_frame
        tf.transform.translation.x, tf.transform.translation.y = x, y
        (tf.transform.rotation.x, tf.transform.rotation.y,
         tf.transform.rotation.z, tf.transform.rotation.w) = q
        self.tf_broadcaster.sendTransform(tf)

    def _publish_ground_truth(self):
        d = self.data
        pos = d.site_xpos[self.footprint_site]
        qw, qx, qy, qz = d.qpos[self.base_qpos + 3:self.base_qpos + 7]
        rot = d.xmat[self.base_body].reshape(3, 3)
        lin_body = rot.T @ d.qvel[self.base_dof:self.base_dof + 3]  # free joint: world-frame linear vel
        ang_body = d.qvel[self.base_dof + 3:self.base_dof + 6]       # free joint: body-frame angular vel

        msg = Odometry()
        msg.header.stamp = to_time_msg(d.time)
        msg.header.frame_id = self.world_frame
        msg.child_frame_id = self.base_frame
        p = msg.pose.pose
        p.position.x, p.position.y, p.position.z = map(float, pos)
        p.orientation.x, p.orientation.y, p.orientation.z, p.orientation.w = map(float, (qx, qy, qz, qw))
        t = msg.twist.twist
        t.linear.x, t.linear.y, t.linear.z = map(float, lin_body)
        t.angular.x, t.angular.y, t.angular.z = map(float, ang_body)
        self.gt_pub.publish(msg)

    def _publish_imu(self):
        d = self.data
        msg = Imu()
        msg.header.stamp = to_time_msg(d.time)
        msg.header.frame_id = 'imu_link'
        qw, qx, qy, qz = d.sensordata[self.s_quat]
        msg.orientation.x, msg.orientation.y, msg.orientation.z, msg.orientation.w = map(float, (qx, qy, qz, qw))
        g = d.sensordata[self.s_gyro]
        a = d.sensordata[self.s_accel]
        msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z = map(float, g)
        msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z = map(float, a)
        self.imu_pub.publish(msg)

    def _publish_scan(self):
        m, d = self.model, self.data
        origin = d.site_xpos[self.lidar_site].copy()
        vec = (self.lidar_dirs @ d.site_xmat[self.lidar_site].reshape(3, 3).T).ravel()
        mujoco.mj_multiRay(m, d, origin, vec, LIDAR_GEOMGROUP, 1, -1,
                           self.lidar_geomid, self.lidar_dist, None, self.lidar_n, self.lidar_max)
        ranges = self.lidar_dist.copy()
        hit = ranges >= 0.0
        ranges[hit] += self.rng.normal(0.0, self.lidar_noise, hit.sum())
        ranges[~hit | (ranges > self.lidar_max)] = math.inf
        ranges[ranges < self.lidar_min] = math.inf

        msg = LaserScan()
        msg.header.stamp = to_time_msg(d.time)
        msg.header.frame_id = self.lidar_frame
        msg.angle_min = float(self.lidar_angles[0])
        msg.angle_increment = 2 * math.pi / self.lidar_n
        msg.angle_max = float(self.lidar_angles[-1])
        msg.scan_time = self.lidar_dt
        msg.time_increment = 0.0  # all beams are cast at the same instant
        msg.range_min = self.lidar_min
        msg.range_max = self.lidar_max
        msg.ranges = ranges.tolist()
        self.scan_pub.publish(msg)

    def _publish_objects(self):
        d = self.data
        for name, body in self.tracked_bodies.items():
            msg = PoseStamped()
            msg.header.stamp = to_time_msg(d.time)
            msg.header.frame_id = self.world_frame
            p = msg.pose
            p.position.x, p.position.y, p.position.z = map(float, d.xpos[body])
            p.orientation.w, p.orientation.x, p.orientation.y, p.orientation.z = map(float, d.xquat[body])
            self.object_pubs[name].publish(msg)

    def _publish_camera(self, renderer):
        d = self.data
        renderer.update_scene(d, camera=self.camera_id)
        rgb = renderer.render()
        stamp = to_time_msg(d.time)

        img = Image()
        img.header.stamp = stamp
        img.header.frame_id = self.camera_frame
        img.height, img.width = rgb.shape[:2]
        img.encoding = 'rgb8'
        img.step = img.width * 3
        img.data = array.array('B', rgb.tobytes())  # bytes would be validated element by element (~130 ms)
        self.image_pub.publish(img)

        info = CameraInfo()
        info.header = img.header
        info.height, info.width = img.height, img.width
        info.distortion_model = 'plumb_bob'
        info.d = [0.0] * 5
        info.k = self.cam_k
        info.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        fx, cx, fy, cy = self.cam_k[0], self.cam_k[2], self.cam_k[4], self.cam_k[5]
        info.p = [fx, 0.0, cx, 0.0, 0.0, fy, cy, 0.0, 0.0, 0.0, 1.0, 0.0]
        self.camera_info_pub.publish(info)

    # -------------------------------------------------------------- run loop
    def run(self):
        m, d = self.model, self.data
        viewer = None
        if self.use_viewer:
            viewer = mujoco.viewer.launch_passive(m, d)
            if self.track_robot:
                viewer.cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
                viewer.cam.trackbodyid = self.base_body
                viewer.cam.distance, viewer.cam.elevation, viewer.cam.azimuth = 3.0, -25.0, 150.0
        renderer = None
        if self.camera_id >= 0:
            renderer = mujoco.Renderer(m, self.cam_h, self.cam_w)
            # shadows and reflections cost ~4x the render time and don't help marker detection
            renderer.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW] = False
            renderer.scene.flags[mujoco.mjtRndFlag.mjRND_REFLECTION] = False

        max_steps = max(1, int(0.05 / m.opt.timestep))  # catch up at most 50 ms per cycle
        view_dt, next_view = 1.0 / 60.0, 0.0
        wall0, sim0 = time.monotonic(), d.time
        warned_slow = False

        while rclpy.ok() and (viewer is None or viewer.is_running()):
            self._apply_commands()
            target = sim0 + (time.monotonic() - wall0) * self.rtf

            steps = 0
            while d.time < target and steps < max_steps:
                mujoco.mj_step(m, d)
                self._publish_due()
                steps += 1
            if steps == max_steps:
                # Physics can't keep up: re-anchor instead of spiralling behind.
                wall0, sim0 = time.monotonic(), d.time
                if not warned_slow:
                    self.get_logger().warn('simulation is slower than real_time_factor; running as fast as possible')
                    warned_slow = True

            if self.camera_due:
                self.camera_due = False
                self._publish_camera(renderer)

            now = time.monotonic()
            if viewer is not None and now >= next_view:
                viewer.sync()
                next_view = now + view_dt
            if steps < max_steps:
                time.sleep(0.001)

        if viewer is not None:
            viewer.close()
        if renderer is not None:
            renderer.close()


def main():
    rclpy.init()
    node = MujocoBridge()
    # Multi-threaded so long-running trajectory executions don't block the subscribers.
    executor = MultiThreadedExecutor(num_threads=6)
    executor.add_node(node)
    spinner = threading.Thread(target=executor.spin, daemon=True)
    spinner.start()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
