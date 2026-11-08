#!/bin/bash
# the comparison on an idle machine: CPU inference time, then IK and CNN through the whole stack
P=/mnt/c/Users/sejin/AppData/Local/Temp/claude/C--Claude-project-AIRLAB/6128f651-d74c-4b9c-8b5a-3013d0c6e619/scratchpad/paper
source /opt/ros/humble/setup.bash; source /mnt/c/Claude-project/AIRLAB/ros2_ws/install/setup.bash

stop_stack() {
  curl -s -m 5 -X POST localhost:8080/api/stack/stop > /dev/null
  for i in $(seq 40); do
    curl -s -m 3 localhost:8080/api/stack | grep -q '"state": "stopped"' && break
    sleep 1
  done
  sleep 5
}
start() {
  curl -s -m 15 -X POST -H 'Content-Type: application/json' -d "$1" localhost:8080/api/stack/start | cut -c1-100; echo
  for i in $(seq 90); do
    curl -s -m 3 localhost:8080/api/stack | grep -q '"ready": true' && break
    sleep 2
  done
  sleep 15
}

stop_stack
pkill -9 -f fake_serve[r].py
python3 - <<'EOF'
import os, torch
s = torch.load(os.path.expanduser('~/airlab_vla/policy.pt'), map_location='cpu', weights_only=False)['state_dict']
print('cnn parameters', sum(v.numel() for k, v in s.items() if k not in ('mean', 'std')))
EOF
python3 $P/latency_cnn.py 2>&1 | tail -1

for mode in task vla; do
  echo "=== $mode $(date +%H:%M:%S)"
  start "{\"mode\":\"$mode\",\"llm\":\"scripted\",\"use_viewer\":false,\"rviz\":false,\"map\":\"\"}"
  python3 $P/trial.py $mode 3 $P/trial.jsonl 2>&1 | grep -v '^$' | cut -c1-170
  stop_stack
done
echo "ALL DONE $(date +%H:%M:%S)"
