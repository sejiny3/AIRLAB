#!/bin/bash
# stage 2, π0.5 data: row demos -> LeRobot airlab/row_pi05 -> norm stats -> tar for Drive
set -e
export PATH=$HOME/.local/bin:$HOME/.cargo/bin:$PATH
cd /mnt/c/Claude-project/AIRLAB
rm -rf ~/.cache/huggingface/lerobot/airlab/row_pi05
time uv run pi05/convert_to_lerobot.py --demos ~/airlab_vla/demos_row_pi05 --repo-id airlab/row_pi05
cd ~/airlab_vla/openpi
time .venv/bin/python /mnt/c/Claude-project/AIRLAB/pi05/run_openpi.py scripts/compute_norm_stats.py --config-name pi05_airlab_row
ls -l /mnt/c/Claude-project/AIRLAB/pi05/assets/pi05_airlab_row/airlab/row_pi05/
tar -cf ~/airlab_vla/row_pi05.tar -C ~/.cache/huggingface/lerobot/airlab row_pi05
ls -lh ~/airlab_vla/row_pi05.tar
echo CONVERT_DONE
