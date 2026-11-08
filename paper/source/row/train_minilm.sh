#!/bin/bash
# stage 2: CNN+MiniLM alone (run side by side with the norm stats it was OOM-killed at 11.5 GB)
cd /mnt/c/Claude-project/AIRLAB/ros2_ws/src/airlab_vla
python3 -m airlab_vla.train --demos ~/airlab_vla/demos_row --out ~/airlab_vla/policy_row_minilm.pt --text minilm --threads 6 > ~/airlab_vla/train_row_minilm.log 2>&1
tail -n 2 ~/airlab_vla/train_row_minilm.log
