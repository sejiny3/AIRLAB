"""Step statistics of the two closed-loop evaluations on the same 100 setups, and the small policy's size."""
import json
import os
import re
import statistics as st

PI05 = [83, 76, 68, 85, 79, 78, 75, 90, 73, 78, 71, 78, 74, 78, 78, 78, 75, 78, 78, 76,
        75, 79, 75, 76, 74, 74, 90, 78, 70, 80, 71, 80, 76, 78, 77, 73, 80, 90, 76, 83,
        71, 72, 73, 76, 88, 68, 68, 83, 73, 75, 74, 83, 78, 83, 73, 87, 81, 75, 75, 76,
        73, 78, 77, 79, 77, 74, 84, 73, 81, 75, 83, 73, 74, 80, 75, 78, 73, 83, 77, 73,
        89, 83, 75, 73, 83, 78, 78, 77, 88, 78, 73, 78, 69, 83, 79, 74, 67, 90, 78, 78]
# the setups as π0.5's log names them, to confirm both ran the same scenes
HEAD_PI05 = ['supply_1 blue with', 'supply_2 red alone', 'supply_3 red alone', 'supply_2 blue alone', 'supply_3 blue alone']

text = open(os.path.expanduser('~/airlab_vla/eval100.txt')).read()
rows = re.findall(r'episode\s+(\d+)\s+(\S+)\s+(\S+)\s+(alone|with 2nd box)\s+policy (\w+) in\s+(\d+) steps\s+expert (\w+)', text)
print(len(rows), 'rows; first:', rows[:5])
cnn = [int(r[5]) for r in rows]
print('same setups (first 5):', [f'{r[1]} {r[2]} {r[3].split()[0]}' for r in rows[:5]] == HEAD_PI05)


def line(name, x):
    x = sorted(x)
    print(f'{name}: n={len(x)} mean {st.mean(x):.2f} sd {st.stdev(x):.2f} min {x[0]} q1 {x[len(x)//4]} median {st.median(x)} q3 {x[3*len(x)//4]} max {x[-1]} sum {sum(x)}')


line('cnn', cnn)
line('pi05', PI05)
d = [a - b for a, b in zip(PI05, cnn)]
print(f'paired pi05-cnn: mean {st.mean(d):.2f} sd {st.stdev(d):.2f}')
print('wilcoxon needs scipy:', end=' ')
try:
    from scipy.stats import wilcoxon
    print(wilcoxon(PI05, cnn))
except Exception as e:
    print(repr(e))
json.dump({'cnn': cnn, 'pi05': PI05}, open(os.path.dirname(os.path.abspath(__file__)) + '/steps.json', 'w'))
print('tail of train.log:', open(os.path.expanduser('~/airlab_vla/train.log')).read().splitlines()[0][:120])

import torch
sd = torch.load(os.path.expanduser('~/airlab_vla/policy.pt'), map_location='cpu', weights_only=False)
state = sd.get('model', sd) if isinstance(sd, dict) else sd
state = state if 'mean' in state or any('.' in k for k in state) else sd
print('keys', list(sd)[:6] if isinstance(sd, dict) else type(sd))
n = sum(v.numel() for k, v in state.items() if hasattr(v, 'numel') and k not in ('mean', 'std'))
print('parameters', n)
