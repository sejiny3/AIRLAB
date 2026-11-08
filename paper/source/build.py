"""Build the draft from the KSME template: build.py out_stem"""
import faulthandler
import json
import math
import os
import statistics as st
import sys

from PIL import Image

import paper_text as T
from hwplib import Doc

sys.stdout.reconfigure(encoding='utf-8')
faulthandler.dump_traceback_later(60, exit=True)
out = sys.argv[1] if len(sys.argv) > 1 else 'draft'


def fisher(a, b, c, d):
    """Two-sided Fisher exact test of [[a, b], [c, d]]."""
    n, row, col = a + b + c + d, a + b, a + c
    p = lambda x: math.comb(col, x) * math.comb(n - col, row - x) / math.comb(n, row)
    seen = p(a)
    return sum(p(x) for x in range(max(0, row + col - n), min(row, col) + 1) if p(x) <= seen * (1 + 1e-9))


def metrics():
    rows = [json.loads(line) for line in open('trial.jsonl', encoding='utf8')]
    m = {}
    tally = {}
    for labels, key in ((('task', 'task2'), 'ik'), (('vla',), 'cnn'), (('pi05',), 'pi05')):
        calls = [r for r in rows if r['label'] in labels and r.get('type') == 'tool_result']
        real = lambda r: r['ok'] or 'grasping' in str(r['result']) or 'could not line up' in str(r['result'])
        picks = [r for r in calls if r['name'] == 'pick_object' and real(r)]
        # a place fails on its own only when the robot held the box
        places = [r for r in calls if r['name'] == 'place_object' and 'not holding' not in str(r['result'])]
        nav = [r['seconds'] for r in calls if r['name'] == 'navigate_to' and r['ok']]
        good = [r['seconds'] for r in picks if r['ok']]
        ok, n = len(good), len(picks)
        tally[key] = (ok, n - ok)
        m[f'{key}_rate'] = f'{ok}/{n}'
        m[f'{key}_rate_long'] = f'{100 * ok / n:.1f}% ({ok}/{n})'
        m[f'{key}_time'] = f'{st.mean(good):.1f}'
        m[f'{key}_time_sd'] = f'{st.mean(good):.1f} ± {st.stdev(good):.1f}'
        m[f'{key}_nav'] = f'{st.mean(nav):.1f}'
        m[f'{key}_nav_sd'] = f'{st.mean(nav):.1f} ± {st.stdev(nav):.1f}'
        m[f'{key}_place'] = f'{sum(r["ok"] for r in places)}/{len(places)}'
        gather = [r for r in picks if '모아' in r['command']]
        back = [r for r in picks if '제자리' in r['command']]
        print(key, m[f'{key}_rate'], 'gather', sum(r['ok'] for r in gather), len(gather), 'return', sum(r['ok'] for r in back), len(back),
              m[f'{key}_time_sd'], 'nav', m[f'{key}_nav_sd'], 'place', m[f'{key}_place'])
        m[f'{key}_gather'] = str(len(gather))
        m[f'{key}_fail'] = str(n - ok)
    for label, key in (('vla', 'cnn'), ('pi05', 'pi05')):
        steps = [r['steps'] for r in rows if r.get('kind') == 'vla_result' and r['label'] == label and r.get('ok')]
        m[f'{key}_steps'] = f'{st.mean(steps):.1f}'
        print(key, 'steps', m[f'{key}_steps'], len(steps))
    # /vla/status repeats the last round trip on every step until the next answer, so a run of one value is one call
    calls, last = [], None
    for r in rows:
        if r['label'] != 'pi05':
            continue
        if r.get('kind') == 'latency':
            if r['latency'] != last:
                calls.append(r['latency'])
            last = r['latency']
        elif r.get('kind') == 'vla_result':
            last = None
    m['rtt_n'] = f'{len(calls)}'
    m['rtt_median'] = f'{st.median(calls):.2f}'
    m['rtt_mean'] = f'{st.mean(calls):.2f}'
    m['rtt_max'] = f'{max(calls):.2f}'
    m['rtt_per_pick'] = f'{len(calls) / int(m["pi05_rate"].split("/")[1]):.0f}'
    m['rtt_wait'] = f'{st.mean(calls) * len(calls) / int(m["pi05_rate"].split("/")[1]):.0f}'
    m['pi05_minus_cnn'] = f'{float(m["pi05_time"]) - float(m["cnn_time"]):.1f}'
    # closed-loop picks with sentences the demonstrations never used (paraphrase.py)
    para = [json.loads(line) for line in open('paraphrase.jsonl', encoding='utf8')]
    for policy in ('cnn', 'pi05'):
        for name in ('seen', 'unseen_words', 'distracting', 'korean'):
            eps = [r for r in para if r['policy'] == policy and r['set'] == name]
            ok = sum(r['ok'] for r in eps)
            m[f'para_{policy}_{name}'] = f'{ok}/{len(eps)}'
            m[f'para_{policy}_{name}_n'] = (ok, len(eps) - ok)
            m[f'para_{policy}_{name}_other'] = sum(r['other'] for r in eps)
    for name in ('unseen_words', 'distracting', 'korean'):
        p = fisher(*m[f'para_cnn_{name}_n'], *m[f'para_pi05_{name}_n'])
        m[f'para_p_{name}'] = '< 0.001' if p < 0.001 else f'= {p:.2f}'
    print('paraphrase', {k: v for k, v in m.items() if k.startswith('para_') and not k.endswith('_n')})
    # closed-loop picks under visual changes (perturb.py); cnn_aug is the CNN retrained with openpi's augmentation
    vis = [json.loads(line) for line in open('perturb.jsonl', encoding='utf8')]
    pval = lambda p: '< 0.001' if p < 0.001 else f'{p:.3f}' if p < 0.01 else f'{p:.2f}'
    pairs = {'p': ('cnn', 'pi05'), 'pa': ('cnn_aug', 'pi05'), 'pc': ('cnn', 'cnn_aug')}
    for cond in [f'V{i}' for i in range(9)] + ['all']:
        n = {}
        for policy in ('cnn', 'cnn_aug', 'pi05'):
            eps = [r for r in vis if r['policy'] == policy and (r['cond'] == cond or cond == 'all' and r['cond'] != 'V0')]
            ok = sum(r['ok'] for r in eps)
            m[f'vis_{policy}_{cond}'] = f'{ok}/{len(eps)}'
            m[f'vis_{policy}_{cond}_ok'] = ok
            if cond == 'all':  # the eight changed conditions together
                m[f'vis_{policy}_pct'] = f'{100 * ok / len(eps):.1f}'
            n[policy] = (ok, len(eps) - ok)
        for key, (a, b) in pairs.items():
            m[f'vis_{key}_{cond}'] = pval(fisher(*n[a], *n[b]))
    # the same 100 closed-loop scenes and 20 ask-other scenes as Table 2 (evaluate.py)
    lines = open('eval100_aug.txt', encoding='utf8').read().splitlines()
    steps = [int(l.split(' in ')[1].split()[0]) for l in lines if ' lifted in ' in l]
    m['aug_rate'] = f'{len(steps)}/{sum(l.startswith("episode") for l in lines)}'
    m['aug_steps'] = f'{st.mean(steps):.1f} ± {st.stdev(steps):.1f}'
    other = open('ask_other_aug.txt', encoding='utf8').read().splitlines()[-1]  # named box: a/n, lined-up box: b/n, ...
    got = dict(part.split(': ') for part in other.split(', '))
    m['aug_other'] = f'{got["named box"]}, {got["lined-up box"]}'
    print('aug', m['aug_rate'], m['aug_steps'], m['aug_other'])
    print('visual', {k: v for k, v in m.items() if k.startswith('vis_')})
    # stage 2: choosing one of three boxes by the instruction (row/language.py), 50 scenes per condition
    row = [json.loads(line) for line in open('row/language.jsonl', encoding='utf8')]
    expert = [json.loads(line) for line in open('row/language_expert.jsonl', encoding='utf8')]
    conds = ('L1', 'L2', 'L3', 'L4', 'L5', 'L6')
    for cond in conds:
        m[f'row_expert_{cond}'] = f'{sum(r["ok"] for r in expert if r["cond"] == cond)}/50'
        n = {}
        for policy in ('cnn', 'minilm', 'pi05'):
            eps = [r for r in row if r['policy'] == policy and r['cond'] == cond]
            ok = sum(r['ok'] for r in eps)
            n[policy] = (ok, len(eps) - ok)
            m[f'row_{policy}_{cond}'] = f'{ok}/{len(eps)}'
            m[f'row_{policy}_{cond}_wrong'] = sum(not r['ok'] and r['lifted'] != 'none' for r in eps)
            for t in ('left', 'middle', 'right'):
                te = [r for r in eps if r['target'] == t]
                m[f'row_{policy}_{cond}_{t}'] = f'{sum(r["ok"] for r in te)}/{len(te)}'
            if cond == 'L5':  # even episodes unseen English words, odd ones Korean
                for lang, par in (('en', 0), ('ko', 1)):
                    le = [r for r in eps if r['episode'] % 2 == par]
                    m[f'row_{policy}_L5_{lang}'] = f'{sum(r["ok"] for r in le)}/{len(le)}'
            if cond == 'L4':
                m[f'row_{policy}_L4_lifted'] = {s: sum(r['lifted'] == s for r in eps) for s in ('left', 'middle', 'right', 'none')}
        m[f'row_p_cnn_{cond}'] = pval(fisher(*n['pi05'], *n['cnn']))
        m[f'row_p_minilm_{cond}'] = pval(fisher(*n['pi05'], *n['minilm']))
    for lang, par in (('en', 0), ('ko', 1)):
        le = [r for r in expert if r['cond'] == 'L5' and r['episode'] % 2 == par]
        m[f'row_expert_L5_{lang}'] = f'{sum(r["ok"] for r in le)}/{len(le)}'
    m['row_expert_all'] = f'{sum(r["ok"] for r in expert)}/{len(expert)}'
    for policy in ('cnn', 'minilm', 'pi05'):
        m[f'row_{policy}_all'] = f'{sum(r["ok"] for r in row if r["policy"] == policy)}/300'
    k = int(m['row_pi05_L4'].split('/')[0])  # one-sided binomial against picking one of three boxes at random
    m['row_p_chance_L4'] = f'{sum(math.comb(50, i) * (1 / 3) ** i * (2 / 3) ** (50 - i) for i in range(k, 51)):.2f}'
    print('row', {k: v for k, v in m.items() if k.startswith('row_')})
    m['fisher'] = f'{fisher(*tally["ik"], *tally["cnn"]):.2f}'
    m['fisher_pi05'] = f'{fisher(*tally["ik"], *tally["pi05"]):.2f}'
    print('fisher', m['fisher'], m['fisher_pi05'], 'rtt', m['rtt_n'], m['rtt_median'], m['rtt_mean'], m['rtt_max'],
          'per pick', m['rtt_per_pick'], m['rtt_wait'], 's')
    return m


