"""The AIRLAB pick in openpi: what goes into π0.5, what comes out, and the training config.

openpi's own code stays as it is: run_openpi.py adds CONFIG to its list and runs its scripts.

  image   the head camera is the base view, the right wrist camera the right wrist view;
          the left wrist view is masked (the left arm stays tucked)
  state   8 joint angles (right arm 1-7, finger). π0.5 reads them as part of the prompt
  action  9 numbers per step: the 8 joint targets and "done". The first 7 are learned relative
          to the state at the start of the chunk; the finger and "done" stay absolute
"""

import dataclasses
import pathlib

import einops
import numpy as np
from openpi import transforms
import openpi.models.pi0_config as pi0_config
from openpi.training import config as _config
import openpi.training.optimizer as _optimizer
import openpi.training.weight_loaders as weight_loaders

ACTION_DIM = 9   # 8 joint targets + done
HORIZON = 10     # the small policy's chunk (airlab_vla.model.CHUNK), 1 s at 10 Hz
STEPS = 15_000


def _image(image):
    """LeRobot gives float (c, h, w), the policy client uint8 (h, w, c)."""
    image = np.asarray(image)
    if np.issubdtype(image.dtype, np.floating):
        image = (255 * image).astype(np.uint8)
    if image.shape[0] == 3:
        image = einops.rearrange(image, 'c h w -> h w c')
    return image


@dataclasses.dataclass(frozen=True)
class AirlabInputs(transforms.DataTransformFn):
    def __call__(self, data):
        head, wrist = _image(data['observation/image']), _image(data['observation/wrist_image'])
        inputs = {
            'state': data['observation/state'],
            'image': {'base_0_rgb': head, 'left_wrist_0_rgb': np.zeros_like(head), 'right_wrist_0_rgb': wrist},
            'image_mask': {'base_0_rgb': np.True_, 'left_wrist_0_rgb': np.False_, 'right_wrist_0_rgb': np.True_},
        }
        if 'actions' in data:  # training only
            inputs['actions'] = np.concatenate([data['actions'], np.asarray(data['done']).reshape(-1, 1)], axis=-1)
        if 'prompt' in data:
            inputs['prompt'] = data['prompt']
        return inputs


@dataclasses.dataclass(frozen=True)
class AirlabOutputs(transforms.DataTransformFn):
    def __call__(self, data):
        return {'actions': np.asarray(data['actions'][..., :ACTION_DIM])}  # the model pads to 32


@dataclasses.dataclass(frozen=True)
class AirlabDataConfig(_config.DataConfigFactory):
    def create(self, assets_dirs, model_config):
        repack = transforms.Group(inputs=[transforms.RepackTransform({
            'observation/image': 'image',
            'observation/wrist_image': 'wrist_image',
            'observation/state': 'state',
            'actions': 'actions',
            'done': 'done',
            'prompt': 'prompt',
        })])
        relative = transforms.make_bool_mask(7)  # the arm joints; a shorter mask leaves the rest as it is
        data = transforms.Group(inputs=[AirlabInputs()], outputs=[AirlabOutputs()]).push(
            inputs=[transforms.DeltaActions(relative)],
            outputs=[transforms.AbsoluteActions(relative)],
        )
        return dataclasses.replace(
            self.create_base_config(assets_dirs, model_config),
            repack_transforms=repack,
            data_transforms=data,
            model_transforms=_config.ModelTransformFactory()(model_config),
        )


# LoRA: PaliGemma and the action expert keep their pretrained weights and only small low-rank
# additions are trained, which is what lets this fit on one 40 GB (or 24 GB) GPU.
MODEL = pi0_config.Pi0Config(
    pi05=True,
    action_horizon=HORIZON,
    paligemma_variant='gemma_2b_lora',
    action_expert_variant='gemma_300m_lora',
)

CONFIG = _config.TrainConfig(
    name='pi05_airlab',
    model=MODEL,
    data=AirlabDataConfig(
        repo_id='airlab/pick_pi05',
        base_config=_config.DataConfig(prompt_from_task=True, action_sequence_keys=('actions', 'done')),
    ),
    weight_loader=weight_loaders.CheckpointWeightLoader('gs://openpi-assets/checkpoints/pi05_base/params'),
    freeze_filter=MODEL.get_freeze_filter(),
    ema_decay=None,  # openpi turns EMA off for LoRA fine-tuning
    lr_schedule=_optimizer.CosineDecaySchedule(decay_steps=STEPS),
    num_train_steps=STEPS,
    save_interval=5000,  # a checkpoint is about 11 GB
    keep_period=None,
    wandb_enabled=False,
    assets_base_dir=str(pathlib.Path(__file__).parent / 'assets'),  # norm_stats.json, computed once and committed
)
