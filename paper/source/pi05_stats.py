"""π0.5 per-call round trip and steps from trial.jsonl. /vla/status repeats the last round trip
on every step until the next answer, so runs of the same value are one call."""
import json
import statistics as st
import sys

sys.stdout.reconfigure(encoding='utf-8')
rows = [json.loads(line) for line in open(sys.argv[1], encoding='utf8')]
rows = [r for r in rows if r['label'] == 'pi05']
calls, last = [], None
for r in rows:
    if r['kind'] == 'latency':
        if r['latency'] != last:
            calls.append(r['latency'])
        last = r['latency']
    elif r['kind'] == 'vla_result':
        last = None
calls.sort()
print('calls', len(calls), f'mean {st.mean(calls):.3f} median {st.median(calls):.3f} sd {st.stdev(calls):.3f}',
      f'p95 {calls[int(0.95 * len(calls))]:.3f} max {calls[-1]:.3f}')
steps = [r['steps'] for r in rows if r['kind'] == 'vla_result' and r.get('ok')]
print('steps', len(steps), f'mean {st.mean(steps):.1f} sd {st.stdev(steps):.1f} range {min(steps)}-{max(steps)}')
fails = [r for r in rows if r['kind'] == 'vla_result' and not r.get('ok')]
print('vla failures', len(fails))
