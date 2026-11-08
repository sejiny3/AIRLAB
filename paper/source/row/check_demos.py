import glob, os, collections, numpy as np
c = collections.Counter()
for f in sorted(glob.glob(os.path.expanduser('~/airlab_vla/demos_row/*.npz'))):
    d = np.load(f)
    order, target, ins, kind = list(d['order']), str(d['target']), str(d['instruction']), str(d['kind'])
    slot = ['left', 'middle', 'right'].index(target)
    if kind == 'colour':
        c['colour ok' if order[slot] in ins else 'colour MISMATCH'] += 1
    else:
        c['pos ' + target] += 1
    c[f'{kind} {target}'] += 1
print(c)
