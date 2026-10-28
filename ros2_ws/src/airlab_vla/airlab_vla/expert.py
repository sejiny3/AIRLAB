"""Scripted expert for the pick: the demonstrations the VLA policy learns from.

It does what skills.pick() does with MoveIt, but with a plain damped-least-squares IK on the
MuJoCo model, because it knows the true box pose: open the hand on the way to a pre-grasp
pose behind and above the box, slide in along the pitched approach, close, lift. The output
is one joint target per control step (CONTROL_HZ), exactly the action the policy will produce.
"""

import math

import mujoco
import numpy as np

from airlab_vla.sim import BOX_HALF, CONTROL_HZ, FINGER_CLOSED, FINGER_OPEN

GRASP_PITCH = math.radians(15)   # approach axis pitched down (skills.py)
GRASP_HEIGHT = 0.015             # pads this far above the box centre (keeps the hand off the table)
PRE_GRASP_BACK = 0.10            # pre-grasp offset back along the approach [m]
PRE_GRASP_UP = 0.04              # and this much higher
VIA_UP = 0.10                    # the reach from 'tuck' passes this far above the pre-grasp
LIFT = 0.08
HOME = np.array([0, 0, 0, math.pi / 2, 0, 0, 0])  # elbow at 90 deg: a better IK seed than 'tuck'
TCP = np.array([0.0, 0.0, -0.14])  # pad centre in the right_ee_control_point frame (-z = toward the fingertips)
SITE_IN_GRASP = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], float)  # site axes from grasp axes (x approach, y closing)

# phases: (name, seconds)
TIMING = {'reach': 2.5, 'pre': 1.0, 'approach': 1.5, 'close': 1.0, 'lift': 1.2, 'hold': 0.5}


def grasp_rotation(yaw):
    """Grasp frame in the base frame: x = approach (forward, pitched down), y = finger closing axis."""
    c, s = math.cos(GRASP_PITCH), math.sin(GRASP_PITCH)
    ry = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    cz, sz = math.cos(yaw), math.sin(yaw)
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry


def grasp_yaw(R_box):
    """Turn the grasp so the fingers close on a pair of faces (fold the box yaw into +-45 deg)."""
    yaw = math.atan2(R_box[1, 0], R_box[0, 0])
    return (yaw + math.pi / 4) % (math.pi / 2) - math.pi / 4


def rot_error(R_goal, R):
    """Axis-angle vector that turns R into R_goal (world frame)."""
    E = R_goal @ R.T
    v = np.array([E[2, 1] - E[1, 2], E[0, 2] - E[2, 0], E[1, 0] - E[0, 1]]) / 2
    s, c = np.linalg.norm(v), (np.trace(E) - 1) / 2
    return v if s < 1e-9 else v * math.atan2(s, c) / s


class IK:
    """Damped least squares on the 7 right arm joints, for the TCP pose in the world frame."""

    def __init__(self, scene):
        self.scene = scene
        self.model = scene.model
        self.data = mujoco.MjData(self.model)
        m = self.model
        self.dof = np.array([m.jnt_dofadr[m.jnt_qposadr.tolist().index(q)] for q in scene.qadr[:7]])
        self.lo = m.jnt_range[[m.jnt_qposadr.tolist().index(q) for q in scene.qadr[:7]], 0]
        self.hi = m.jnt_range[[m.jnt_qposadr.tolist().index(q) for q in scene.qadr[:7]], 1]
        self.rng = np.random.default_rng(0)

    def tcp(self, q):
        d = self.data
        d.qpos[self.scene.qadr[:7]] = q
        mujoco.mj_kinematics(self.model, d)
        R = d.site_xmat[self.scene.site].reshape(3, 3)
        return d.site_xpos[self.scene.site] + R @ TCP, R

    def solve(self, q0, p_goal, R_goal, iters=100, tol=1e-4):
        m, d, site = self.model, self.data, self.scene.site
        d.qpos[:] = self.scene.data.qpos  # base and the rest of the robot where they are now
        q = np.array(q0, float)
        jp, jr = np.zeros((3, m.nv)), np.zeros((3, m.nv))
        for _ in range(iters):
            p, R = self.tcp(q)
            err = np.concatenate([p_goal - p, 0.5 * rot_error(R_goal, R)])
            if np.linalg.norm(err) < tol:
                break
            mujoco.mj_comPos(m, d)
            mujoco.mj_jac(m, d, jp, jr, p, m.site_bodyid[site])
            J = np.vstack([jp[:, self.dof], 0.5 * jr[:, self.dof]])
            dq = J.T @ np.linalg.solve(J @ J.T + 1e-4 * np.eye(6), err)
            q = np.clip(q + np.clip(dq, -0.2, 0.2), self.lo, self.hi)
        p, R = self.tcp(q)
        return q, np.linalg.norm(p_goal - p), np.linalg.norm(rot_error(R_goal, R))

    def best(self, p_goal, R_goal, seeds):
        """The first seed (in order) that converges, else the closest miss. Fixed seeds come first
        so that every demo uses the same arm configuration (elbow out), which keeps them learnable."""
        sols = []
        for s in seeds:
            sols.append(self.solve(s, p_goal, R_goal, iters=300))
            if sols[-1][1] < 0.002 and sols[-1][2] < 0.02:
                break
        return min(sols, key=lambda s: s[1] + 0.05 * s[2])[0]

    def random_seeds(self, n):
        return [self.rng.uniform(self.lo, self.hi) for _ in range(n)]


