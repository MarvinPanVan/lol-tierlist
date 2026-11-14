"""Build the site from pipeline/template.html + pipeline/tiers.json.
Writes public/index.html, public/<role>/index.html, public/method/index.html, public/404.html, robots.txt, sitemap.xml.
Run: python3 pipeline/build.py   (then pipeline/scripts/assets.py for favicon and link previews)"""
import os, re, json, html, datetime, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); PUB = os.path.join(os.path.dirname(HERE), 'public')
SITE = 'https://lol-tierlist.pages.dev/'
ROLES = [('top', 'Top', 'top laners'), ('jungle', 'Jungle', 'junglers'), ('mid', 'Mid', 'mid laners'), ('adc', 'ADC', 'ADCs'), ('support', 'Support', 'supports')]
T = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
RAW = open(os.path.join(HERE, 'tiers.json'), encoding='utf-8').read()
D = json.loads(RAW); P = json.load(open(os.path.join(HERE, 'patch.json'), encoding='utf-8'))
PATCH = P['patch']
assert T.count('__DATA__') == 1
# CSS and JS live in the template for editing, but ship as shared cached files (assets/app.<hash>.css/js)
def _cut(src, start, end):
    i = src.index(start); j = src.index(end, i) + len(end); return src[i:j], src[i + len(start):j - len(end)]
_css_block, CSS = _cut(T, '<style>\n/* DESIGN', '</style>'); CSS = '/* DESIGN' + CSS
_js_block, JS = _cut(T, '<script>\n{', '</script>'); JS = '{' + JS
def _asset(ext, body):
    h = hashlib.sha1(body.encode()).hexdigest()[:10]; name = f'app.{h}.{ext}'
    d = os.path.join(PUB, 'assets'); os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if f.startswith('app.') and f.endswith('.' + ext) and f != name: os.remove(os.path.join(d, f))
    open(os.path.join(d, name), 'w', encoding='utf-8').write(body); return name
CSS_NAME, JS_NAME = _asset('css', CSS), _asset('js', JS)
T = T.replace(_css_block, '<link rel="stylesheet" href="__ROOT__assets/' + CSS_NAME + '">').replace(_js_block, '<script src="__ROOT__assets/' + JS_NAME + '" defer></script>')
TR = {'Z': 0, 'S': 1, 'A': 2, 'B': 3, 'C': 4, 'D': 5, 'P': 6}

def strip(h, keep):
    drop = 'M' if keep == 'B' else 'B'
    h = re.sub(rf'<!--{drop}-->.*?<!--/{drop}-->', '', h, flags=re.S)
    return h.replace(f'<!--{keep}-->', '').replace(f'<!--/{keep}-->', '')

def write(rel, h):
    path = os.path.join(PUB, rel); os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(h)

# each page carries only its own role (plus a small summary); the site loads data/<patch>.json when you switch roles or search
def best(r):
    L = sorted([e for e in D[r] if e['t'] != 'P'], key=lambda e: (TR[e['t']], -e['score']))
    return [L[0]['c'], L[0]['t'], L[0]['score']] if L else None
META_SLIM = {k: v for k, v in D['_meta'].items() if k != 'tau'}
META_SLIM['best'] = {r: best(r) for r, _, _ in ROLES}
_arch = {f for f in os.listdir(os.path.join(PUB, 'data')) if re.fullmatch(r'\d+\.\d+\.json', f)} if os.path.isdir(os.path.join(PUB, 'data')) else set()
META_SLIM['hist'] = len(_arch | {f'{PATCH}.json'})   # patches with data; the panel shows a history chart from 3 on
def data_for(role, page_kind):
    m = dict(META_SLIM, part=True)
    return json.dumps({'_meta': m} if page_kind in ('method', 'champ') else {'_meta': m, role: D[role]}, ensure_ascii=False, separators=(',', ':'))

# ---------- static page headers (role pages, homepage, champion pages) ----------
RICON = {
 'top': '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 3h11l-3.5 3.5H6.5v4L3 14z" fill="currentColor"/><path d="M7.5 17h9.5V7.5" fill="none" stroke="currentColor" stroke-width="1.6" opacity=".45"/></svg>',
 'jungle': '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M6 2.5c2.6 3.2 3.4 7.6 2.4 13.5M10.2 2.5c1.6 3 2 7 1.2 11.5M14.2 3c1 2.4 1.3 5.4.6 8.8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
 'mid': '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 16 16 4" stroke="currentColor" stroke-width="3" stroke-linecap="round"/><path d="M3 9.5V3h6.5M17 10.5V17h-6.5" fill="none" stroke="currentColor" stroke-width="1.6" opacity=".45"/></svg>',
 'adc': '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M17 17H6l3.5-3.5h4v-4L17 6z" fill="currentColor"/><path d="M12.5 3H3v9.5" fill="none" stroke="currentColor" stroke-width="1.6" opacity=".45"/></svg>',
 'support': '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 2.2 16.5 5v4.6c0 4-2.7 6.9-6.5 8.2-3.8-1.3-6.5-4.2-6.5-8.2V5z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M10 6.2v7.6M6.4 9.6h7.2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'}
