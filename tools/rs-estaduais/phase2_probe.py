"""Read public institutional pages and expose review locators, never infer a mandate.
No login, form submission, private-network requests or source writes. Raw page
text is kept only in a short-lived review artifact, not the repository/site.
"""
from __future__ import annotations
import asyncio
import hashlib
import ipaddress
import json
import re
import socket
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from playwright.async_api import async_playwright

OUT=Path('/tmp/rs-phase2-probe')
URLS=[
 'https://ww4.al.rs.gov.br/deputados',
 'https://www.al.rs.gov.br/deputados',
 'https://camara-sm.rs.gov.br/',
 'https://camara-sm.rs.gov.br/vereadores',
 'https://www.camarapf.rs.gov.br/',
 'https://www.camarapf.rs.gov.br/vereador/view/662',
 'https://erechim.rs.leg.br/vereadores',
 'https://www.camaracanoas.rs.gov.br/',
 'https://www.camaracaxias.rs.gov.br/',
 'https://www.camarapelotas.rs.gov.br/',
 'https://www.legislativotaquara.rs.gov.br/',
]

def public_host(host):
    if not host:return False
    try:return all(ipaddress.ip_address(item[4][0]).is_global for item in socket.getaddrinfo(host,None,type=socket.SOCK_STREAM))
    except OSError:return False

async def run():
    OUT.mkdir(parents=True,exist_ok=True)
    limits=asyncio.Semaphore(3)
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        async def inspect(url):
            async with limits:
                data={'url':url,'checked_at':datetime.now(timezone.utc).isoformat(),'responses':[]}
                ctx=await browser.new_context(service_workers='block')
                allowed={};jobs=[]
                async def route(r):
                    parsed=urlsplit(r.request.url)
                    host=parsed.hostname or ''
                    if host not in allowed:allowed[host]=await asyncio.to_thread(public_host,host)
                    if parsed.scheme not in ('http','https') or not allowed[host] or r.request.method!='GET':await r.abort();return
                    if r.request.resource_type in ('image','font','media'):await r.abort();return
                    await r.continue_()
                await ctx.route('**/*',route)
                page=await ctx.new_page()
                async def response(resp):
                    address=resp.url
                    content_type=resp.headers.get('content-type','')
                    if 'json' not in content_type or not any(token in address.lower() for token in ('deput','parlam','vereador','bancada')):return
                    try:
                        raw=await resp.body()
                        if len(raw)>2_000_000:return
                        value=json.loads(raw)
                        # No full personnel records: discover schemas and exact public-role fields only.
                        allowed_keys={'id','nome','nomeCivil','nomeCompleto','nomeParlamentar','nomeVereador','nomeDeputado','nome_deputado','siglaPartido','partido','situacao','status','emExercicio','exercicio','ativo','titular','legislatura','licenciado','idDeputado','id_deputado','idParlamentar','codParlamentar','cod_deputado','url','slug'}
                        def project(obj):
                            if isinstance(obj,list):return [project(x) for x in obj[:150]]
                            if isinstance(obj,dict):return {k:(project(v) if isinstance(v,(dict,list)) else v) for k,v in obj.items() if k in allowed_keys or isinstance(v,(dict,list))}
                            return obj
                        data['responses'].append({'url':address,'status':resp.status,'sha256':hashlib.sha256(raw).hexdigest(),'keys':list(value)[:30] if isinstance(value,dict) else None,'public_projection':project(value)})
                    except Exception as exc:data['responses'].append({'url':address,'error':str(exc)})
                page.on('response',lambda resp:jobs.append(asyncio.create_task(response(resp))))
                try:
                    resp=await page.goto(url,wait_until='domcontentloaded',timeout=35000)
                    await page.wait_for_timeout(1800)
                    body=await page.locator('body').inner_text(timeout=5000)
                    data.update({'status':resp.status if resp else None,'final_url':page.url,'title':await page.title(),'body_sha256':hashlib.sha256(body.encode()).hexdigest()})
                    lines=[line.strip() for line in body.splitlines() if line.strip() and '@' not in line and not re.search(r'\d{3,}.*\d{3,}',line)]
                    data['body_review']='\n'.join(lines)[:24000]
                    data['links']=await page.locator('a[href]').evaluate_all("els=>els.map(a=>({url:a.href,text:(a.innerText||'').trim()})).filter(x=>/deputad|parlament|vereador|legislatura|comiss|sandra|alice|helen|callegaro|regina|lorenzato/i.test(x.url+' '+x.text)).slice(0,120)")
                    data['scripts']=await page.locator('script[src]').evaluate_all('els=>els.map(x=>x.src)')
                    if jobs:await asyncio.gather(*jobs,return_exceptions=True)
                except Exception as exc:data['error']=str(exc)
                await ctx.close();return data
        output=await asyncio.gather(*(inspect(url) for url in URLS))
        await browser.close()
    (OUT/'probe.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'pages':len(output),'read':sum('body_sha256' in d for d in output),'artifact':'temporary review only'}))

if __name__=='__main__':asyncio.run(run())
