"""CPU inference time of the small policy, one thread pool as in the node: 200 calls on real-sized input."""
import statistics as st
import time

import numpy as np
from airlab_vla.runner import DEFAULT_POLICY, PolicyRunner

r = PolicyRunner(DEFAULT_POLICY)
r.reset('pick up the red box')
head = np.zeros((72, 128, 3), np.uint8)
wrist = np.zeros((96, 96, 3), np.uint8)
state = np.zeros(8, np.float32)
times = []
for k in range(220):
    t0 = time.perf_counter()
    r.act(head, wrist, state)
    times.append(time.perf_counter() - t0)
times = sorted(t * 1000 for t in times[20:])
print(f'act(): n={len(times)} mean {st.mean(times):.2f} ms median {st.median(times):.2f} ms p95 {times[189]:.2f} ms max {times[-1]:.2f} ms')
