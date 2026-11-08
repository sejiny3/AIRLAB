#!/bin/bash
# stage 2: the CNN policy on the row demos, with hashed words and with frozen MiniLM (4 threads each, side by side)
cd /mnt/c/Claude-project/AIRLAB/ros2_ws/src/airlab_vla
python3 -m airlab_vla.train --demos ~/airlab_vla/demos_row --out ~/airlab_vla/policy_row.pt --threads 4 > ~/airlab_vla/train_row.log 2>&1 &
python3 -m airlab_vla.train --demos ~/airlab_vla/demos_row --out ~/airlab_vla/policy_row_minilm.pt --text minilm --threads 4 > ~/airlab_vla/train_row_minilm.log 2>&1 &
wait
tail -1 ~/airlab_vla/train_row.log ~/airlab_vla/train_row_minilm.log
