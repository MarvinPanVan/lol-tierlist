"""Make favicon.svg, favicon.ico, apple-touch-icon.png, og.png and og-<role>.png, plus the patch notes link previews
(public/og/patch/<patch>.jpg and <patch>/<change>.jpg, described by build.py in .og_jobs.json) in public/.
Run after build.py whenever the patch or the top picks change: python3 pipeline/scripts/assets.py"""
import os, re, json, shutil, asyncio, io
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # pipeline/
from playwright.async_api import async_playwright
from PIL import Image
PUB=os.path.abspath('../public')
mark=open('assets/mark.svg').read()
shutil.copy('assets/mark.svg',f'{PUB}/favicon.svg')
tpl=open('template.html',encoding='utf-8').read()
patch=re.search(r'class="pill">Patch ([\d.]+)</span>',tpl).group(1)
upd=json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'patch.json')))['updated']
data=json.load(open('tiers.json',encoding='utf-8'))
TR={'Z':0,'S':1,'A':2,'B':3,'C':4,'D':5,'P':6}
COL={'Z':'#fbcd68','S':'#fbaa71','A':'#beaa85','B':'#7fa48f','C':'#638c9a','D':'#5d7094','P':'#ac96c8'}
ROLES=[('top','Top'),('jungle','Jungle'),('mid','Mid'),('adc','ADC'),('support','Support')]
SL=lambda c: re.sub(r'[^a-z0-9]','',c.lower())
IMG=lambda c: f"file://{PUB}/img/champ/{SL(c)}.webp"
def sc(v):
    import math; r=math.floor(v*10+.5)/10   # same rounding as the site
    return ('+' if r>0 else '\u2212' if r<0 else '')+f"{abs(r):.1f}"
rows=''
for r,n in ROLES:
    d=sorted([x for x in data[r] if x['t']!='P'],key=lambda x:(TR[x['t']],-x['score']))[0]
    rows+=f'<div class="r"><span class="rl">{n}</span><span class="cn"><img src="{IMG(d["c"])}">{d["c"]}</span><span class="sc">{sc(d["score"])}</span><span class="tg" style="background:{COL[d["t"]]}">{d["t"]}</span></div>'
