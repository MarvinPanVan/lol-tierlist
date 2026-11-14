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

def strip(h, keep):   # template blocks: B = tier list pages, M = method page, N = patch notes pages
    for b in 'BMN':
        if b != keep: h = re.sub(rf'<!--{b}-->.*?<!--/{b}-->', '', h, flags=re.S)
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
NOTES = P.get('notes', {})
META_SLIM['nitems'] = sorted({x['c'] for n in NOTES.values() for x in n.get('items', [])})   # item names: no portrait to load
META_SLIM['notes'] = {p: [x['c'] for x in n['champs'] + n.get('items', [])] for p, n in NOTES.items()}   # the panel links to /patch/<p>/#<champion>
if PATCH in NOTES:   # the short lines on the panels (changes, item_changes) and the full notes must list the same things
    assert {x['c']: [x['kind'], x['short']] for x in NOTES[PATCH]['champs']} == P.get('changes'), 'patch.json: "changes" and "notes" disagree'
    assert {x['c']: [x['kind'], x['short'], x['slot']] for x in NOTES[PATCH].get('items', [])} == P.get('item_changes', {}), 'patch.json: "item_changes" and "notes" disagree'
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
    return sorted([(r, e) for r, _, _ in ROLES for e in D[r] if vk in e['v'] and e['v'][vk][2] in ('Z', 'S')], key=lambda x: (TR[x[1]['v'][vk][2]], -x[1]['v'][vk][0]))
def head_home(root):
    # the patch story: fixed for the patch (Emerald+, all regions). Everything under the control bar follows the visitor's rank and region.
    strong = strongest()
    lc = ''.join(f'<a class="lead" href="{root}{r}/{slug(e["c"])}/" data-jr="{r}" data-jc="{E(e["c"])}" style="--art:url(/img/splash/{slug(e["c"])}.webp);--R:var(--R{r})">'
                 f'<span class="lr"><span class="ri">{RICON[r]}</span>{RNAME[r]}</span><span class="lb"><b>{E(e["c"])}</b>'
                 f'<span><span class="tg" style="background:var(--{e["t"]})">{e["t"]}</span> {f1(e["score"])} · {fx(e["pick"])}% pick</span></span></a>' for r, e in strong[:3])
    nx = P.get('next', {})
    pl = f'<a href="{root}patch/{PATCH}/">Patch {PATCH}</a>' if PATCH in NOTES else f'Patch {PATCH}'
    nl = (f'<a href="{root}patch/{nx["patch"]}/">Next patch on {E(nx.get("date", ""))}</a>' if nx.get('patch') in NOTES else f'Next patch on {E(nx.get("date", ""))}') if nx else ''
    when = f'{pl}, updated {E(UPD)}.' + (f' {nl}.' if nl else '')
    return (f'<header class="band head home"><div class="wrap"><div class="hero2"><div class="htxt"><p class="dl">{when}</p>'
            f'<h1>{E(P.get("headline", ""))}</h1><p class="lede">{P.get("lede", "")}</p></div><div class="leads">{lc}</div></div></div></header>')
RKN = [('E', 'Emerald+'), ('D', 'Diamond+'), ('M', 'Master+')]
def head_champ(r, e, root):
    s_ = slug(e['c']); tc = lambda t: f'var(--{t})' if t else 'var(--E)'
    tiers = ''.join(f'<span style="background:{tc(e["v"][k][2])}">{n} {e["v"][k][2]} {f1(e["v"][k][0])}</span>' for k, n in RKN if k in e.get('v', {}))
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
base_desc = f'LoL tier list for patch {PATCH}, every role. Nine stat sites combined, corrected for small samples and one-tricks. No ads.'
z = [c for r, _, _ in ROLES for c in D['_meta']['facts']['z'][r]]
page('index.html', 'B', '', 'home', 'top', f'LoL Tier List: patch {PATCH}, every role', f'LoL Tier List {PATCH}' + (f": {', '.join(z[:-1])} and {z[-1]} lead" if len(z) > 1 else ''), base_desc, SITE, SITE + 'og.png', head=head_home(''))
for r, name, plural in ROLES:
    page(f'{r}/index.html', 'B', '../', 'board', r, f'{name} tier list, patch {PATCH} | LoL Tier List', f'{name} tier list for patch {PATCH}',
         f'Best {plural} in patch {PATCH}: {top_line(r)}. Nine stat sites combined, no ads.'[:160],
         SITE + r + '/', SITE + f'og-{r}.png', head=head_role(r))
    for e in D[r]:   # one page per champion and role
        sl = slug(e['c']); tiers = ', '.join(f"{n} {e['v'][k][2]}" for k, n in RKN if k in e['v'])
        page(f'{r}/{sl}/index.html', 'B', '../../', 'champ', r, f"{e['c']} {name}, patch {PATCH}: {e['t']} tier | LoL Tier List",
             f"{e['c']} {name}, patch {PATCH}: {tiers}", cdesc(e, name, tiers),
             SITE + f'{r}/{sl}/', SITE + f'img/splash/{sl}.webp', champ=e['c'], head=head_champ(r, e, '../../'))
