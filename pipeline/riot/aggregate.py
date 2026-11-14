"""Turn the stored matches into champion win rates and lane matchups per role.
Writes pipeline/data/riot/agg_<patch>.json"""
import os, json, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); OUT = os.path.join(ROOT, 'data', 'riot')
patch = json.load(open(os.path.join(ROOT, 'patch.json')))['game_version']
POS = {'TOP': 'top', 'JUNGLE': 'jungle', 'MIDDLE': 'mid', 'BOTTOM': 'adc', 'UTILITY': 'support'}
ddn = {}
dd = os.path.join(ROOT, 'data', 'ddragon_champions.json')
if os.path.exists(dd): ddn = {int(k): v for k, v in json.load(open(dd))['by_key'].items()}
idname = lambda c: ddn.get(c, c)
games = collections.Counter(); wins = collections.Counter(); mu = collections.Counter(); muw = collections.Counter(); bans = collections.Counter()
matches = 0; regions = collections.Counter()
for fn in glob.glob(os.path.join(OUT, f'matches_*_{patch}.jsonl')):
    reg = os.path.basename(fn).split('_')[1]
    for line in open(fn):
        m = json.loads(line); matches += 1; regions[reg] += 1
        by = {}
        for champ, pos, team, win in m['p']:
            r = POS.get(pos)
            if not r: continue
            games[(r, champ)] += 1; wins[(r, champ)] += win; by.setdefault(r, []).append((champ, team, win))
        for r, xs in by.items():
            if len(xs) == 2 and xs[0][1] != xs[1][1]:
                (a, _, wa), (b, _, wb) = xs
                mu[(r, a, b)] += 1; muw[(r, a, b)] += wa; mu[(r, b, a)] += 1; muw[(r, b, a)] += wb
        for c in set(m.get('b', [])): bans[idname(c)] += 1
out = {'patch': patch, 'matches': matches, 'regions': dict(regions), 'roles': {}}
for (r, c), g in games.items():
    out['roles'].setdefault(r, {})[c] = {'games': g, 'win': round(100 * wins[(r, c)] / g, 2), 'pick': round(100 * g / matches, 2) if matches else 0}
out['matchups'] = {f'{r}|{a}|{b}': [g, muw[(r, a, b)]] for (r, a, b), g in mu.items() if g >= 5}
out['bans'] = {str(k): round(100 * v / matches, 2) for k, v in bans.items()} if matches else {}
json.dump(out, open(os.path.join(OUT, f'agg_{patch}.json'), 'w'), ensure_ascii=False)
print(f'{matches} matches ({dict(regions)}) -> agg_{patch}.json, {len(out["matchups"])} matchup pairs')
