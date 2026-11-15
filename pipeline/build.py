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
TR = {'Z': 0, 'S': 1, 'A': 2, 'B': 3, 'C': 4, 'D': 5, 'P': 6, 'R': 7}
TV = lambda t: 'var(--E)' if t in (None, 'R') else f'var(--{t})'   # tier colour; R has none (and --R is the role colour)

def strip(h, keep):   # template blocks: B = tier list pages, M = method page, N = patch notes pages
    for b in 'BMN':
        if b != keep: h = re.sub(rf'<!--{b}-->.*?<!--/{b}-->', '', h, flags=re.S)
    return h.replace(f'<!--{keep}-->', '').replace(f'<!--/{keep}-->', '')

def write(rel, h):
    path = os.path.join(PUB, rel); os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(h)

# each page carries only its own role (plus a small summary); the site loads data/<patch>.json when you switch roles or search
def best(r):
    L = sorted([e for e in D[r] if e['t'] != 'P' and not e.get('rare')], key=lambda e: (TR[e['t']], -e['score']))
    return [L[0]['c'], L[0]['t'], L[0]['score']] if L else None
META_SLIM = {k: v for k, v in D['_meta'].items() if k != 'tau'}
META_SLIM['best'] = {r: best(r) for r, _, _ in ROLES}
_arch = {f for f in os.listdir(os.path.join(PUB, 'data')) if re.fullmatch(r'\d+\.\d+\.json', f)} if os.path.isdir(os.path.join(PUB, 'data')) else set()
META_SLIM['hist'] = len(_arch | {f'{PATCH}.json'})   # patches with data; the panel shows a history chart from 3 on
NOTES = P.get('notes', {})
def _item_ids():   # item name -> Data Dragon id (OP.GG's build ids win), for item icons on the panel and the next-patch card
    di, bp = os.path.join(HERE, 'data', 'ddragon_items.json'), os.path.join(HERE, 'data', 'opgg_builds.json')
    ids = dict(json.load(open(di, encoding='utf-8')).get('by_name', {})) if os.path.exists(di) else {}
    for r in (json.load(open(bp, encoding='utf-8')) if os.path.exists(bp) else {}).values():
        for b in r.values():
            for k in ['c0', 'c1', 'b0', 's0']:
                for iid, nm_ in b.get(k, []): ids[nm_] = str(iid)
    return ids
_IIDS = _item_ids()
META_SLIM['nitems'] = {x['c']: _IIDS.get(x['c']) for n in NOTES.values() for x in n.get('items', [])}   # items: icon, not a portrait
META_SLIM['notes'] = {p: [x['c'] for x in n['champs'] + n.get('items', [])] for p, n in NOTES.items()}   # the panel links to /patch/<p>/#<champion>
# names and Riot's own short descriptions for the build card, only for the ids the builds use: items {id: name},
# summoner spells {id: [name, description]}, runes {id: [name, description]}; from Data Dragon (saved by the icons workflow)
def _lookup():
    _bp = os.path.join(HERE, 'data', 'opgg_builds.json'); BUILDS = json.load(open(_bp, encoding='utf-8')) if os.path.exists(_bp) else {}
    used = {'i': set(), 's': set(), 'r': set()}; keys = set()   # keystones: the only runes the card describes
    for r, _, _ in ROLES:
        for e in D[r]:
            b = e.get('bd') or {}
            for x in b.get('sp', []): used['s'].update(map(str, x[0]))
            for x in b.get('rn', []): used['r'].update(map(str, [x[0], x[1], x[2], *x[3], *x[4]])); keys.add(str(x[0]))
            for k in ['co', 'st']:
                for x in b.get(k, []): used['i'].update(map(str, x[0]))
            for x in b.get('bo', []): used['i'].add(str(x[0]))
    di, ds = os.path.join(HERE, 'data', 'ddragon_items.json'), os.path.join(HERE, 'data', 'ddragon_spells_runes.json')
    if not (os.path.exists(di) and os.path.exists(ds)): return None
    iname = {v: k for k, v in json.load(open(di, encoding='utf-8'))['by_name'].items() if '<' not in k}
    for i in list(used['i']):   # Data Dragon files some support items twice and keeps the 32xxxx id; OP.GG uses the short one
        if i not in iname and '32' + i in iname: iname[i] = iname['32' + i]
    for r in BUILDS.values():   # last resort: OP.GG's own item names
        for b in r.values():
            for k in ['c0', 'c1', 'b0', 's0']:
                for iid, nm_ in b.get(k, []): iname.setdefault(str(iid), nm_)
    SR = json.load(open(ds, encoding='utf-8'))
    pair = lambda x: [x.get('name', ''), x.get('desc', '')]
    lk = {'i': {i: iname[i] for i in sorted(used['i']) if i in iname},
          's': {i: pair(SR['summoners'][i]) for i in sorted(used['s']) if i in SR['summoners']},
          'r': {i: pair(SR['runes'][i]) if i in keys else [SR['runes'][i].get('name', ''), ''] for i in sorted(used['r']) if i in SR['runes']}}
    miss = [(k, i) for k in 'isr' for i in used[k] if i not in lk[k]]
    if miss: print('build card: no Data Dragon name for', miss[:10])
    return lk
META_SLIM['lk'] = _lookup()
# counter-pick finder data (update.py writes counters.json); the site loads it only when the finder opens
_CPF = os.path.join(HERE, 'counters.json')
if os.path.exists(_CPF):
    import shutil; os.makedirs(os.path.join(PUB, 'data'), exist_ok=True)
    for f in os.listdir(os.path.join(PUB, 'data')):
        if f.endswith('-counters.json'): os.remove(os.path.join(PUB, 'data', f))
    META_SLIM['cpf'] = f'{PATCH}-counters.json'; shutil.copy(_CPF, os.path.join(PUB, 'data', META_SLIM['cpf']))
if PATCH in NOTES:   # the short lines on the panels (changes, item_changes) and the full notes must list the same things
    assert {x['c']: [x['kind'], x['short']] for x in NOTES[PATCH]['champs']} == P.get('changes'), 'patch.json: "changes" and "notes" disagree'
    assert {x['c']: [x['kind'], x['short'], x['slot']] for x in NOTES[PATCH].get('items', [])} == P.get('item_changes', {}), 'patch.json: "item_changes" and "notes" disagree'
_nx = P.get('next', {})
if _nx.get('patch') in NOTES:   # the "Changing next patch" card: one row per champion, and nothing from the preview left out
    _rows = [x for L in _nx.get('roles', {}).values() for x in L]
    assert not [x[0] for x in _rows if ',' in x[0]], 'patch.json next.roles: one champion per row, no "A, B, C" groups: ' + str([x[0] for x in _rows if ',' in x[0]])
    _miss = [x['c'] for x in NOTES[_nx['patch']]['champs'] + NOTES[_nx['patch']].get('items', []) if x['c'] not in {r[0] for r in _rows}]
    assert not _miss, 'patch.json next.roles is missing changes from the preview notes: ' + ', '.join(_miss)
