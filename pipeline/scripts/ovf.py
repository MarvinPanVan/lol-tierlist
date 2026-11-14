import os; os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # run from anywhere; paths are relative to pipeline/
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        pg=await b.new_page(viewport={'width':390,'height':900})
        await pg.route('**/fonts.googleapis.com/**',lambda r: r.abort())
        await pg.goto('file://'+os.path.abspath('../public/index.html')+'#top'); await pg.wait_for_timeout(300)
        r=await pg.evaluate('''[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.right>391}).slice(0,12).map(e=>e.tagName+'.'+e.className+' '+e.id+' right='+Math.round(e.getBoundingClientRect().right))''')
        print('\n'.join(r))
        await b.close()
asyncio.run(main())
