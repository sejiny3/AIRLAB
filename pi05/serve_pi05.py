"""Serve the fine-tuned π0.5 to the robot's vla_pick node, from the openpi folder:

  .venv/bin/python ../AIRLAB/pi05/serve_pi05.py --checkpoint /path/to/checkpoints/pi05_airlab/run1/5000

openpi's websocket server, on this machine only: a tunnel (see serve_colab.sh) carries it out.
/healthz answers once the model is loaded and compiled, so a robot never waits on that.
"""

import argparse
import logging

import numpy as np
import airlab_policy
from openpi.policies import policy_config
from openpi.serving import websocket_policy_server

SIZE = 224


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--checkpoint', required=True, help='a step folder, e.g. .../pi05_airlab/run1/5000')
    ap.add_argument('--config', default=airlab_policy.CONFIG.name, choices=sorted(airlab_policy.CONFIGS))
    ap.add_argument('--port', type=int, default=8000)
    a = ap.parse_args()

    logging.basicConfig(level=logging.INFO, force=True)
    policy = policy_config.create_trained_policy(airlab_policy.CONFIGS[a.config], a.checkpoint)
    logging.info('loaded, compiling')
    black = np.zeros((SIZE, SIZE, 3), np.uint8)
    policy.infer({'observation/image': black, 'observation/wrist_image': black,
                  'observation/state': np.zeros(8, np.float32), 'prompt': 'pick up the red box'})
    logging.info('compiled, serving on port %d', a.port)
    websocket_policy_server.WebsocketPolicyServer(policy, '127.0.0.1', a.port, policy.metadata).serve_forever()


if __name__ == '__main__':
    main()
