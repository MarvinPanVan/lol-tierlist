"""One run from raw files to tiers.json.  python3 pipeline/update.py

Inputs (pipeline/):
  data/opgg_{global,euw,kr,na}_{e,d,m}_{role}.csv   OP.GG Emerald+ / Diamond+ / Master+ per region (champion,win,pick,ban)
  data/prev/opgg_global_e_{role}_<prev>.csv   OP.GG Global Emerald+ of the previous patch
  data/samples.json                           OP.GG 'Total analyzed samples' per dataset (= 10 x matches)
  data/lolalytics_global_e_{role}.csv         Lolalytics Emerald+ (letters only)
  data2/ugg_{d,m}.txt  data2/blitz_d.txt  data2/dpm_d.txt  data2/log_d.csv  data2/ms_d_{role}.txt  data2/moba_highelo.json
  patch.json                                  patch numbers, next patch preview, champions changed this patch
Output: tiers.json (roles + _meta) with a score, ± and tier for every rank x region view, printed summary incl. backtest.
Check: python3 pipeline/scripts/verify_views.py
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
VIEW_W = {'glob': .50, 'euw': .20, 'kr': .20, 'na': .10}   # weights of an 'All regions' view, same for every rank
# Global block per rank: OP.GG Emerald+; Diamond+ from OP.GG, U.GG, Blitz, dpm.lol and League of Graphs (half weight); Master+ from OP.GG and U.GG
GBLK = {'e': [('g', 1)], 'd': [('d_op', 1), ('U.GG|D', 1), ('Blitz|D', 1), ('dpm.lol|D', 1), ('League of Graphs|D', .5)], 'm': [('m_op', 1), ('U.GG|M', 1)]}
REGK = {'e': {'euw': 'euw', 'kr': 'kr', 'na': 'na'}, 'd': {'euw': 'euwd', 'kr': 'krd', 'na': 'nad'}, 'm': {'euw': 'euwm', 'kr': 'krm', 'na': 'nam'}}
PICKK = {'e': 'g', 'd': 'd_op', 'm': 'm_op'}   # pick rate used for the one-trick correction and the Z/P rules

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
# OP.GG's three hardest matchups per champion (tier list Counter column), Emerald+ and Diamond+. Stopgap until the Riot data has enough games.
CTR = json.load(open('data/opgg_counters.json')) if os.path.exists('data/opgg_counters.json') else {'e': {}, 'd': {}}
# entries: [opponent, games, wins of this champion]; stored as [opponent, win rate, games]
CTR = {rk: {r: {nm(c): [[nm(x[0]), round(100 * x[2] / x[1], 1), x[1]] for x in cs] for c, cs in v.items()} for r, v in CTR.get(rk, {}).items()} for rk in ['e', 'd']}
# OP.GG Emerald+ builds per champion and role: {role: {champ: {c0, c1: core builds, b0: boots, s0: starter, as [[item id, name], ...]}}}
BUILDS = json.load(open('data/opgg_builds.json', encoding='utf-8')) if os.path.exists('data/opgg_builds.json') else {}

# tiers: fixed rules, the same for every view, no hand edits
def tier(v, pk, allpos, zcheck):
    if v is None: return None
    if zcheck and pk >= 2: return 'Z'
    if pk < 1.5 and v >= .6: return 'P'
    if v >= 1.15 and allpos: return 'S'
    if v >= .6: return 'A'
    if v >= .15: return 'B'
    if v >= -.45: return 'C'
    return 'D'

out, meta_tau, prev_cmp = {}, {}, []
for role in ROLES:
    base = opgg('opgg_global_e', role)
    comp = {}          # name -> dict(raw delta, shrunk, sd, n)
    def add(key, d, label):
        if d is None: return
        dl = deltas(d); t2 = fit_tau2(dl, d.n); s, sd = shrink(dl, d.n, t2)
        meta_tau[f'{label}|{role}'] = round(math.sqrt(t2), 2)
        comp[key] = pd.DataFrame({'raw': dl, 'sh': s, 'sd': sd, 'n': d.n, 'pick': d.pick, 'ban': d.ban, 'win': d.win})
    add('g', base, 'OP.GG Global E+'); add('euw', opgg('opgg_euw_e', role), 'OP.GG EUW E+')
    add('kr', opgg('opgg_kr_e', role), 'OP.GG KR E+'); add('na', opgg('opgg_na_e', role), 'OP.GG NA E+')
    add('m_op', opgg('opgg_global_m', role), 'OP.GG Master+'); add('d_op', opgg('opgg_global_d', role), 'OP.GG Diamond+')
    add('euwd', opgg('opgg_euw_d', role), 'OP.GG EUW Diamond+'); add('euwm', opgg('opgg_euw_m', role), 'OP.GG EUW Master+')
    for rg in ['kr', 'na']:
        add(f'{rg}d', opgg(f'opgg_{rg}_d', role), f'OP.GG {rg.upper()} Diamond+'); add(f'{rg}m', opgg(f'opgg_{rg}_m', role), f'OP.GG {rg.upper()} Master+')
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
        # Lolalytics: best players on the champion (last 7 days) vs the Emerald+ average on it
        if best is not None and c in best.index and best.loc[c, 'best_games'] >= 1500:
            e['mx'] = round(float(best.loc[c, 'best_delta']), 1); e['mxw'] = round(float(best.loc[c, 'best_win']), 1)
        else: e['mx'] = e['mxw'] = None
        # every rank x region view, all scored the same way:
        #   All regions = Global block 50%, EUW 20%, KR 20%, NA 10% (all at that rank, each shrunk), minus the one-trick correction
        #   one region  = that OP.GG dataset alone, shrunk, minus the one-trick correction
        V = {}
        for rk in 'edm':
            blk = GBLK[rk]
            parts = {'glob': (avg([(val(k, c), w) for k, w in blk]), avg([(val(k, c, 'sd'), w) for k, w in blk]), avg([(val(k, c, 'raw'), w) for k, w in blk]))}
            for rg, k in REGK[rk].items(): parts[rg] = (val(k, c), val(k, c, 'sd'), val(k, c, 'raw'))
            pk = val(PICKK[rk], c, 'pick'); pk = pick if pk is None else pk
            av = {k: p for k, p in parts.items() if p[0] is not None}
            if not av: continue
            ws = sum(VIEW_W[k] for k in av)
            s_ = round(sum(VIEW_W[k] * p[0] for k, p in av.items()) / ws - spec(pk), 2)
            se_ = round(1.64 * sum(VIEW_W[k] * p[1] for k, p in av.items()) / ws, 2)   # errors treated as fully correlated (datasets overlap)
            raws = [p[2] for p in av.values()]
            V[rk.upper()] = [s_, se_, tier(s_, pk, all(x > 0 for x in raws), s_ >= 1.8 and min(raws) >= 1.5)]
            for rg, k in REGK[rk].items():
                if val(k, c) is None: continue
                pk2 = val(k, c, 'pick'); raw = val(k, c, 'raw')
                s2 = round(val(k, c) - spec(pk2), 2)
                V[k] = [s2, round(1.64 * val(k, c, 'sd'), 2), tier(s2, pk2, raw > 0, s2 >= 1.8 and raw >= 1.5)]
        e['v'] = V
        e['score'], e['se'], e['t'] = V['E']   # Emerald+, all regions: the default view (homepage, link previews, history)
        e['g'] = None if val('g', c, 'raw') is None else round(val('g', c, 'raw'), 2)   # raw Global Emerald+, for the history chart
        # games, pick, ban and win rate per dataset, so the site can show the numbers of the view you are in
        st = {}
        for k, ck in [('g', 'g'), ('euw', 'euw'), ('kr', 'kr'), ('na', 'na'), ('dia', 'd_op'), ('m', 'm_op'), ('euwd', 'euwd'), ('euwm', 'euwm'),
                      ('krd', 'krd'), ('krm', 'krm'), ('nad', 'nad'), ('nam', 'nam')]:
            dd = comp.get(ck)
            if dd is not None and c in dd.index:
                r = dd.loc[c]
                st[k] = [int(r.n), round(float(r.pick), 2), None if pd.isna(r.ban) else round(float(r.ban), 1), round(float(r.win), 2)]
        e['st'] = st
        # previous patch (Global Emerald+), both shrunk
        pv, gv = val('prev', c), val('g', c)
        e['tr'] = None if pv is None or gv is None else round(gv - pv, 2)
        # facts behind a move, no guessing: this patch's change from the patch notes, last patch's pick rate,
        # and how big the raw change is against normal sampling noise (z; under 1.64 it could be chance)
        e['ch'] = P.get('changes', {}).get(c)
        # changed items in the champion's most common OP.GG builds (Emerald+): two core builds and the boots, not starter items
        bd = BUILDS.get(role, {}).get(c) or {}
        own = {name for key in ['c0', 'c1', 'b0'] for _, name in bd.get(key, [])}
        e['it'] = [[name, kind, text] for name, (kind, text, slot) in P.get('item_changes', {}).items() if slot != 'starter' and name in own] or None
        e['pk0'] = None if val('prev', c, 'pick') is None else round(val('prev', c, 'pick'), 2)
        e['wr0'] = None if val('prev', c, 'win') is None else round(val('prev', c, 'win'), 2)   # last patch's win rate, Global Emerald+ (patch notes page)
        rg, rp = val('g', c, 'raw'), val('prev', c, 'raw')
        e['trz'] = None if rg is None or rp is None else round((rg - rp) / math.sqrt(2500 / val('g', c, 'n') + 2500 / val('prev', c, 'n')), 1)
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
        e['ctr'] = CTR['e'].get(role, {}).get(c); e['ctr_d'] = CTR['d'].get(role, {}).get(c)
        res.append(e)
    out[role] = res

# ---------- next patch flags ----------
for role, L in out.items():
    flags = {}
    for name, txt, kind in P['next']['roles'].get(role, []):
        for n in [x.strip() for x in name.split(',')]: flags[n] = (kind, txt)
    for e in L:
        f = flags.get(e['c']); e['nx'] = f[0] if f else None; e['nxt'] = f[1] if f else None

# ---------- notes, written from the numbers (the same view scores the site shows) ----------
from decimal import Decimal, ROUND_HALF_UP
def fx(v, nd=1):  # same as JavaScript's toFixed, which the site uses for pick rates
    return str(Decimal(v).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)) if nd else str(Decimal(v).quantize(Decimal(1), rounding=ROUND_HALF_UP))
def f1(v):  # same rounding as the site (Math.round), so notes and numbers match
    r = math.floor(v * 10 + .5) / 10; return ('+' if r > 0 else '−' if r < 0 else '') + f'{abs(r):.1f}'
LV = {'S+': 6, 'S': 5, 'S-': 4.5, 'A+': 4.3, 'A': 4, 'A-': 3.7, 'B+': 3.3, 'B': 3, 'B-': 2.7, 'C': 2, 'D': 1}
RKN = {'e': 'Emerald+', 'd': 'Diamond+', 'm': 'Master+'}
VN = {rk.upper(): RKN[rk] for rk in RKN} | {k: f'{rg.upper()} {RKN[rk]}' for rk in REGK for rg, k in REGK[rk].items()}
def note(e):
    v = {k: x[0] for k, x in e['v'].items()}; ts = [x[2] for x in e['v'].values()]
    lo, hi = min(v.values()), max(v.values())
    sure = {k: x[0] for k, x in e['v'].items() if x[1] <= 1}   # 'Mixed' only compares views with enough games
    lo_k, hi_k = (min(sure, key=sure.get), max(sure, key=sure.get)) if sure else (None, None)
    out = []
    ev_ = [v[k] for k in ['euw', 'kr', 'na'] if k in v]
    if all(t in 'ZS' for t in ts) and 'Z' in ts: out.append((10, f'Clear outlier: Z or S in all {len(ts)} rank and region views.'))
    elif all(e['v'].get(k, [0, 0, ''])[2] == 'Z' for k in 'EDM'): out.append((10, f'Outlier at every rank: {f1(v["E"])} in Emerald+, {f1(v["D"])} in Diamond+, {f1(v["M"])} in Master+.'))
    elif e['t'] == 'Z' and ev_: out.append((10, f'Outlier in Emerald+, ahead in every region there ({f1(min(ev_))} to {f1(max(ev_))}).'))
    elif lo >= .5: out.append((7, f'Above average in every rank and region ({f1(lo)} to {f1(hi)}).'))
    elif hi <= -.5: out.append((7, f'Below average in every rank and region ({f1(lo)} to {f1(hi)}).'))
    elif sure and sure[hi_k] - sure[lo_k] >= 1.8 and sure[hi_k] > .3 and sure[lo_k] < -.3: out.append((8, f'Mixed: {f1(sure[hi_k])} in {VN[hi_k]}, {f1(sure[lo_k])} in {VN[lo_k]}.'))
    E, D, M = v.get('E'), v.get('D'), v.get('M')
    if E is not None and D is not None and M is not None and not any(t.startswith('Outlier at every rank') for _, t in out):
        ranks = f'{f1(E)} in Emerald+, {f1(D)} in Diamond+, {f1(M)} in Master+.'
        if M - E >= .8: out.append((7, (('Less bad the higher the rank: ' if max(D, M) < 0 else 'Gets better with rank: ') if D >= E else 'Best in Master+: ') + ranks))
        elif E - M >= .8: out.append((7, (('Even worse the higher the rank: ' if E < 0 else 'Falls off with rank: ') if D <= E else 'Drops in Master+: ') + ranks))
    if e['pick'] >= 8 and e['score'] <= -.3: out.append((9, f'Very popular ({fx(e["pick"])}% pick in Emerald+) and still losing.'))
    elif e['pick'] >= 5 and e['score'] >= 1: out.append((8, f'Popular ({fx(e["pick"])}% pick in Emerald+) and still winning.'))
    elif e['pick'] < 1.5: out.append((8, f'Rarely picked ({fx(e["pick"])}% in Emerald+), mostly by mains. Expect less if you are new to it.'))
    # EUW Diamond+ and Master+ against all regions at the same ranks (EUW is the site's home server)
    if all(k in v for k in ['euwd', 'euwm', 'D', 'M']):
        ev, hb = (v['euwd'] + v['euwm']) / 2, (v['D'] + v['M']) / 2
        if abs(ev - hb) >= 1: out.append((6, f'{"Better" if ev > hb else "Worse"} on EUW in Diamond+ and Master+ ({f1(ev)} vs {f1(hb)} in all regions).'))
    sl = {k: x for k, x in e['sites'].items() if x in LV}
    if len(sl) >= 3:
        a, b = max(sl, key=lambda k: LV[sl[k]]), min(sl, key=lambda k: LV[sl[k]])
        if LV[sl[a]] - LV[sl[b]] >= 3: out.append((5, f'Sites disagree: {a} gives {sl[a]}, {b} gives {sl[b]}.'))
    if e.get('tr') is not None and abs(e['tr']) >= 1:
        out.append((6, f'{"Up" if e["tr"] > 0 else "Down"} {f1(e["tr"]).lstrip("+−")} points in Global Emerald+ since {P["prev_patch"]}.'))
    if e.get('mx') is not None and e['mx'] >= 6:
        out.append((7, f'Rewards mastery: the best players on it win {fx(e["mxw"], 0)}%, {fx(e["mx"])} points above the Emerald+ average on it.'))
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
                'tau': meta_tau, 'facts': facts, 'weights': {'all_regions': VIEW_W}}
json.dump(out, open('tiers.json', 'w', encoding='utf-8'), ensure_ascii=False)

# ---------- summary ----------
print('backtest', backtest)
print('facts', facts)
print('grade', grade)
taus = pd.Series(meta_tau); print('fitted spread (tau, points) median by dataset:'); print(taus.groupby(lambda k: k.split('|')[0]).median().round(2).to_string())
for r in ROLES:
    print(f'== {r}', ' | '.join(f"{t}: " + ', '.join(f"{e['c']} {e['score']:+.1f}" for e in sorted(out[r], key=lambda e: -e['score']) if e['t'] == t) for t in 'ZSAP'))
