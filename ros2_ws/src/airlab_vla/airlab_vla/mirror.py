"""Drive the LEFT arm with a policy trained on the right arm, through the mirror.

The two OpenArm arms are exact mirror images across the robot base's x-z plane: left joint =
sim.MIRROR * right joint puts every link and the wrist camera at the mirror image (checked by
forward kinematics), the head camera sits on that plane looking forward, and the left wrist
camera is the mirror of the right one. So the left arm's situation, seen in a mirror, is a
right-arm situation the policy knows:

  images        head and wrist flipped left-right
  state/action  multiplied by MIRROR (the left arm's joints as the right arm's, and back)
  instruction   'left' and 'right' swapped ('왼쪽' and '오른쪽' too), nothing else

The room is not symmetric, so the flipped background is one the policy never saw.
"""

import re

import numpy as np

from airlab_vla.sim import MIRROR

SWAP = {'left': 'right', 'right': 'left', '왼쪽': '오른쪽', '오른쪽': '왼쪽'}
SWAP_WORDS = re.compile(r'\b(left|right)\b|왼쪽|오른쪽', re.IGNORECASE)


def mirror_words(text):
    """The instruction as seen in the mirror: left and right swap, nothing else changes."""
    def swap(m):
        word = m.group(0)
        out = SWAP[word.lower()]
        return out.capitalize() if word[0].isupper() else out
    return SWAP_WORDS.sub(swap, text)


class MirroredRunner:
    """A right-arm policy (runner.PolicyRunner, or remote.RemoteRunner for π0.5) on the left arm."""

    def __init__(self, runner):
        self.runner = runner

    @property
    def latency(self):
        return self.runner.latency

    def reset(self, instruction):
        self.runner.reset(mirror_words(instruction))

    def act(self, head, wrist, state):
        """The left arm's view and joint angles in, the left arm's targets out (None while a
        remote policy is still thinking, as RemoteRunner.act)."""
        got = self.runner.act(np.ascontiguousarray(head[:, ::-1]), np.ascontiguousarray(wrist[:, ::-1]),
                              MIRROR * np.asarray(state, np.float32))
        if got is None:
            return None
        action, done = got
        return MIRROR * np.asarray(action, np.float32), done