def data_for(role, page_kind):
    m = dict(META_SLIM, part=True)
    return json.dumps({'_meta': m} if page_kind in ('method', 'champ', 'patch') else {'_meta': m, role: D[role]}, ensure_ascii=False, separators=(',', ':'))

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
from decimal import Decimal, ROUND_HALF_UP
def fx(v, nd=1): return str(Decimal(v).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP))   # = JavaScript toFixed
def f1(v):
    import math
    r = math.floor(v * 10 + .5) / 10; return ('+' if r > 0 else '−' if r < 0 else '') + f'{abs(r):.1f}'
def slug(c): return re.sub(r'[^a-z0-9]', '', c.lower())
E = html.escape
UPD = P.get('updated', '')
def dline(extra=''):
    return f'<p class="dl">Patch {PATCH}, ranked solo/duo, updated {E(UPD)}.{extra}</p>'
SHARE = '<button type="button" class="ext" data-share="">Share</button>'
SHARE_ICO = '<button type="button" class="ext ico hico" data-share="" aria-label="Share this page" title="Share"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3v10M6 7l4-4 4 4M4 12v4h12v-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></button>'
def head_role(r):
    return (f'<header class="band head" style="--R:var(--R{r})"><div class="wrap"><div class="rh"><div class="rt"><span class="ri">{RICON[r]}</span>'
            f'<div><h1>{RNAME[r]} tier list {SHARE_ICO}</h1>{dline()}</div></div><p class="take">{E(P.get("takes", {}).get(r, ""))}</p></div></div></header>')
def strongest(vk='E'):   # every Z and S pick across roles, Z first, then by score (same order as the site's "Strongest picks" card)
    return sorted([(r, e) for r, _, _ in ROLES for e in D[r] if vk in e['v'] and e['v'][vk][2] in ('Z', 'S') and not (e['v'][vk][3:] or [0])[0]], key=lambda x: (TR[x[1]['v'][vk][2]], -x[1]['v'][vk][0]))
def head_home(root):
    # the patch story: fixed for the patch (Emerald+, all regions). Everything under the control bar follows the visitor's rank and region.
    strong = strongest()
    hl = P.get('headline', '')
    # the three cards appear in the order the headline names them, so the text and the cards match
    top3 = sorted(strong[:3], key=lambda t: (hl.find(t[1]['c']) if t[1]['c'] in hl else 999))
    lc = ''.join(f'<a class="lead" href="{root}{r}/{slug(e["c"])}/" data-jr="{r}" data-jc="{E(e["c"])}" style="--art:url(/img/splash/{slug(e["c"])}.webp);--R:var(--R{r})">'
                 f'<span class="lr"><span class="ri">{RICON[r]}</span>{RNAME[r]}</span><span class="lb"><b>{E(e["c"])}</b>'
                 f'<span><span class="tg" style="--T:{TV(e["t"])}">{e["t"]}</span> {f1(e["score"])} · {fx(e["pick"])}% pick</span></span></a>' for r, e in top3)
    nx = P.get('next', {})
    pl = f'<a href="{root}patch/{PATCH}/">Patch {PATCH}</a>' if PATCH in NOTES else f'Patch {PATCH}'
    nl = (f'<a href="{root}patch/{nx["patch"]}/">Next patch on {E(nx.get("date", ""))}</a>' if nx.get('patch') in NOTES else f'Next patch on {E(nx.get("date", ""))}') if nx else ''
    nl = (f'<a class="dlnx" href="{root}patch/{nx["patch"]}/">Patch {nx["patch"]} on {E(nx.get("date", ""))}: see what changes</a>' if nx.get('patch') in NOTES else f'<span class="dlnx">Next patch on {E(nx.get("date", ""))}</span>') if nx else ''
    when = f'<span>Patch {PATCH}, updated {E(UPD)}</span>{nl}'
    return (f'<header class="band head home"><div class="wrap"><div class="hero2"><div class="htxt"><p class="dl">{when}</p>'
            f'<h1>{E(P.get("headline", ""))}</h1><p class="lede">{P.get("lede", "")}</p></div><div class="leads">{lc}</div></div></div></header>')
RKN = [('E', 'Emerald+'), ('D', 'Diamond+'), ('M', 'Master+')]
def head_champ(r, e, root):
    s_ = slug(e['c']); tc = TV
    tiers = ''.join(f'<span><b class="tg" style="--T:{tc(e["v"][k][2])}">{e["v"][k][2]}</b>{n} {f1(e["v"][k][0])}</span>' for k, n in RKN if k in e.get('v', {}))
    return (f'<header class="band head champ-head" style="--art:url(/img/splash/{s_}.webp)"><div class="wrap"><a class="crumb" href="../">← {RNAME[r]} tier list</a>'
            f'<div class="ch"><img class="pic big" src="{root}img/champ/{s_}.webp" alt="" width="72" height="72"><div><h1>{E(e["c"])}</h1>'
            f'<p class="dl">{RNAME[r]}, patch {PATCH}: {e["games"]:,} games in Global Emerald+, updated {E(UPD)}.</p></div></div>'
            f'<div class="ctiers">{tiers}</div>'
            f'<p class="take">{E(e.get("note") or "")}</p><div class="hacts">{SHARE}</div></div></header>')

def page(rel, keep, root, page_kind, role, title, ogtitle, desc, url, ogimg, champ='', head=''):
    h = strip(T, keep)
    rep = {'__HEAD__': head, '__CHAMP__': json.dumps(champ, ensure_ascii=False), '__TITLE__': html.escape(title), '__OGTITLE__': html.escape(ogtitle, quote=True), '__DESC__': html.escape(desc, quote=True),
           '__URL__': url, '__OGIMG__': ogimg, '__ROOT__': root, '__PAGE__': page_kind, '__ROLE__': role, '__PATCH__': PATCH}
    for k, v in rep.items(): h = h.replace(k, v)
    write(rel, h.replace('__DATA__', data_for(role, page_kind)))

def top_line(role):
    L = sorted([e for e in D[role] if e['t'] in 'ZS'], key=lambda e: (TR[e['t']], -e['score']))[:5]
    parts = [f"{e['c']} ({e['t']})" for e in L]
    return ', '.join(parts[:-1]) + (' and ' + parts[-1] if len(parts) > 1 else (parts[0] if parts else ''))

def cdesc(e, name, tiers):   # champion page description: tiers, then whole note sentences while it stays under 160 characters
    d = f"{e['c']} {name} in patch {PATCH}: {tiers}."
    for sn in re.split(r'(?<=\.) ', e.get('note') or ''):
        if sn and len(d) + 1 + len(sn) <= 160: d += ' ' + sn
        else: break
    return d
