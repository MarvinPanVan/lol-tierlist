"""One run from raw files to tiers.json.  python3 pipeline/update.py

Inputs (pipeline/):
  data/opgg_{global,euw,kr,na}_e_{role}.csv   OP.GG Emerald+ (champion,win,pick,ban)
  data/opgg_global_{m,d}_{role}.csv           OP.GG Master+ / Diamond+ (global)
  data/opgg_euw_{d,m}_{role}.csv              OP.GG EUW Diamond+ / Master+
  data/prev/opgg_global_e_{role}_<prev>.csv   OP.GG Global Emerald+ of the previous patch
  data/samples.json                           OP.GG 'Total analyzed samples' per dataset (= 10 x matches)
  data/lolalytics_global_e_{role}.csv         Lolalytics Emerald+ (letters only)
  data2/ugg_{d,m}.txt  data2/blitz_d.txt  data2/dpm_d.txt  data2/log_d.csv  data2/ms_d_{role}.txt  data2/moba_highelo.json
  patch.json                                  patch numbers, next patch preview, champions changed this patch
Output: tiers.json (roles + _meta), printed summary incl. backtest.
"""
import os, re, json, glob, math
import numpy as np, pandas as pd
from scipy.stats import spearmanr
os.chdir(os.path.dirname(os.path.abspath(__file__)))

ROLES = ['top', 'jungle', 'mid', 'adc', 'support']
ROLEMAP = {'top': 'top', 'jungle': 'jungle', 'mid': 'mid', 'middle': 'mid', 'adc': 'adc', 'bottom': 'adc', 'support': 'support',
           'utility': 'support', 'T': 'top', 'J': 'jungle', 'M': 'mid', 'B': 'adc', 'S': 'support'}
P = json.load(open('patch.json', encoding='utf-8'))
SAMPLES = json.load(open('data/samples.json'))
SPEC = 0.4          # one-trick correction: points per ln-unit of pick rate below 2%
TAU_FLOOR = 0.35    # never assume the true spread between champions is below 0.35 points
CONS_W = {'g': .30, 'euw': .20, 'kr': .20, 'na': .10, 'm': .20}
HI_W = {'D': .40, 'M': .35, 'E': .25}

def slug(s): return re.sub(r'[^a-z0-9]', '', s.lower())
SPECIAL = {'monkeyking': 'Wukong', 'nunu': 'Nunu & Willump', 'nunuwillump': 'Nunu & Willump', 'renata': 'Renata Glasc'}
NAMES = {}
for f in glob.glob('data/opgg_*.csv') + glob.glob('data/prev/*.csv'):
    for c in pd.read_csv(f).champion: NAMES[slug(c)] = c
def nm(s): k = slug(s); return SPECIAL.get(k, NAMES.get(k, s))

def opgg(ds, role, prev=None):
    f = f'data/prev/{ds}_{role}_{prev}.csv' if prev else f'data/{ds}_{role}.csv'
    if not os.path.exists(f): return None
    d = pd.read_csv(f).drop_duplicates('champion').set_index('champion')
    key = f'{ds}_{prev}' if prev else ds
    d['n'] = d.pick / 100 * SAMPLES[key] / 10
    return d

def deltas(d, weights=None):
    w = d.pick if weights is None else weights
    m = (d.win * w).sum() / w.sum()
    return d.win - m

def fit_tau2(delta, n):
    ok = n >= 300
    v = 2500 / n[ok]
    t2 = float((delta[ok] ** 2).mean() - v.mean())
    return max(TAU_FLOOR ** 2, t2)

def shrink(delta, n, tau2):
    v = 2500 / n
    k = tau2 / (tau2 + v)
    return delta * k, np.sqrt(tau2 * v / (tau2 + v))

def spec(pick): return SPEC * math.log(max(1.0, 2 / pick)) if pick and pick > 0 else SPEC * math.log(2 / 0.3)

# ---------- third-party site files ----------
rows = []
for line in open('data2/ugg_d.txt'):
    c, r, t, w, p, b, g = line.strip().split(';'); rows.append(('U.GG', 'D', ROLEMAP[r], nm(c), t, float(w), float(p), float(b), int(g)))
