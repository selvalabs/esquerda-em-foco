"""Read-only, bounded AD3 follow-up. Nothing here updates a policy or vote total.
Temporary text is for review only. Public metadata is projected before export.
"""
from __future__ import annotations
import asyncio, collections, concurrent.futures, hashlib, importlib.util, json, re, urllib.parse
from datetime import datetime,timezone
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2];OUT=Path('/tmp/rs-ad3-follow');D=ROOT/'data/rs-estaduais'
spec=importlib.util.spec_from_file_location('ad3_safe',ROOT/'tools/rs-estaduais/research.py');safe=importlib.util.module_from_spec(spec);spec.loader.exec_module(safe)
URLS={
 'https://sapl.uruguaiana.rs.leg.br/parlamentar/':'210002539807',
 'https://sapl.uruguaiana.rs.leg.br/parlamentar/210':'210002539807',
 'https://sapl.esteio.rs.leg.br/parlamentar/':'210002537544',
 'https://www.esteio.rs.leg.br/amaral-negrito':'210002537544',
 'https://sapl.saojeronimo.rs.leg.br/parlamentar/':'210002539795',
 'https://sapl.saojeronimo.rs.leg.br/parlamentar/42':'210002539795',
 'https://www.camaracq.rs.gov.br/vereador/joao-pedro-grill-3395':'210002537545',
 'https://www.camararosariodosul.rs.gov.br/atas/sessao_solene/2026/1/0/461':'210002539779',
 'https://www.camararosariodosul.rs.gov.br/proposicoes/Convocacao-/0/1/0/8324':'210002539779',
 'https://camaracrz.rs.gov.br/bruno-berte/pt_BR/projetos/331235/':'210002539801',
 'https://lucianoorsi.com.br/pages/compromissos.html':'210002539806',
 'https://nelsongrasselli.com.br/quem-e-grasselli':'210002534015',
 'https://grupoahora.net.br/conteudos/2026/07/25/maneco-hassen-e-confirmado-como-candidato-a-deputado-estadual-pelo-pt-2/':'210002534007',
 'https://ww4.al.rs.gov.br/deputados':'alrs-current-directory',
 'https://www.camarataquara.rs.gov.br/camara/membros/show/12':'210002534011',
 'https://www.camarasapiranga.rs.gov.br/camara/membros/show/12':'210002534042'}

def clean(body):
    lines=[line for line in body.splitlines() if '@' not in line and not re.search(r'\bCPF\b|CNPJ|\d{3}\.\d{3}\.\d{3}-\d{2}|\b\d{11}\b|\(\d{2}\)\s?\d|doadores|Chave PIX',line,re.I)]
    return ' '.join(('\n'.join(lines)).split()[:2000])

async def browser_reads():
    from playwright.async_api import async_playwright
    sem=asyncio.Semaphore(3)
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        async def inspect(item):
            url,cid=item
            async with sem:
                row={'url':url,'candidate_id':cid,'checked_at':datetime.now(timezone.utc).isoformat(),'read':False,'editorial_verified':False}
                context=await browser.new_context(service_workers='block')
                # Navigation must stay public; never submit forms or POST requests.
                async def route_handler(route):
                    address=route.request.url
                    if route.request.method!='GET' or not safe.normalize_url(address):return await route.abort()
                    if route.request.is_navigation_request():
                        try:await asyncio.to_thread(safe.public_address,address)
                        except Exception:return await route.abort()
                    await route.continue_()
                await context.route('**/*',route_handler)
                page=await context.new_page()
                try:
                    await asyncio.to_thread(safe.public_address,url)
                    response=await page.goto(url,wait_until='domcontentloaded',timeout=20000)
                    await page.wait_for_timeout(2000)
                    text=await page.locator('body').inner_text(timeout=6000)
                    row.update({'http_status':response.status if response else None,'final_url':page.url,'rendered_sha256':hashlib.sha256(text.encode()).hexdigest()})
                    if re.search(r'captcha|verifica.{0,30}rob[oô]|access denied|just a moment|verify you are human|verificando sua conex',text[:3000],re.I):row['outcome']='access_interstitial'
                    else:
                        row.update({'read':True,'outcome':'rendered_body_requires_review','review_text':clean(text)})
                        row['links']=await page.locator('a[href]').evaluate_all("els=>els.map(a=>({label:(a.innerText||'').trim().slice(0,100),url:a.href})).filter(x=>/mandat|legislatura|projeto|ativo|parlament|braite|amaral|danrlei|sistcop/i.test(x.label)).slice(0,35)")
                except Exception as exc:row['outcome']='read_failed';row['error_type']=type(exc).__name__
                await context.close()
                return row
        results=await asyncio.gather(*(inspect(item) for item in URLS.items()));await browser.close()
    return results

def historical(row):
    review=row['historical_registration_review'];url=review['source_url'];result={'candidate_id':row['candidate_id'],'historical_id':row['historical_id'],'source_url':url,'checked_at':datetime.now(timezone.utc).isoformat(),'nominal_total_verified':False}
    try:
        raw,final,status,mime=safe.read(url,15);data=json.loads(raw)
        if str(data.get('id'))!=str(row['historical_id']):raise ValueError('Historical ID mismatch')
        allowed=('id','numero','nomeUrna','nomeCompleto','cargo','eleicao','descricaoSituacao','descricaoTotalizacao','descricaoSituacaoCandidato')
        result.update({'read':True,'source_sha256':hashlib.sha256(raw).hexdigest(),'public_projection':{k:data[k] for k in allowed if k in data},'available_top_level_keys':[k for k in data if re.search(r'voto|elei|total|turno|urna|quant',k,re.I)]})
    except Exception as exc:result.update({'read':False,'error_type':type(exc).__name__})
    return result

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    results=asyncio.run(browser_reads())
    rows=[r for r in json.loads((ROOT/'docs/rs-estaduais/ad2-close/historical-vote-pendencies.json').read_text()) if r['requires_nominal_research']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:history=list(pool.map(historical,rows))
    (OUT/'follow.json').write_text(json.dumps({'sources':results,'historical':history,'automatic_changes':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'source_count':len(results),'historical_count':len(history),'outcomes':dict(collections.Counter(x['outcome'] for x in results))}))
if __name__=='__main__':main()