page('method/index.html', 'M', '../', 'method', 'top', 'How the tier list is made | LoL Tier List', 'How the LoL tier list is made',
     'Where the numbers come from, how nine stat sites are combined into one score and tier, how far each site can be trusted, and what a tier list cannot tell you.',
     SITE + 'method/', SITE + 'og.png')

# ---------- patch notes: /patch/<patch>/ for every patch in patch.json "notes", /patch/ = the newest live one ----------
# Lines are [key, stat, old, new, tag, dir]. The "what it means" sentence comes only from these rules (or a hand-written
# "m" that says nothing the numbers don't show): which ranks change, whether only the scaling changes, base stats per level.
_BP = os.path.join(HERE, 'data', 'opgg_builds.json')
BUILDS = json.load(open(_BP, encoding='utf-8')) if os.path.exists(_BP) else {}
NUM = r'\d+(?:\.\d+)?'
def _ranks(s):   # leading numbers: "10 / 9 / 8s" (per rank), "45 - 165" (low to high end), "56" (one value)
    s = s.strip()
    m = re.match(rf'({NUM}(?:\s*/\s*{NUM})+)', s)
    if m: return [float(x) for x in re.split(r'\s*/\s*', m.group(1))], 'rank'
    m = re.match(rf'({NUM})%?\s*-\s*({NUM})', s)
    if m: return [float(m.group(1)), float(m.group(2))], 'range'
    m = re.match(rf'({NUM})', s)
    return ([float(m.group(1))], 'one') if m else (None, None)
def _stat(s):   # "590 + 107/level", "5.4/level", "54"
    m = re.match(rf'({NUM})\s*\+\s*({NUM})%?/level', s)
    if m: return float(m.group(1)), float(m.group(2))
    m = re.match(rf'\+?({NUM})%?/level', s)
    if m: return None, float(m.group(1))
    m = re.fullmatch(rf'({NUM})', s.strip())
    return (float(m.group(1)), None) if m else (None, None)
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
    (a, ka), (b, kb) = _ranks(old), _ranks(new); ph, det = set(), None
    if a and b:
        if len(a) == 1 and len(b) == 1:
            if a != b: ph.add('all')
        else:
            f0, f1, l0, l1 = a[0], b[0], a[-1], b[-1]
            rf = abs(f1 - f0) / f0 if f0 else float(f1 != f0); rl = abs(l1 - l0) / l0 if l0 else float(l1 != l0)
            if rf and not rl: ph.add('early')
            elif rl and not rf: ph.add('late')
            elif rf and rl: ph.add('early' if rf >= 2 * rl else 'late' if rl >= 2 * rf else 'all')
            det = ('range' if 'range' in (ka, kb) else 'rank', f0, f1, l0, l1)
    if re.findall(r'\(([^)]*)\)', old) != re.findall(r'\(([^)]*)\)', new): ph.add('items')
    return ph, det
