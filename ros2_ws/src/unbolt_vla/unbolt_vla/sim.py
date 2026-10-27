"""A pick-only MuJoCo scene for the VLA policy, without ROS: demos, training and evaluation.

The robot stands in front of the supply table or the work table the way the task planner
leaves it after a coarse line-up: the red box is roughly where the right arm reaches best (GRASP_XY right),
give or take a few centimetres and degrees, and turned by any angle. Everything the policy
sees and does goes through this class:

  observation  head camera image, right wrist camera image, right arm + finger joint angles
  action       position targets for the 7 right arm joints and the finger, at CONTROL_HZ

The same scene file, actuators and gravity compensation as the ROS bridge, so a policy that
works here sees the same robot in the full stack.
"""

import math
import os

import mujoco
import numpy as np

CONTROL_HZ = 10
ARM = [f'openarm_right_joint{i}' for i in range(1, 8)]
FINGER = 'openarm_right_finger_joint1'
JOINTS = ARM + [FINGER]
TUCK = np.array([0, 0, 0, 2.3, 0, 0, 0, 0.0])      # arm folded, fingers closed (how the robot drives)
FINGER_OPEN, FINGER_CLOSED = -0.6, 0.0
HEAD_SIZE = (128, 72)    # (width, height): the 1280x720 ROS head image scaled down 10x
HEAD_SUPERSAMPLE = 3     # rendered 3x larger and box-filtered, like the ROS image's area resize
WRIST_SIZE = (96, 96)    # the bridge renders the wrist camera at this size directly
BOX_HALF = 0.025
GRASP_XY = (0.38, -0.15)  # where the box should be in the base frame for the right arm (skills.py)

# How far the line-up may be off. The classical servo stops within 1 cm; the policy is
# trained on a wider spread so that a coarse line-up is enough.
SPREAD = {'x': 0.04, 'y': 0.05, 'heading': math.radians(8), 'box_yaw': math.radians(45)}
# The two tables the box can be picked from: where the box usually rests (world x, y; it starts
# on the supply table and is put back there, and lands on the work table's place pad) and which
# way the robot faces when it stands in front of the table. They look different (blue / wood).
TABLES = {
    'supply': {'box': (-0.30, -2.36), 'box_spread': (0.06, 0.04), 'heading': -math.pi / 2},
    'work': {'box': (2.00, -0.15), 'box_spread': (0.04, 0.06), 'heading': 0.0},
}


def repo_root():
    here = os.path.dirname(os.path.realpath(__file__))
    for up in range(6):
        root = os.path.abspath(os.path.join(here, *['..'] * up))
        if os.path.isfile(os.path.join(root, 'models', 'scene.xml')):
            return root
    return os.environ.get('UNBOLT_ROOT') or os.path.expanduser('~/unbolt')


def load_model(path, gravity_compensation=True):
    """The scene as the bridge compiles it (arm gravity compensated through the actuators)."""
    try:
        from unbolt_mujoco_bridge.mujoco_bridge_node import load_model as bridge_load
        return bridge_load(path, gravity_compensation)
    except ImportError:  # ROS not sourced (rclpy missing): the same code, inlined
        spec = mujoco.MjSpec.from_file(path)
        if gravity_compensation:
            arm_joints = {a.target for a in spec.actuators if a.name not in ('left_wheel_vel', 'right_wheel_vel')}
            for joint in spec.joints:
                if joint.name in arm_joints:
                    joint.actgravcomp = 1
                    for body in [joint.parent] + list(joint.parent.find_all(mujoco.mjtObj.mjOBJ_BODY)):
                        body.gravcomp = 1.0
        return spec.compile()


