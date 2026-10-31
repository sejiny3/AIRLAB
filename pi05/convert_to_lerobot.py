# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = [
#     "lerobot @ git+https://github.com/huggingface/lerobot@0cf864870cf29f4738d3ade893e6fd13fbd7cdb5",
#     "numpy>=1.22.4,<2",
#     "torch",
#     "torchvision",
# ]
#
# [tool.uv]
# # packages as they were when openpi pinned this lerobot commit (newer pyarrow needs numpy 2)
# exclude-newer = "2025-04-01T00:00:00Z"
#
# # the laptop has no GPU: CPU wheels instead of the 2.5 GB CUDA ones
# [[tool.uv.index]]
# name = "pytorch-cpu"
# url = "https://download.pytorch.org/whl/cpu"
# explicit = true
#
# [tool.uv.sources]
# torch = { index = "pytorch-cpu" }
# torchvision = { index = "pytorch-cpu" }
# ///
"""Turn the π0.5 demos (record --cameras pi05) into a LeRobot dataset for openpi.

  uv run pi05/convert_to_lerobot.py --demos ~/airlab_vla/demos_pi05

The same LeRobot version openpi pins, and the feature names its LIBERO example uses, so the
openpi training config only has to map them (see pi05/README.md):

  image        (224, 224, 3) uint8   head camera: 224x126, padded to a square with black bars
                                     above and below (what openpi's resize_with_pad does)
  wrist_image  (224, 224, 3) uint8   right wrist camera
  state        (8,) float32          right arm joints 1-7 + finger, measured
  actions      (8,) float32          joint targets the expert commands at that step
  done         (1,) float32          1 on the final hold steps (the pick is finished)
  task         the instruction sentence ("pick up the red box")

One LeRobot episode per demo, at the 10 Hz the demos were recorded at. The dataset is written
to $HF_LEROBOT_HOME/<repo-id> (default ~/.cache/huggingface/lerobot/<repo-id>).
"""

import argparse
import glob
import os
import shutil
import time

import numpy as np
from lerobot.common.datasets.lerobot_dataset import HF_LEROBOT_HOME, LeRobotDataset

FPS = 10  # airlab_vla.sim.CONTROL_HZ
SIZE = 224


def pad_square(images):
    """(T, h, 224, 3) -> (T, 224, 224, 3), the image centred between black bars."""
    t, h, w, c = images.shape
    top = (SIZE - h) // 2
    out = np.zeros((t, SIZE, SIZE, c), np.uint8)
    out[:, top:top + h] = images
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--demos', default=os.path.expanduser('~/airlab_vla/demos_pi05'))
    ap.add_argument('--repo-id', default='airlab/pick_pi05', help='dataset name (and Hub repo if pushed)')
    ap.add_argument('--limit', type=int, help='only the first N demos (a quick test)')
    ap.add_argument('--push', action='store_true', help='upload to the Hugging Face Hub as a private dataset')
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(a.demos, 'ep_*.npz')))[:a.limit]
    if not files:
        raise SystemExit(f'no ep_*.npz in {a.demos}')
    first = np.load(files[0])
    if first['wrist'].shape[1:3] != (SIZE, SIZE) or first['head'].shape[2] != SIZE:
        raise SystemExit(f'{a.demos} was not recorded with --cameras pi05 '
                         f'(head {first["head"].shape[1:3]}, wrist {first["wrist"].shape[1:3]})')

    out = HF_LEROBOT_HOME / a.repo_id
    shutil.rmtree(out, ignore_errors=True)
    image = {'dtype': 'image', 'shape': (SIZE, SIZE, 3), 'names': ['height', 'width', 'channel']}
    dataset = LeRobotDataset.create(
        repo_id=a.repo_id,
        robot_type='openarm',
        fps=FPS,
        features={
            'image': image,
            'wrist_image': dict(image),
            'state': {'dtype': 'float32', 'shape': (8,), 'names': ['state']},
            'actions': {'dtype': 'float32', 'shape': (8,), 'names': ['actions']},
            'done': {'dtype': 'float32', 'shape': (1,), 'names': ['done']},
        },
        image_writer_threads=10,
        image_writer_processes=5,
    )

    t0, frames = time.time(), 0
    for i, f in enumerate(files):
        ep = np.load(f)
        head, task = pad_square(ep['head']), str(ep['instruction'])
        for t in range(len(ep['action'])):
            dataset.add_frame({
                'image': head[t],
                'wrist_image': ep['wrist'][t],
                'state': ep['state'][t].astype(np.float32),
                'actions': ep['action'][t].astype(np.float32),
                'done': ep['done'][t:t + 1].astype(np.float32),
                'task': task,
            })
        dataset.save_episode()
        frames += len(ep['action'])
        if (i + 1) % 50 == 0 or i + 1 == len(files):
            print(f'{i + 1}/{len(files)} episodes, {frames} frames ({time.time() - t0:.0f} s)', flush=True)

    print(f'dataset in {out}')
    if a.push:
        dataset.push_to_hub(private=True, tags=['airlab', 'openarm', 'pi05'])
        print(f'pushed to https://huggingface.co/datasets/{a.repo_id}')


if __name__ == '__main__':
    main()