m = metrics()
ko, en = T.abstract_ko(m), T.abstract_en(m)
print('abstract', len(ko), 'chars ko,', len(en.split()), 'words en')

faulthandler.dump_traceback_later(1800, exit=True)  # Hancom may ask on screen to allow access to the work file
d = Doc('template.hwp')
faulthandler.dump_traceback_later(60, exit=True)
h = d.h

# everything that deletes comes first; colouring ends Hancom's Delete for this session otherwise
d.set_text(3, 0, '[저자명]·[저자명]·[저자명]')
d.set_text(8, 0, T.RUNNING)
d.set_text(4, 0, T.EMAIL, 22)
d.set_text(5, 3, T.TITLE_KO[0])
d.set_text(5, 4, T.TITLE_KO[1], black=True)
d.set_text(5, 6, T.AUTHORS_KO, black=True)
d.set_text(5, 7, T.AFFIL_KO, black=True)
d.set_text(5, 9, T.TITLE_EN, black=True)
d.set_text(5, 11, T.AUTHORS_EN, black=True)
d.set_text(5, 12, T.AFFIL_EN[0], black=True)
d.set_text(5, 13, T.AFFIL_EN[1])
d.set_text(5, 15, T.RECEIVED, black=True)
d.set_text(6, 0, T.KEYWORDS, 11, black=True)
d.set_text(6, 1, ko, 4, black=True)
d.set_text(7, 0, en, 10, 854, black=True)
h.SetPos(7, 0, 10 + len(en))
print('last abstract char removed:', h.HAction.Run('Delete'))
d.set_text(0, 6, '', 16)
d.clear_from(7)
print('template cleared', h.GetPos(), h.PageCount)

