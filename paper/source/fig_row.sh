#!/bin/bash
# Fig. 3 of the paper: the policy inputs of the first choosing-task scene (run from Windows: MSYS_NO_PATHCONV=1 wsl bash -l fig_row.sh)
export PYTHONPATH=/mnt/c/Claude-project/AIRLAB/ros2_ws/src/airlab_vla:$PYTHONPATH
source /opt/ros/humble/setup.bash 2>/dev/null
cd /tmp
python3 /mnt/c/Claude-project/AIRLAB/paper/source/fig_row.py
