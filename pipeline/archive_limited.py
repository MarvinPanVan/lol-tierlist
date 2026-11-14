"""Build a reduced tier list for an older patch from OP.GG Global Emerald+ only (data/prev/opgg_global_e_<role>_<code>.csv).
OP.GG only keeps the current and the previous patch, so older patches can't be rebuilt in full later.
Usage: python3 pipeline/archive_limited.py 26.21 2621   -> public/data/26.21.json"""
import os, sys, json, math
import pandas as pd
os.chdir(os.path.dirname(os.path.abspath(__file__)))
patch, code = sys.argv[1], sys.argv[2]
SAMPLES = json.load(open('data/samples.json'))[f'opgg_global_e_{code}']
ROLES = ['top', 'jungle', 'mid', 'adc', 'support']
from decimal import Decimal, ROUND_HALF_UP
def f1(v): r = math.floor(v * 10 + .5) / 10; return ('+' if r > 0 else '−' if r < 0 else '') + f'{abs(r):.1f}'   # same rounding as the site
def fx(v): return str(Decimal(v).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
out = {}
for role in ROLES:
    d = pd.read_csv(f'data/prev/opgg_global_e_{role}_{code}.csv').drop_duplicates('champion').set_index('champion')
    # same as update.py: role average and fitted spread over every champion OP.GG lists, then keep 0.6%+ pick
    n = d.pick / 100 * SAMPLES / 10
    m = (d.win * d.pick).sum() / d.pick.sum(); delta = d.win - m
    ok = n >= 300; v = 2500 / n
    t2 = max(0.35 ** 2, float((delta[ok] ** 2).mean() - v[ok].mean()))
    d = d[d.pick >= 0.6]
    k = t2 / (t2 + v); sh = delta * k; sd = (t2 * v / (t2 + v)) ** .5
    L = []
    for c in d.index:
        pick = float(d.loc[c, 'pick']); spec = 0.4 * math.log(max(1.0, 2 / pick))
        score = float(sh[c]) - spec
        t = 'Z' if score >= 1.8 and pick >= 2 and float(delta[c]) >= 1.5 else 'P' if pick < 1.5 and score >= .6 else 'S' if score >= 1.15 else 'A' if score >= .6 else 'B' if score >= .15 else 'C' if score >= -.45 else 'D'
        note = f'Global Emerald+ only: {f1(float(delta[c]))} vs the role average at {fx(pick)}% pick.'
        L.append({'c': c, 't': t, 'score': round(score, 2), 'se': round(1.64 * float(sd[c]), 2), 'pick': round(pick, 2), 'ban': round(float(d.loc[c, 'ban']), 2),
                  'wr': round(float(d.loc[c, 'win']), 2), 'games': int(n[c]), 'g': round(float(delta[c]), 2), 'euw': None, 'kr': None, 'na': None, 'm': None,
                  'dia': None, 'euwd': None, 'euwm': None, 'hi': None, 'ht': None, 'pick_d': None, 'tr': None, 'sites': {}, 'll': None, 'mx': None, 'mxw': None,
                  'nx': None, 'nxt': None, 'note': note})
    out[role] = L
out['_meta'] = {'patch': patch, 'kind': 'limited', 'label': 'Global Emerald+ only'}
os.makedirs('../public/data', exist_ok=True)
json.dump(out, open(f'../public/data/{patch}.json', 'w', encoding='utf-8'), ensure_ascii=False)
print(patch, {r: len(out[r]) for r in ROLES}, {r: [e['c'] for e in out[r] if e['t'] in 'ZS'][:5] for r in ROLES})