class Expert:
    """Plans the whole pick at the start of an episode, then plays it back step by step."""

    def __init__(self, scene):
        self.scene = scene
        self.ik = IK(scene)

    def plan(self):
        sc = self.scene
        p_base, R_base = sc.base_pose()
        d = sc.data
        center = d.xpos[sc.box_body].copy()
        R_box = R_base.T @ d.xmat[sc.box_body].reshape(3, 3)
        Rg = R_base @ grasp_rotation(grasp_yaw(R_box))
        R_site = Rg @ SITE_IN_GRASP
        approach = Rg[:, 0]
        up = np.array([0.0, 0.0, 1.0])
        grasp = center + GRASP_HEIGHT * up
        pre = grasp - PRE_GRASP_BACK * approach + PRE_GRASP_UP * up

        q_now = d.qpos[sc.qadr[:7]].copy()
        n = lambda phase: max(1, int(round(TIMING[phase] * CONTROL_HZ)))
        steps, worst = [], 0.0

        # The tucked arm is a poor IK seed: solve the pre-grasp from a few seeds, then go up from it
        # (lowering the via point when the arm cannot reach that high with this hand angle).
        q_pre = self.ik.best(pre, R_site, [q_now, HOME, *self.ik.random_seeds(4)])
        for rise in (VIA_UP, VIA_UP / 2, 0.0):
            q_via, ep, er = self.ik.solve(q_pre, pre + rise * up, R_site, iters=300)
            if ep < 0.003 and er < 0.02:
                break
        via = pre + rise * up
        worst = max(worst, ep)
        for k in range(1, n('reach') + 1):  # joint space from tuck, opening the hand on the way
            a = smooth(k / n('reach'))
            steps.append(np.append(q_now + a * (q_via - q_now), FINGER_CLOSED + a * (FINGER_OPEN - FINGER_CLOSED)))
        q = q_via
        for phase, start, goal in (('pre', via, pre), ('approach', pre, grasp)):
            for k in range(1, n(phase) + 1):  # Cartesian straight lines
                q, ep, er = self.ik.solve(q, start + smooth(k / n(phase)) * (goal - start), R_site)
                worst = max(worst, ep)
                steps.append(np.append(q, FINGER_OPEN))
        for k in range(1, n('close') + 1):
            steps.append(np.append(q, FINGER_OPEN + smooth(k / n('close')) * (FINGER_CLOSED - FINGER_OPEN)))
        for k in range(1, n('lift') + 1):
            q, ep, er = self.ik.solve(q, grasp + smooth(k / n('lift')) * LIFT * up, R_site)
            worst = max(worst, ep)
            steps.append(np.append(q, FINGER_CLOSED))
        steps += [steps[-1]] * n('hold')
        self.actions = np.array(steps, np.float32)
        self.ik_error = worst
        return self.actions


def smooth(t):
    """Minimum-jerk-like ease in/out on [0, 1]."""
    return t * t * (3 - 2 * t)


__all__ = ['Expert', 'IK', 'BOX_HALF']