for line in open('data2/ugg_m.txt'):
    c, r, t, w, p, b, g = line.strip().split(';'); rows.append(('U.GG', 'M', ROLEMAP[r], nm(c), t, float(w), float(p), float(b), int(g)))
for line in open('data2/dpm_d.txt'):
    x = line.strip().split(';'); c, r = x[1].split('|')
    rows.append(('dpm.lol', 'D', ROLEMAP[r], nm(c), x[3], float(x[4].strip('%')), float(x[6].strip('%')), np.nan, int(x[7].replace('.', ''))))
for line in open('data2/blitz_d.txt'):
    t, rest = line.strip().split('=', 1)
    for it in rest.split():
        c, r, w = it.split('/'); rows.append(('Blitz', 'D', ROLEMAP[r], nm(c), t, float(w), np.nan, np.nan, np.nan))
for i, line in enumerate(open('data2/log_d.csv')):
    if i == 0: continue
    c, r, t, pop, w, b = line.strip().split(';'); rows.append(('League of Graphs', 'D', ROLEMAP[r], nm(c), t, float(w), float(pop), float(b), np.nan))
for r in ROLES:
    for it in open(f'data2/ms_d_{r}.txt').read().strip().split('|'):
        c, t, w, p, b, g = it.split(','); rows.append(('METAsrc', 'D', r, nm(c), t, float(w), float(p), float(b), np.nan))
SITE = pd.DataFrame(rows, columns=['site', 'rank', 'role', 'c', 'tier', 'win', 'pick', 'ban', 'games'])
MOBA = json.load(open('data2/moba_highelo.json'))

