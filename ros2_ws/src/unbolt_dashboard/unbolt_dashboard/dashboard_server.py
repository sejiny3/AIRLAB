"""ROS side of the UNBOLT dashboard (started by dashboard.launch.py with rosbridge).

Serves the dashboard page (see site.py) unless dashboard_launcher already does: then
port 8080 is taken and this node only does its ROS jobs.

Live data (camera, task progress, ...) flows browser <-> rosbridge_websocket directly.
The node also publishes /dashboard/robot_pose (geometry_msgs/PoseStamped, map frame) at
10 Hz from TF map -> base_footprint: /amcl_pose alone is latched and only updates after
0.2 m / 0.2 rad of motion, so a page that composes it with odometry gets stale headings.

/dashboard/shutdown (std_msgs/Empty) is the page's "시스템 종료" button: the node announces
it on /task_status and exits cleanly, and dashboard.launch.py turns that clean exit into a
shutdown of the whole launch (simulator, Nav2, MoveIt, planner, RViz).

  ros2 run unbolt_dashboard dashboard_server --ros-args -p port:=8080
"""

import errno
import json
import threading
import time
from http.server import ThreadingHTTPServer

import rclpy
import tf2_ros
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from rclpy.time import Time
from std_msgs.msg import Empty, String

from unbolt_dashboard.site import Site, default_map_yaml


class DashboardServer(Node):
    def __init__(self):
        super().__init__('dashboard_server', parameter_overrides=[
            rclpy.parameter.Parameter('use_sim_time', value=True)])
        self.tf = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf, self)
        self.pose_pub = self.create_publisher(PoseStamped, '/dashboard/robot_pose', 10)
        self.create_timer(0.1, self._publish_pose)
        self.status_pub = self.create_publisher(String, '/task_status', 10)
        self.create_subscription(Empty, '/dashboard/shutdown', self._on_shutdown, 10)
        self.shutdown_at = None  # wall time to exit at, once the button was pressed
        self.declare_parameter('port', 8080)
        self.declare_parameter('rosbridge_port', 9090)
        self.declare_parameter('map_yaml', '')

        port = self.get_parameter('port').value
        rosbridge_port = self.get_parameter('rosbridge_port').value
        site = Site(self.get_parameter('map_yaml').value or default_map_yaml(), rosbridge_port)
        self.httpd = None
        try:
            self.httpd = ThreadingHTTPServer(('0.0.0.0', port), site.handler())
        except OSError as e:
            if e.errno != errno.EADDRINUSE:
                raise
            self.get_logger().info(f'port {port} is taken (dashboard_launcher serves the page); '
                                   'running the ROS side only')
        if self.httpd is not None:
            threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
            self.get_logger().info(f'dashboard on http://localhost:{port}/ (rosbridge ws port {rosbridge_port})')

    def _on_shutdown(self, _msg):
        if self.shutdown_at is not None:
            return
        self.get_logger().warn('shutdown requested from the dashboard: stopping every program of this launch')
        self.status_pub.publish(String(data=json.dumps({'type': 'shutdown'})))
        self.shutdown_at = time.monotonic() + 1.0  # give rosbridge a moment to relay the event

    def _publish_pose(self):
        try:
            t = self.tf.lookup_transform('map', 'base_footprint', Time())
        except tf2_ros.TransformException:
            return  # no localization yet
        msg = PoseStamped()
        msg.header = t.header
        msg.pose.position.x, msg.pose.position.y = t.transform.translation.x, t.transform.translation.y
        msg.pose.orientation = t.transform.rotation
        self.pose_pub.publish(msg)


def main():
    rclpy.init()
    node = DashboardServer()
    try:
        # exit code 0 after the button is what dashboard.launch.py waits for
        while rclpy.ok() and (node.shutdown_at is None or time.monotonic() < node.shutdown_at):
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        if node.httpd is not None:
            node.httpd.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
