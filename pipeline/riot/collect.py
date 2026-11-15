"""Collect ranked solo/duo matches of Master+ players from the Riot API (runs in GitHub Actions).

Stores no player identifiers: per match only the match id, game version, duration, and for each of the
10 players champion name, position, team and win, plus the banned champion ids. Since 15 Nov 2026 also each player's
build ('k', same order as 'p'): summoner spells, keystone, secondary rune tree and final items, so the site can say when
players switch (enemy team AD/AP, ranged lane opponent...) once there are enough matches.
Usage: RIOT_API_KEY=... python pipeline/riot/collect.py --minutes 45 --regions euw1,kr
"""
import os, sys, json, time, argparse, urllib.request, urllib.error, random
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'data', 'riot')
ROUTE = {'euw1': 'europe', 'eun1': 'europe', 'kr': 'asia', 'na1': 'americas'}
KEY = os.environ.get('RIOT_API_KEY', '').strip()

class Api:
    def __init__(self, key, gap):
        self.key, self.gap, self.last, self.calls = key, gap, 0.0, 0
    def get(self, url, tries=5):
        for t in range(tries):
            wait = self.last + self.gap - time.time()
            if wait > 0: time.sleep(wait)
            self.last = time.time(); self.calls += 1
            req = urllib.request.Request(url, headers={'X-Riot-Token': self.key, 'User-Agent': 'lol-tierlist-collector'})
            try:
                with urllib.request.urlopen(req, timeout=20) as r:
                    return json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    ra = int(e.headers.get('Retry-After', '10')); print(f'429, sleeping {ra}s', flush=True); time.sleep(ra + 1); continue
                if e.code in (401, 403):
                    sys.exit(f'Riot API says {e.code}: the key is missing, expired or not allowed. Regenerate it and update the RIOT_API_KEY secret.')
                if e.code == 404: return None
                if e.code >= 500: time.sleep(2 + 2 * t); continue
                raise
            except (urllib.error.URLError, TimeoutError):
                time.sleep(2 + 2 * t)
        return None

def build(p):   # [spell 1, spell 2, keystone, secondary rune tree, [final items 0-5]] - game data only, nothing about the player
    st = (p.get('perks') or {}).get('styles') or [{}, {}]
    key = ((st[0].get('selections') or [{}])[0]).get('perk') if st else None
    sec = st[1].get('style') if len(st) > 1 else None
    return [p.get('summoner1Id'), p.get('summoner2Id'), key, sec, [p.get(f'item{i}', 0) for i in range(6)]]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--minutes', type=float, default=45)
    ap.add_argument('--regions', default='euw1,kr')
    ap.add_argument('--per-player', type=int, default=20)
    ap.add_argument('--gap', type=float, default=1.25, help='seconds between calls; 1.25 fits a development key (100 per 2 minutes)')
    a = ap.parse_args()
    if not KEY: sys.exit('RIOT_API_KEY is not set.')
    patch = json.load(open(os.path.join(ROOT, 'patch.json')))['game_version']
    api = Api(KEY, a.gap)
    deadline = time.time() + a.minutes * 60
    regions = a.regions.split(',')
    os.makedirs(OUT, exist_ok=True)
    total_new = 0
    for i, reg in enumerate(regions):
        reg_deadline = time.time() + (deadline - time.time()) / (len(regions) - i)
        plat, rte = f'https://{reg}.api.riotgames.com', f'https://{ROUTE[reg]}.api.riotgames.com'
        fn = os.path.join(OUT, f'matches_{reg}_{patch}.jsonl')
        seen = set()
        if os.path.exists(fn):
            for line in open(fn): seen.add(json.loads(line)['id'])
        players = []
        for lg in ['challengerleagues', 'grandmasterleagues', 'masterleagues']:
            d = api.get(f'{plat}/lol/league/v4/{lg}/by-queue/RANKED_SOLO_5x5')
            if d: players += [e.get('puuid') for e in d.get('entries', []) if e.get('puuid')]
        random.shuffle(players)
        print(f'{reg}: {len(players)} Master+ players, {len(seen)} matches already stored', flush=True)
        start = int(time.time()) - 14 * 86400
        new = 0
        with open(fn, 'a') as f:
            for pu in players:
                if time.time() > reg_deadline: break
                ids = api.get(f'{rte}/lol/match/v5/matches/by-puuid/{pu}/ids?queue=420&type=ranked&startTime={start}&count={a.per_player}') or []
                for mid in ids:
                    if mid in seen or time.time() > reg_deadline: continue
                    seen.add(mid)
                    m = api.get(f'{rte}/lol/match/v5/matches/{mid}')
                    if not m: continue
                    info = m['info']
                    if not info.get('gameVersion', '').startswith(patch + '.'):
                        continue
                    ps = info['participants']
                    if any(p.get('gameEndedInEarlySurrender') for p in ps) or info.get('gameDuration', 0) < 600: continue
                    rec = {'id': mid, 'v': info['gameVersion'], 'd': info['gameDuration'],
                           'p': [[p['championName'], p.get('teamPosition', ''), p['teamId'], int(p['win'])] for p in ps],
                           'b': [b['championId'] for t in info.get('teams', []) for b in t.get('bans', []) if b.get('championId', -1) > 0],
                           'k': [build(p) for p in ps]}
                    f.write(json.dumps(rec, separators=(',', ':')) + '\n'); new += 1
                    if new % 50 == 0: print(f'{reg}: {new} new matches ({api.calls} calls)', flush=True); f.flush()
        print(f'{reg}: stored {new} new matches', flush=True); total_new += new
    print(f'done: {total_new} new matches, {api.calls} API calls')

if __name__ == '__main__':
    main()