out, meta_tau, prev_cmp = {}, {}, []
for role in ROLES:
    base = opgg('opgg_global_e', role)
    comp = {}          # name -> dict(raw delta, shrunk, sd, n)
    def add(key, d, label):
        if d is None: return
        dl = deltas(d); t2 = fit_tau2(dl, d.n); s, sd = shrink(dl, d.n, t2)
        meta_tau[f'{label}|{role}'] = round(math.sqrt(t2), 2)
        comp[key] = pd.DataFrame({'raw': dl, 'sh': s, 'sd': sd, 'n': d.n, 'pick': d.pick, 'ban': d.ban})
    add('g', base, 'OP.GG Global E+'); add('euw', opgg('opgg_euw_e', role), 'OP.GG EUW E+')
    add('kr', opgg('opgg_kr_e', role), 'OP.GG KR E+'); add('na', opgg('opgg_na_e', role), 'OP.GG NA E+')
    add('m_op', opgg('opgg_global_m', role), 'OP.GG Master+'); add('d_op', opgg('opgg_global_d', role), 'OP.GG Diamond+')
    add('euwd', opgg('opgg_euw_d', role), 'OP.GG EUW Diamond+'); add('euwm', opgg('opgg_euw_m', role), 'OP.GG EUW Master+')
    add('prev', opgg('opgg_global_e', role, P['prev_patch_code']), 'OP.GG Global E+ prev')
    # last patch as the starting point for champions this patch did not change (Global Emerald+ only):
    # prior = last patch's shrunk value, prior variance = true patch-to-patch change + last patch's own uncertainty
    if 'prev' in comp:
        g, pv = comp['g'], comp['prev']
        same = [c for c in g.index if c in pv.index and c not in P['changed_this_patch']]
        big = [c for c in same if g.loc[c, 'n'] >= 1000 and pv.loc[c, 'n'] >= 1000]
        if len(big) >= 8:
            ch = g.loc[big, 'raw'] - pv.loc[big, 'raw']
            sc2 = max(0.03, float((ch ** 2).mean() - (2500 / g.loc[big, 'n']).mean() - (2500 / pv.loc[big, 'n']).mean()))
            meta_tau[f'patch change|{role}'] = round(math.sqrt(sc2), 2)
            for c in same:
                v = 2500 / g.loc[c, 'n']; mu = pv.loc[c, 'sh']; pvar = sc2 + pv.loc[c, 'sd'] ** 2
                post = (g.loc[c, 'raw'] / v + mu / pvar) / (1 / v + 1 / pvar)
                g.loc[c, 'sh'] = post; g.loc[c, 'sd'] = math.sqrt(1 / (1 / v + 1 / pvar))
    dref = comp['d_op']
    # third-party Diamond+/Master+ sites (deltas against their own role mean; counts from the site or OP.GG Diamond+)
    for (site, rk), g in SITE[SITE.role == role].groupby(['site', 'rank']):
        if site == 'METAsrc': continue
        g = g.drop_duplicates('c').set_index('c')
        w = g.pick if g.pick.notna().all() else dref.pick.reindex(g.index).fillna(0.3)
        dl = deltas(g, w)
        n = g.games if g.games.notna().all() else dref.n.reindex(g.index).fillna(300)
        n = n.clip(lower=50)
        t2 = fit_tau2(dl, n); s, sd = shrink(dl, n, t2)
        meta_tau[f'{site} {rk}+|{role}'] = round(math.sqrt(t2), 2)
        comp[f'{site}|{rk}'] = pd.DataFrame({'raw': dl, 'sh': s, 'sd': sd, 'n': n})
    bestf = f'data/lolalytics_best_{role}.csv'
    best = pd.read_csv(bestf).drop_duplicates('champion').set_index('champion') if os.path.exists(bestf) else None
    lolal = pd.read_csv(f'data/lolalytics_global_e_{role}.csv').set_index('champion') if os.path.exists(f'data/lolalytics_global_e_{role}.csv') else None

    def val(key, c, f='sh'):
        d = comp.get(key)
        return float(d.loc[c, f]) if d is not None and c in d.index else None
    def avg(pairs):  # [(value, weight)] -> weighted mean ignoring None
        pr = [(v, w) for v, w in pairs if v is not None]
        return sum(v * w for v, w in pr) / sum(w for _, w in pr) if pr else None

    # list a champion in a role if it has real presence there: 0.6%+ pick in Global Emerald+ and data in 4 of 5 consensus sets
    cov = lambda c: sum(c in comp[k].index for k in ['g', 'euw', 'kr', 'na', 'm_op'])
    champs = [c for c in base.index if base.loc[c, 'pick'] >= 0.6 and cov(c) >= 4]
    res = []
    for c in champs:
        e = {'c': c}
        pick = float(base.loc[c, 'pick']); ban = float(base.loc[c, 'ban'])
        e['pick'] = round(pick, 2); e['ban'] = round(ban, 2)
        e['wr'] = round(float(base.loc[c, 'win']), 2); e['games'] = int(base.loc[c, 'n'])
        e['games_d'] = int(dref.loc[c, 'n']) if c in dref.index else None
        # Lolalytics: best players on the champion (last 7 days) vs the Emerald+ average on it
        if best is not None and c in best.index and best.loc[c, 'best_games'] >= 1500:
            e['mx'] = round(float(best.loc[c, 'best_delta']), 1); e['mxw'] = round(float(best.loc[c, 'best_win']), 1)
        else: e['mx'] = e['mxw'] = None
        # consensus parts (shrunk) and display (raw)
        m_sh = avg([(val('m_op', c), 1), (val('U.GG|M', c), 1)]); m_raw = avg([(val('m_op', c, 'raw'), 1), (val('U.GG|M', c, 'raw'), 1)])
        m_sd = avg([(val('m_op', c, 'sd'), 1), (val('U.GG|M', c, 'sd'), 1)])
        parts = {'g': (val('g', c), val('g', c, 'sd')), 'euw': (val('euw', c), val('euw', c, 'sd')), 'kr': (val('kr', c), val('kr', c, 'sd')),
                 'na': (val('na', c), val('na', c, 'sd')), 'm': (m_sh, m_sd)}
        ws = sum(CONS_W[k] for k, (v, _) in parts.items() if v is not None)
        cons = sum(CONS_W[k] * v for k, (v, _) in parts.items() if v is not None) / ws
        se = sum(CONS_W[k] * s for k, (v, s) in parts.items() if v is not None) / ws   # errors treated as fully correlated (datasets overlap)
        e['score'] = round(cons - spec(pick), 2)
        e['se'] = round(1.64 * se, 2)
        for k in ['g', 'euw', 'kr', 'na']:
            v = val(k, c, 'raw'); e[k] = None if v is None else round(v, 2)
        e['m'] = None if m_raw is None else round(m_raw, 2)
        # Diamond+ block: OP.GG, U.GG, Blitz, dpm.lol at 1, League of Graphs at 0.5
        dsrc = [('d_op', 1), ('U.GG|D', 1), ('Blitz|D', 1), ('dpm.lol|D', 1), ('League of Graphs|D', .5)]
        D_sh = avg([(val(k, c), w) for k, w in dsrc]); D_raw = avg([(val(k, c, 'raw'), w) for k, w in dsrc])
        e['ndia'] = sum(1 for k, _ in dsrc if val(k, c) is not None); e['nm'] = sum(1 for k in ['m_op', 'U.GG|M'] if val(k, c) is not None)
        e['dia'] = None if D_raw is None else round(D_raw, 2)
        for k in ['euwd', 'euwm']:
            v = val(k, c, 'raw'); e[k] = None if v is None else round(v, 2)
        E_sh = avg([(val('euwd', c), 1), (val('euwm', c), 1)])
        pick_d = float(dref.loc[c, 'pick']) if c in dref.index else None
        e['pick_d'] = None if pick_d is None else round(pick_d, 2)
        hi = avg([(D_sh, HI_W['D']), (m_sh, HI_W['M']), (E_sh, HI_W['E'])])
        e['hi'] = None if hi is None else round(hi - spec(pick_d if pick_d else pick), 2)
        # previous patch (Global Emerald+), both shrunk
        pv, gv = val('prev', c), val('g', c)
        e['tr'] = None if pv is None or gv is None else round(gv - pv, 2)
        if pv is not None and c not in P['changed_this_patch']:
            prev_cmp.append((role, c, val('prev', c, 'raw'), pv, val('g', c, 'raw'), float(comp['prev'].loc[c, 'n']), float(comp['g'].loc[c, 'n'])))
        # site letters at Diamond+
        sites = {}
        for site in ['U.GG', 'Blitz', 'dpm.lol', 'League of Graphs', 'METAsrc']:
            s = SITE[(SITE.site == site) & (SITE['rank'] == 'D') & (SITE.role == role) & (SITE.c == c)]
            sites[site] = s.tier.iloc[0] if len(s) else None
        mt = None
        for t, cs in MOBA.get(role, {}).items():
            if c in cs: mt = t
        sites['Mobalytics experts'] = mt
        e['sites'] = sites
        e['ll'] = lolal.loc[c, 'tier'] if lolal is not None and c in lolal.index else None
        res.append(e)
    out[role] = res

