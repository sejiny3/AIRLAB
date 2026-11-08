#!/bin/bash
# paraphrase.sh cnn|pi05 [episodes] [server]
P=/mnt/c/Users/sejin/AppData/Local/Temp/claude/C--Claude-project-AIRLAB/6128f651-d74c-4b9c-8b5a-3013d0c6e619/scratchpad/paper
source /opt/ros/humble/setup.bash; source /mnt/c/Claude-project/AIRLAB/ros2_ws/install/setup.bash
cd /tmp && python3 $P/paraphrase.py "$1" $P/paraphrase.jsonl "${2:-50}" "$3" 2>&1 | grep -v '^$'
