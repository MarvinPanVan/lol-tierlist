"""Build the site from pipeline/template.html + pipeline/tiers.json.
Writes public/index.html, public/<role>/index.html, public/method/index.html, public/404.html, robots.txt, sitemap.xml.
Run: python3 pipeline/build.py   (then pipeline/scripts/assets.py for favicon and link previews)"""
import os, re, json, html, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); PUB = os.path.join(os.path.dirname(HERE), 'public')
SITE = 'https://lol-tierlist.pages.dev/'
ROLES = [('top', 'Top', 'top laners'), ('jungle', 'Jungle', 'junglers'), ('mid', 'Mid', 'mid laners'), ('adc', 'ADC', 'ADCs'), ('support', 'Support', 'supports')]
T = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
RAW = open(os.path.join(HERE, 'tiers.json'), encoding='utf-8').read()
D = json.loads(RAW); P = json.load(open(os.path.join(HERE, 'patch.json'), encoding='utf-8'))
PATCH = P['patch']
assert T.count('__DATA__') == 1
TR = {'Z': 0, 'S': 1, 'A': 2, 'B': 3, 'C': 4, 'D': 5, 'P': 6}

def strip(h, keep):
    drop = 'M' if keep == 'B' else 'B'
    h = re.sub(rf'<!--{drop}-->.*?<!--/{drop}-->', '', h, flags=re.S)
    return h.replace(f'<!--{keep}-->', '').replace(f'<!--/{keep}-->', '')

def write(rel, h):
    path = os.path.join(PUB, rel); os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(h)

def page(rel, keep, root, page_kind, role, title, ogtitle, desc, url, ogimg):
    h = strip(T, keep)
    rep = {'__TITLE__': html.escape(title), '__OGTITLE__': html.escape(ogtitle, quote=True), '__DESC__': html.escape(desc, quote=True),
           '__URL__': url, '__OGIMG__': ogimg, '__ROOT__': root, '__PAGE__': page_kind, '__ROLE__': role, '__PATCH__': PATCH}
    for k, v in rep.items(): h = h.replace(k, v)
    write(rel, h.replace('__DATA__', RAW))

def top_line(role):
    L = sorted([e for e in D[role] if e['t'] in 'ZS'], key=lambda e: (TR[e['t']], -e['score']))[:5]
    parts = [f"{e['c']} ({e['t']})" for e in L]
    return ', '.join(parts[:-1]) + (' and ' + parts[-1] if len(parts) > 1 else (parts[0] if parts else ''))

base_desc = f'League of Legends tier list for patch {PATCH}, every role, built from nine stat sites (OP.GG, U.GG, Blitz, dpm.lol, League of Graphs and more) and corrected for sample size and one-trick inflation.'
z = [c for r, _, _ in ROLES for c in D['_meta']['facts']['z'][r]]
page('index.html', 'B', '', 'board', 'top', f'LoL Tier List: patch {PATCH}, every role', f'LoL Tier List {PATCH}' + (f": {', '.join(z[:-1])} and {z[-1]} lead" if len(z) > 1 else ''), base_desc, SITE, SITE + 'og.png')
for r, name, plural in ROLES:
    page(f'{r}/index.html', 'B', '../', 'board', r, f'{name} tier list, patch {PATCH} | LoL Tier List', f'{name} tier list for patch {PATCH}',
         f'Best {plural} in patch {PATCH}: {top_line(r)}. Win rate above the role average from nine stat sites, corrected for sample size and one-tricks.',
         SITE + r + '/', SITE + f'og-{r}.png')
page('method/index.html', 'M', '../', 'method', 'top', 'How the tier list is made | LoL Tier List', 'How the LoL tier list is made',
     'Where the numbers come from, how nine stat sites are combined into one score and tier, how far each site can be trusted, and what a tier list cannot tell you.',
     SITE + 'method/', SITE + 'og.png')

# patch archive: the current patch in full, plus every older patch file already in public/data
cur = json.loads(RAW); cur['_meta']['kind'] = 'full'; cur['_meta']['label'] = 'Full data'
os.makedirs(os.path.join(PUB, 'data'), exist_ok=True)
json.dump(cur, open(os.path.join(PUB, 'data', f'{PATCH}.json'), 'w', encoding='utf-8'), ensure_ascii=False)
pl = []
for f in os.listdir(os.path.join(PUB, 'data')):
    if re.fullmatch(r'\d+\.\d+\.json', f):
        m = json.load(open(os.path.join(PUB, 'data', f), encoding='utf-8'))['_meta']
        pl.append({'patch': f[:-5], 'kind': m.get('kind', 'full'), 'label': m.get('label', '')})
pl.sort(key=lambda x: [int(p) for p in x['patch'].split('.')], reverse=True)
json.dump({'current': PATCH, 'patches': pl[:6]}, open(os.path.join(PUB, 'data', 'patches.json'), 'w'), indent=0)
write('404.html', f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Page not found | LoL Tier List</title><meta name="robots" content="noindex"><link rel="icon" href="/favicon.svg" type="image/svg+xml">
<style>@font-face{{font-family:Inter;font-weight:800;src:url(/fonts/inter-latin-800-normal.woff2) format('woff2')}}@font-face{{font-family:Inter;font-weight:400;src:url(/fonts/inter-latin-400-normal.woff2) format('woff2')}}
:root{{color-scheme:light dark}}body{{margin:0;min-height:100svh;display:grid;place-items:center;font:16px/1.6 Inter,system-ui,sans-serif;background:light-dark(#f5f6f8,#0b0c0f);color:light-dark(#0f1115,#eceef2)}}
main{{text-align:center;padding:24px}}h1{{font-weight:800;font-size:44px;letter-spacing:-.03em;margin:16px 0 6px}}p{{color:light-dark(#646b78,#959cab);margin:0 0 22px}}
a{{display:inline-block;padding:11px 18px;border-radius:999px;background:light-dark(#0f1115,#eceef2);color:light-dark(#fff,#0b0c0f);text-decoration:none;font-weight:600}}img{{width:56px;height:56px}}</style></head>
<body><main><img src="/favicon.svg" alt=""><h1>Nothing here</h1><p>That page doesn't exist. The tier list does.</p><a href="/">Open the tier list</a></main></body></html>''')
write('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\n')
today = datetime.date.today().isoformat()
urls = [SITE] + [SITE + r + '/' for r, _, _ in ROLES] + [SITE + 'method/']
write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n' for u in urls) + '</urlset>\n')
print('built: index, ' + ', '.join(r for r, _, _ in ROLES) + ', method, 404, robots, sitemap')