base_desc = f'LoL tier list for patch {PATCH}, every role. Five stat sites combined, four more as checks, corrected for small samples and one-tricks. No ads.'
z = [c for r, _, _ in ROLES for c in D['_meta']['facts']['z'][r]]
page('index.html', 'B', '', 'home', 'top', f'LoL Tier List: patch {PATCH}, every role', f'LoL Tier List {PATCH}' + (f": {', '.join(z[:-1])} and {z[-1]} lead" if len(z) > 1 else ''), base_desc, SITE, SITE + 'og.png', head=head_home(''))
for r, name, plural in ROLES:
    page(f'{r}/index.html', 'B', '../', 'board', r, f'{name} tier list, patch {PATCH} | LoL Tier List', f'{name} tier list for patch {PATCH}',
         f'Best {plural} in patch {PATCH}: {top_line(r)}. Five stat sites combined, no ads.'[:160],
         SITE + r + '/', SITE + f'og-{r}.png', head=head_role(r))
    for e in D[r]:   # one page per champion and role
        sl = slug(e['c']); tiers = ', '.join(f"{n} {e['v'][k][2]}" for k, n in RKN if k in e['v'])
        page(f'{r}/{sl}/index.html', 'B', '../../', 'champ', r, f"{e['c']} {name}, patch {PATCH}: {e['t']} tier | LoL Tier List",
             f"{e['c']} {name}, patch {PATCH}: {tiers}", cdesc(e, name, tiers),
             SITE + f'{r}/{sl}/', SITE + f'img/splash/{sl}.webp', champ=e['c'], head=head_champ(r, e, '../../'))
page('method/index.html', 'M', '../', 'method', 'top', 'How the tier list is made | LoL Tier List', 'How the LoL tier list is made',
     'Where the numbers come from, how five stat sites are combined into one score and tier, how far each site can be trusted, and what a tier list cannot tell you.',
     SITE + 'method/', SITE + 'og.png')

# ---------- patch notes: /patch/<patch>/ for every patch in patch.json "notes", /patch/ = the newest live one ----------
# Lines are [key, stat, old, new, tag, dir]. The "what it means" sentence comes only from these rules (or a hand-written
# "m" that says nothing the numbers don't show): which ranks change, whether only the scaling changes, base stats per level.
_BP = os.path.join(HERE, 'data', 'opgg_builds.json')
BUILDS = json.load(open(_BP, encoding='utf-8')) if os.path.exists(_BP) else {}
_DI = os.path.join(HERE, 'data', 'ddragon_items.json')
ITEM_ID = json.load(open(_DI, encoding='utf-8')).get('by_name', {}) if os.path.exists(_DI) else {}
for _r in BUILDS.values():   # item ids from the OP.GG builds win over Data Dragon names
    for _b in _r.values():
        for _k in _b.values():
            for _id, _nm in _k: ITEM_ID[_nm] = str(_id)
NUM = r'\d+(?:\.\d+)?'
def _ranks(s):   # leading numbers: "10 / 9 / 8s" (per rank), "45 - 165" (low to high end), "56" (one value); plus the unit right after
    s = s.strip()
    for rx, kind in ((rf'({NUM}(?:\s*/\s*{NUM})+)', 'rank'), (rf'({NUM})%?\s*-\s*({NUM})', 'range'), (rf'({NUM})', 'one')):
        m = re.match(rx, s)
        if m:
            vals = [float(x) for x in re.split(r'\s*/\s*', m.group(1))] if kind == 'rank' else [float(g) for g in m.groups()]
            u = s[m.end():m.end() + 1]
            return vals, kind, (u if u in ('%', 's') else '')
    return None, None, ''
def _stat(s):   # "590 + 107/level", "5.4/level", "54"
    m = re.match(rf'({NUM})\s*\+\s*({NUM})%?/level', s)
    if m: return float(m.group(1)), float(m.group(2))
    m = re.match(rf'\+?({NUM})%?/level', s)
    if m: return None, float(m.group(1))
    m = re.fullmatch(rf'({NUM})', s.strip())
    return (float(m.group(1)), None) if m else (None, None)
def _par(s): return re.findall(r'\(([^)]*)\)', s)
def _phase(l):   # when the change matters: early, late, all, items (scaling), pct (% of target health)
    _, _, old, new, tag, _ = l
    if tag == 'mech' or not old: return set(), None
    if tag == 'ratio': return {'items'}, None
    if tag == 'pct': return {'pct'}, None
    if tag == 'stats':
        (b0, g0), (b1, g1) = _stat(old), _stat(new); ph = set()
        if g0 is not None and g1 is not None and g0 != g1: ph.add('late')
        if b0 is not None and b1 is not None and b0 != b1: ph.add('all')
        return ph, None
    (a, ka, ua), (b, kb, ub) = _ranks(old), _ranks(new); ph, det = set(), None
    if a and b:
        if len(a) == 1 and len(b) == 1:
            if a != b: ph.add('all')
        else:
            f0, f1, l0, l1 = a[0], b[0], a[-1], b[-1]
            rf = abs(f1 - f0) / f0 if f0 else float(f1 != f0); rl = abs(l1 - l0) / l0 if l0 else float(l1 != l0)
            if rf and not rl: ph.add('early')
            elif rl and not rf: ph.add('late')
            elif rf and rl: ph.add('early' if rf >= 2 * rl else 'late' if rl >= 2 * rf else 'all')
            det = ('range' if 'range' in (ka, kb) else 'rank', f0, f1, l0, l1, ua or ub or ('s' if tag == 'cd' else ''))
    if _par(old) != _par(new): ph.add('items')
    return ph, det
def _g(v): return f'{v:g}'
def _who(l):   # how a line is named inside a sentence: "Q", "the passive", "attack damage"
    return l[0] if l[0] in ('Q', 'W', 'E', 'R') else 'the passive' if l[0] == 'P' else l[1].lower()
