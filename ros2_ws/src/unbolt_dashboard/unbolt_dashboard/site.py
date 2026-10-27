"""The dashboard web page and the two generated files it needs, for any HTTP server.

Both dashboard_server (inside the ROS launch) and dashboard_launcher (outside it, so the
page stays up while ROS is off) serve the same site:
  /             web/index.html
  /map.png      the Nav2 map in use (default unbolt_navigation/maps/unbolt_room) as an image
  /config.json  map geometry (resolution, origin, size), known places and the rosbridge port
"""

import json
import os
from http.server import SimpleHTTPRequestHandler

import cv2
import yaml
from ament_index_python.packages import get_package_share_directory

from unbolt_manipulation.task_planner_core import LOCATIONS, OBJECTS

# Table footprints from models/scene.xml (centre x, y, half sizes along map x and y), for drawing on the map.
TABLES = {
    'supply_1': (0.0, -3.7, 0.60, 0.25),
    'supply_2': (2.0, 3.7, 0.60, 0.25),
    'supply_3': (-2.95, 2.6, 0.25, 0.60),
    'work_table': (4.8, 0.0, 0.35, 0.60),
}


def default_map_yaml():
    return os.path.join(get_package_share_directory('unbolt_navigation'), 'maps', 'unbolt_room.yaml')


class Site:
    def __init__(self, map_yaml, rosbridge_port, launcher=False):
        self.web_dir = os.path.join(get_package_share_directory('unbolt_dashboard'), 'web')
        self.rosbridge_port = rosbridge_port
        self.launcher = launcher
        self.load(map_yaml)

    def load(self, map_yaml):
        """Serve `map_yaml` (a Nav2 map) as /map.png and in /config.json from now on."""
        meta = yaml.safe_load(open(map_yaml))
        img = cv2.imread(os.path.join(os.path.dirname(map_yaml), meta['image']), cv2.IMREAD_GRAYSCALE)
        self.map_yaml = map_yaml
        self.map_png = cv2.imencode('.png', img)[1].tobytes()
        self.config = json.dumps({
            'rosbridge_port': self.rosbridge_port,
            'launcher': self.launcher,  # the page offers the "연결" (start) button only with a launcher
            'map_name': os.path.splitext(os.path.basename(map_yaml))[0],
            'map': {'resolution': meta['resolution'], 'origin': meta['origin'][:2],
                    'width': int(img.shape[1]), 'height': int(img.shape[0])},
            'locations': {k: {'staging': v['staging'], 'spots': v['spots'],
                              'description': v['description']} for k, v in LOCATIONS.items()},
            'tables': {k: {'center': v[:2], 'half': v[2:]} for k, v in TABLES.items()},
            'objects': {k: {'marker': v['marker'], 'description': v['description']} for k, v in OBJECTS.items()},
        }, ensure_ascii=False).encode()

    def handler(self, api=None):
        """Request handler class; `api(handler, method, path)` may answer /api/... requests."""
        site = self

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=site.web_dir, **kwargs)

            def do_GET(self):
                path = self.path.split('?')[0]
                if path == '/map.png':
                    return self.send_body(site.map_png, 'image/png')
                if path == '/config.json':
                    return self.send_body(site.config, 'application/json; charset=utf-8')
                if path.startswith('/api/'):
                    return self._api('GET', path)
                return super().do_GET()

            def do_POST(self):
                return self._api('POST', self.path.split('?')[0])

            def _api(self, method, path):
                if api is None or not path.startswith('/api/'):
                    return self.send_error(404)
                return api(self, method, path)

            def send_json(self, obj, code=200):
                self.send_body(json.dumps(obj, ensure_ascii=False).encode(), 'application/json; charset=utf-8', code)

            def read_json(self):
                n = int(self.headers.get('Content-Length') or 0)
                try:
                    return json.loads(self.rfile.read(n) or b'{}')
                except ValueError:
                    return {}

            def send_body(self, body, ctype, code=200):
                self.send_response(code)
                self.send_header('Content-Type', ctype)
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def end_headers(self):
                if self.path.endswith('.html') or self.path == '/':
                    self.send_header('Cache-Control', 'no-store')
                super().end_headers()

            def log_message(self, fmt, *args):  # keep the logs quiet
                pass

        return Handler