def _g(v): return f'{v:g}'
def meaning(x):
    if x.get('m'): return x['m']
    L = [l for l in x['lines'] if l[4] != 'mech' and l[5] in '+-' and l[2]]
    if not L: return ''
    info = [(l, *_phase(l)) for l in L]; dirs = {l[5] for l in L}; name = x['c']; out = []
    if len(dirs) == 1:
        w = 'helps' if '+' in dirs else 'hurts'
        ph = set().union(*[p for _, p, _ in info]); dets = [d for _, p, d in info if d]
        lo, hi = ('rank 1', 'max rank') if dets and dets[0][0] == 'rank' else ('the low end', 'the top end')
        if ph == {'early'} and dets:
            d = dets[0]
            out.append(f'Mostly {w} early: {hi} stays the same.' if all(t[3] == t[4] for t in dets) else
                       f'Mostly {w} early: {_g(d[1])} → {_g(d[2])} at {lo} is a much bigger change than {_g(d[3])} → {_g(d[4])} at {hi}.')
        elif ph == {'late'} and dets:
            d = dets[0]
            out.append(f'Mostly {w} later: {lo} stays the same.' if all(t[1] == t[2] for t in dets) else
                       f'Mostly {w} later: {_g(d[1])} → {_g(d[2])} at {lo} is a much smaller change than {_g(d[3])} → {_g(d[4])} at {hi}.')
        elif ph == {'items'}: out.append(f'Only the scaling changes, so it {w} more the more items {name} has.')
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

PILL = {'buff': 'pos', 'nerf': 'neg'}
def _lines(L):
    li = []
    for k, stat, old, new, tag, d in L:
        v = (f'<span class="pn-o">{E(old)}</span> <span class="pn-ar" aria-label="changed to">→</span> ' if old else '') + f'<span class="pn-n">{E(new)}</span>'
        li.append(f'<li class="pn-l{" pn-up" if d == "+" else " pn-dn" if d == "-" else ""}">' + (f'<span class="pn-k">{E(k)}</span>' if k else '') + f'<div><b>{E(stat)}</b><p>{v}</p></div></li>')
    if len(li) > 8:   # long reworks: the first 6 lines, the rest behind a toggle
        return f'<ul class="pn-ls">{"".join(li[:6])}</ul><details class="pn-more"><summary>Show all {len(li)} changes</summary><ul class="pn-ls">{"".join(li[6:])}</ul></details>'
    return f'<ul class="pn-ls">{"".join(li)}</ul>'
def _roles(c, root, moves):   # where the champion stands now, every role it is listed in, most played first
    rs = sorted([(r, e) for r, _, _ in ROLES for e in D[r] if e['c'] == c], key=lambda x: -x[1]['pick'])
    if not rs: return '<p class="pn-nl">Not in the tier list: too few games in every role.</p>'
    ch = []
    for r, e in rs:
        mv = ''
        if moves and e.get('tr') is not None:
            weak = e.get('trz') is not None and abs(e['trz']) < 1.64
            mv = f' <span class="pn-mv{" pn-weak" if weak else " pos" if e["tr"] > 0 else " neg"}"{" title=\"Could be chance\"" if weak else ""}>{"↑" if e["tr"] > 0 else "↓" if e["tr"] < 0 else "·"} {f1(e["tr"])}</span>'
        ch.append(f'<a class="pn-r" href="{root}{r}/{slug(c)}/" style="--R:var(--R{r})"><span class="ri">{RICON[r]}</span>{RNAME[r]} '
                  f'<span class="tg sm" style="background:var(--{e["t"]})">{e["t"]}</span> <b>{f1(e["score"])}</b>{mv}</a>')
    return f'<div class="pn-rs">{"".join(ch)}</div>'
def _users(name):   # listed champions with the item in their OP.GG core build or boots, and as starting item: {champion: [roles]}, most played first
    core, start, pk = {}, {}, {}
    for r, _, _ in ROLES:
        for e in D[r]:
            b = BUILDS.get(r, {}).get(e['c'], {}); pk[e['c']] = pk.get(e['c'], 0) + e['pick']
            if any(n == name for k in ('c0', 'c1', 'b0') for _, n in b.get(k, [])): core.setdefault(e['c'], []).append(r)
            if any(n == name for _, n in b.get('s0', [])): start.setdefault(e['c'], []).append(r)
    order = lambda m: dict(sorted(m.items(), key=lambda kv: -pk[kv[0]]))
    return order(core), order(start)