def meaning(x):
    if x.get('m'): return x['m']
    L = [l for l in x['lines'] if l[4] != 'mech' and l[5] in '+-' and l[2]]
    if not L: return ''
    info = [(l, *_phase(l)) for l in L]; dirs = {l[5] for l in L}; name = x['c']; out = []
    if len(dirs) == 1:
        w = 'helps' if '+' in dirs else 'hurts'
        ph = set().union(*[p for _, p, _ in info]); dl = [(l, d) for l, _, d in info if d]
        if ph <= {'early', 'late'} and len(ph) == 1 and dl:
            l, (kind, f0, f1, l0, l1, u) = dl[0]; k = _who(l)
            lo, hi = ('at rank 1', 'at max rank') if kind == 'rank' else ('at the low end', 'at the top end')
            a, b, c, d = f'{_g(f0)}{u}', f'{_g(f1)}{u}', f'{_g(l0)}{u}', f'{_g(l1)}{u}'
            if ph == {'early'}:
                out.append(f'Mostly {w} early: {k} goes {a} → {b} {lo} and stays {c} {hi}.' if l0 == l1 else
                           f'Mostly {w} early: {k} goes {a} → {b} {lo}, only {c} → {d} {hi}.')
            else:
                out.append(f'Mostly {w} later: {k} stays {a} {lo} and goes {c} → {d} {hi}.' if f0 == f1 else
                           f'Mostly {w} later: {k} goes only {a} → {b} {lo}, but {c} → {d} {hi}.')
        elif ph == {'items'}:
            l = L[0]; po, pn = _par(l[2]), _par(l[3])
            ch = next(((o, n) for o, n in zip(po, pn) if o != n), None) if l[4] != 'ratio' else (l[2], l[3])
            out.append(f'Only the scaling changes' + (f' ({ch[0]} → {ch[1]})' if ch else '') + f', so it {w} more the more items {name} has.')
        elif ph == {'late', 'items'}: out.append(f'Matters more later in the game, once {name} has ranks and items.')
        elif ph == {'pct'}: out.append(f'Only the % max health part changes, so it {w} most against tanky targets.')
    else:
        plus = set().union(*[p for l, p, _ in info if l[5] == '+']); minus = set().union(*[p for l, p, _ in info if l[5] == '-'])
        if plus and minus and minus <= {'early'} and plus <= {'late', 'items'}: out.append('Weaker early, stronger later.')
        elif plus and minus and plus <= {'early'} and minus <= {'late', 'items'}: out.append('Stronger early, weaker later.')
    for l in L:   # base stats: what the per-level change adds up to
        if l[4] != 'stats': continue
        (b0, g0), (b1, g1) = _stat(l[2]), _stat(l[3]); lab = l[1].replace(' growth', '')
        if g0 is not None and g1 is not None and g0 != g1 and (b0 is None or b0 == b1):
            out.append(f'{lab}: {"+" if g1 > g0 else "−"}{_g(round(abs(g1 - g0) * 17, 1))} at level 18.')
        elif None not in (b0, b1, g0, g1) and (b1 - b0) * (g1 - g0) < 0:
            lv = next((v for v in range(2, 19) if (b1 + g1 * (v - 1) - b0 - g0 * (v - 1)) * (b1 - b0) < 0), None)
            if lv: out.append(f'{lab}: {"less" if b1 < b0 else "more"} at level 1, {"more" if b1 < b0 else "less"} from level {lv}.')
    return ' '.join(out)

import difflib
SEGRX = re.compile(r'\([^)]*\)|[^()]+')
def _skel(t): return re.sub(NUM, '#', t).strip()
def _wrap(t):   # mark a whole piece, keeping the spaces around it outside the mark
    m = re.match(r'(\s*)(.*?)(\s*)$', t, re.S)
    return E(m.group(1)) + (f'<em>{E(m.group(2))}</em>' if m.group(2) else '') + E(m.group(3))
def _pair(a, b):   # same shape: mark the numbers that changed, rank by rank; different shape: mark the whole piece
    if a == b: return E(a), E(b)
    if _skel(a) != _skel(b): return _wrap(a), _wrap(b)
    na, nb = re.findall(NUM, a), re.findall(NUM, b)
    def mark(t, mine, other):
        out, k = [], 0
        for part in re.split(rf'({NUM})', t):
            if re.fullmatch(NUM, part): out.append(f'<em>{part}</em>' if float(part) != float(other[k]) else part); k += 1
            else: out.append(E(part))
        return ''.join(out)
    return mark(a, na, nb), mark(b, nb, na)
def _diff(old, new):   # "(+105% AD) → (+100% AD)" marks only 105 and 100; a list that changes length is marked whole
    A, B = SEGRX.findall(old), SEGRX.findall(new); ho, hn = [], []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, [_skel(x) for x in A], [_skel(x) for x in B], autojunk=False).get_opcodes():
        if op == 'equal' or (op == 'replace' and i2 - i1 == j2 - j1):
            for x, y in zip(A[i1:i2], B[j1:j2]): o, n = _pair(x, y); ho.append(o); hn.append(n)
        else: ho += [_wrap(x) for x in A[i1:i2]]; hn += [_wrap(y) for y in B[j1:j2]]
    return ''.join(ho), ''.join(hn)
ROOTP = ''
KEYN = {'P': 'Passive', 'Q': 'Q', 'W': 'W', 'E': 'E', 'R': 'R (ultimate)', 'Base': 'Base stats'}
KORD = {'Base': 0, 'P': 1, 'Q': 2, 'W': 3, 'E': 4, 'R': 5}
def _line(stat, old, new, d):
    cls = ' pn-up' if d == '+' else ' pn-dn' if d == '-' else ''
    if not old: v = f'<p class="pn-v"><span class="pn-n">{E(new)}</span></p>'
    else:
        o, n = _diff(old, new)
        if len(old) + len(new) <= 34: v = f'<p class="pn-v"><span class="pn-o">{o}</span> <span class="pn-ar" aria-label="changed to">→</span> <span class="pn-n">{n}</span></p>'
        else: v = f'<p class="pn-v pn-st"><span class="pn-lb">Was</span><span class="pn-o">{o}</span><span class="pn-lb">Now</span><span class="pn-n">{n}</span></p>'
    return f'<li class="pn-l{cls}"><b>{E(stat)}</b>{v}</li>'
def _lines(x, item=False):   # grouped by ability like Riot's notes (base stats first, then P Q W E R), the changed part of each value marked
    if item: return f'<ul class="pn-ls pn-nk">{"".join(_line(l[1], l[2], l[3], l[5]) for l in x["lines"])}</ul>'
    ab, out = x.get('ab', {}), []
    for k in sorted(dict.fromkeys(l[0] for l in x['lines']), key=lambda k: KORD.get(k, 9)):
        nm = 'Base stats' if k == 'Base' else ab.get(k, 'Passive' if k == 'P' else '')
        icon = f'<img class="pn-sp" src="{ROOTP}img/spell/{slug(x["c"])}_{k.lower()}.webp" alt="" width="28" height="28" loading="lazy" onerror="this.remove()">' if k in KEYN and k != 'Base' else ''
        out.append(f'<div class="pn-ab"><p class="pn-abh">{icon}' + (f'<span class="pn-k" title="{KEYN.get(k, k)}">{E(k)}</span>' if k != 'Base' else '')
                   + f'{E(nm)}</p><ul class="pn-ls">{"".join(_line(l[1], l[2], l[3], l[5]) for l in x["lines"] if l[0] == k)}</ul></div>')
    return f'<div class="pn-abs">{"".join(out)}</div>'
def _main_role(c):
    rs = [(r, e) for r, _, _ in ROLES for e in D[r] if e['c'] == c]
    return max(rs, key=lambda x: x[1]['pick']) if rs else (None, None)
