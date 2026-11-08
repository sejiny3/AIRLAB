#!/bin/bash
# π0.5 through the whole stack, served from Colab
P=/mnt/c/Users/sejin/AppData/Local/Temp/claude/C--Claude-project-AIRLAB/6128f651-d74c-4b9c-8b5a-3013d0c6e619/scratchpad/paper
SERVER=https://usa-teeth-ebony-along.trycloudflare.com
source /opt/ros/humble/setup.bash; source /mnt/c/Claude-project/AIRLAB/ros2_ws/install/setup.bash
stop_stack() {
  curl -s -m 5 -X POST localhost:8080/api/stack/stop > /dev/null
  for i in $(seq 40); do
    curl -s -m 3 localhost:8080/api/stack | grep -q '"state": "stopped"' && break
    sleep 1
  done
  sleep 5
}
stop_stack
echo "=== pi05 $(date +%H:%M:%S)"
curl -s -m 15 -X POST -H 'Content-Type: application/json' -d "{\"mode\":\"pi05\",\"llm\":\"scripted\",\"use_viewer\":false,\"rviz\":false,\"map\":\"\",\"server\":\"$SERVER\"}" localhost:8080/api/stack/start | cut -c1-100; echo
for i in $(seq 90); do
  curl -s -m 3 localhost:8080/api/stack | grep -q '"ready": true' && break
  sleep 2
done
sleep 15
python3 $P/trial.py pi05 3 $P/trial.jsonl 2>&1 | grep -v '^$' | cut -c1-170
stop_stack
echo "PI05 DONE $(date +%H:%M:%S)"
