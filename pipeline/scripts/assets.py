"""Make favicon.svg, favicon.ico, apple-touch-icon.png and og.png (link preview) in public/.
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
upd=re.search(r'class="pill">Updated ([^<]+)</span>',tpl).group(1)
data=json.load(open('tiers.json',encoding='utf-8'))
TR={'Z':0,'S':1,'A':2,'B':3,'C':4,'D':5,'P':6}
COL={'Z':'#ff4fbf','S':'#ff6b6b','A':'#ff9f43','B':'#ffd23f','C':'#a6dc5c','D':'#6db3ff','P':'#b99dff'}
ROLES=[('top','Top'),('jungle','Jungle'),('mid','Mid'),('adc','ADC'),('support','Support')]
rows=''
for r,n in ROLES:
    d=sorted([x for x in data[r] if x['t']!='P'],key=lambda x:(TR[x['t']],-x['score']))[0]
    s=('+' if d['score']>0 else '−' if d['score']<0 else '')+f"{abs(d['score']):.1f}"
    rows+=f'<div class="r"><span class="rl">{n}</span><span class="cn">{d["c"]}</span><span class="sc">{s}</span><span class="tg" style="background:{COL[d["t"]]}">{d["t"]}</span></div>'
fonts=''.join(f"@font-face{{font-family:'{fam}';font-weight:{w};src:url(file://{PUB}/fonts/{f}-latin-{w}-normal.woff2)}}" for fam,f,ws in [('Inter','inter',(400,500,600,700)),('Barlow Condensed','barlow-condensed',(600,700,800))] for w in ws)
og=f'''<html><head><style>{fonts}
body{{margin:0;width:1200px;height:630px;background:#0f1013;color:#ededf0;font-family:Inter;display:grid;grid-template-columns:1fr 470px;gap:56px;padding:64px 72px;box-sizing:border-box}}
.b{{display:flex;align-items:center;gap:14px;font:800 34px 'Barlow Condensed'}} .b svg{{width:48px;height:48px}}
h1{{font:800 104px/0.95 'Barlow Condensed';margin:46px 0 18px;letter-spacing:-1px}}
p{{font-size:25px;line-height:1.4;color:#9da1aa;margin:0}} .u{{margin-top:30px;font-size:20px;color:#9da1aa}}
.card{{background:#17191e;border:1px solid #272a31;border-radius:22px;padding:22px 26px;align-self:center}}
.card h2{{font:800 30px 'Barlow Condensed';margin:0 0 6px}}
.r{{display:grid;grid-template-columns:96px 1fr auto 46px;gap:14px;align-items:center;padding:13px 0;border-top:1px solid #272a31}} .r:first-of-type{{border-top:0}}
.rl{{color:#9da1aa;font-size:20px}} .cn{{font:700 32px 'Barlow Condensed'}} .sc{{color:#9da1aa;font-size:20px}}
.tg{{font:800 24px 'Barlow Condensed';color:#121316;border-radius:7px;text-align:center;padding:3px 0}}
</style></head><body><div><div class="b">{mark}LoL Tier List</div><h1>Patch {patch} tier list</h1>
<p>Every role, built from nine stat sites. Win rate above the role average, corrected for sample size and one-tricks.</p><div class="u">Updated {upd} &middot; lol-tierlist.pages.dev</div></div>
<div class="card"><h2>Best pick per role</h2>{rows}</div></body></html>'''
open('/tmp/og.html','w',encoding='utf-8').write(og)
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