def _roles(c, root, moves):   # where the champion stands now, every role it is listed in, most played first
    rs = sorted([(r, e) for r, _, _ in ROLES for e in D[r] if e['c'] == c], key=lambda x: -x[1]['pick'])
    if not rs: return '<p class="pn-nl">Not in the tier list: too few games in every role.</p>'
    ch = []
    for r, e in rs:
        mv = ''
        if moves and e.get('tr') is not None and round(e['tr'], 1):
            weak = e.get('trz') is not None and abs(e['trz']) < 1.64
            mv = (f'<span class="pn-mv{" pn-weak" if weak else " pos" if e["tr"] > 0 else " neg"}" title="Change since {P["prev_patch"]}{", too small to be sure" if weak else ""}">'
                  f'{"↑" if e["tr"] > 0 else "↓"}{f1(abs(e["tr"])).lstrip("+")}</span>')
        off = e['pick'] < 1
        ch.append(f'<a class="pn-r{" pn-off" if off else ""}" href="{root}{r}/{slug(c)}/" style="--R:var(--R{r})" title="{RNAME[r]}: {e["t"]} tier, score {f1(e["score"])}, {fx(e["pick"])}% pick">'
                  f'<span class="ri">{RICON[r]}</span>{RNAME[r]} <span class="tg sm" style="--T:{TV(e["t"])}">{e["t"]}</span> <b>{f1(e["score"])}</b>{mv}</a>')
    return f'<div class="pn-rs">{"".join(ch)}</div>'
def _effect(c):   # what happened since last patch in the champion's most played role, Global Emerald+ (live patch only)
    r, e = _main_role(c)
    if not e or e.get('tr') is None or not e.get('st', {}).get('g'): return None
    w1, p1 = e['st']['g'][3], e['st']['g'][1]; w0, p0 = e.get('wr0'), e.get('pk0')
    clear = e.get('trz') is not None and abs(e['trz']) >= 1.64
    bits = ([f'win rate {fx(w0)}% → {fx(w1)}%'] if w0 is not None else []) + ([f'pick rate {fx(p0)}% → {fx(p1)}%'] if p0 is not None else [])
    v = (f'<span class="pn-vd {"pos" if e["tr"] > 0 else "neg"}">Clearly {"better" if e["tr"] > 0 else "worse"}.</span>' if clear else '<span class="pn-vd">No clear change.</span>')
    return f'{v} {RNAME[r]}, Global Emerald+: {E(", ".join(bits))}.'
def _users(name):   # listed champions with the item in their OP.GG core build or boots, and as starting item: {champion: [roles]}, most played first
    core, start, pk = {}, {}, {}
    for r, _, _ in ROLES:
        for e in D[r]:
            b = BUILDS.get(r, {}).get(e['c'], {}); pk[e['c']] = pk.get(e['c'], 0) + e['pick']
            if any(n == name for k in ('c0', 'c1', 'b0') for _, n in b.get(k, [])): core.setdefault(e['c'], []).append(r)
            if any(n == name for _, n in b.get('s0', [])): start.setdefault(e['c'], []).append(r)
    order = lambda m: dict(sorted(m.items(), key=lambda kv: -pk[kv[0]]))
    return order(core), order(start)
def _faces(M, root, label):   # who builds an item: names when there are a few, faces plus a count per role when there are many
    if not M: return ''
    many = len(M) > 6
    fs = ''.join(f'<a class="pn-f{" pn-fo" if many else ""}" href="{root}{rs[0]}/{slug(c)}/" title="{E(c)}, {", ".join(RNAME[r] for r in rs)}" aria-label="{E(c)}">'
                 f'<img class="pic" src="{root}img/champ/{slug(c)}.webp" alt="" width="26" height="26" loading="lazy">{"" if many else f"<span>{E(c)}</span>"}</a>' for c, rs in M.items())
    from collections import Counter
    rc = Counter(r for rs in M.values() for r in rs)
    split = f' ({", ".join(f"{RNAME[r]} {k}" for r, k in rc.most_common())})' if many else ''
    return f'<div class="pn-us"><p class="pn-ul">{label} for {_count(len(M), "listed champion", "listed champions")}{split}</p><div class="pn-fs">{fs}</div></div>'
def _count(n, one, many): return f'{n} {one if n == 1 else many}'
def _and(L): return ', '.join(L[:-1]) + (' and ' if len(L) > 1 else '') + (L[-1] if L else '')
def tldr(p, n):
    out, live = [], n['status'] == 'live'
    ks = [x['kind'] for x in n['champs']]; adj = [x['c'] for x in n['champs'] if x['kind'] not in ('buff', 'nerf')]
    parts = [_count(ks.count('buff'), 'buff', 'buffs'), _count(ks.count('nerf'), 'nerf', 'nerfs')] + ([f'{_and(adj)} reworked'] if adj else [])
    out.append(f'{_count(len(ks), "champion", "champions")} {"changed" if live else "planned"}: {_and(parts)}.')
    if live and p == PATCH:
        mv = []
        for x in n['champs']:
            es = [(r, e) for r, _, _ in ROLES for e in D[r] if e['c'] == x['c'] and e.get('tr') is not None and e.get('trz') is not None and abs(e['trz']) >= 1.64]
            if es:
                r, e = max(es, key=lambda t: abs(t[1]['tr'])); mv.append((abs(e['tr']), f'{x["c"]} ({RNAME[r]}) {"up" if e["tr"] > 0 else "down"} {f1(abs(e["tr"])).lstrip("+")}'))
        out.append(f'Clear moves since {P["prev_patch"]}: {_and([t for _, t in sorted(mv, reverse=True)[:4]])}. The rest moved too little to be sure.'
                   if mv else 'None of the changed champions moved clearly in our numbers yet.')
    its = []
    for x in n.get('items', []):
        core, start = _users(x['c'])
        who = f'core for {_count(len(core), "listed champion", "listed champions")}' if core else f'starting item for {_count(len(start), "listed champion", "listed champions")}' if start else 'in no listed build'
        its.append(f'{x["c"]} {"buffed" if x["kind"] == "buff" else "nerfed" if x["kind"] == "nerf" else "adjusted"} ({who})')
    if its: out.append('Items: ' + _and(its) + '.')
    for k, t in n.get('other', []): out.append(f'{k}: {t.split(". ")[0].rstrip(".")}.')
    if n.get('skins'): out.append(f'{_count(len(n["skins"]), "new skin", "new skins")}' + (f' and {_count(len(n.get("chromas", [])), "chroma", "chromas")}' if n.get('chromas') else '') + '.')
    if not live: out.append(f'This is the preview. Numbers can still change before the patch goes live on {n["live"]}.')
    return out
PILL = {'buff': 'pos', 'nerf': 'neg'}
GROUPS = [('buff', 'Buffs'), ('nerf', 'Nerfs'), ('adjust', 'Adjusted')]
def _ipic(x, root):   # item icon, self-hosted from Data Dragon; the sword placeholder shows if it is missing
    iid = ITEM_ID.get(x['c'])
    return f'<span class="pw">{f"""<img class="pic" src="{root}img/item/{iid}.webp" alt="" width="40" height="40" loading="lazy" onerror="this.remove()">""" if iid else ""}</span>'
