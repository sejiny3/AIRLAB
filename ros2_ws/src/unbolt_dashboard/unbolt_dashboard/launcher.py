"""Keeps the dashboard page up while ROS is off, and starts the stack from its "연결" button.

  ros2 run unbolt_dashboard dashboard_launcher          # then open http://localhost:8080
  ros2 run unbolt_dashboard dashboard_launcher --port 8080 --allow-remote

It serves the same page as dashboard_server (site.py) and runs
  ros2 launch unbolt_manipulation bringup.launch.py planner:=true dashboard:=true ...
as a child process when the page asks. Inside that launch dashboard_server finds port
8080 taken and only does its ROS jobs; the page talks to ROS through rosbridge as usual,
and the "시스템 종료" button still ends the launch (the launcher just sees its child exit).

API (JSON), start/stop only from this machine unless --allow-remote:
  GET  /api/stack        state ("stopped" | "running" | "stopping"), ready, options, log tail, ...
  POST /api/stack/start  {"llm": "claude" | "scripted", "use_viewer": bool, "rviz": bool}
  POST /api/stack/stop   Ctrl+C for the launch (for a start that hangs before ROS connects)
"""

import argparse
import os
import re
import shutil
import signal
import socket
import subprocess
import threading
import time
from collections import deque
from http.server import ThreadingHTTPServer

from unbolt_dashboard.site import Site, default_map_yaml

ANSI = re.compile(r'\x1b\[[0-9;]*m')
READY_LINE = 'task planner ready'


def group_alive(pgid):
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def reap_group(pgid):
    """Stop whatever of the launch's process group outlived `ros2 launch` itself.

    A Ctrl+C that lands while the launch is still spawning its nodes reaches the launch
    but not the nodes started a moment later; they would keep rosbridge's port and the
    simulator alive with no parent."""
    for sig, wait in ((signal.SIGINT, 8), (signal.SIGTERM, 5), (signal.SIGKILL, 2)):
        if not group_alive(pgid):
            return
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            return
        end = time.time() + wait
        while time.time() < end and group_alive(pgid):
            time.sleep(0.2)


STACK_NODES = ('mujoco_bridge', 'component_container', 'move_group', 'task_planner', 'rosbridge_websocket')


def leftover_nodes():
    """Names of UNBOLT stack processes still running (e.g. a launch that is still shutting down)."""
    found = set()
    for pid in filter(str.isdigit, os.listdir('/proc')):
        try:
            with open(f'/proc/{pid}/cmdline', 'rb') as f:
                cmd = f.read().replace(b'\0', b' ').decode(errors='ignore')
        except OSError:
            continue
        found.update(n for n in STACK_NODES if n in cmd)
    return sorted(found)


def port_open(port):
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(('127.0.0.1', port)) == 0


