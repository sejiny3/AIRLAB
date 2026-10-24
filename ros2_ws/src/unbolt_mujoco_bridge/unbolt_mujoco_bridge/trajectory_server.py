"""FollowJointTrajectory action server that streams position targets into the MuJoCo bridge.

MoveIt (moveit_simple_controller_manager) sends time-parameterized trajectories
here. Positions are linearly interpolated between waypoints on simulation time
and handed to the bridge, which applies them as position-actuator targets.
"""

import threading
import time

from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup

RATE_HZ = 100.0


def duration_to_sec(d):
    return d.sec + d.nanosec * 1e-9


class TrajectoryServer:
    def __init__(self, bridge, controller_name, joints, goal_tolerance, settle_time=1.0):
        """bridge must provide sim_time(), joint_positions(names) and set_joint_targets(dict)."""
        self.bridge = bridge
        self.joints = list(joints)
        self.goal_tolerance = goal_tolerance
        self.settle_time = settle_time
        self._active_lock = threading.Lock()
        self._active_goal = None
        self.server = ActionServer(
            bridge, FollowJointTrajectory, f'/{controller_name}/follow_joint_trajectory',
            execute_callback=self._execute,
            goal_callback=self._on_goal,
            cancel_callback=lambda _: CancelResponse.ACCEPT,
            callback_group=ReentrantCallbackGroup(),
        )

    def _on_goal(self, goal):
        names = goal.trajectory.joint_names
        if not names or not set(names) <= set(self.joints):
            self.bridge.get_logger().error(f'trajectory joints {list(names)} do not belong to {self.joints}')
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def _execute(self, goal_handle):
        with self._active_lock:
            if self._active_goal is not None and self._active_goal.is_active:
                self._active_goal.abort()  # newest goal preempts
            self._active_goal = goal_handle

        traj = goal_handle.request.trajectory
        names = list(traj.joint_names)
        result = FollowJointTrajectory.Result()
        if not traj.points:
            goal_handle.succeed()
            return result

        times = [duration_to_sec(p.time_from_start) for p in traj.points]
        points = [list(p.positions) for p in traj.points]
        start_pos = self.bridge.joint_positions(names)
        if times[0] > 0.0:  # interpolate from the current state into the first waypoint
            times.insert(0, 0.0)
            points.insert(0, start_pos)
        t0 = self.bridge.sim_time()
        end = times[-1]

        feedback = FollowJointTrajectory.Feedback()
        feedback.joint_names = names
        k = 0
        while True:
            if goal_handle.is_cancel_requested:
                self.bridge.set_joint_targets(dict(zip(names, self.bridge.joint_positions(names))))
                goal_handle.canceled()
                return result
            if not goal_handle.is_active:  # preempted by a newer goal
                return result
            t = self.bridge.sim_time() - t0
            if t >= end:
                break
            while k + 1 < len(times) - 1 and times[k + 1] <= t:
                k += 1
            span = times[k + 1] - times[k]
            a = 0.0 if span <= 0 else min(1.0, max(0.0, (t - times[k]) / span))
            target = [p0 + a * (p1 - p0) for p0, p1 in zip(points[k], points[k + 1])]
            self.bridge.set_joint_targets(dict(zip(names, target)))
            feedback.desired.positions = target
            feedback.actual.positions = self.bridge.joint_positions(names)
            goal_handle.publish_feedback(feedback)
            time.sleep(1.0 / RATE_HZ)

        # Hold the final waypoint and give the joints settle_time (sim) to converge.
        final = points[-1]
        self.bridge.set_joint_targets(dict(zip(names, final)))
        deadline = self.bridge.sim_time() + self.settle_time
        while True:
            err = max(abs(a - b) for a, b in zip(self.bridge.joint_positions(names), final))
            if err <= self.goal_tolerance or self.bridge.sim_time() >= deadline:
                break
            time.sleep(1.0 / RATE_HZ)

        if err > self.goal_tolerance:
            result.error_code = FollowJointTrajectory.Result.GOAL_TOLERANCE_VIOLATED
            result.error_string = f'final joint error {err:.3f} rad > tolerance {self.goal_tolerance:.3f}'
            self.bridge.get_logger().warn(result.error_string)
            goal_handle.abort()
        else:
            result.error_code = FollowJointTrajectory.Result.SUCCESSFUL
            goal_handle.succeed()
        return result