def _sid(x, item=False): return ('i-' if item else '') + slug(x['c'])   # card id on the patch page = name of its share page
def _share(p, x, item=False):   # copies (or on phones shares) the change's own link, which has its own preview in chats
    u = f"{SITE}patch/{p}/{_sid(x, item)}/"
    return f'<button type="button" class="pn-share" data-u="{u}" data-t="{E(x["c"])}, patch {p}" title="Copy a link to this change. In Discord and other chats it shows this change, not the whole patch.">Copy link</button>'
def notes_body(p, root):
    global ROOTP; ROOTP = root
    n = NOTES[p]; live = n['status'] == 'live'; moves = live and p == PATCH
    order = sorted(NOTES, key=lambda q: [int(v) for v in q.split('.')], reverse=True)
    sw = ''.join(f'<a href="{root}patch/{q}/"{" aria-current=\"page\"" if q == p else ""}>{q}{" preview" if NOTES[q]["status"] != "live" else ""}</a>' for q in order)
    head = (f'<header class="band hero-band pn-hero"><div class="wrap"><p class="meta"><span>Patch {p}</span><span>{"Live since" if live else "Preview, goes live"} {E(n["live"])}</span></p>'
            f'<h1>Patch {p} {"notes" if live else "preview"}</h1><p class="lede">Every Summoner\'s Rift change with the exact numbers, what they mean, '
            f'and where each champion stands in this tier list right now.</p><nav class="pn-sw" aria-label="Patches">{sw}</nav></div></header>')
    ks = [x['kind'] for x in n['champs']]; nadj = len([k for k in ks if k not in ('buff', 'nerf')])
    st = ''.join(f'<div class="{c}"><b>{v}</b><span>{lab}</span></div>' for c, v, lab in
                  [('pos', ks.count('buff'), 'buffs' if ks.count('buff') != 1 else 'buff'), ('neg', ks.count('nerf'), 'nerfs' if ks.count('nerf') != 1 else 'nerf'),
                   ('', nadj, 'adjusted'), ('', len(n.get('items', [])), 'items' if len(n.get('items', [])) != 1 else 'item')] if v)
    tl = (f'<section class="card pn-tl" aria-labelledby="pn-tlh"><h2 id="pn-tlh" class="sr">Short version</h2><div class="pn-num">{st}</div><ul>{"".join(f"<li>{E(t)}</li>" for t in tldr(p, n)[1:])}</ul>'
          f'<p class="pn-mine" id="pnmine" hidden></p></section>')
    groups = [(k, lab, [x for x in n['champs'] if (x['kind'] if x['kind'] in ('buff', 'nerf') else 'adjust') == k]) for k, lab in GROUPS]
    groups = [(k, lab, sorted(xs, key=lambda x: x['c'])) for k, lab, xs in groups if xs]
    # index: every change on the page, jump links (sticky on desktop)
    def ix(x, item=False):
        if item: return f'<li><a class="pn-ix" href="{root}patch/{p}/i-{slug(x["c"])}/">{_ipic(x, root)}<span class="pn-ixn">{E(x["c"])}</span></a></li>'
        r, e = _main_role(x['c'])
        tg = f'<span class="tg sm" style="--T:{TV(e["t"])}" title="{RNAME[r]}, now">{e["t"]}</span>' if e else ''
        return f'<li><a class="pn-ix" href="{root}patch/{p}/{slug(x["c"])}/" data-pc="{E(x["c"])}"><img class="pic" src="{root}img/champ/{slug(x["c"])}.webp" alt="" width="26" height="26"><span class="pn-ixn">{E(x["c"])}</span>{tg}</a></li>'
    idx = ''.join(f'<p class="pn-ih pn-{k}">{lab} <span>{len(xs)}</span></p><ul>{"".join(ix(x) for x in xs)}</ul>' for k, lab, xs in groups)
    if n.get('items'): idx += f'<p class="pn-ih">Items <span>{len(n["items"])}</span></p><ul>{"".join(ix(x, True) for x in n["items"])}</ul>'
    has_other = bool(n.get('other') or n.get('skins') or n.get('none'))
    if has_other: idx += '<p class="pn-ih"><a href="#other">Everything else</a></p>'
    nav = f'<nav class="pn-idx" aria-label="Changes in patch {p}">{idx}</nav>'
    def facts(x, live_now):   # Riot's stated reason, what happened in our numbers, what the numbers mean
        fs = []
        if x.get('why'): fs.append(('Riot says', E(x['why'])))
        if live_now and not x.get('item'):
            ef = _effect(x['c'])
            if ef: fs.append(('So far', ef))
        mn = meaning(x)
        if mn: fs.append(('Means', E(mn)))
        return f'<dl class="pn-fx">{"".join(f"<dt>{lab}</dt><dd>{t}</dd>" for lab, t in fs)}</dl>' if fs else ''
    def card(x):
        body = _lines(x) if x['lines'] else '<p class="pn-nl">Riot listed this change, but the preview has no numbers for it yet.</p>'
        return (f'<article class="card pn-c pn-{x["kind"]}" id="{slug(x["c"])}"><div class="pn-h"><img class="pic" src="{root}img/champ/{slug(x["c"])}.webp" alt="" width="44" height="44" loading="lazy" onerror="this.remove()">'
                f'<h3>{E(x["c"])}</h3><span class="pill {PILL.get(x["kind"], "pn-adj")}">{E(x["kind"])}</span>{_share(p, x)}</div>{_roles(x["c"], root, moves)}'
                f'{facts(x, moves)}{body}</article>')
    leg = 'Chips: tier and score per role right now (Emerald+, all regions). Score = win rate points above the role average, corrected for small samples.' + (f' Arrow = change since {P["prev_patch"]}, grey when it is too small to be sure.' if moves else '')
    champs = (f'<section class="pn-sec" id="champions"><h2>Champions</h2><p class="cap">{E(leg)}</p>'
              + ''.join(f'<h3 class="pn-gh pn-{k}">{lab} <span>{len(xs)}</span></h3><div class="pn-grid{" pn-one" if len(xs) == 1 else ""}">{"".join(card(x) for x in xs)}</div>' for k, lab, xs in groups) + '</section>')
    items = ''
    if n.get('items'):
        ic = []
        for x in n['items']:
            core, start = _users(x['c'])
            who = _faces(core, root, 'Core item') + _faces(start, root, 'Starting item') or '<p class="pn-nl">Not in the core build of any listed champion.</p>'
            ic.append(f'<article class="card pn-c pn-{x["kind"]}" id="i-{slug(x["c"])}"><div class="pn-h">{_ipic(x, root)}<h3>{E(x["c"])}</h3><span class="pill {PILL.get(x["kind"], "pn-adj")}">{E(x["kind"])}</span>{_share(p, x, True)}</div>'
                      + facts(dict(x, item=True), False) + _lines(x, item=True) + who + '</article>')
        items = f'<section class="pn-sec" id="items"><h2>Items</h2><p class="cap">Who builds it: OP.GG core builds, boots and starting items, Global Emerald+.</p><div class="pn-grid">{"".join(ic)}</div></section>'
    oc = [f'<article class="card pn-c"><h3>{E(k)}</h3><p>{E(t)}</p></article>' for k, t in n.get('other', [])]
    if n.get('skins'):
        oc.append(f'<article class="card pn-c"><h3>New skins <span class="pn-cnt">{len(n["skins"])}</span></h3><ul class="pn-sk">{"".join(f"<li>{E(s)}</li>" for s in n["skins"])}</ul>'
                  + (f'<p class="pn-nl">Chromas: {E(", ".join(n["chromas"]))}.</p>' if n.get('chromas') else '') + '</article>')
    other = (f'<section class="pn-sec" id="other"><h2>Everything else</h2>' + (f'<p class="cap">{E(n["none"])}</p>' if n.get('none') else '')
             + (f'<div class="pn-grid">{"".join(oc)}</div>' if oc else '') + '</section>') if has_other else ''
    src = (f'<p class="pn-src">Source: <a href="{E(n["url"])}" rel="noopener">{E(n["src"])}</a>. Written short in our own words, the numbers are copied as listed. '
           'ARAM, Arena, Classic and other modes are left out on purpose.</p>')
    return head + f'<main class="band pn"><div class="wrap">{tl}<div class="pn-lay">{nav}<div class="pn-body">{champs}{items}{other}{src}</div></div></div></main>'
