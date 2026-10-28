"""Send one natural-language command to the task planner and print its progress until it finishes.

  ros2 run airlab_manipulation ask "빨간 상자를 작업대로 옮겨줘"
"""

import json
import sys
import time

import rclpy
from std_msgs.msg import String


def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith('--'):
        print('usage: ros2 run airlab_manipulation ask "<command>"')
        return 2
    command = sys.argv[1]
    rclpy.init()
    node = rclpy.create_node('task_ask')
    done = {}

    def on_status(msg):
        e = json.loads(msg.data)
        t = e.get('type')
        if t == 'command' and e.get('text') == command:
            done['started'] = True
        if not done.get('started') and t != 'error':
            return
        if t == 'tool_call':
            print(f'  -> {e["name"]}({json.dumps(e["input"], ensure_ascii=False)})', flush=True)
        elif t == 'tool_result':
            r = e['result']
            res = r.get('message') or r.get('error') or ''
            if 'spots' in r:  # check_table: what the camera saw on each spot
                res = ', '.join(f'{s}: {b or "empty"}' for s, b in r['spots'].items())
                res += f'; not found: {", ".join(r["not_found"])}' if r.get('not_found') else ''
            print(f'     {"OK" if e["ok"] else "FAILED"} ({e["seconds"]:.0f} s) {res}', flush=True)
        elif t in ('thought', 'reply'):
            print(f'  [claude] {e["text"]}', flush=True)
        elif t == 'error':
            print(f'  [error] {e["text"]}', flush=True)
            done['final'] = e
        elif t == 'final':
            print(f'== {"done" if e["ok"] else "FAILED"} in {e.get("seconds", 0):.0f} s: {e["text"]}', flush=True)
            u = e.get('usage') or {}
            if u.get('input_tokens'):
                # list price of claude-opus-5-5: $4 / $20 per million input / output tokens
                cost = (u['input_tokens'] * 4 + u['output_tokens'] * 20) / 1e6
                print(f'   tokens: {u["input_tokens"]} in / {u["output_tokens"]} out (about ${cost:.3f})', flush=True)
            done['final'] = e

    node.create_subscription(String, '/task_status', on_status, 50)
    pub = node.create_publisher(String, '/task_command', 10)
    while pub.get_subscription_count() == 0:
        rclpy.spin_once(node, timeout_sec=0.2)
    time.sleep(0.5)
    print(f'>> {command}', flush=True)
    pub.publish(String(data=command))
    while 'final' not in done:
        rclpy.spin_once(node, timeout_sec=0.2)
    node.destroy_node()
    rclpy.shutdown()
    return 0 if done['final'].get('ok') else 1


if __name__ == '__main__':
    sys.exit(main())
