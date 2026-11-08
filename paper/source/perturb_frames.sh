#!/bin/bash
# episode 0's views under every condition, both camera sizes, one process each
P=/mnt/c/Users/sejin/AppData/Local/Temp/claude/C--Claude-project-AIRLAB/6128f651-d74c-4b9c-8b5a-3013d0c6e619/scratchpad/paper
source /opt/ros/humble/setup.bash; source /mnt/c/Claude-project/AIRLAB/ros2_ws/install/setup.bash
mkdir -p $P/frames
cd /tmp
for c in V0 V1 V2 V3 V4 V5 V6 V7 V8; do
  for cam in small pi05; do
    python3 $P/perturb.py frame $cam $c $P/frames/${c}_$cam.png 2>&1 | grep -v '^$' | tail -1
  done
done