def notes_page(rel, p, root, url):
    n = NOTES[p]; live = n['status'] == 'live'; kind = 'notes' if live else 'preview'
    desc = f'Patch {p} {kind} for Summoner\'s Rift: every champion and item change with exact numbers, what it means and where each champion stands now.'[:160]
    page(rel, 'N', root, 'patch', 'top', f'Patch {p} {kind}: every change with numbers | LoL Tier List', f'LoL patch {p} {kind}: {_and([x["c"] for x in n["champs"][:3]])} and more',
         desc, url, SITE + f'og/patch/{p}.jpg', head=notes_body(p, root))
LIVE_NOTES = sorted([q for q in NOTES if NOTES[q]['status'] == 'live'], key=lambda q: [int(v) for v in q.split('.')])
for q in NOTES: notes_page(f'patch/{q}/index.html', q, '../../', SITE + f'patch/{q}/')
if LIVE_NOTES: notes_page('patch/index.html', LIVE_NOTES[-1], '../', SITE + f'patch/{LIVE_NOTES[-1]}/')

# ---------- one share page per change: /patch/<p>/<champion>/ and /patch/<p>/i-<item>/ ----------
# Link previews (Discord, X, WhatsApp) never see the #part of a link, so /patch/26.23/#ezreal can only show the whole patch.
# Each change gets a tiny page with its own title, text and picture (og/patch/<p>/<id>.jpg, made by scripts/assets.py) that
# sends people on to its card. noindex: search engines should list the patch page, not 40 copies of it.
def _plain(v): return re.sub(r'\s+', ' ', str(v)).strip()
def share_text(p, x, item=False):
    n = NOTES[p]; pre = n['status'] != 'live'; ab = x.get('ab') or {}
    title = f"{x['c']}: {x['kind']} in patch {p}" + (' (preview)' if pre else '')
    parts = []
    for key, stat, old, new, tag, d in x['lines']:
        pre_ = [v for v in [key, ab.get(key, '')] if v and key not in ('', 'Base')]
        st_ = stat[0].lower() + stat[1:] if pre_ and len(stat) > 1 and stat[1].islower() else stat
        lab = ' '.join(pre_ + [st_])
        parts.append(f'{lab}: {old} → {new}' if old and new else f'{lab}: {new or old}')
    head = f"{x['kind'].capitalize()} in patch {p}" + (', preview (numbers can still change)' if pre else '') + '. '
    d, used = head, 0
    for t in parts:
        if len(d) + len(t) + 2 > 290: break
        d += t + '; '; used += 1
    d = d.rstrip('; ') + ('.' if used else '')
    if used < len(parts): d += f' Plus {len(parts) - used} more.'
    mn = '' if item else meaning(x)
    if mn and len(d) + len(mn) + 1 <= 400: d += ' ' + mn
    if not parts: d += _plain(x.get('short', ''))
    return title, d
def share_page(p, x, item=False):
    # a full copy of the patch notes that opens at this change, so the address bar itself holds the shareable link
    sid = _sid(x, item); title, d = share_text(p, x, item); url = f'{SITE}patch/{p}/{sid}/'; rel = f'patch/{p}/{sid}/index.html'
    page(rel, 'N', '../../../', 'patch', 'top', f'{title} | LoL Tier List', title, d, url, f'{SITE}og/patch/{p}/{sid}.jpg', champ=sid, head=notes_body(p, '../../../'))
    path = os.path.join(PUB, rel); h = open(path, encoding='utf-8').read()   # search engines: list the patch page, not 40 copies
    h = h.replace(f'<link rel="canonical" href="{url}">', f'<link rel="canonical" href="{SITE}patch/{p}/"><meta name="robots" content="noindex">', 1)
    open(path, 'w', encoding='utf-8').write(h)
for q, n in NOTES.items():
    for x in n['champs']: share_page(q, x)
    for x in n.get('items', []): share_page(q, x, True)

