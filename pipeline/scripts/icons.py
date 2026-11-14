"""Download champion portraits from Riot's Data Dragon into public/img/champ/<slug>.webp (64x64).
Runs in GitHub Actions (the build sandbox can't reach Riot). Also writes pipeline/data/ddragon_champions.json."""
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
print(f'{len(champs)} portraits from Data Dragon {ver}')
