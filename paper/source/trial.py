"""Comparison trial through the whole ROS stack: trial.py <label> <rounds> <out.jsonl>

Each round resets the world, gathers the three boxes on the work table and puts them back (six
picks, six places), with the planner's scripted plan. Every planner event and every policy report
goes to the JSONL file with its receive time.
"""
import json
import statistics as st
import sys
import threading
import time

import rclpy
from rcl_interfaces.msg import Log
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile
from std_msgs.msg import Empty, String

label, rounds, path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
COMMANDS = ['상자를 모두 작업대에 모아 줘', '작업대의 상자를 모두 제자리로']
LIMIT = 1200.0

rclpy.init()
node = Node('trial')
out = open(path, 'a', encoding='utf8')
done, reset = threading.Event(), threading.Event()
final = {}
latencies = []
current = {'round': -1, 'command': ''}


def log(kind, e):
    out.write(json.dumps({'t': time.time(), 'label': label, **current, 'kind': kind, **e}, ensure_ascii=False) + '\n')
    out.flush()


def on_status(msg):
    e = json.loads(msg.data)
    if e.get('type') in ('tool_result', 'final', 'reset'):
        log('task', e)
    if e.get('type') == 'final':
        final.update(e)
        done.set()
    if e.get('type') == 'reset':
        final.update(e)
        reset.set()


def on_vla(msg):
    e = json.loads(msg.data)
    if e.get('latency') is not None:
        latencies.append(e['latency'])
        log('latency', {'latency': e['latency'], 'step': e.get('step')})


def on_result(msg):
    log('vla_result', json.loads(msg.data))


def on_log(msg):
    # why a pick failed: warnings and errors, and the skill's own account of each pick
    if msg.level >= 30 or ('pick' in msg.msg and msg.name != 'trial'):
        log('rosout', {'node': msg.name, 'level': msg.level, 'msg': msg.msg[:300]})


node.create_subscription(Log, '/rosout', on_log, QoSProfile(depth=200, durability=QoSDurabilityPolicy.VOLATILE))
node.create_subscription(String, '/task_status', on_status, 50)
node.create_subscription(String, '/vla/status', on_vla, 50)
node.create_subscription(String, '/vla/result', on_result, 10)
command = node.create_publisher(String, '/task_command', 10)
reset_pub = node.create_publisher(Empty, '/task_reset', 10)
threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()
time.sleep(3)

for r in range(rounds):
    current['round'] = r
    current['command'] = 'reset'
    reset.clear()
    reset_pub.publish(Empty())
    if not reset.wait(120):
        print('reset timed out', flush=True)
        break
    print(f'round {r}: reset ok={final.get("ok")}', flush=True)
    time.sleep(3)
    for c in COMMANDS:
        current['command'] = c
        done.clear()
        t0 = time.time()
        command.publish(String(data=c))
        finished = done.wait(LIMIT)
        print(f'round {r}: {c}: ok={final.get("ok") if finished else "TIMEOUT"} {time.time() - t0:.0f} s', flush=True)
        if not finished:
            break
        time.sleep(2)

rows = [json.loads(line) for line in open(path, encoding='utf8')]
rows = [x for x in rows if x['label'] == label and x.get('type') == 'tool_result']
for name in ('pick_object', 'place_object', 'navigate_to'):
    calls = [x for x in rows if x['name'] == name]
    good = [x['seconds'] for x in calls if x['ok']]
    if calls:
        print(f'{name}: {len(good)}/{len(calls)} ok, mean {st.mean(good) if good else 0:.1f} s, '
              f'sd {st.pstdev(good) if good else 0:.1f} s', flush=True)
if latencies:
    print(f'latency: n={len(latencies)} mean {st.mean(latencies):.3f} s, median {st.median(latencies):.3f} s, '
          f'max {max(latencies):.3f} s', flush=True)
rclpy.shutdown()
