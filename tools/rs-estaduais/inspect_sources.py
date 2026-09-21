"""Read-only supplemental research. Review excerpts stay outside the repository.
No account login, form submission, posting, source mutation or automatic agenda
assignment occurs. Only declared public hosts are navigated. Public summaries
must be authored separately after a source-level editorial review.
"""
from __future__ import annotations
import asyncio
import hashlib
import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais'
OUT=Path('/tmp/rs-state-source-review')

async def run():
    OUT.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location('source_safety',ROOT/'tools/rs-estaduais/research.py')
    safety=importlib.util.module_from_spec(spec);spec.loader.exec_module(safety)
    records={r['SQ_CANDIDATO']:r for r in json.loads((D/'candidates-official.json').read_text())}
    audits=json.loads((D/'web-research.json').read_text())
    tasks=[]
    for cid,row in audits.items():
        for site in row['websites']:
            if site.get('read') and 'flickr.com' not in site.get('final_url',''):
                tasks.append((cid,site.get('final_url') or site['url']))
    sem=asyncio.Semaphore(3)
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        async def inspect(cid,address):
            async with sem:
                result={'candidate_id':cid,'name':records[cid]['NM_URNA_CANDIDATO'],'url':address,'checked_at':datetime.now(timezone.utc).isoformat()}
                context=await browser.new_context(service_workers='block')
                host=urlsplit(address).hostname
                permitted={host,host.removeprefix('www.'),'www.'+host.removeprefix('www.')}
                await context.route('**/*',lambda route:route.continue_() if urlsplit(route.request.url).hostname in permitted and route.request.url.startswith(('https://','http://')) and route.request.method=='GET' else route.abort())
                page=await context.new_page()
                try:
                    if not safety.normalize_url(address):raise ValueError('Invalid public URL')
                    await asyncio.to_thread(safety.public_address,address)
                    response=await page.goto(address,wait_until='domcontentloaded',timeout=20000)
                    await page.wait_for_timeout(1000)
                    body=await page.locator('body').inner_text(timeout=5000)
                    result.update({'status':response.status if response else None,'final_url':page.url,'body_sha256':hashlib.sha256(body.encode()).hexdigest(),'title':await page.title()})
                    # Small internal review windows. No raw webpage content is committed.
                    lines=[re.sub(r'\s+',' ',x).strip() for x in body.splitlines()]
                    lines=[x for x in lines if x and '@' not in x and not re.search(r'\b(?:cnpj|whatsapp|cookies|telefone|comitê|copyright)\b',x,re.I)]
                    compact='\n'.join(lines)
                    result['opening_review_window']=' '.join(compact.split()[:140])
                    matches=list(re.finditer(r'(?:Minhas lutas|Nossas lutas|Nossas propostas|Propostas para|Compromissos para|Bandeiras|Prioridades|Saúde|Educação|Agricultura|Meio ambiente|Reconstrução)',compact,re.I))
                    windows=[]
                    for m in matches:
                        if any(abs(m.start()-start)<220 for start,_ in windows):continue
                        text=' '.join(compact[m.start():].split()[:90])
                        windows.append((m.start(),text))
                        if len(windows)==4:break
                    result['policy_review_windows']=[text for _,text in windows]
                    result['links']=await page.locator('a[href]').evaluate_all("els=>els.map(a=>({label:(a.innerText||'').trim(),url:a.href})).filter(x=>/propost|compromiss|biograf|quem|trajet|manifest|bandeir/i.test(x.label)).slice(0,10)")
                except Exception as exc:result['error']=str(exc)
                await context.close()
                return result
        output=await asyncio.gather(*(inspect(cid,address) for cid,address in tasks))
        await browser.close()
    (OUT/'source-review.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'sites_inspected':len(output),'read_successfully':sum('body_sha256' in x for x in output),'output':'temporary review artifact only'}))

if __name__=='__main__':asyncio.run(run())
