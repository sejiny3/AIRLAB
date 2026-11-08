#!/bin/bash
# eval_aug.sh: the openpi-augmented CNN on the 100 closed-loop scenes, the ask-other scenes, then V0-V8
P=/mnt/c/Users/sejin/AppData/Local/Temp/claude/C--Claude-project-AIRLAB/6128f651-d74c-4b9c-8b5a-3013d0c6e619/scratchpad/paper
source /opt/ros/humble/setup.bash; source /mnt/c/Claude-project/AIRLAB/ros2_ws/install/setup.bash
export PYTHONPATH=/mnt/c/Claude-project/AIRLAB/ros2_ws/src/airlab_vla:$PYTHONPATH
cd /tmp
python3 -m airlab_vla.evaluate --policy ~/airlab_vla/policy_aug.pt --episodes 100 2>&1 | tee $P/eval100_aug.txt | tail -4
python3 -m airlab_vla.evaluate --policy ~/airlab_vla/policy_aug.pt --episodes 20 --ask-other 2>&1 | tee $P/ask_other_aug.txt | tail -3
bash $P/perturb_run.sh cnn_aug