RNAME = {r: n for r, n, _ in ROLES}
SAMP = json.load(open(os.path.join(HERE, 'data', 'samples.json')))
GAMES = SAMP.get('opgg_global_e', 0) / 10
def kfmt(n): return f'{n / 1e6:.1f}M' if n >= 1e6 else f'{round(n / 1e3)}k'
def f1(v):
    import math
    r = math.floor(v * 10 + .5) / 10; return ('+' if r > 0 else '−' if r < 0 else '') + f'{abs(r):.1f}'
def slug(c): return re.sub(r'[^a-z0-9]', '', c.lower())
E = html.escape
UPD = P.get('updated', '')
def dline(extra=''):
    return f'<p class="dl">Patch <b>{PATCH}</b> · ranked solo/duo · 9 stat sites · {kfmt(GAMES)} Emerald+ games · updated {E(UPD)}{extra}</p>'
SHARE = '<button type="button" class="ext" data-share="">Share</button>'
def head_role(r):
    return (f'<header class="band head" style="--R:var(--R{r})"><div class="wrap"><div class="rh"><div class="rt"><span class="ri">{RICON[r]}</span>'
            f'<div><h1>{RNAME[r]} tier list</h1>{dline()}</div></div><div><p class="take">{E(P.get("takes", {}).get(r, ""))}</p>'
            f'<div class="hacts">{SHARE}</div></div></div></div></header>')
def head_home(root):
    cards = ''
    for r, n, _ in ROLES:
        b = best(r)
        if not b: continue
        c, t, sc = b
        cards += (f'<a class="rcd" href="{root}{r}/" style="--R:var(--R{r});--art:url({root}img/tile/{slug(c)}.webp)"><span class="rn"><span class="ri">{RICON[r]}</span>{n}</span>'
                  f'<span class="bp"><small>Best pick</small><b>{E(c)} <span class="tg" style="background:var(--{t})">{t}</span></b><small>{f1(sc)} vs role average</small></span></a>')
    mv = sorted([(e['tr'], r, e['c']) for r, _, _ in ROLES for e in D[r] if e.get('tr') is not None and e['pick'] >= 1 and abs(e['tr']) >= .4], reverse=True)
    pick = mv[:4] + [x for x in mv[::-1][:4] if x[0] < 0]
    chips = ''.join(f'<a href="{root}{r}/{slug(c)}/"><img class="pic" src="{root}img/champ/{slug(c)}.webp" alt="" width="22" height="22" loading="lazy">{E(c)} <span class="mu">{RNAME[r]}</span><em class="{"up" if t > 0 else "dn"}">{"↑" if t > 0 else "↓"} {f1(t)}</em></a>' for t, r, c in pick)
    nx = P.get('next', {}); nxt = f" · next patch {E(nx.get('patch', ''))} on {E(nx.get('date', ''))}" if nx else ''
    return (f'<header class="band head home"><div class="wrap">{dline(nxt)}'
            f'<h1>{E(P.get("headline", ""))}</h1><p class="lede">{P.get("lede", "")}</p><div class="rcards">{cards}</div>'
            f'<div class="mvs"><span>Moved most since {E(P.get("prev_patch", ""))}:</span>{chips}</div></div></header>')
def head_champ(r, e, root):
    s_ = slug(e['c']); tc = lambda t: f'var(--{t})' if t else 'var(--E)'
    hi = f'<span style="background:{tc(e.get("ht"))}">High elo {e.get("ht") or "–"} {f1(e["hi"])}</span>' if e.get('hi') is not None else ''
    return (f'<header class="band head champ-head" style="--art:url({root}img/splash/{s_}.webp)"><div class="wrap"><a class="crumb" href="../">← {RNAME[r]} tier list</a>'
            f'<div class="ch"><img class="pic big" src="{root}img/champ/{s_}.webp" alt="" width="72" height="72"><div><h1>{E(e["c"])}</h1>'
            f'<p class="dl">{RNAME[r]} · patch <b>{PATCH}</b> · {e["games"]:,} games in Global Emerald+ · updated {E(UPD)}</p></div></div>'
            f'<div class="ctiers"><span style="background:{tc(e["t"])}">Overall {e["t"]} {f1(e["score"])}</span>{hi}</div>'
            f'<p class="take">{E(e.get("note") or "")}</p><div class="hacts">{SHARE}</div></div></header>')

def page(rel, keep, root, page_kind, role, title, ogtitle, desc, url, ogimg, champ='', head=''):
    h = strip(T, keep)
    rep = {'__HEAD__': head, '__CHAMP__': champ, '__TITLE__': html.escape(title), '__OGTITLE__': html.escape(ogtitle, quote=True), '__DESC__': html.escape(desc, quote=True),
           '__URL__': url, '__OGIMG__': ogimg, '__ROOT__': root, '__PAGE__': page_kind, '__ROLE__': role, '__PATCH__': PATCH}
    for k, v in rep.items(): h = h.replace(k, v)
    write(rel, h.replace('__DATA__', data_for(role, page_kind)))

