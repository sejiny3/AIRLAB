"""Run one of openpi's scripts with the AIRLAB config added to its list, from the openpi folder:

  .venv/bin/python ../AIRLAB/pi05/run_openpi.py scripts/compute_norm_stats.py --config-name pi05_airlab
  .venv/bin/python ../AIRLAB/pi05/run_openpi.py scripts/train.py pi05_airlab --exp-name run1
"""

import runpy
import sys

if __name__ == '__main__':  # data loader workers import this file again: they must not start the script
    import airlab_policy
    from openpi.training import config as _config

    _config._CONFIGS_DICT[airlab_policy.CONFIG.name] = airlab_policy.CONFIG
    sys.argv = sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name='__main__')