def _names(M, n=6):
    s = [f'{c} ({", ".join(RNAME[r] for r in rs)})' for c, rs in list(M.items())[:n]]
    if len(M) > n: return ', '.join(s) + f' and {len(M) - n} more'
    return ', '.join(s[:-1]) + (' and ' if len(s) > 1 else '') + s[-1]
def _count(n, one, many): return f'{n} {one if n == 1 else many}'
def tldr(p, n):
    out, live = [], n['status'] == 'live'
    ks = [x['kind'] for x in n['champs']]; adj = [x['c'] for x in n['champs'] if x['kind'] not in ('buff', 'nerf')]
    parts = [_count(ks.count('buff'), 'buff', 'buffs'), _count(ks.count('nerf'), 'nerf', 'nerfs')] + ([f'{" and ".join(adj)} reworked'] if adj else [])
    out.append(f'{_count(len(ks), "champion", "champions")} {"changed" if live else "planned"}: {", ".join(parts[:-1])} and {parts[-1]}.')
    if live and p == PATCH:
        mv = []
        for x in n['champs']:
            es = [(r, e) for r, _, _ in ROLES for e in D[r] if e['c'] == x['c'] and e.get('tr') is not None and e.get('trz') is not None and abs(e['trz']) >= 1.64]
            if es:
                r, e = max(es, key=lambda t: abs(t[1]['tr'])); mv.append((abs(e['tr']), f'{x["c"]} {RNAME[r]} {"↑" if e["tr"] > 0 else "↓"} {f1(e["tr"])}'))
        out.append(f'Clear moves in our score since {P["prev_patch"]}: {", ".join(t for _, t in sorted(mv, reverse=True)[:4])}. Everything else moved too little to rule out chance.'
                   if mv else 'None of the changed champions moved clearly in our numbers yet.')
    its = []
    for x in n.get('items', []):
        core, start = _users(x['c'])
        who = f'core for {_count(len(core), "listed champion", "listed champions")}' if core else f'starting item for {_count(len(start), "listed champion", "listed champions")}' if start else 'in no listed build'
        its.append(f'{x["c"]} {"buffed" if x["kind"] == "buff" else "nerfed" if x["kind"] == "nerf" else "adjusted"} ({who})')
    if its: out.append('Items: ' + ', '.join(its) + '.')
    for k, t in n.get('other', []): out.append(f'{k}: {t.split(". ")[0].rstrip(".")}.')
    if n.get('skins'): out.append(f'{_count(len(n["skins"]), "new skin", "new skins")}' + (f' and {_count(len(n.get("chromas", [])), "chroma", "chromas")}' if n.get('chromas') else '') + '.')
    if not live: out.append(f'This is the preview. Numbers can still change before the patch goes live on {n["live"]}.')
    return out
