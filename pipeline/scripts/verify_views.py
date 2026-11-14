"""Independent recompute of every rank x region view from the raw files, compared with tiers.json.
Run after update.py: python3 pipeline/scripts/verify_views.py  (prints mismatches, ends with a count)"""
import json, math, re, csv, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
T = json.load(open('tiers.json')); P = json.load(open('patch.json')); S = json.load(open('data/samples.json'))
sl = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
RM = {'T':'top','J':'jungle','M':'mid','B':'adc','S':'support','top':'top','jungle':'jungle','mid':'mid','middle':'mid','adc':'adc','bottom':'adc','support':'support','utility':'support'}
def readop(name, role, prev=None):
    f = f'data/prev/{name}_{role}_{prev}.csv' if prev else f'data/{name}_{role}.csv'
    rows = {}
    for r in csv.DictReader(open(f, encoding='utf-8')):
        if r['champion'] in rows: continue
        pk = float(r['pick']); rows[r['champion']] = dict(w=float(r['win']), p=pk, n=pk/100*S[f'{name}_{prev}' if prev else name]/10)
    return rows
def fit(rows, wkey='p', nkey='n'):
    tw = sum(x[wkey] for x in rows.values()); m = sum(x['w']*x[wkey] for x in rows.values())/tw
    d = {c: x['w']-m for c, x in rows.items()}
    big = [c for c in rows if rows[c][nkey] >= 300]
    t2 = max(.35**2, sum(d[c]**2 for c in big)/len(big) - sum(2500/rows[c][nkey] for c in big)/len(big))
    out = {}
    for c, x in rows.items():
        v = 2500/x[nkey]; out[c] = dict(raw=d[c], sh=d[c]*t2/(t2+v), sd=math.sqrt(t2*v/(t2+v)), p=x[wkey], n=x[nkey])
    return out
def spec(p): return .4*math.log(max(1, 2/p)) if p and p > 0 else .4*math.log(2/.3)
def tier(v, pk, allpos, z):
    if z and pk >= 2: return 'Z'
    if pk < 1.5 and v >= .6: return 'P'
    if v >= 1.15 and allpos: return 'S'
    return 'A' if v >= .6 else 'B' if v >= .15 else 'C' if v >= -.45 else 'D'
# third-party Diamond+/Master+ files -> {(site,rank,role): {champ: dict(w,p,n or None)}}
alias = {}
for f in os.listdir('data'):
    if f.startswith('opgg_') and f.endswith('.csv'):
        for r in csv.DictReader(open('data/'+f, encoding='utf-8')): alias[sl(r['champion'])] = r['champion']
alias.update({'monkeyking':'Wukong','nunu':'Nunu & Willump','nunuwillump':'Nunu & Willump','renata':'Renata Glasc'})
nm = lambda s: alias.get(sl(s), s)
TP = {}
def add(site, rk, role, c, w, p, n):
    TP.setdefault((site, rk, RM[role]), {}).setdefault(nm(c), dict(w=w, p=p, n=n))
for line in open('data2/ugg_d.txt'): c, r, t, w, p, b, g = line.strip().split(';'); add('U.GG','D',r,c,float(w),float(p),int(g))
for line in open('data2/ugg_m.txt'): c, r, t, w, p, b, g = line.strip().split(';'); add('U.GG','M',r,c,float(w),float(p),int(g))
for line in open('data2/dpm_d.txt'):
    x = line.strip().split(';'); c, r = x[1].split('|'); add('dpm.lol','D',r,c,float(x[4].strip('%')),float(x[6].strip('%')),int(x[7].replace('.','')))
for line in open('data2/blitz_d.txt'):
    t, rest = line.strip().split('=', 1)
    for it in rest.split(): c, r, w = it.split('/'); add('Blitz','D',r,c,float(w),None,None)
for i, line in enumerate(open('data2/log_d.csv')):
    if i: c, r, t, pop, w, b = line.strip().split(';'); add('League of Graphs','D',r,c,float(w),float(pop),None)
