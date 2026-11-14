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
json.dump({'version': ver, 'by_key': by_key}, open(os.path.join(PIPE, 'data', 'ddragon_champions.json'), 'w'), ensure_ascii=False, indent=0)
print(f'{len(champs)} portraits from Data Dragon {ver}')
