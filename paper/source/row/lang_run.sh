#!/bin/bash
# stage 2 tests L1-L6 (50 scenes each) for the given policies: lang_run.sh cnn minilm  |  lang_run.sh pi05 <server>
export PYTHONPATH=/mnt/c/Claude-project/AIRLAB/ros2_ws/src/airlab_vla:$PYTHONPATH
source /opt/ros/humble/setup.bash 2>/dev/null
cd /tmp
if [ "$1" = pi05 ]; then
  for c in L1 L2 L3 L4 L5 L6; do python3 /mnt/c/Users/sejin/AppData/Local/Temp/claude/bebbd7cfb1237ce8/6128f651-d74c-4b9c-8b5a-3013d0c6e619/scratchpad/row/language.py run pi05 $c /mnt/c/Users/sejin/AppData/Local/Temp/claude/bebbd7cfb1237ce8/6128f651-d74c-4b9c-8b5a-3013d0c6e619/scratchpad/row/language.jsonl 50 "$2"; done
else
  for p in "$@"; do for c in L1 L2 L3 L4 L5 L6; do python3 /mnt/c/Users/sejin/AppData/Local/Temp/claude/bebbd7cfb1237ce8/6128f651-d74c-4b9c-8b5a-3013d0c6e619/scratchpad/row/language.py run $p $c /mnt/c/Users/sejin/AppData/Local/Temp/claude/bebbd7cfb1237ce8/6128f651-d74c-4b9c-8b5a-3013d0c6e619/scratchpad/row/language.jsonl 50; done; done
fi
echo DONE $(date +%T)