def downsample(img, k):
    """Box filter by an integer factor (what cv2.INTER_AREA does for integer factors)."""
    h, w, c = img.shape
    return img.reshape(h // k, k, w // k, k, c).mean(axis=(1, 3)).round().astype(np.uint8)


class PickScene:
    def __init__(self, seed=None, render=True):
        self.model = load_model(os.path.join(repo_root(), 'models', 'scene.xml'))
        self.data = mujoco.MjData(self.model)
        m = self.model
        self.rng = np.random.default_rng(seed)
        self.qadr = np.array([m.jnt_qposadr[m.joint(j).id] for j in JOINTS])
        self.act = np.array([next(i for i in range(m.nu) if m.actuator(i).trnid[0] == m.joint(j).id) for j in JOINTS])
        self.other_act = [i for i in range(m.nu) if i not in self.act]
        base_joint = m.joint('base_free')
        self.base_q = m.jnt_qposadr[base_joint.id]
        box_joint = m.joint('red_box_free')
        self.box_q = m.jnt_qposadr[box_joint.id]
        self.box_body = m.body('red_box').id
        self.site = m.site('right_ee_control_point').id
        self.steps_per_control = int(round(1.0 / (CONTROL_HZ * m.opt.timestep)))
        self.renderers = None
        if render:
            k = HEAD_SUPERSAMPLE
            self.renderers = {'head': mujoco.Renderer(m, HEAD_SIZE[1] * k, HEAD_SIZE[0] * k),
                              'wrist': mujoco.Renderer(m, WRIST_SIZE[1], WRIST_SIZE[0])}
            for r in self.renderers.values():
                r.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW] = False
                r.scene.flags[mujoco.mjtRndFlag.mjRND_REFLECTION] = False
        self.cams = {'head': 'head_camera', 'wrist': 'camera_wrist_right'}

    # ------------------------------------------------------------------ episode
    def reset(self, table=None):
        """New episode: box somewhere on a table ('supply', 'work', or None = either), robot
        lined up roughly with it."""
        m, d, rng = self.model, self.data, self.rng
        mujoco.mj_resetData(m, d)
        self.table = table or rng.choice(sorted(TABLES))
        t = TABLES[self.table]
        box = np.array(t['box']) + rng.uniform(-1, 1, 2) * t['box_spread']
        box_yaw = rng.uniform(-SPREAD['box_yaw'], SPREAD['box_yaw'])
        d.qpos[self.box_q:self.box_q + 3] = [box[0], box[1], 0.676]
        d.qpos[self.box_q + 3:self.box_q + 7] = [math.cos(box_yaw / 2), 0, 0, math.sin(box_yaw / 2)]
        # robot facing the table, box at GRASP_XY (+ noise) in its base frame
        heading = t['heading'] + rng.uniform(-SPREAD['heading'], SPREAD['heading'])
        rel = np.array([GRASP_XY[0] + rng.uniform(-SPREAD['x'], SPREAD['x']),
                        GRASP_XY[1] + rng.uniform(-SPREAD['y'], SPREAD['y'])])
        c, s = math.cos(heading), math.sin(heading)
        base = box - np.array([c * rel[0] - s * rel[1], s * rel[0] + c * rel[1]])
        d.qpos[self.base_q:self.base_q + 2] = base
        d.qpos[self.base_q + 3:self.base_q + 7] = [math.cos(heading / 2), 0, 0, math.sin(heading / 2)]
        d.qpos[self.qadr] = TUCK
        d.qpos[m.jnt_qposadr[m.joint('openarm_left_joint4').id]] = TUCK[3]  # the planner tucks both arms
        d.ctrl[:] = 0.0
        for i in range(m.nu):  # position actuators hold where their joint is
            if m.actuator(i).name not in ('left_wheel_vel', 'right_wheel_vel'):
                d.ctrl[i] = d.qpos[m.jnt_qposadr[m.actuator(i).trnid[0]]]
        mujoco.mj_forward(m, d)
        for _ in range(300):  # let the box and the robot settle (0.3 s)
            mujoco.mj_step(m, d)
        self.box_z0 = d.xpos[self.box_body][2]
        return self.observe()

    def step(self, action):
        """Hold `action` (8 joint targets) for one control period."""
        d = self.data
        d.ctrl[self.act] = np.clip(action, self.model.actuator_ctrlrange[self.act, 0], self.model.actuator_ctrlrange[self.act, 1])
        for _ in range(self.steps_per_control):
            mujoco.mj_step(self.model, d)
        return self.observe()

    def observe(self):
        obs = {'state': self.data.qpos[self.qadr].astype(np.float32)}
        if self.renderers:
            for name, r in self.renderers.items():
                r.update_scene(self.data, camera=self.cams[name])
                obs[name] = r.render().copy()
            obs['head'] = downsample(obs['head'], HEAD_SUPERSAMPLE)
        return obs

    # ------------------------------------------------------------------ geometry and outcome
    def base_pose(self):
        """Base position (x, y) and rotation matrix in the world."""
        d = self.data
        b = self.model.body('base_link').id
        return d.xpos[b].copy(), d.xmat[b].reshape(3, 3).copy()

    def box_in_base(self):
        p, R = self.base_pose()
        d = self.data
        rot = R.T @ d.xmat[self.box_body].reshape(3, 3)
        footprint_z = self.data.site_xpos[self.model.site('base_footprint').id][2]
        pos = R.T @ (d.xpos[self.box_body] - p)
        pos[2] += p[2] - footprint_z
        return pos, rot

    def lifted(self):
        """The box is off the table by 3 cm or more."""
        return self.data.xpos[self.box_body][2] - self.box_z0 > 0.03

    def finger(self):
        return self.data.qpos[self.qadr[-1]]