bad = 0; checked = 0
for role in ['top','jungle','mid','adc','support']:
    D = {k: fit(readop(f'opgg_{k}', role)) for k in ['global_e','euw_e','kr_e','na_e','global_d','euw_d','kr_d','na_d','global_m','euw_m','kr_m','na_m']}
    prv = fit(readop('opgg_global_e', role, P['prev_patch_code']))
    g = D['global_e']; same = [c for c in g if c in prv and c not in P['changed_this_patch']]
    bigc = [c for c in same if g[c]['n'] >= 1000 and prv[c]['n'] >= 1000]
    sc2 = max(.03, sum((g[c]['raw']-prv[c]['raw'])**2 for c in bigc)/len(bigc) - sum(2500/g[c]['n'] for c in bigc)/len(bigc) - sum(2500/prv[c]['n'] for c in bigc)/len(bigc))
    for c in same:
        v = 2500/g[c]['n']; pv = sc2 + prv[c]['sd']**2
        g[c] = dict(g[c], sh=(g[c]['raw']/v + prv[c]['sh']/pv)/(1/v+1/pv), sd=math.sqrt(1/(1/v+1/pv)))
    tps = {}
    for (site, rk, r), rows in TP.items():
        if r != role: continue
        rows = {c: dict(x) for c, x in rows.items()}
        for c, x in rows.items():
            if x['p'] is None: x['p'] = D['global_d'][c]['p'] if c in D['global_d'] else .3
            if x['n'] is None: x['n'] = D['global_d'][c]['n'] if c in D['global_d'] else 300
            x['n'] = max(50, x['n'])
        tps[(site, rk)] = fit(rows)
    GB = {'e': [(g, 1)], 'd': [(D['global_d'], 1), (tps[('U.GG','D')], 1), (tps[('Blitz','D')], 1), (tps[('dpm.lol','D')], 1), (tps[('League of Graphs','D')], .5)], 'm': [(D['global_m'], 1), (tps[('U.GG','M')], 1)]}
    for e in T[role]:
        c = e['c']
        for rk in 'edm':
            def bavg(f):
                pr = [(src[c][f], w) for src, w in GB[rk] if c in src]
                return sum(a*w for a, w in pr)/sum(w for _, w in pr) if pr else None
            parts = {'glob': (bavg('sh'), bavg('sd'), bavg('raw'), .5)}
            for rg, wt in [('euw', .2), ('kr', .2), ('na', .1)]:
                x = D[f'{rg}_{rk}'].get(c); parts[rg] = (x['sh'], x['sd'], x['raw'], wt) if x else (None,)*3 + (wt,)
            av = [p for p in parts.values() if p[0] is not None]
            pk = D[f'global_{rk}'][c]['p'] if c in D[f'global_{rk}'] else g[c]['p']
            s = round(sum(p[0]*p[3] for p in av)/sum(p[3] for p in av) - spec(pk), 2)
            se = round(1.64*sum(p[1]*p[3] for p in av)/sum(p[3] for p in av), 2)
            want = [s, se, tier(s, pk, all(p[2] > 0 for p in av), s >= 1.8 and min(p[2] for p in av) >= 1.5)]
            got = e['v'].get(rk.upper()); checked += 1
            if got != want and not (got and abs(got[0]-want[0]) <= .011 and abs(got[1]-want[1]) <= .011 and got[2] == want[2]): bad += 1; print('MISMATCH', role, c, rk.upper(), got, want)
            for rg in ['euw','kr','na']:
                x = D[f'{rg}_{rk}'].get(c); k = rg + ('' if rk == 'e' else rk)
                if not x:
                    if k in e['v']: bad += 1; print('EXTRA', role, c, k)
                    continue
                s2 = round(x['sh']-spec(x['p']), 2); want = [s2, round(1.64*x['sd'], 2), tier(s2, x['p'], x['raw'] > 0, s2 >= 1.8 and x['raw'] >= 1.5)]
                got = e['v'].get(k); checked += 1
                if got != want and not (got and abs(got[0]-want[0]) <= .011 and abs(got[1]-want[1]) <= .011 and got[2] == want[2]): bad += 1; print('MISMATCH', role, c, k, got, want)
        if [e['score'], e['se'], e['t']] != e['v']['E']: bad += 1; print('E fields differ', role, c)
print(f'checked {checked} view values, {bad} mismatches')