# ---------- tiers (fixed rules, same cutoffs for consensus and high elo) ----------
def tier(v, pk, allpos, zcheck):
    if v is None: return None
    if zcheck and pk >= 2: return 'Z'
    if pk < 1.5 and v >= .6: return 'P'
    if v >= 1.15 and allpos: return 'S'
    if v >= .6: return 'A'
    if v >= .15: return 'B'
    if v >= -.45: return 'C'
    return 'D'
for role, L in out.items():
    for e in L:
        reg = [e[k] for k in ['g', 'euw', 'kr', 'na', 'm'] if e[k] is not None]
        e['t'] = tier(e['score'], e['pick'], all(x > 0 for x in reg), e['score'] >= 1.8 and min(reg) >= 1.5)
        hreg = [e[k] for k in ['dia', 'm', 'euwd', 'euwm'] if e[k] is not None]
        e['ht'] = tier(e['hi'], e['pick_d'] or e['pick'], all(x > 0 for x in hreg), e['hi'] is not None and e['hi'] >= 1.8 and min(hreg) >= 1.5)

# ---------- next patch flags ----------
for role, L in out.items():
    flags = {}
    for name, txt, kind in P['next']['roles'].get(role, []):
        for n in [x.strip() for x in name.split(',')]: flags[n] = (kind, txt)
    for e in L:
        f = flags.get(e['c']); e['nx'] = f[0] if f else None; e['nxt'] = f[1] if f else None

