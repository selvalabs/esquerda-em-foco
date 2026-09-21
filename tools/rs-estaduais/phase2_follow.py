"""Read-only public-source follow-up; no login, forms, private hosts or writes.
Review excerpts are short-lived artifact material, not published candidate text.
"""
from __future__ import annotations
import asyncio,hashlib,importlib.util,json,re
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[2]
OUT=Path('/tmp/rs-phase2-follow')
URLS=['https://nossaspropostas.netlify.app/','https://humbertomatos.com.br/','https://xn--garomroni-s3a.com.br/','https://queroapoiar.com.br/MARIAEUNICE','https://www.camarapf.rs.gov.br/vereador/view/672','https://www.camarapf.rs.gov.br/vereador/view/662','https://www.camarapf.rs.gov.br/vereador/view/669','https://www.erechim.rs.leg.br/mandatos','https://www.erechim.rs.leg.br/mesa-diretora','https://www.pelotas.rs.leg.br/vereador/fernanda-miranda','https://www.pelotas.rs.leg.br/','https://www.camarataquara.rs.gov.br/camara/membros/show/12','https://www.camarataquara.rs.gov.br/camara/membros','https://monicafacio.com.br/','https://www.camaracanoas.rs.gov.br/']
async def run():
    OUT.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location('public_source_safety',ROOT/'tools/rs-estaduais/phase2_probe.py');safety=importlib.util.module_from_spec(spec);spec.loader.exec_module(safety)
    sem=asyncio.Semaphore(3)
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        async def inspect(url):
            async with sem:
                item={'url':url,'checked_at':datetime.now(timezone.utc).isoformat()};context=await browser.new_context(service_workers='block');cache={}
                async def route(r):
                    parsed=urlsplit(r.request.url);host=parsed.hostname or ''
                    if host not in cache:cache[host]=await asyncio.to_thread(safety.public_host,host)
                    if parsed.scheme not in ('http','https') or not cache[host] or r.request.method!='GET' or r.request.resource_type in ('image','font','media'):
                        await r.abort();return
                    await r.continue_()
                await context.route('**/*',route);page=await context.new_page()
                try:
                    response=await page.goto(url,wait_until='domcontentloaded',timeout=25000);await page.wait_for_timeout(1500)
                    body=await page.locator('body').inner_text(timeout=5000)
                    item.update({'status':response.status if response else None,'final_url':page.url,'title':await page.title(),'body_sha256':hashlib.sha256(body.encode()).hexdigest()})
                    lines=[line.strip() for line in body.splitlines() if line.strip() and '@' not in line and not re.search(r'\d{3,}.*\d{3,}',line)]
                    item['body_review']='\n'.join(lines)[:32000]
                    item['links']=await page.locator('a[href]').evaluate_all("els=>els.map(a=>({url:a.href,text:(a.innerText||'').trim()})).filter(x=>/propost|document|projet|mandat|vereador|parlament|legislatura|regina|eva|marina|sandra|monica|mônica|fernanda|impositiv|comiss/i.test(x.url+' '+x.text)).slice(0,100)")
                except Exception as exc:item['error']=str(exc)
                await context.close();return item
        output=await asyncio.gather(*(inspect(url) for url in URLS));await browser.close()
    (OUT/'follow.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'source_count':len(output),'read_count':sum('body_sha256' in x for x in output),'use':'temporary source review only'}))
if __name__=='__main__':asyncio.run(run())
