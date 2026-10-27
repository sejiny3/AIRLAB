"""ROS 2 front end of the LLM task planner.

  ros2 run unbolt_manipulation task_planner --ros-args -p use_sim_time:=true
  ros2 run unbolt_manipulation ask "빨간 상자를 작업대로 옮겨줘"

Subscribes /task_command (std_msgs/String, one natural-language command) and
publishes every planning/execution event as JSON on /task_status (std_msgs/String).
One command runs at a time; commands that arrive while busy are rejected.
/task_cancel (std_msgs/Empty) stops the running task: base motions stop at once, an arm
motion in progress finishes, and no further step is started. /task_world (std_msgs/Empty)
asks for the current world state to be re-published (for a dashboard that just connected).
/task_reset (std_msgs/Empty) cancels a running task, then puts the robot and the objects back
at the start (simulator reset + AMCL re-initialised + planner world state reset).
/task_manual_drive (std_msgs/Empty) says the robot is being driven by hand (the dashboard's
keyboard driving): the robot is no longer at a known place, so the next task navigates first.

Parameters:
  llm      'claude' (default; needs ANTHROPIC_API_KEY or an `ant auth login` profile)
           'scripted' (replays the red-box plan without calling an LLM, for testing)
  model    Claude model id (default claude-opus-5-5)
  effort   output_config effort (default medium)
"""

import json
import threading

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from std_msgs.msg import Empty, String

from unbolt_manipulation.skills import RobotSkills
from unbolt_manipulation.task_planner_core import MODEL, ScriptedLLM, TaskExecutor, TaskPlanner


class TaskPlannerNode(Node):
    def __init__(self):
        super().__init__('task_planner')
        self.declare_parameter('llm', 'claude')
        self.declare_parameter('model', MODEL)
        self.declare_parameter('effort', 'medium')
        self.declare_parameter('pick_mode', 'classical')  # or 'vla': grasp with unbolt_vla's learned policy
        self.status_pub = self.create_publisher(String, '/task_status', 50)
        self.create_subscription(String, '/task_command', self._on_command, 10)
        self.create_subscription(Empty, '/task_cancel', self._on_cancel, 10)
        self.create_subscription(Empty, '/task_world', lambda _: self._publish_world(), 10)
        self.create_subscription(Empty, '/task_reset', self._on_reset, 10)
        self.create_subscription(Empty, '/task_manual_drive', self._on_manual_drive, 10)
        self.busy = threading.Lock()
        self.resetting = threading.Lock()

        self.get_logger().info('connecting to Nav2 / MoveIt ...')
        self.skills = RobotSkills()
        self.skills.wait_ready()
        self.executor_ = TaskExecutor(self.skills, pick_mode=self.get_parameter('pick_mode').value)
        llm_kind = self.get_parameter('llm').value
        llm = ScriptedLLM() if llm_kind == 'scripted' else None
        self.planner = TaskPlanner(self.executor_, llm=llm, model=self.get_parameter('model').value,
                                   effort=self.get_parameter('effort').value)
        self.llm_kind = llm_kind
        self._publish({'type': 'ready', 'llm': llm_kind, 'model': self.planner.model,
                       'pick_mode': self.executor_.pick_mode, 'world': self.executor_.world_state()})
        self.get_logger().info(f'task planner ready (llm={llm_kind}, pick={self.executor_.pick_mode}); '
                               'send commands on /task_command')

    def _publish(self, event):
        self.status_pub.publish(String(data=json.dumps(event, ensure_ascii=False)))
        if event['type'] == 'tool_result':  # keep dashboards' robot/object state current step by step
            self._publish_world()
        if event['type'] in ('command', 'tool_call', 'tool_result', 'final', 'thought', 'reply', 'error',
                             'cancel_requested', 'reset_requested', 'reset'):
            summary = {k: v for k, v in event.items() if k != 'type'}
            self.get_logger().info(f'[{event["type"]}] {json.dumps(summary, ensure_ascii=False)}')

    def _publish_world(self):
        self._publish({'type': 'world', 'busy': self.busy.locked(), 'llm': self.llm_kind,
                       'model': self.planner.model, 'pick_mode': self.executor_.pick_mode,
                       'world': self.executor_.world_state()})

    def _on_cancel(self, _msg):
        if self.busy.locked():
            self.skills.cancel_event.set()
            self.skills.stop()
            self._publish({'type': 'cancel_requested'})

    def _on_manual_drive(self, _msg):
        if self.busy.locked() or self.executor_.robot_location is None:
            return
        self.executor_.robot_location = None  # driven away from wherever it was
        self.get_logger().info('driven by hand: robot location now unknown')
        self._publish_world()

    def _on_reset(self, _msg):
        if self.resetting.acquire(blocking=False):  # a second press while resetting is ignored
            threading.Thread(target=self._reset, daemon=True).start()

    def _reset(self):
        try:
            self._publish({'type': 'reset_requested', 'busy': self.busy.locked()})
            self._on_cancel(None)
            # wait for the cancelled task to wind down (an arm motion in progress finishes first)
            if not self.busy.acquire(timeout=120.0):
                self._publish({'type': 'reset', 'ok': False, 'text': '진행 중인 작업이 끝나지 않아 초기화하지 못했습니다.'})
                return
            try:
                self._publish_world()
                ok = self.skills.reset_world()
                if ok:
                    self.executor_.reset()
                self.skills.cancel_event.clear()
                self._publish({'type': 'reset', 'ok': ok, 'text': '로봇과 물체를 처음 위치로 되돌렸습니다.' if ok
                               else '시뮬레이터 초기화에 실패했습니다. bringup 로그를 확인하세요.'})
            finally:
                self.busy.release()
                self._publish_world()
        finally:
            self.resetting.release()

    def _on_command(self, msg):
        if not self.busy.acquire(blocking=False):
            self._publish({'type': 'error', 'text': f'busy; ignored command: {msg.data}'})
            return
        threading.Thread(target=self._run, args=(msg.data,), daemon=True).start()

    def _run(self, command):
        try:
            if self.llm_kind == 'scripted':  # fresh script for every command
                self.planner.llm = ScriptedLLM()
            self.planner.run(command, on_event=self._publish)
        except Exception as e:  # API/auth errors etc. end the task, not the node
            self._publish({'type': 'final', 'ok': False, 'text': f'{type(e).__name__}: {e}'})
        finally:
            self.busy.release()
            self._publish_world()


def main():
    rclpy.init()
    node = TaskPlannerNode()
    # A private executor: Nav2's BasicNavigator spins the *global* executor from the planner
    # thread (spin_until_future_complete), so this node must not occupy it.
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.skills.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
