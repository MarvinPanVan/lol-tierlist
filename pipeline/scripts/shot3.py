import os; os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # run from anywhere; paths are relative to pipeline/
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        errs=[]
        for w,h,name,theme,hashv in [(1280,1500,'d_light','light','#mid'),(1280,1500,'d_dark','dark','#jungle'),(390,1700,'m_light','light','#top')]:
            pg=await b.new_page(viewport={'width':w,'height':h})
            pg.on('pageerror',lambda e: errs.append(str(e)))
            await pg.route('**/fonts.googleapis.com/**',lambda r: r.abort())
            await pg.goto('file://'+os.path.abspath('../public/index.html')+''+hashv)
            await pg.evaluate(f"document.documentElement.dataset.theme='{theme}'")
            await pg.wait_for_timeout(300)
            print(name,'scrollW',await pg.evaluate('document.documentElement.scrollWidth'),'chips',await pg.locator('.chip').count())
            await pg.screenshot(path=f'shots/{name}.png',full_page=False)
            if name=='d_light':
                await pg.locator('#fig').scroll_into_view_if_needed(); await pg.wait_for_timeout(200)
                await pg.screenshot(path='shots/d_map.png')
                await pg.locator('#grade').scroll_into_view_if_needed(); await pg.wait_for_timeout(200)
                await pg.screenshot(path='shots/d_grade.png')
            if name=='m_light':
                await pg.locator('.chip').first.click(); await pg.wait_for_timeout(400)
                await pg.screenshot(path='shots/m_sheet.png')
                await pg.fill('#q','yas'); await pg.wait_for_timeout(200)
                print('search results', await pg.locator('#res [data-jr]').count())
        print('errors',errs)
        await b.close()
asyncio.run(main())