for sym, text in T.NOTATION:
    print('notation', sym, flush=True)
    d.para('body', f'{sym} : {text}')

for kind, payload in T.body(m):
    print(kind, str(payload)[:40], flush=True)
    faulthandler.dump_traceback_later(60, exit=True)
    if kind == 'fig':
        path, w, height, caption = payload
        if height is None:
            px = Image.open(path).size
            height = w * px[1] / px[0]
        d.picture(path, w, height)
        label, rest = caption.split(' ', 2)[:2], caption.split(' ', 2)[2]
        d.para('fig', f'~{{{" ".join(label)}}} {rest}')
    elif kind == 'table':
        caption, widths, rows = payload
        label, rest = caption.split(' ', 2)[:2], caption.split(' ', 2)[2]
        d.para('table', f'~{{{" ".join(label)}}} {rest}')
        d.table(rows, widths)
    elif kind == 'eq':
        d.equation(*payload)
    else:
        d.para(kind, payload)

d.para('ack', '후 기')
d.para('body', '[연구비 지원 등 감사의 글을 입력하시오]')
d.para('ref_title', '참고문헌')
d.para('ref_title', '(References)')
for i, ref in enumerate(T.REFS, 1):
    d.para('ref', f'({i}) {ref}')

print(d.save(out + '.hwp'), d.save(out + '.pdf', 'PDF'), 'pages', h.PageCount)
d.close()
