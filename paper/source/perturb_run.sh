#!/bin/bash
# perturb_run.sh cnn|pi05 [server]: every condition, 50 scenes each, one process per condition
P=/mnt/c/Users/sejin/AppData/Local/Temp/claude/C--Claude-project-AIRLAB/6128f651-d74c-4b9c-8b5a-3013d0c6e619/scratchpad/paper
source /opt/ros/humble/setup.bash; source /mnt/c/Claude-project/AIRLAB/ros2_ws/install/setup.bash
cd /tmp
for c in V0 V1 V2 V3 V4 V5 V6 V7 V8; do
  python3 $P/perturb.py run "$1" $c $P/perturb.jsonl 50 "$2" 2>&1 | grep -v '^$' | tail -1
done
echo "DONE $1 $(date +%H:%M:%S)"