def top_line(role):
    L = sorted([e for e in D[role] if e['t'] in 'ZS'], key=lambda e: (TR[e['t']], -e['score']))[:5]
    parts = [f"{e['c']} ({e['t']})" for e in L]
    return ', '.join(parts[:-1]) + (' and ' + parts[-1] if len(parts) > 1 else (parts[0] if parts else ''))

base_desc = f'League of Legends tier list for patch {PATCH}, every role, built from nine stat sites (OP.GG, U.GG, Blitz, dpm.lol, League of Graphs and more) and corrected for sample size and one-trick inflation.'
z = [c for r, _, _ in ROLES for c in D['_meta']['facts']['z'][r]]
page('index.html', 'B', '', 'home', 'top', f'LoL Tier List: patch {PATCH}, every role', f'LoL Tier List {PATCH}' + (f": {', '.join(z[:-1])} and {z[-1]} lead" if len(z) > 1 else ''), base_desc, SITE, SITE + 'og.png', head=head_home(''))
for r, name, plural in ROLES:
    page(f'{r}/index.html', 'B', '../', 'board', r, f'{name} tier list, patch {PATCH} | LoL Tier List', f'{name} tier list for patch {PATCH}',
         f'Best {plural} in patch {PATCH}: {top_line(r)}. Win rate above the role average from nine stat sites, corrected for sample size and one-tricks.',
         SITE + r + '/', SITE + f'og-{r}.png', head=head_role(r))
    for e in D[r]:   # one page per champion and role
        sl = slug(e['c']); tiers = f"Overall {e['t']}" + (f", high elo {e['ht']}" if e.get('ht') else '')
        page(f'{r}/{sl}/index.html', 'B', '../../', 'champ', r, f"{e['c']} {name}, patch {PATCH}: {e['t']} tier | LoL Tier List",
             f"{e['c']} {name}, patch {PATCH}: {tiers}", f"{e['c']} {name} in patch {PATCH}: {tiers}. {e.get('note') or ''}".strip(),
             SITE + f'{r}/{sl}/', SITE + f'img/splash/{sl}.webp', champ=e['c'], head=head_champ(r, e, '../../'))
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
# score history: Global Emerald+ (the one dataset every archived patch has), oldest to newest, last 12 patches
hp = [x['patch'] for x in reversed(pl[:12])]
H = {'patches': hp, 'roles': {}}
for p_ in hp:
    a = json.load(open(os.path.join(PUB, 'data', f'{p_}.json'), encoding='utf-8'))
    for r, _, _ in ROLES:
        for e in a.get(r, []):
            H['roles'].setdefault(r, {}).setdefault(e['c'], [None] * len(hp))[hp.index(p_)] = e.get('g')
json.dump(H, open(os.path.join(PUB, 'data', 'history.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
write('404.html', f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Page not found | LoL Tier List</title><meta name="robots" content="noindex"><link rel="icon" href="/favicon.svg" type="image/svg+xml">
<script>try{{document.documentElement.style.colorScheme=localStorage.getItem("tl-theme")==="light"?"light":"dark";}}catch(e){{document.documentElement.style.colorScheme="dark";}}</script>
<style>@font-face{{font-family:Inter;font-weight:800;src:url(/fonts/inter-latin-800-normal.woff2) format('woff2')}}@font-face{{font-family:Inter;font-weight:400;src:url(/fonts/inter-latin-400-normal.woff2) format('woff2')}}
:root{{color-scheme:light dark}}body{{margin:0;min-height:100svh;display:grid;place-items:center;font:16px/1.6 Inter,system-ui,sans-serif;background:light-dark(#f5f6f8,#0b0c0f);color:light-dark(#0f1115,#eceef2)}}
main{{text-align:center;padding:24px}}h1{{font-weight:800;font-size:44px;letter-spacing:-.03em;margin:16px 0 6px}}p{{color:light-dark(#646b78,#959cab);margin:0 0 22px}}
a{{display:inline-block;padding:11px 18px;border-radius:999px;background:light-dark(#0f1115,#eceef2);color:light-dark(#fff,#0b0c0f);text-decoration:none;font-weight:600}}img{{width:56px;height:56px}}</style></head>
<body><main><img src="/favicon.svg" alt=""><h1>Nothing here</h1><p>That page doesn't exist. The tier list does.</p><a href="/">Open the tier list</a></main></body></html>''')
PRIV = open(os.path.join(HERE, 'privacy.html'), encoding='utf-8').read()
write('privacy/index.html', PRIV.replace('__UPDATED__', P.get('privacy_updated', '14 Nov 2026')))
write('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\n')
today = datetime.date.today().isoformat()
urls = [SITE] + [SITE + r + '/' for r, _, _ in ROLES] + [SITE + 'method/', SITE + 'privacy/'] + [SITE + f"{r}/{slug(e['c'])}/" for r, _, _ in ROLES for e in D[r]]
write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n' for u in urls) + '</urlset>\n')
print('built: index, ' + ', '.join(r for r, _, _ in ROLES) + f", {sum(len(D[r]) for r, _, _ in ROLES)} champion pages, method, privacy, 404, robots, sitemap")
