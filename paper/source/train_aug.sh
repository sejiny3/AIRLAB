#!/bin/bash
# CNN policy with openpi's image augmentation; the original policy.pt stays untouched
cd /mnt/c/Claude-project/AIRLAB/ros2_ws/src/airlab_vla
head -1 ~/airlab_vla/train.log
python3 -m airlab_vla.train --augment openpi --out ~/airlab_vla/policy_aug.pt 2>&1 | tee ~/airlab_vla/train_aug.log
