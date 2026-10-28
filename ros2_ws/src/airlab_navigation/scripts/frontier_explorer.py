#!/usr/bin/env python3
"""Frontier-based active exploration: Nav2 drives to the edge of the known map until none is left.

  ros2 launch airlab_navigation explore.launch.py      # sim + slam_toolbox + Nav2 + this node
  ros2 run airlab_navigation frontier_explorer.py --ros-args -p use_sim_time:=true

A frontier cell is a known-free cell of /map (slam_toolbox) next to an unknown one; touching
frontier cells form a cluster. For every cluster the node looks for a spot the robot can stand
on (low cost in /global_costmap/costmap, reachable through known free space, within `approach`
of the cluster through free space, so never behind a wall from it; among those the one with
a short drive that is also close to the frontier's middle) and sends the best cluster's spot
(short path, long frontier) to Nav2's navigate_to_pose. The 360-degree LiDAR uncovers the unknown beyond the
frontier on the way, so as soon as the cluster it is heading for is gone the node moves on.
A spot that failed (or did not uncover its frontier) is not used again; a frontier is given
up after two such spots. Exploration ends when no reachable cluster is left; the map is
then saved (save_on_done).

Topics:
  /explore/control  std_msgs/String  'start' | 'stop' | 'save'
  /explore/status   std_msgs/String  JSON (2 Hz): state ('waiting' | 'idle' | 'exploring' |
                    'done' | 'stopped'), message, goal, frontiers [[x, y, length_m], ...],
                    known_m2, goals, failures, elapsed, saved (path of the last saved map)
Parameters:
  autostart (true)       start exploring as soon as the map and Nav2 are up
  min_frontier (0.3 m)   ignore shorter frontier clusters
  approach (1.0 m)       stand at most this far (through free space) from the frontier
  goal_timeout (60 s)    give up on a goal after this long
  map_dir (~/maps)       where maps are saved (airlab_explored_<date>_<time>.yaml/.pgm)
  save_on_done (true)
"""

import json
import math
import os
import time

import cv2
import numpy as np
import rclpy
import tf2_ros
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped, Twist
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import OccupancyGrid
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from rclpy.time import Time
from std_msgs.msg import String

GOAL_COST = 75       # costmap 0-100: about 0.57 m from the nearest obstacle (explore.launch.py inflation)
BLOCKED_COST = 99    # inscribed / lethal: the robot cannot be there
EMPTY_TICKS = 3      # this many plans in a row without a goal = done (the map updates every 2 s)
MAX_TRIES = 2        # goals (from different spots) spent on one frontier before giving it up
MID_WEIGHT = 1.5     # standing spot score: path from the robot + this x distance to the frontier's middle


def yaw_quat(yaw):
    return math.sin(yaw / 2), math.cos(yaw / 2)


