"""Download champion portraits from Riot's Data Dragon into public/img/champ/<slug>.webp (64x64).
Runs in GitHub Actions (the build sandbox can't reach Riot). Also writes pipeline/data/ddragon_champions.json,
item icons to public/img/item/<id>.webp plus pipeline/data/ddragon_items.json, and ability icons to
public/img/spell/<champion slug>_<p|q|w|e|r>.webp,
summoner spell icons public/img/sum/<key>.webp, rune icons public/img/rune/<id>.webp and pipeline/data/ddragon_spells_runes.json."""
import os, re, json, io, urllib.request
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); PIPE = os.path.dirname(HERE); PUB = os.path.join(os.path.dirname(PIPE), 'public')
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'lol-tierlist'}), timeout=30).read()
ver = json.loads(get('https://ddragon.leagueoflegends.com/api/versions.json'))[0]
champs = json.loads(get(f'https://ddragon.leagueoflegends.com/cdn/{ver}/data/en_US/champion.json'))['data']
slug = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
os.makedirs(os.path.join(PUB, 'img', 'champ'), exist_ok=True)
by_key = {}
for cid, c in champs.items():
    by_key[c['key']] = c['name']
    im = Image.open(io.BytesIO(get(f'https://ddragon.leagueoflegends.com/cdn/{ver}/img/champion/{c["image"]["full"]}'))).convert('RGB')
    im = im.resize((64, 64), Image.LANCZOS)
    im.save(os.path.join(PUB, 'img', 'champ', slug(c['name']) + '.webp'), 'WEBP', quality=82, method=6)
    # art for the redesign: square face crop (tile) and wide centered splash. Art does not change between patches,
    # so only missing files are fetched (delete a file to refresh it).
    for kind, size, q in [('splash', (960, 540), 70), ('tile', (192, 192), 76)]:
        out = os.path.join(PUB, 'img', kind, slug(c['name']) + '.webp')
        if os.path.exists(out): continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        urls = [f'https://ddragon.leagueoflegends.com/cdn/img/champion/tiles/{cid}_0.jpg'] if kind == 'tile' else \
               [f'https://ddragon.leagueoflegends.com/cdn/img/champion/centered/{cid}_0.jpg', f'https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{cid}_0.jpg']
        for u in urls:
            try:
                a = Image.open(io.BytesIO(get(u))).convert('RGB')
            except Exception as e:
                print('miss', kind, cid, u, e); continue
            if kind == 'splash':   # cover-crop to 16:9
                w, h = a.size; th = int(w * 9 / 16)
                if th <= h: a = a.crop((0, (h - th) // 2, w, (h - th) // 2 + th))
            a = a.resize(size, Image.LANCZOS); a.save(out, 'WEBP', quality=q, method=6); break
        if kind == 'tile' and not os.path.exists(out):   # no tile on Data Dragon (e.g. Fiddlesticks): crop the splash
            sp = os.path.join(PUB, 'img', 'splash', slug(c['name']) + '.webp')
            if os.path.exists(sp):
                a = Image.open(sp); w, h = a.size; a.crop(((w - h) // 2, 0, (w - h) // 2 + h, h)).resize(size, Image.LANCZOS).save(out, 'WEBP', quality=q, method=6)
json.dump({'version': ver, 'by_key': by_key}, open(os.path.join(PIPE, 'data', 'ddragon_champions.json'), 'w'), ensure_ascii=False, indent=0)
# item icons for the patch notes pages: every Summoner's Rift item, 64x64 webp in public/img/item/<id>.webp (only missing files)
items = json.loads(get(f'https://ddragon.leagueoflegends.com/cdn/{ver}/data/en_US/item.json'))['data']
os.makedirs(os.path.join(PUB, 'img', 'item'), exist_ok=True)
by_name, got = {}, 0
for iid, it in items.items():
    if not it.get('maps', {}).get('11'): continue
    by_name.setdefault(it['name'], iid)
    out = os.path.join(PUB, 'img', 'item', f'{iid}.webp')
    if os.path.exists(out): continue
    try:
        Image.open(io.BytesIO(get(f'https://ddragon.leagueoflegends.com/cdn/{ver}/img/item/{iid}.png'))).convert('RGB').resize((64, 64), Image.LANCZOS).save(out, 'WEBP', quality=82, method=6); got += 1
    except Exception as e:
        print('miss item', iid, e)
json.dump({'version': ver, 'by_name': by_name}, open(os.path.join(PIPE, 'data', 'ddragon_items.json'), 'w'), ensure_ascii=False, indent=0)
print(f'{got} new item icons')
# ability icons for the patch notes pages: public/img/spell/<champion slug>_<p|q|w|e|r>.webp, 48x48 (only missing files)
os.makedirs(os.path.join(PUB, 'img', 'spell'), exist_ok=True); sp = 0
DD = 'https://ddragon.leagueoflegends.com/cdn'
for cid, c in champs.items():
    s_ = slug(c['name']); path = lambda k: os.path.join(PUB, 'img', 'spell', f'{s_}_{k}.webp')
    if all(os.path.exists(path(k)) for k in 'pqwer'): continue
    try:
        d = json.loads(get(f'{DD}/{ver}/data/en_US/champion/{cid}.json'))['data'][cid]
    except Exception as e:
        print('miss champion data', cid, e); continue
    for k, u in [('p', f'{DD}/{ver}/img/passive/{d["passive"]["image"]["full"]}')] + [(k, f'{DD}/{ver}/img/spell/{x["image"]["full"]}') for k, x in zip('qwer', d['spells'])]:
        if os.path.exists(path(k)): continue
        try:
            Image.open(io.BytesIO(get(u))).convert('RGB').resize((48, 48), Image.LANCZOS).save(path(k), 'WEBP', quality=82, method=6); sp += 1
        except Exception as e:
            print('miss spell', cid, k, e)
print(f'{sp} new ability icons')
# summoner spells and runes for the build section: icons + Riot's own short descriptions (shown as "what it does")
clean = lambda h: re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h or '')).replace(' .', '.').strip()
sums = json.loads(get(f'{DD}/{ver}/data/en_US/summoner.json'))['data']
os.makedirs(os.path.join(PUB, 'img', 'sum'), exist_ok=True); SUM = {}
for k, x in sums.items():
    if 'CLASSIC' not in x.get('modes', []): continue
    SUM[x['key']] = {'name': x['name'], 'desc': clean(x.get('description'))}
    out = os.path.join(PUB, 'img', 'sum', f'{x["key"]}.webp')
    if not os.path.exists(out):
        try: Image.open(io.BytesIO(get(f'{DD}/{ver}/img/spell/{x["image"]["full"]}'))).convert('RGB').resize((48, 48), Image.LANCZOS).save(out, 'WEBP', quality=82, method=6)
        except Exception as e: print('miss summoner', k, e)
runes = json.loads(get(f'{DD}/{ver}/data/en_US/runesReforged.json'))
os.makedirs(os.path.join(PUB, 'img', 'rune'), exist_ok=True); RUNE = {}
for tree in runes:
    RUNE[str(tree['id'])] = {'name': tree['name'], 'tree': True}
    items = [(tree['id'], tree['icon'])] + [(r['id'], r['icon']) for slot in tree['slots'] for r in slot['runes']]
    for slot in tree['slots']:
        for r in slot['runes']: RUNE[str(r['id'])] = {'name': r['name'], 'desc': clean(r.get('shortDesc')), 'style': tree['id']}
    for rid, icon in items:
        out = os.path.join(PUB, 'img', 'rune', f'{rid}.webp')
        if os.path.exists(out): continue
        try: Image.open(io.BytesIO(get(f'https://ddragon.leagueoflegends.com/cdn/img/{icon}'))).convert('RGBA').resize((48, 48), Image.LANCZOS).save(out, 'WEBP', quality=85, method=6)
        except Exception as e: print('miss rune', rid, e)
json.dump({'version': ver, 'summoners': SUM, 'runes': RUNE}, open(os.path.join(PIPE, 'data', 'ddragon_spells_runes.json'), 'w'), ensure_ascii=False, indent=0)
print(f'{len(SUM)} summoner spells, {len(RUNE)} runes')
print(f'{len(champs)} portraits from Data Dragon {ver}')