def notes_body(p, root):
    n = NOTES[p]; live = n['status'] == 'live'; moves = live and p == PATCH
    order = sorted(NOTES, key=lambda q: [int(v) for v in q.split('.')], reverse=True)
    sw = ''.join(f'<a href="{root}patch/{q}/"{" aria-current=\"page\"" if q == p else ""}>{q}{" preview" if NOTES[q]["status"] != "live" else ""}</a>' for q in order)
    head = (f'<header class="band hero-band pn-hero"><div class="wrap pn-w"><p class="meta"><span>Patch {p}</span><span>{"Live since" if live else "Preview, goes live"} {E(n["live"])}</span></p>'
            f'<h1>Patch {p} {"notes" if live else "preview"}, short</h1><p class="lede">Summoner\'s Rift only: champions, items and anything else that touches ranked games. '
            f'Exact numbers, what they mean, and where each champion stands in this tier list right now.</p><nav class="pn-sw" aria-label="Patches">{sw}</nav></div></header>')
    tl = f'<section class="card pn-tl"><h2>Short version</h2><ul>{"".join(f"<li>{E(t)}</li>" for t in tldr(p, n))}</ul></section>'
    cards = []
    for x in sorted(n['champs'], key=lambda x: ({'buff': 0, 'nerf': 1}.get(x['kind'], 2), x['c'])):
        mn = meaning(x)
        body = _lines(x['lines']) if x['lines'] else '<p class="pn-nl">Riot listed this change but the preview shows no numbers yet.</p>'
        cards.append(f'<article class="card pn-c" id="{slug(x["c"])}"><div class="pn-h"><img class="pic" src="{root}img/champ/{slug(x["c"])}.webp" alt="" width="40" height="40" loading="lazy" onerror="this.remove()">'
                     f'<h3>{E(x["c"])}</h3><span class="pill {PILL.get(x["kind"], "pn-adj")}">{E(x["kind"])}</span></div>{_roles(x["c"], root, moves)}'
                     + (f'<p class="pn-m">{E(mn)}</p>' if mn else '') + f'{body}</article>')
    since = f', then the change since {P["prev_patch"]}' if moves else ''
    leg = f'Tier and score now (Emerald+, all regions){since}. ' + ('A grey change is small enough to be chance. ' if moves else '') + 'Tap a role to open the champion.'
    champs = f'<section class="pn-sec" id="champions"><h2>Champions <span class="pn-cnt">{len(n["champs"])}</span></h2><p class="cap">{E(leg)}</p><div class="pn-grid">{"".join(cards)}</div></section>'
    items = ''
    if n.get('items'):
        ic = []
        for x in n['items']:
            core, start = _users(x['c']); mn = meaning(x)
            who = (f'<p class="pn-u">Core item for {E(_names(core))}.</p>' if core else '') + (f'<p class="pn-u">Starting item for {E(_names(start))}.</p>' if start else '')
            if not who: who = '<p class="pn-u">Not in the core build of any listed champion.</p>'
            ic.append(f'<article class="card pn-c" id="i-{slug(x["c"])}"><div class="pn-h"><span class="pw"></span><h3>{E(x["c"])}</h3><span class="pill {PILL.get(x["kind"], "pn-adj")}">{E(x["kind"])}</span></div>'
                      + who + (f'<p class="pn-m">{E(mn)}</p>' if mn else '') + _lines(x['lines']) + '</article>')
        items = f'<section class="pn-sec" id="items"><h2>Items <span class="pn-cnt">{len(n["items"])}</span></h2><p class="cap">Builds from OP.GG, Global Emerald+.</p><div class="pn-grid">{"".join(ic)}</div></section>'
    rest = ''.join(f'<div class="pn-o2"><h3>{E(k)}</h3><p>{E(t)}</p></div>' for k, t in n.get('other', []))
    if n.get('none'): rest += f'<div class="pn-o2"><p class="pn-nl">{E(n["none"])}</p></div>'
    if n.get('skins'):
        rest += f'<div class="pn-o2"><h3>New skins</h3><p>{E(", ".join(n["skins"]))}.</p>' + (f'<p class="pn-nl">Chromas: {E(", ".join(n["chromas"]))}.</p>' if n.get('chromas') else '') + '</div>'
    other = f'<section class="pn-sec" id="other"><h2>Everything else</h2>{rest}</section>' if rest else ''
    src = (f'<p class="pn-src">Source: <a href="{E(n["url"])}" rel="noopener">{E(n["src"])}</a>. Written short in our own words, the numbers are copied as listed. '
           'ARAM, Arena, Classic and other modes are left out on purpose.</p>')
    return head + f'<main class="band pn"><div class="wrap pn-w">{tl}{champs}{items}{other}{src}</div></main>'
def notes_page(rel, p, root, url):
    n = NOTES[p]; live = n['status'] == 'live'
    nm = ', '.join(x['c'] for x in n['champs'][:4])
    desc = f'Patch {p} {"notes" if live else "preview"} for Summoner\'s Rift: every champion and item change with exact numbers, what it means and where each champion stands now.'[:160]
    page(rel, 'N', root, 'patch', 'top', f'Patch {p} {"notes" if live else "preview"}, short with numbers | LoL Tier List', f'LoL patch {p} {"notes" if live else "preview"}: {nm} and more',
         desc, url, SITE + 'og.png', head=notes_body(p, root))
LIVE_NOTES = sorted([q for q in NOTES if NOTES[q]['status'] == 'live'], key=lambda q: [int(v) for v in q.split('.')])
for q in NOTES: notes_page(f'patch/{q}/index.html', q, '../../', SITE + f'patch/{q}/')
if LIVE_NOTES: notes_page('patch/index.html', LIVE_NOTES[-1], '../', SITE + f'patch/{LIVE_NOTES[-1]}/')

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