# ---------- link preview pictures (1200x630): build.py describes each one as HTML, scripts/assets.py renders only the ones whose
# HTML changed (hashes in data/og_hashes.json), so the repo does not grow with every build. Placeholders: __PUB__ (public/ on
# disk), __FONTS__, __MARK__ (filled by assets.py).
TCOL = {'Z': '#fbcd68', 'S': '#fbaa71', 'A': '#beaa85', 'B': '#7fa48f', 'C': '#638c9a', 'D': '#5d7094', 'P': '#ac96c8'}
KCOL = {'buff': '#3fd17f', 'nerf': '#ff7a68'}
OG_CSS = """__FONTS__
*{box-sizing:border-box}body{margin:0;width:1200px;height:630px;overflow:hidden;background:#0b0c0f;color:#eceef2;font-family:Inter;position:relative}
.art{position:absolute;right:0;top:0;width:760px;height:630px;background-size:cover;background-position:center 20%;opacity:.55;
 -webkit-mask-image:linear-gradient(90deg,transparent,#000 45%)}
.ico{position:absolute;right:90px;top:150px;width:300px;height:300px;border-radius:40px;opacity:.9;image-rendering:auto}
.c{position:relative;padding:52px 64px;height:100%;display:flex;flex-direction:column}
.b{display:flex;align-items:center;gap:12px;font:700 24px Inter;color:#cfd3db}.b svg{width:36px;height:36px}.b span{color:#959cab;font-weight:500}
h1{font:800 88px/1 Inter;letter-spacing:-.04em;margin:30px 0 0;display:flex;align-items:center;gap:22px}
.k{font:800 30px 'Barlow Condensed';letter-spacing:.02em;text-transform:uppercase;color:#0b0c0f;border-radius:10px;padding:4px 14px;margin-top:8px}
.ls{margin-top:30px;display:grid;gap:18px;max-width:840px}
.ln{display:grid;grid-template-columns:52px 1fr;gap:16px;align-items:start}.ln img{width:52px;height:52px;border-radius:12px}
.ln.ni{grid-template-columns:1fr}
.lb{margin:0;font:600 21px Inter;color:#959cab}.v{margin:3px 0 0;font:600 27px/1.25 Inter;letter-spacing:-.01em}
.o{color:#959cab}.o em{font-style:normal;text-decoration:line-through}.n em{font-style:normal;font-weight:800;color:#e3b34c}
.up .n em{color:#3fd17f}.dn .n em{color:#ff7a68}
.more{margin:4px 0 0;font:600 21px Inter;color:#959cab}
.ft{margin-top:auto;display:flex;align-items:center;gap:14px;font:600 22px Inter;color:#959cab}
.ch{display:inline-flex;align-items:center;gap:10px;background:#181b21;border:1px solid #2a2e37;border-radius:999px;padding:6px 14px 6px 8px;color:#eceef2}
.t{font:800 22px 'Barlow Condensed';color:#14151a;border-radius:6px;padding:1px 9px}
.u{margin-left:auto}
.grid{margin-top:34px;display:flex;flex-wrap:wrap;gap:14px;max-width:1080px}.f{width:86px;height:86px;border-radius:20px;border:4px solid #2a2e37}
"""
OG_JOBS = {}
def og_change(p, x, item=False):
    n = NOTES[p]; sid = _sid(x, item); pre = n['status'] != 'live'; ab = x.get('ab') or {}; sl = slug(x['c'])
    rows = []
    for key, stat, old, new, tag, d in x['lines'][:3]:
        pre_ = [v for v in [key, ab.get(key, '')] if v and key not in ('', 'Base')]
        lab = ' '.join(pre_) + ' · ' + stat if pre_ else ('Base stats · ' + stat if key == 'Base' else stat)
        o, nn = _diff(old, new) if old else ('', E(new))
        icon = f'<img src="__PUB__/img/spell/{sl}_{key.lower()}.webp">' if not item and key in KEYN and key != 'Base' else ''
        cls = 'up' if d == '+' else 'dn' if d == '-' else ''
        rows.append(f'<div class="ln {cls}{"" if icon else " ni"}">{icon}<div><p class="lb">{E(lab)}</p><p class="v">'
                    + (f'<span class="o">{o}</span> → ' if old else '') + f'<span class="n">{nn}</span></p></div></div>')
    if not rows: rows.append(f'<p class="more">{E(x.get("short", ""))}. Numbers not out yet.</p>')
    more = len(x['lines']) - 3
    if more > 0: rows.append(f'<p class="more">+{more} more change{"s" if more > 1 else ""}</p>')
    chips = ''
    if not item:
        L = sorted([(r, nm_, e) for r, nm_, _ in ROLES for e in D[r] if e['c'] == x['c']], key=lambda t: -t[2]['pick'])[:3]
        chips = ''.join(f'<span class="ch">{nm_} <span class="t" style="background:{TCOL.get(e["t"], "#959cab")}">{e["t"]}</span> {"+" if e["score"] > 0 else "−" if e["score"] < 0 else ""}{abs(e["score"]):.1f}</span>' for r, nm_, e in L)
        chips = (f'<span>{"Now, before the change:" if pre else "Now:"}</span>' + chips) if chips else ''
    art = f'<img class="ico" src="__PUB__/img/item/{ITEM_ID.get(x["c"], "")}.webp">' if item else f'<div class="art" style="background-image:url(__PUB__/img/splash/{sl}.webp)"></div>'
    kc = KCOL.get(x['kind'], '#e3b34c')
    OG_JOBS[f'og/patch/{p}/{sid}.jpg'] = (f'<html><head><style>{OG_CSS}</style></head><body>{art}<div class="c"><div class="b">__MARK__LoL Tier List <span>· Patch {p}{" preview" if pre else ""}</span></div>'
        f'<h1>{E(x["c"])}<span class="k" style="background:{kc}">{E(x["kind"])}</span></h1><div class="ls">{"".join(rows)}</div>'
        f'<div class="ft">{chips}<span class="u">lol-tierlist.pages.dev</span></div></div></body></html>')
def og_patch(p):
    n = NOTES[p]; pre = n['status'] != 'live'; cs = n['champs']
    cnt = {k: sum(1 for x in cs if x['kind'] == k) for k in ('buff', 'nerf', 'adjust')}
    line = ', '.join(f'{v} {k if k != "adjust" else "adjusted"}{"s" if v > 1 and k != "adjust" else ""}' for k, v in cnt.items() if v) + (f', {len(n["items"])} item{"s" if len(n["items"]) > 1 else ""}' if n.get('items') else '')
    faces = ''.join(f'<img class="f" style="border-color:{KCOL.get(x["kind"], "#e3b34c")}" src="__PUB__/img/tile/{slug(x["c"])}.webp">' for x in cs[:20])
    OG_JOBS[f'og/patch/{p}.jpg'] = (f'<html><head><style>{OG_CSS}</style></head><body><div class="c"><div class="b">__MARK__LoL Tier List</div>'
        f'<h1 style="font-size:80px">Patch {p} {"preview" if pre else "notes"}</h1><p class="more" style="font-size:26px;margin-top:14px">{E(line)}. Every number, Summoner\'s Rift only.</p>'
        f'<div class="grid">{faces}</div><div class="ft">' + ''.join(f'<span style="color:{KCOL.get(k, "#e3b34c")}">■ {lab}</span>' for k, lab in (('buff', 'buff'), ('nerf', 'nerf'), ('adjust', 'adjusted')) if cnt[k]) + '<span class="u">lol-tierlist.pages.dev</span></div></div></body></html>')
for q, n in NOTES.items():
    og_patch(q)
    for x in n['champs']: og_change(q, x)
    for x in n.get('items', []): og_change(q, x, True)
json.dump(OG_JOBS, open(os.path.join(HERE, '.og_jobs.json'), 'w', encoding='utf-8'), ensure_ascii=False)

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
urls = [SITE] + [SITE + r + '/' for r, _, _ in ROLES] + [SITE + 'method/', SITE + 'privacy/'] + [SITE + f'patch/{q}/' for q in NOTES] + [SITE + f"{r}/{slug(e['c'])}/" for r, _, _ in ROLES for e in D[r]]
write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n' for u in urls) + '</urlset>\n')
print('built: index, ' + ', '.join(r for r, _, _ in ROLES) + f", {sum(len(D[r]) for r, _, _ in ROLES)} champion pages, method, " + ", ".join(f"patch/{q}" for q in NOTES) + ", privacy, 404, robots, sitemap")
