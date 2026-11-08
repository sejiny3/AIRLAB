#!/bin/bash
# stage 2 demos: the three-box row, 2000 attempts at each camera size (same seeds, so the same scenes)
export PYTHONPATH=/mnt/c/Claude-project/AIRLAB/ros2_ws/src/airlab_vla
cd /tmp
python3 -m airlab_vla.record --task row --episodes 2000 --workers 7 2>&1 | tail -2
python3 -m airlab_vla.record --task row --episodes 2000 --workers 7 --cameras pi05 2>&1 | tail -2
echo DONE $(date +%T)
