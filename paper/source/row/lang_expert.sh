#!/bin/bash
export PYTHONPATH=/mnt/c/Claude-project/AIRLAB/ros2_ws/src/airlab_vla
cd /tmp
python3 /mnt/c/Users/sejin/AppData/Local/Temp/claude/bebbd7cfb1237ce8/6128f651-d74c-4b9c-8b5a-3013d0c6e619/scratchpad/row/language.py list 3
rm -f /mnt/c/Users/sejin/AppData/Local/Temp/claude/bebbd7cfb1237ce8/6128f651-d74c-4b9c-8b5a-3013d0c6e619/scratchpad/row/language_expert.jsonl
for c in L1 L2 L3 L4 L5 L6; do python3 /mnt/c/Users/sejin/AppData/Local/Temp/claude/bebbd7cfb1237ce8/6128f651-d74c-4b9c-8b5a-3013d0c6e619/scratchpad/row/language.py expert $c /mnt/c/Users/sejin/AppData/Local/Temp/claude/bebbd7cfb1237ce8/6128f651-d74c-4b9c-8b5a-3013d0c6e619/scratchpad/row/language_expert.jsonl 50; done