# ---------- notes, written from the numbers ----------
DSN = {'g': 'Global', 'euw': 'EUW', 'kr': 'KR', 'na': 'NA', 'm': 'Master+', 'dia': 'Diamond+', 'euwd': 'EUW Diamond+', 'euwm': 'EUW Master+'}
def f1(v): r = round(v, 1); return ('+' if r > 0 else '−' if r < 0 else '') + f'{abs(r):.1f}'
LV = {'S+': 6, 'S': 5, 'S-': 4.5, 'A+': 4.3, 'A': 4, 'A-': 3.7, 'B+': 3.3, 'B': 3, 'B-': 2.7, 'C': 2, 'D': 1}
def note(e):
    vals = {k: e[k] for k in DSN if e.get(k) is not None}
    lo_k, hi_k = min(vals, key=vals.get), max(vals, key=vals.get)
    lo, hi = vals[lo_k], vals[hi_k]
    out = []
    if e['t'] == 'Z': out.append((10, f'Clear outlier: {f1(lo)} to {f1(hi)} in every dataset.'))
    elif lo >= .5: out.append((7, f'Above average in all {len(vals)} datasets ({f1(lo)} to {f1(hi)}).'))
    elif hi <= -.5: out.append((7, f'Below average in all {len(vals)} datasets.'))
    elif hi - lo >= 1.8 and hi > .3 and lo < -.3: out.append((8, f'Mixed: {f1(hi)} in {DSN[hi_k]}, {f1(lo)} in {DSN[lo_k]}.'))
    low_elo, high = e.get('g'), e.get('hi')
    if low_elo is not None and high is not None:
        if high - low_elo >= .8:
            out.append((7, f'Less bad in high elo: {f1(low_elo)} in Emerald+, {f1(high)} higher up.' if high < 0 else f'Gets better with rank: {f1(low_elo)} in Emerald+, {f1(high)} in high elo.'))
        elif high - low_elo <= -.8:
            out.append((7, f'Even worse in high elo: {f1(low_elo)} in Emerald+, {f1(high)} higher up.' if low_elo < 0 else f'Falls off with rank: {f1(low_elo)} in Emerald+, {f1(high)} in high elo.'))
    if e['pick'] >= 8 and e['score'] <= -.3: out.append((9, f'Very popular ({e["pick"]:.1f}% pick) and still losing.'))
    elif e['pick'] >= 5 and e['score'] >= 1: out.append((8, f'Popular ({e["pick"]:.1f}% pick) and still winning.'))
    elif e['pick'] < 1.5: out.append((8, f'Rarely picked ({e["pick"]:.1f}%), mostly by mains. Expect less if you are new to it.'))
    eu = [e[k] for k in ['euwd', 'euwm'] if e.get(k) is not None]
    if eu and high is not None:
        ev = sum(eu) / len(eu)
        if ev - high >= 1: out.append((6, f'Even better on EUW high elo ({f1(ev)}).'))
        elif ev - high <= -1: out.append((6, f'Worse on EUW high elo ({f1(ev)}).'))
    sl = {k: v for k, v in e['sites'].items() if v in LV}
    if len(sl) >= 3:
        a, b = max(sl, key=lambda k: LV[sl[k]]), min(sl, key=lambda k: LV[sl[k]])
        if LV[sl[a]] - LV[sl[b]] >= 3: out.append((5, f'Sites disagree: {a} gives {sl[a]}, {b} gives {sl[b]}.'))
    if e.get('tr') is not None and abs(e['tr']) >= 1:
        out.append((6, f'{"Up" if e["tr"] > 0 else "Down"} {abs(e["tr"]):.1f} points in Global since {P["prev_patch"]}.'))
    if e.get('mx') is not None and e['mx'] >= 6:
        out.append((7, f'Rewards mastery: the best players on it win {e["mxw"]:.0f}%, {e["mx"]:.1f} points above the Emerald+ average on it.'))
    if e['se'] >= .8: out.append((4, 'Small sample, so treat the tier as rough.'))
    out.sort(key=lambda x: -x[0])
    return ' '.join(t for _, t in out[:2])
