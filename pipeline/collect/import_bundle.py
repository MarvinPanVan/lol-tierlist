"""Check a file saved by pipeline/collect/opgg_collect.js and split it into pipeline/data/.
   python3 pipeline/collect/import_bundle.py <file> [<length> <number sum>]
The length and number sum come from TLC.run() in the browser; if they don't match, nothing is written (the file is damaged
or from another run). Parts it understands: stats (+ samples), counters, builds, skills, vs, rune_pages, game_length, synergy.
For a NEW patch, first copy the current data/opgg_global_e_<role>.csv files to data/prev/ (trend arrows and backtest)."""
import os, re, sys, json, math
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); DATA = os.path.join(HERE, 'data')
src = sys.argv[1]; txt = open(src, encoding='utf-8').read()
if len(sys.argv) >= 4:
    L, S = int(sys.argv[2]), int(sys.argv[3]); s = sum(int(x) for x in re.findall(r'-?\d+', txt))
    if (len(txt), s) != (L, S): sys.exit(f'file does not match the browser: length {len(txt)} vs {L}, sum {s} vs {S}. Nothing written.')
B = json.loads(txt); wrote = []
def dump(name, obj):
    json.dump(obj, open(os.path.join(DATA, name), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':')); wrote.append(name)

if B.get('stats'):   # tier list pages -> CSV per dataset and role, plus OP.GG's sample totals
    for key, rows in B['stats'].items():
        tot_pick = sum(float(r[2]) for r in rows); avg = sum(float(r[1]) * float(r[2]) for r in rows) / tot_pick if tot_pick else 0
        if not (150 <= tot_pick <= 210 and 48 <= avg <= 52): print(f'CHECK {key}: picks add to {tot_pick:.0f}%, average win {avg:.1f}%')
        with open(os.path.join(DATA, key + '.csv'), 'w', encoding='utf-8') as f:
            f.write('champion,win,pick,ban\n' + ''.join(f'{c},{w},{p},{b}\n' for c, w, p, b in rows))
    wrote.append(f'{len(B["stats"])} stats CSVs')
    if B.get('samples'):
        sp = os.path.join(DATA, 'samples.json'); cur = json.load(open(sp)) if os.path.exists(sp) else {}
        cur.update(B['samples']); json.dump(cur, open(sp, 'w'), indent=1); wrote.append('samples.json')

if B.get('counters'):   # matchups: rank by the gap to the champion's own win rate, shrunk by sample size (see CLAUDE.md)
    out, full = {}, {}
    for rk, M in B['counters'].items():
        pre, roles = {}, {}
        for k, Lm in M.items():
            if not Lm: continue
            N = sum(x[1] for x in Lm); W = sum(x[2] for x in Lm); o = W / N
            pre[k] = (N, W, [(op, n, w, 100 * (w / n - o), 2500 / n) for op, n, w in Lm])
            roles.setdefault(k.split('|')[0], []).extend(x for x in pre[k][2] if x[1] >= 300)
        tau = {r: max(sum(d * d - v for *_, d, v in Lx) / len(Lx), 1) for r, Lx in roles.items()}
        names, m = [], {}
        ix = lambda n: names.index(n) if n in names else (names.append(n) or len(names) - 1)
        for k, (N, W, Lm) in pre.items():
            t2 = tau[k.split('|')[0]]
            E = [(op, n, w, d * t2 / (t2 + v), 1 if abs(d) / math.sqrt(v) >= 1.64 else 0) for op, n, w, d, v in Lm if n >= 150]
            h = sorted([x for x in E if x[3] < 0], key=lambda x: x[3])[:5]; g = sorted([x for x in E if x[3] > 0], key=lambda x: -x[3])[:5]
            m[k] = {'o': [N, W], 'h': [[ix(op), n, w, c] for op, n, w, _, c in h], 'g': [[ix(op), n, w, c] for op, n, w, _, c in g]}
        out[rk] = {'names': names, 'm': m}
        # every opponent with 150+ games, for the counter-pick finder ("best picks into X" = X's own list, turned around)
        full[rk] = {k: [[op, n, w] for op, n, w, d, v in Lm if n >= 150] for k, (N, W, Lm) in pre.items()}
        clear = sum(x[4] for k in pre for x in [(0, 0, 0, 0, 1 if abs(d) / math.sqrt(v) >= 1.64 else 0) for _, n, _, d, v in pre[k][2] if n >= 150])
        total = sum(1 for k in pre for x in pre[k][2] if x[1] >= 150)
        print(f'matchups {rk}: {len(m)} champions, {clear / max(total, 1):.0%} of 150+ game matchups clear, tau by role', {r: round(v, 1) for r, v in tau.items()})
    dump('opgg_matchups.json', out); dump('opgg_matchups_full.json', full)

if B.get('builds'):
    dump('opgg_build_stats.json', B['builds'])
    # opgg_builds.json (item names of the two core builds, boots and start; used to match item changes) from the same data
    di = os.path.join(DATA, 'ddragon_items.json')
    iname = {v: k for k, v in json.load(open(di, encoding='utf-8'))['by_name'].items() if '<' not in k} if os.path.exists(di) else {}
    nm = lambda i: iname.get(str(i)) or iname.get('32' + str(i)) or str(i)
    ob = {}
    for k, (sp, rn, co, bo, st) in B['builds'].items():
        r, c = k.split('|')
        ob.setdefault(r, {})[c] = {'c0': [[i, nm(i)] for i in co[0][0]] if co else [], 'c1': [[i, nm(i)] for i in co[1][0]] if len(co) > 1 else [],
                                   'b0': [[bo[0][0], nm(bo[0][0])]] if bo else [], 's0': [[i, nm(i)] for i in st[0][0]] if st else []}
    dump('opgg_builds.json', ob)
if B.get('synergy'):   # OP.GG synergies page: the 10 most played partners per other position, [position, partner, games, wins]
    dump('opgg_synergy.json', B['synergy'])
for part, name in [('skills', 'opgg_skills.json'), ('vs', 'opgg_vs_builds.json'), ('rune_pages', 'opgg_rune_pages.json'), ('game_length', 'opgg_game_length.json')]:
    if B.get(part):
        if part == 'game_length':
            bad = [k for k, v in B[part].items() if len(v) != 5]
            if bad: print(f'CHECK game_length: {len(bad)} champions without 5 buckets, e.g. {bad[:3]}')
        dump(name, B[part])
if B.get('errors'): print(f'{len(B["errors"])} pages failed in the browser, e.g. {B["errors"][:3]}')
print(f'patch {B.get("patch")}, made {B.get("made")}: wrote', ', '.join(wrote) or 'nothing')