fonts=''.join(f"@font-face{{font-family:'{fam}';font-weight:{w};src:url(file://{PUB}/fonts/{f}-latin-{w}-normal.woff2)}}" for fam,f,ws in [('Inter','inter',(400,500,600,700,800)),('Barlow Condensed','barlow-condensed',(600,700,800))] for w in ws)
CSS=f"""{fonts}
body{{margin:0;width:1200px;height:630px;background:radial-gradient(900px 500px at 85% 0%,rgba(251,205,104,.11),transparent 60%),#0b0c0f;color:#eceef2;font-family:Inter;box-sizing:border-box;padding:60px 68px}}
.b{{display:flex;align-items:center;gap:14px;font:800 30px Inter;letter-spacing:-.02em}} .b svg{{width:46px;height:46px}}
h1{{font:800 86px/1 Inter;letter-spacing:-.04em;margin:40px 0 16px}}
p{{font-size:24px;line-height:1.4;color:#959cab;margin:0}} .u{{margin-top:26px;font-size:19px;color:#959cab}}
.card{{background:#14161b;border:1px solid #252830;border-radius:24px;padding:20px 24px}}
.r{{display:grid;grid-template-columns:90px 1fr auto 44px;gap:14px;align-items:center;padding:11px 0;border-top:1px solid #252830}} .r:first-of-type{{border-top:0}}
.rl{{color:#959cab;font-size:19px}} .cn{{display:flex;align-items:center;gap:12px;font:700 27px Inter;letter-spacing:-.02em}} .cn img{{width:42px;height:42px;border-radius:11px}}
.sc{{color:#959cab;font-size:19px;font-weight:600}}
.tg{{font:800 24px 'Barlow Condensed';color:#14151a;border-radius:8px;text-align:center;padding:4px 0}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}} .c{{display:flex;align-items:center;gap:14px;background:#14161b;border:1px solid #252830;border-radius:18px;padding:12px 16px}}
.c img{{width:54px;height:54px;border-radius:13px}} .c b{{font:700 26px Inter;letter-spacing:-.02em;flex:1}} .c span.s{{color:#959cab;font-size:19px;font-weight:600}}"""
og=f'''<html><head><style>{CSS}
body{{display:grid;grid-template-columns:1fr 480px;gap:52px}}</style></head><body><div><div class="b">{mark}LoL Tier List</div><h1>Patch {patch}<br>tier list</h1>
<p>Every role, five stat sites combined. Win rate above the role average, corrected for sample size and one-tricks.</p><div class="u">Updated {upd} &middot; lol-tierlist.pages.dev</div></div>
<div class="card" style="align-self:center"><div style="font:700 17px Inter;color:#959cab;margin-bottom:4px">Best pick per role</div>{rows}</div></body></html>'''
open('/tmp/og.html','w',encoding='utf-8').write(og)
ROLEPAGES={}
for r,n in ROLES:
    L=sorted([x for x in data[r] if x['t']!='P'],key=lambda x:(TR[x['t']],-x['score']))[:6]
    cells=''.join(f'<div class="c"><img src="{IMG(x["c"])}"><b>{x["c"]}</b><span class="s">{sc(x["score"])}</span><span class="tg" style="background:{COL[x["t"]]};width:40px">{x["t"]}</span></div>' for x in L)
    ROLEPAGES[r]=f'''<html><head><style>{CSS}</style></head><body><div style="display:flex;justify-content:space-between;align-items:center"><div class="b">{mark}LoL Tier List</div><div style="font-size:19px;color:#959cab">Patch {patch} &middot; updated {upd}</div></div>
<h1 style="font-size:72px;margin:34px 0 28px">{n} tier list</h1><div class="grid">{cells}</div></body></html>'''
FULL='<svg style="display:block;width:100vw;height:100vh" '
icon='<html><body style="margin:0;background:transparent">'+mark.replace('<svg ',FULL)+'</body></html>'
open('/tmp/icon.html','w').write(icon)
touch='<html><body style="margin:0;background:#16181d">'+mark.replace('rx="15"','rx="0"').replace('<svg ',FULL)+'</body></html>'
open('/tmp/touch.html','w').write(touch)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        pg=await b.new_page(viewport={'width':1200,'height':630})
        await pg.goto('file:///tmp/og.html'); await pg.wait_for_timeout(400)
        await pg.screenshot(path=f'{PUB}/og.png')
        for r,h in ROLEPAGES.items():
            open('/tmp/og_r.html','w',encoding='utf-8').write(h)
            await pg.goto('file:///tmp/og_r.html'); await pg.wait_for_timeout(300)
            await pg.screenshot(path=f'{PUB}/og-{r}.png')
        # link preview pictures for the patch notes (one per change, one per patch): only the ones whose HTML changed
        jobs=json.load(open('.og_jobs.json',encoding='utf-8')) if os.path.exists('.og_jobs.json') else {}
        hp='data/og_hashes.json'; hashes=json.load(open(hp)) if os.path.exists(hp) else {}
        import hashlib; made=0
        for rel,h in jobs.items():
            h=h.replace('__FONTS__',fonts).replace('__MARK__',mark).replace('__PUB__','file://'+PUB)
            k=hashlib.sha1(h.encode()).hexdigest(); out=os.path.join(PUB,rel)
            if hashes.get(rel)==k and os.path.exists(out): continue
            os.makedirs(os.path.dirname(out),exist_ok=True); open('/tmp/og_c.html','w',encoding='utf-8').write(h)
            await pg.goto('file:///tmp/og_c.html'); await pg.wait_for_timeout(250)
            await pg.screenshot(path=out,type='jpeg',quality=84); hashes[rel]=k; made+=1
        ogdir=os.path.join(PUB,'og','patch')   # pictures of changes no longer listed
        for root,_,fs in os.walk(ogdir):
            for f in fs:
                rel=os.path.relpath(os.path.join(root,f),PUB).replace(os.sep,'/')
                if rel not in jobs: os.remove(os.path.join(root,f)); hashes.pop(rel,None)
        json.dump({k:v for k,v in sorted(hashes.items()) if k in jobs},open(hp,'w'),indent=0)
        print(made,'link preview pictures rendered,',len(jobs)-made,'unchanged')
        pg=await b.new_page(viewport={'width':180,'height':180})
        await pg.goto('file:///tmp/touch.html'); await pg.screenshot(path=f'{PUB}/apple-touch-icon.png')
        pngs=[]
        for s in (16,32,48):
            pg=await b.new_page(viewport={'width':s,'height':s})
            await pg.goto('file:///tmp/icon.html'); pngs.append(await pg.screenshot(omit_background=True))
        await b.close()
    ims=[Image.open(io.BytesIO(x)).convert('RGBA') for x in pngs]
    ims[-1].save(f'{PUB}/favicon.ico',sizes=[(16,16),(32,32),(48,48)],append_images=ims[:-1])
asyncio.run(main())
print('assets for patch',patch,'written')
