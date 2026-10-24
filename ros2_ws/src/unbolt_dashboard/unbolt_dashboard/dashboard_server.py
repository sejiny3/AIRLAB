"""Static web server for the UNBOLT dashboard.

Serves web/index.html plus two generated files the page needs before it talks to
rosbridge:
  /map.png      the saved Nav2 map (unbolt_navigation/maps/unbolt_room) as an image
  /config.json  map geometry (resolution, origin, size), known places and the rosbridge port

Live data (camera, task progress, ...) flows browser <-> rosbridge_websocket directly.
The node also publishes /dashboard/robot_pose (geometry_msgs/PoseStamped, map frame) at
10 Hz from TF map -> base_footprint: /amcl_pose alone is latched and only updates after
0.2 m / 0.2 rad of motion, so a page that composes it with odometry gets stale headings.

  ros2 run unbolt_dashboard dashboard_server --ros-args -p port:=8080
"""

import json
import os
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import cv2
import rclpy
import tf2_ros
import yaml
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from rclpy.time import Time

from unbolt_manipulation.task_planner_core import LOCATIONS, OBJECTS

# Table footprints from models/scene.xml (centre x, y, half sizes), for drawing on the map.
TABLES = {
    'supply_table': (-0.15, -2.45, 0.40, 0.25),
    'work_table': (2.20, 0.00, 0.35, 0.50),
}


class DashboardServer(Node):
    def __init__(self):
        super().__init__('dashboard_server', parameter_overrides=[
            rclpy.parameter.Parameter('use_sim_time', value=True)])
        self.tf = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf, self)
        self.pose_pub = self.create_publisher(PoseStamped, '/dashboard/robot_pose', 10)
        self.create_timer(0.1, self._publish_pose)
        self.declare_parameter('port', 8080)
        self.declare_parameter('rosbridge_port', 9090)
        nav_share = get_package_share_directory('unbolt_navigation')
        self.declare_parameter('map_yaml', os.path.join(nav_share, 'maps', 'unbolt_room.yaml'))
        self.web_dir = os.path.join(get_package_share_directory('unbolt_dashboard'), 'web')

        map_yaml = self.get_parameter('map_yaml').value
        meta = yaml.safe_load(open(map_yaml))
        img = cv2.imread(os.path.join(os.path.dirname(map_yaml), meta['image']), cv2.IMREAD_GRAYSCALE)
        self.map_png = cv2.imencode('.png', img)[1].tobytes()
        self.config = json.dumps({
            'rosbridge_port': self.get_parameter('rosbridge_port').value,
            'map': {'resolution': meta['resolution'], 'origin': meta['origin'][:2],
                    'width': int(img.shape[1]), 'height': int(img.shape[0])},
            'locations': {k: {'staging': v['staging'], 'place_marker': v['place_marker'],
                              'description': v['description']} for k, v in LOCATIONS.items()},
            'tables': {k: {'center': v[:2], 'half': v[2:]} for k, v in TABLES.items()},
            'objects': {k: {'marker': v['marker'], 'description': v['description']} for k, v in OBJECTS.items()},
        }, ensure_ascii=False).encode()

        server = self

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=server.web_dir, **kwargs)

            def do_GET(self):
                if self.path.split('?')[0] == '/map.png':
                    return self._send(server.map_png, 'image/png')
                if self.path.split('?')[0] == '/config.json':
                    return self._send(server.config, 'application/json; charset=utf-8')
                return super().do_GET()

            def _send(self, body, ctype):
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def end_headers(self):
                if self.path.endswith('.html') or self.path == '/':
                    self.send_header('Cache-Control', 'no-store')
                super().end_headers()

            def log_message(self, fmt, *args):  # keep the ROS log quiet
                pass

        port = self.get_parameter('port').value
        self.httpd = ThreadingHTTPServer(('0.0.0.0', port), Handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.get_logger().info(f'dashboard on http://localhost:{port}/ (rosbridge ws port '
                               f'{self.get_parameter("rosbridge_port").value})')

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
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.httpd.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