for L in out.values():
    for e in L: e['note'] = note(e)

# ---------- site grading (rank correlation of letters with win rate vs popularity, Diamond+) ----------
grade = []
ref = {}
for role in ROLES:
    d = opgg('opgg_global_d', role); dl = deltas(d)
    for c in d.index: ref[(role, c)] = (float(dl[c]), math.log(float(d.loc[c, 'pick'])))
for site in ['U.GG', 'Blitz', 'dpm.lol', 'League of Graphs', 'Mobalytics experts', 'METAsrc']:
    tv, wr, lp, sd_, od = [], [], [], [], []
    if site == 'Mobalytics experts':
        for role, ts in MOBA.items():
            for t, cs in ts.items():
                for c in cs:
                    if (role, c) in ref: tv.append({'S': 3, 'A': 2, 'B': 1}[t]); wr.append(ref[(role, c)][0]); lp.append(ref[(role, c)][1])
        corr_num = None
    else:
        s = SITE[(SITE.site == site) & (SITE['rank'] == 'D')]
        for role, g in s.groupby('role'):
            g = g.drop_duplicates('c').set_index('c')
            w = g.pick if g.pick.notna().all() else pd.Series([1.0] * len(g), index=g.index)
            dl = deltas(g, w)
            for c, x in g.iterrows():
                if (role, c) in ref and x.tier in LV:
                    tv.append(LV[x.tier]); wr.append(ref[(role, c)][0]); lp.append(ref[(role, c)][1]); sd_.append(float(dl[c])); od.append(ref[(role, c)][0])
        corr_num = round(float(np.corrcoef(sd_, od)[0, 1]), 2) if len(sd_) > 10 else None
    grade.append([site, round(spearmanr(tv, wr).correlation, 2), round(spearmanr(tv, lp).correlation, 2), corr_num, len(tv)])

# ---------- backtest: does last patch predict this patch for champions that were not changed? ----------
bt = pd.DataFrame(prev_cmp, columns=['role', 'c', 'prev_raw', 'prev_sh', 'cur_raw', 'n_prev', 'n_cur'])
bt = bt[bt.n_cur >= 1000]
r_raw = float(np.corrcoef(bt.prev_raw, bt.cur_raw)[0, 1])
mse_raw = float(((bt.cur_raw - bt.prev_raw) ** 2).mean()); mse_sh = float(((bt.cur_raw - bt.prev_sh) ** 2).mean()); mse_0 = float((bt.cur_raw ** 2).mean())
backtest = {'n': int(len(bt)), 'r': round(r_raw, 2), 'mse_raw': round(mse_raw, 3), 'mse_shrunk': round(mse_sh, 3), 'mse_zero': round(mse_0, 3)}

# ---------- headline facts ----------
pop = [(r, e) for r in ROLES for e in out[r] if e['pick'] >= 5]
n_lose = 0
for r, e in pop:
    d = opgg('opgg_global_e', r)
    if float(d.loc[e['c'], 'win']) < 50: n_lose += 1
facts = {'n5': len(pop), 'n5_lose': n_lose, 'z': {r: [e['c'] for e in out[r] if e['t'] == 'Z'] for r in ROLES}}

out['_meta'] = {'patch': P['patch'], 'prev_patch': P['prev_patch'], 'next': P['next'], 'grade': grade, 'backtest': backtest,
                'tau': meta_tau, 'facts': facts, 'weights': {'consensus': CONS_W, 'high_elo': HI_W}}
json.dump(out, open('tiers.json', 'w', encoding='utf-8'), ensure_ascii=False)

# ---------- summary ----------
print('backtest', backtest)
print('facts', facts)
print('grade', grade)
taus = pd.Series(meta_tau); print('fitted spread (tau, points) median by dataset:'); print(taus.groupby(lambda k: k.split('|')[0]).median().round(2).to_string())
for r in ROLES:
    print(f'== {r}', ' | '.join(f"{t}: " + ', '.join(f"{e['c']} {e['score']:+.1f}" for e in sorted(out[r], key=lambda e: -e['score']) if e['t'] == t) for t in 'ZSAP'))