class Stack:
    """The bringup launch as a child process (at most one)."""

    def __init__(self, rosbridge_port, log_path):
        self.rosbridge_port = rosbridge_port
        self.log_path = log_path
        self.lock = threading.Lock()
        self.proc = None
        self.state = 'stopped'
        self.options = None
        self.started = None
        self.ready = False
        self.returncode = None
        self.tail = deque(maxlen=12)

    def status(self):
        with self.lock:
            return {
                'state': self.state,
                'ready': self.ready,
                'options': self.options,
                'since': self.started,
                'elapsed': None if self.started is None else round(time.time() - self.started, 1),
                'returncode': self.returncode,
                'log': list(self.tail),
                'api_key': bool(os.environ.get('ANTHROPIC_API_KEY')),
                # a stack started from a terminal (not by this launcher) owns the rosbridge port
                'external': self.proc is None and port_open(self.rosbridge_port),
            }

    def start(self, llm='claude', use_viewer=True, rviz=False):
        with self.lock:
            if self.proc is not None:
                return False, '이미 실행 중입니다.'
            if port_open(self.rosbridge_port):
                return False, f'다른 곳에서 켠 ROS가 이미 실행 중입니다 (포트 {self.rosbridge_port} 사용 중).'
            left = leftover_nodes()
            if left:
                return False, f'이전 프로그램이 아직 꺼지는 중입니다 ({", ".join(left)}). 10초쯤 뒤에 다시 누르세요.'
            if llm not in ('claude', 'scripted'):
                return False, 'llm은 claude 또는 scripted'
            if llm == 'claude' and not os.environ.get('ANTHROPIC_API_KEY'):
                return False, 'ANTHROPIC_API_KEY가 없어 Claude를 쓸 수 없습니다. 대역(scripted)을 고르세요.'
            cmd = ['ros2', 'launch', 'unbolt_manipulation', 'bringup.launch.py', 'planner:=true', 'dashboard:=true',
                   f'llm:={llm}', f'use_viewer:={str(bool(use_viewer)).lower()}', f'rviz:={str(bool(rviz)).lower()}']
            env = dict(os.environ)
            if shutil.which('python3') != '/usr/bin/python3':
                # conda/venv first on PATH breaks every "#!/usr/bin/env python3" ROS tool (rosbridge first)
                env['PATH'] = '/usr/bin:/bin:' + env.get('PATH', '')
            log = open(self.log_path, 'w')
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
                                         start_new_session=True, text=True, bufsize=1)
            self.state, self.ready, self.returncode = 'running', False, None
            self.options = {'llm': llm, 'use_viewer': bool(use_viewer), 'rviz': bool(rviz)}
            self.started = time.time()
            self.tail.clear()
            threading.Thread(target=self._pump, args=(self.proc, log), daemon=True).start()
            return True, ' '.join(cmd)

    def stop(self):
        with self.lock:
            proc = self.proc
            if proc is None:
                return False, '실행 중이 아닙니다.'
            self.state = 'stopping'
        os.killpg(proc.pid, signal.SIGINT)  # what Ctrl+C in a terminal sends
        threading.Thread(target=self._escalate, args=(proc,), daemon=True).start()
        return True, 'Ctrl+C를 보냈습니다.'

    def _escalate(self, proc):
        for sig, wait in ((signal.SIGTERM, 30), (signal.SIGKILL, 10)):
            try:
                proc.wait(timeout=wait)
                return
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, sig)
                except ProcessLookupError:
                    return

    def _pump(self, proc, log):
        for line in proc.stdout:
            log.write(line)
            log.flush()
            text = ANSI.sub('', line).rstrip()
            with self.lock:
                if READY_LINE in text:
                    self.ready = True
                if text and 'Message Filter dropping' not in text:
                    self.tail.append(text[:300])
        code = proc.wait()
        with self.lock:
            self.state = 'stopping'
        reap_group(proc.pid)  # the launch is the group leader (start_new_session)
        with self.lock:
            if self.proc is proc:
                self.proc, self.state, self.returncode, self.ready = None, 'stopped', code, False
        log.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--rosbridge-port', type=int, default=9090)
    ap.add_argument('--allow-remote', action='store_true', help='accept start/stop from other machines too')
    ap.add_argument('--log', default=os.path.expanduser('~/.ros/unbolt_launcher.log'))
    args, _ = ap.parse_known_args()  # ros2 run may append --ros-args

    os.makedirs(os.path.dirname(args.log), exist_ok=True)
    stack = Stack(args.rosbridge_port, args.log)

    def api(h, method, path):
        if method == 'GET' and path == '/api/stack':
            return h.send_json(stack.status())
        if method == 'POST' and path in ('/api/stack/start', '/api/stack/stop'):
            if not args.allow_remote and h.client_address[0] not in ('127.0.0.1', '::1', '::ffff:127.0.0.1'):
                return h.send_json({'ok': False, 'message': '이 컴퓨터에서만 켜고 끌 수 있습니다 (--allow-remote).'}, 403)
            if path.endswith('/start'):
                body = h.read_json()
                ok, msg = stack.start(body.get('llm', 'claude'), body.get('use_viewer', True), body.get('rviz', False))
            else:
                ok, msg = stack.stop()
            return h.send_json({'ok': ok, 'message': msg, 'status': stack.status()}, 200 if ok else 409)
        return h.send_error(404)

    site = Site(default_map_yaml(), args.rosbridge_port, launcher=True)
    httpd = ThreadingHTTPServer(('0.0.0.0', args.port), site.handler(api))
    print(f'dashboard launcher on http://localhost:{args.port}/ (press 연결 to start ROS; Ctrl+C here stops both)',
          flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if stack.proc is not None:
            print('stopping the ROS launch ...', flush=True)
            stack.stop()
            end = time.time() + 60
            while stack.proc is not None and time.time() < end:  # includes reaping leftover nodes
                time.sleep(0.2)
        httpd.server_close()


if __name__ == '__main__':
    main()
