"""Turn the files saved from the other stat sites (one download per site, see CLAUDE.md) into pipeline/data2 and data.
   python3 pipeline/collect/import_sites.py <folder with the lol-tierlist-<patch>-*.json/txt/csv files> <patch, e.g. 16.23>
Writes only the sites whose file is there. Prints line counts so a cut-off page is easy to spot."""
import os, sys, json, csv
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D2 = os.path.join(HERE, 'data2'); D = os.path.join(HERE, 'data')
src, patch = sys.argv[1], sys.argv[2]
f = lambda name: os.path.join(src, f'lol-tierlist-{patch}-{name}')
done = []
if os.path.exists(f('log-metasrc.json')) and not os.path.exists(f('metasrc.json')):   # both Chrome sites in one save: {"log": csv text, "ms": {...}}
    LM2 = json.load(open(f('log-metasrc.json'), encoding='utf-8'))
    json.dump(LM2['ms'], open(f('metasrc.json'), 'w', encoding='utf-8'))
    if not os.path.exists(f('log_d-v2.csv')): open(f('log_d-v2.csv'), 'w', encoding='utf-8').write(LM2['log'])

if os.path.exists(f('ugg.json')):   # {"d|top": "slug;role;tier;win;pick;ban;games\n...", "m|top": ...}
    U = json.load(open(f('ugg.json'), encoding='utf-8'))
    for rk in 'dm':
        lines = [l for k in ['top', 'jungle', 'mid', 'adc', 'support'] for l in U.get(f'{rk}|{k}', '').split('\n') if l]
        for l in lines: assert len(l.split(';')) == 7, l
        open(os.path.join(D2, f'ugg_{rk}.txt'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n'); done.append(f'ugg_{rk}.txt {len(lines)}')

for name, out in [('blitz_d.txt', 'blitz_d.txt'), ('dpm_d.txt', 'dpm_d.txt'), ('moba_highelo.json', 'moba_highelo.json')]:
    if os.path.exists(f(name)):
        t = open(f(name), encoding='utf-8').read()
        if name.endswith('.json'): json.loads(t)
        open(os.path.join(D2, out), 'w', encoding='utf-8').write(t); done.append(f'{out} {t.count(chr(10)) or len(t)}')

for name in ['log_d-v2.csv', 'log_d.csv']:   # League of Graphs (Chrome); a -v2 file replaces a bad first save
    if os.path.exists(f(name)):
        rows = open(f(name), encoding='utf-8').read().strip().split('\n')
        assert rows[0] == 'champion,role,tier,pop,win,ban' and all(len(r.split(';')) == 6 for r in rows[1:])
        assert {r.split(';')[1] for r in rows[1:]} <= set('TJMBS'), 'unknown role letter'
        open(os.path.join(D2, 'log_d.csv'), 'w', encoding='utf-8').write('\n'.join(rows) + '\n'); done.append(f'log_d.csv {len(rows) - 1} from {name}'); break

if os.path.exists(f('metasrc.json')):   # {"top": "Name,Tier,win,pick,ban,games|...", ...}
    M = json.load(open(f('metasrc.json'), encoding='utf-8'))
    for r, v in M.items():
        assert all(len(x.split(',')) == 6 for x in v.split('|')), r
        open(os.path.join(D2, f'ms_d_{r}.txt'), 'w', encoding='utf-8').write(v + '\n'); done.append(f'ms_d_{r}.txt {v.count("|") + 1}')

if os.path.exists(f('lolalytics.json')):   # rows per lane: [rank, name, tier, lane %, win, delta, pick, ban, ?, games, ?, best win, best games, best delta, best elo]
    L = json.load(open(f('lolalytics.json'), encoding='utf-8')); LM = {'top': 'top', 'jungle': 'jungle', 'middle': 'mid', 'bottom': 'adc', 'support': 'support'}
    num = lambda s: s.replace(',', '')
    for lane, rows in L.items():
        r = LM[lane]
        with open(os.path.join(D, f'lolalytics_global_e_{r}.csv'), 'w', encoding='utf-8', newline='') as g, open(os.path.join(D, f'lolalytics_best_{r}.csv'), 'w', encoding='utf-8', newline='') as b:
            G, B = csv.writer(g), csv.writer(b)
            G.writerow(['champion', 'tier', 'win', 'pick', 'ban', 'games']); B.writerow(['champion', 'tier', 'win', 'games', 'best_win', 'best_games', 'best_delta', 'best_elo'])
            for x in rows:
                if len(x) < 15: continue
                G.writerow([x[1], x[2], x[4], x[6], x[7], num(x[9])])
                B.writerow([x[1], x[2], x[4], num(x[9]), x[11], num(x[12]), x[13], x[14]])
        done.append(f'lolalytics {r} {len(rows)}')
print('\n'.join(done) or 'nothing found')
