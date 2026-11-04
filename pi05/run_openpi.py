"""Run one of openpi's scripts with the AIRLAB configs added to its list, from the openpi folder:

  .venv/bin/python ../AIRLAB/pi05/run_openpi.py scripts/compute_norm_stats.py --config-name pi05_airlab
  .venv/bin/python ../AIRLAB/pi05/run_openpi.py scripts/train.py pi05_airlab --exp-name run1

pi05_airlab_row is the same for the three-box row task.
"""

import runpy
import sys

if __name__ == '__main__':  # data loader workers import this file again: they must not start the script
    import airlab_policy
    from openpi.training import config as _config

    _config._CONFIGS_DICT.update(airlab_policy.CONFIGS)
    sys.argv = sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name='__main__')
