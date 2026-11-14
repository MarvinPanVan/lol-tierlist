"""Check the built site before pushing: python3 pipeline/scripts/check_site.py  (needs playwright and Google Chrome)
Serves public/ itself, then checks: JS errors and sideways scrolling at phone, laptop and desktop widths in light and dark
mode; broken internal links, images and 4xx responses; duplicate ids, unnamed buttons, title and description lengths,
og images; that champion pages fill their panel; that the Chart layout can always be left again; that a change's own
page in the patch notes keeps its address and opens at its card. Prints PROBLEM lines (fix them) and info lines. Exit code 1 if there is a problem."""
import os, re, sys, json, random, threading, functools, http.server
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PUB, D = os.path.join(ROOT, 'public'), json.load(open(os.path.join(ROOT, 'pipeline', 'tiers.json'), encoding='utf-8'))
slug = lambda c: re.sub(r'[^a-z0-9]', '', c.lower())
ROLES = [r for r in D if r != '_meta']
problems, info = [], []

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True
    def handle_error(self, *a): pass   # browsers drop connections all the time; not a site problem
srv = Server(('127.0.0.1', 0), functools.partial(Quiet, directory=PUB)); PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
B = f'http://127.0.0.1:{PORT}'

for n in sorted({e['c'] for r in ROLES for e in D[r]}):   # art for every listed champion
    for d in ['champ', 'tile', 'splash']:
        if not os.path.exists(os.path.join(PUB, 'img', d, slug(n) + '.webp')): problems.append(f'missing img/{d}/{slug(n)}.webp')

with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome')
    # 1) errors and sideways scrolling
    urls = ['/', '/jungle/', '/method/', '/mid/#katarina', '/patch/', '/privacy/']
    for w, h in [(390, 844), (1024, 768), (1440, 900)]:
        for scheme in ['light', 'dark']:
            pg = b.new_page(viewport={'width': w, 'height': h}, color_scheme=scheme); errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and '404' not in m.text else None)
            pg.goto(B + '/'); pg.evaluate(f"localStorage.setItem('tl-theme','{scheme}')")
            for u in urls:
                pg.goto(B + u); pg.wait_for_timeout(450)
                for mode in (['tiers', 'table', 'chart'] if u in ('/', '/jungle/') else [None]):
                    if mode: pg.evaluate(f"document.querySelector('#modes [data-mode={mode}]').click()"); pg.wait_for_timeout(200)
                    ov = pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
                    if ov > 0: problems.append(f'sideways scroll {ov}px at {w} {scheme} {u} {mode or ""}')
            if errs: problems.append(f'JS errors at {w} {scheme}: {sorted(set(errs))[:3]}')
            pg.close()
    pg = b.new_page(viewport={'width': 1440, 'height': 900}); errs = []
    pg.on('pageerror', lambda e: errs.append((pg.url, str(e))))
    bad = []; pg.on('response', lambda r: bad.append((r.status, r.url)) if r.status >= 400 and not r.url.endswith('/nope') else None)
    # 2) the chart can always be left: header link back, and a reload never comes back as the chart
    pg.goto(B + '/adc/'); pg.wait_for_timeout(900)
    pg.click('nav.links a[data-mode=chart]'); pg.wait_for_timeout(500)
    pg.click('nav.links a[data-go=board]'); pg.wait_for_timeout(500)
    if pg.evaluate("document.querySelectorAll('#board .chip').length") == 0: problems.append('"Tier list" link does not leave the chart')
    pg.click('nav.links a[data-mode=chart]'); pg.wait_for_timeout(400); pg.reload(); pg.wait_for_timeout(1200)
    if pg.evaluate("document.querySelectorAll('#board .chip').length") == 0: problems.append('the chart comes back after a reload')
    # 3) links, images, ids, names, meta
    links = set()
    for u in ['/', '/mid/', '/method/', '/privacy/', '/adc/kogmaw/', '/patch/']:
        pg.goto(B + u); pg.wait_for_timeout(900)
        links |= set(pg.evaluate("[...document.querySelectorAll('a[href]')].map(a=>a.href).filter(h=>h.startsWith(location.origin))"))
        dup = pg.evaluate("(()=>{const c={};document.querySelectorAll('[id]').forEach(e=>c[e.id]=(c[e.id]||0)+1);return Object.entries(c).filter(([k,v])=>v>1)})()")
        if dup: problems.append(f'duplicate ids on {u}: {dup}')
        noname = pg.evaluate("[...document.querySelectorAll('button,a')].filter(e=>e.offsetParent&&!(e.getAttribute('aria-label')||e.textContent.trim()||e.title)).length")
        if noname: problems.append(f'{noname} unnamed buttons/links on {u}')
        imgs = pg.evaluate("[...document.images].filter(i=>i.complete&&i.naturalWidth===0&&i.src).map(i=>i.src)")
        if imgs: problems.append(f'broken images on {u}: {imgs[:3]}')
        m = pg.evaluate("({t:document.title,d:(document.querySelector('meta[name=description]')||{}).content||'',og:(document.querySelector('meta[property=\"og:image\"]')||{}).content||''})")
        if len(m['t']) > 70: problems.append(f'long title ({len(m["t"])}) on {u}')
        if not 50 <= len(m['d']) <= 170: problems.append(f'description length {len(m["d"])} on {u}')
        if not m['og']: problems.append(f'no og:image on {u}')
    for l in sorted(links):
        if pg.request.get(l).status >= 400: problems.append(f'broken link: {l}')
    # 4) champion pages fill their panel (a sample)
    random.seed(3)
    for u in random.sample([f'/{r}/{slug(e["c"])}/' for r in ROLES for e in D[r]], 12):
        pg.goto(B + u); pg.wait_for_timeout(700)
        if pg.evaluate("!document.querySelector('#panel h3')||!document.querySelector('#panel h3').textContent.trim()"): problems.append(f'empty panel on {u}')
    # 5) patch notes share pages send people to their card
    sp = [os.path.relpath(r_, PUB) for r_, _, fs in os.walk(os.path.join(PUB, 'patch')) for f in fs if f == 'index.html' and r_.count(os.sep) - PUB.count(os.sep) == 3]
    for rel in sp[:4]:   # a change's own page: keeps its address (the link to share) and opens at its card
        u = f'{B}/{rel}/'.replace(os.sep, '/'); pg.goto(u); pg.wait_for_timeout(700)
        r_ = pg.evaluate("(()=>{const e=document.querySelector('.pn-focus');if(!e)return null;const b=e.getBoundingClientRect();return [b.top,innerHeight,location.pathname]})()")
        if not r_ or not (-5 <= r_[0] < r_[1]) or not r_[2].endswith('/' + rel.split(os.sep)[-1] + '/'): problems.append(f'change page does not open at its card: {rel} {r_}')
    for u in ['/', '/mid/', '/mid/ekko/']: info.append(f'size {u}: {len(pg.request.get(B + u).body()) // 1024} KB')
    if errs: problems.append(f'page errors: {errs[:3]}')
    if bad: problems.append(f'4xx/5xx: {sorted(set(bad))[:5]}')
    b.close()
srv.shutdown()
for x in problems: print('PROBLEM', x)
for x in info: print('info', x)
print('no problems' if not problems else f'{len(problems)} problems')
sys.exit(1 if problems else 0)