class FrontierExplorer(Node):
    def __init__(self):
        super().__init__('frontier_explorer')
        self.declare_parameter('autostart', True)
        self.declare_parameter('min_frontier', 0.3)
        self.declare_parameter('approach', 1.0)
        self.declare_parameter('goal_timeout', 60.0)
        self.declare_parameter('map_dir', '~/maps')
        self.declare_parameter('save_on_done', True)
        p = lambda n: self.get_parameter(n).value  # noqa: E731
        self.autostart, self.min_frontier, self.approach = p('autostart'), p('min_frontier'), p('approach')
        self.goal_timeout, self.save_on_done = p('goal_timeout'), p('save_on_done')
        self.map_dir = os.path.expanduser(p('map_dir'))

        latched = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.map = None
        self.costmap = None
        self.create_subscription(OccupancyGrid, '/map', lambda m: setattr(self, 'map', m), latched)
        self.create_subscription(OccupancyGrid, '/global_costmap/costmap', lambda m: setattr(self, 'costmap', m), 1)
        self.create_subscription(String, '/explore/control', self._on_control, 10)
        self.status_pub = self.create_publisher(String, '/explore/status', 10)
        self.cmd_vel = self.create_publisher(Twist, '/cmd_vel', 10)
        self.nav = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.tf = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf, self)

        self.state, self.message = 'waiting', '지도와 Nav2를 기다리는 중'
        self.started = None          # wall time exploration (re)started
        self.target = None           # {'goal': (x, y), 'frontier': (x, y), 'sent': wall time, 'id': n}
        self.goal_handle = None
        self.goal_seq = 0
        self.bad_goals, self.bad_frontiers = [], []
        self.frontiers = []
        self._frontier_cells = []
        self.known_m2 = 0.0
        self.goals_sent = self.failures = self.empty_ticks = 0
        self.saved = None
        self.create_timer(1.0, self._tick)
        self.create_timer(0.5, self._publish_status)

    # ------------------------------------------------------------------ control
    def _on_control(self, msg):
        cmd = msg.data.strip()
        if cmd == 'start' and self.state in ('idle', 'done', 'stopped'):
            self._start()
        elif cmd == 'stop' and self.state == 'exploring':
            self._finish('stopped', '멈췄습니다. 키보드로 조종하거나 다시 탐색할 수 있습니다.')
        elif cmd == 'save':
            self._save()
        self._publish_status()

    def _start(self):
        self.state, self.message = 'exploring', '프론티어를 찾는 중'
        self.started = time.time()
        self.bad_goals, self.bad_frontiers = [], []
        self.goals_sent = self.failures = self.empty_ticks = 0
        self.get_logger().info('exploration started')

    def _finish(self, state, message):
        self._cancel_goal()
        self.cmd_vel.publish(Twist())
        self.state, self.message = state, message
        self.get_logger().info(f'exploration {state}: {self.goals_sent} goals, {self.failures} failed, '
                               f'{self.known_m2:.1f} m2 known')
        if state == 'done' and self.save_on_done:
            self._save()

    def _cancel_goal(self):
        if self.goal_handle is not None:
            self.goal_handle.cancel_goal_async()
        self.goal_handle, self.target = None, None

    # ------------------------------------------------------------------ main loop
    def _tick(self):
        if self.state == 'waiting':
            if self.map is not None and self.costmap is not None and self._pose() is not None \
                    and self.nav.server_is_ready():
                self.state, self.message = 'idle', '준비됨'
                self.get_logger().info('frontier explorer ready')
                if self.autostart:
                    self._start()
            return
        if self.state != 'exploring':
            if self.map is not None:  # keep the frontier picture current (manual driving keeps mapping)
                self._plan(self._pose(), goals=False)
            return
        pose = self._pose()
        if pose is None:
            return
        candidates = self._plan(pose)
        if self.target is not None:
            if time.time() - self.target['sent'] > self.goal_timeout:
                self.get_logger().warn(f'goal {self.target["goal"]} timed out')
                self._blacklist(self.target)
                self.failures += 1
                self._cancel_goal()
            elif not self._frontier_left(self.target['frontier']):
                self._cancel_goal()  # its frontier is mapped already: on to the next one
            else:
                return
        if not candidates:
            self.empty_ticks += 1
            self.message = '남은 프론티어를 확인하는 중'
            if self.empty_ticks >= EMPTY_TICKS:
                self._finish('done', '탐색 완료: 갈 수 있는 프론티어가 더 없습니다.')
            return
        self.empty_ticks = 0
        self._send(candidates[0])

    def _send(self, c):
        gx, gy = c['goal']
        fx, fy = c['frontier']
        yaw = math.atan2(fy - gy, fx - gx)
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x, goal.pose.pose.position.y = gx, gy
        goal.pose.pose.orientation.z, goal.pose.pose.orientation.w = yaw_quat(yaw)
        self.goal_seq += 1
        self.goals_sent += 1
        self.target = dict(c, sent=time.time(), id=self.goal_seq)
        self.message = f'프론티어로 이동 중 ({gx:.1f}, {gy:.1f})'
        self.get_logger().info(f'goal {self.goals_sent}: ({gx:.2f}, {gy:.2f}) for a {c["length"]:.1f} m frontier '
                               f'at ({fx:.2f}, {fy:.2f})')
        seq = self.goal_seq
        self.nav.send_goal_async(goal).add_done_callback(lambda f: self._on_accepted(f, seq))

    def _on_accepted(self, future, seq):
        handle = future.result()
        if self.target is None or self.target['id'] != seq:
            if handle.accepted:
                handle.cancel_goal_async()  # superseded while the request was in flight
            return
        if not handle.accepted:
            self.get_logger().warn('goal rejected')
            self._blacklist(self.target)
            self.failures += 1
            self.target = None
            return
        self.goal_handle = handle
        handle.get_result_async().add_done_callback(lambda f: self._on_result(f, seq))

    def _on_result(self, future, seq):
        if self.target is None or self.target['id'] != seq:
            return  # cancelled by us
        status = future.result().status
        if status == GoalStatus.STATUS_SUCCEEDED:
            # standing there did not uncover it (still a frontier): try it from another spot
            if self._frontier_left(self.target['frontier']):
                self._blacklist(self.target)
        else:
            self.get_logger().warn(f'goal {self.target["goal"]} failed (status {status})')
            self._blacklist(self.target)
            self.failures += 1
        self.goal_handle, self.target = None, None

    def _blacklist(self, target):
        """Never stand at this goal again; give the frontier up after MAX_TRIES such goals."""
        self.bad_goals.append(target['goal'])
        self.bad_frontiers.append(target['frontier'])

    def _given_up(self, point):
        return sum(math.hypot(point[0] - x, point[1] - y) < 0.5 for x, y in self.bad_frontiers) >= MAX_TRIES

    # ------------------------------------------------------------------ geometry
    def _pose(self):
        try:
            t = self.tf.lookup_transform('map', 'base_footprint', Time()).transform
        except tf2_ros.TransformException:
            return None
        return t.translation.x, t.translation.y

    def _frontier_left(self, point, radius=0.5):
        return any(math.hypot(x - point[0], y - point[1]) < radius for x, y in self._frontier_cells)

    def _plan(self, pose, goals=True):
        """Find frontier clusters; with goals, also the best standing spot for each, best first."""
        info = self.map.info
        w, h, res = info.width, info.height, info.resolution
        ox, oy = info.origin.position.x, info.origin.position.y
        grid = np.asarray(self.map.data, dtype=np.int8).reshape(h, w)
        free = (grid >= 0) & (grid < 25)
        unknown = grid < 0
        self.known_m2 = float(np.count_nonzero(grid >= 0)) * res * res
        cross = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        frontier = free & (cv2.dilate(unknown.astype(np.uint8), cross) > 0)
        n, labels, stats, _ = cv2.connectedComponentsWithStats(frontier.astype(np.uint8), connectivity=8)
        to_world = lambda r, c: (ox + (c + 0.5) * res, oy + (r + 0.5) * res)  # noqa: E731
        min_cells = max(2, int(round(self.min_frontier / res)))
        clusters = []
        for i in range(1, n):
            if stats[i, cv2.CC_STAT_AREA] < min_cells:
                continue
            cells = np.argwhere(labels == i)
            centre = cells.mean(axis=0)
            r, c = cells[np.argmin(((cells - centre) ** 2).sum(axis=1))]  # a cluster cell near its middle
            clusters.append({'cells': cells, 'cell': (r, c), 'point': to_world(r, c), 'length': len(cells) * res})
        self._frontier_cells = [to_world(r, c) for cl in clusters for r, c in cl['cells'][::2]]
        self.frontiers = [[round(cl['point'][0], 2), round(cl['point'][1], 2), round(cl['length'], 2)] for cl in clusters]
        if not goals or pose is None or self.costmap is None:
            return []

        cost = self._costmap_on_map(w, h, res, ox, oy)
        passable = free & ~(cost >= BLOCKED_COST)
        standable = (free & (cost >= 0) & (cost <= GOAL_COST)).astype(np.uint8)
        for gx, gy in self.bad_goals:  # no standing near a goal that failed
            cv2.circle(standable, (int((gx - ox) / res), int((gy - oy) / res)), int(0.4 / res), 0, -1)
        standable = standable > 0
        # path length from the robot (cells), -1 where it cannot drive
        seed = np.zeros((h, w), np.uint8)
        cv2.circle(seed, (int((pose[0] - ox) / res), int((pose[1] - oy) / res)), int(0.3 / res), 1, -1)
        start = (seed > 0) & passable  # the robot's own cell may sit in inflation
        steps = self._wavefront(start if start.any() else seed > 0, passable)
        reach = int(self.approach / res)
        candidates = []
        for cl in clusters:
            if self._given_up(cl['point']):
                continue
            # spots within `approach` of the frontier *through free space*: in front of it,
            # not on the far side of a wall from it
            cells = np.zeros((h, w), bool)
            cells[cl['cells'][:, 0], cl['cells'][:, 1]] = True
            near = self._wavefront(cells, free, reach) >= 0
            ok = standable & near & (steps >= 0)
            if not ok.any():
                continue
            # short drive, but facing the frontier's middle: a spot at one end of a long frontier
            # (e.g. a doorway, looking along the shadow line behind a wall) sees little of it
            mid = np.zeros((h, w), bool)
            mid[cl['cell']] = True
            to_mid = self._wavefront(mid, free, 4 * reach)
            to_mid = np.where(to_mid >= 0, to_mid, 4 * reach)
            d = np.where(ok, steps + MID_WEIGHT * to_mid, np.inf)
            r, c = np.unravel_index(np.argmin(d), d.shape)
            path_m = steps[r, c] * res
            candidates.append({'goal': to_world(r, c), 'frontier': cl['point'], 'length': cl['length'],
                               'score': path_m - 0.5 * min(cl['length'], 3.0)})
        candidates.sort(key=lambda c: c['score'])
        return candidates

    def _costmap_on_map(self, w, h, res, ox, oy):
        """Global costmap values (0-100, -1 unknown) sampled at the centre of every /map cell."""
        cm = self.costmap
        ci = cm.info
        cgrid = np.asarray(cm.data, dtype=np.int16).reshape(ci.height, ci.width)
        cols = np.floor((ox + (np.arange(w) + 0.5) * res - ci.origin.position.x) / ci.resolution).astype(int)
        rows = np.floor((oy + (np.arange(h) + 0.5) * res - ci.origin.position.y) / ci.resolution).astype(int)
        cv_ok = (cols >= 0) & (cols < ci.width)
        rv_ok = (rows >= 0) & (rows < ci.height)
        out = np.full((h, w), -1, np.int16)
        out[np.ix_(rv_ok, cv_ok)] = cgrid[np.ix_(rows[rv_ok], cols[cv_ok])]
        return out

    @staticmethod
    def _wavefront(seed, allowed, limit=None):
        """Grid steps from the seed cells through allowed cells (8-connected), -1 where not reached."""
        steps = np.full(seed.shape, -1, np.int32)
        reached = seed.copy()
        steps[reached] = 0
        kernel = np.ones((3, 3), np.uint8)
        k = 0
        while limit is None or k < limit:
            k += 1
            grown = (cv2.dilate(reached.astype(np.uint8), kernel) > 0) & allowed & ~reached
            if not grown.any():
                break
            steps[grown] = k
            reached |= grown
        return steps

    # ------------------------------------------------------------------ output
    def _save(self):
        if self.map is None:
            self.message = '저장할 지도가 아직 없습니다.'
            return
        info = self.map.info
        grid = np.asarray(self.map.data, dtype=np.int16).reshape(info.height, info.width)
        img = np.full(grid.shape, 205, np.uint8)  # map_saver's trinary convention
        img[(grid >= 0) & (grid <= 25)] = 254
        img[grid >= 65] = 0
        os.makedirs(self.map_dir, exist_ok=True)
        name = time.strftime('airlab_explored_%Y%m%d_%H%M%S')
        base = os.path.join(self.map_dir, name)
        cv2.imwrite(base + '.pgm', np.flipud(img))  # image rows run top-down, grid rows bottom-up
        q = info.origin.orientation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        with open(base + '.yaml', 'w') as f:
            f.write(f'image: {name}.pgm\nmode: trinary\nresolution: {info.resolution:.3f}\n'
                    f'origin: [{info.origin.position.x:.3f}, {info.origin.position.y:.3f}, {yaw:.3f}]\n'
                    'negate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.25\n')
        self.saved = base + '.yaml'
        self.get_logger().info(f'map saved: {self.saved}')

    def _publish_status(self):
        t = self.target
        self.status_pub.publish(String(data=json.dumps({
            'state': self.state, 'message': self.message,
            'goal': [round(t['goal'][0], 2), round(t['goal'][1], 2)] if t else None,
            'target': [round(t['frontier'][0], 2), round(t['frontier'][1], 2)] if t else None,
            'frontiers': self.frontiers, 'known_m2': round(self.known_m2, 1),
            'goals': self.goals_sent, 'failures': self.failures,
            'elapsed': round(time.time() - self.started) if self.started else None,
            'saved': self.saved,
        }, ensure_ascii=False)))


def main():
    rclpy.init()
    node = FrontierExplorer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node._cancel_goal()
            node.destroy_node()
        except KeyboardInterrupt:  # a second Ctrl+C from ros2 launch while shutting down
            pass
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
