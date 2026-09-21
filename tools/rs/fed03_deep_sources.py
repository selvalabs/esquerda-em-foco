"""Read only explicitly discovered public URLs. No login, CAPTCHA bypass or inference.
Full reading text is ephemeral CI evidence; only availability metadata is committed.
"""
import asyncio,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/rs/fed03';OUT.mkdir(parents=True,exist_ok=True)
SOURCES=[
('210002533912','https://sapl.pelotas.rs.leg.br/materia/44476'),
('210002533912','https://sapl.pelotas.rs.leg.br/materia/49598'),
('210002533912','https://sapl.pelotas.rs.leg.br/materia/46981'),
('210002534602','https://sapl.camaranh.rs.gov.br/materia/33401'),
('210002534602','https://sapl.camaranh.rs.gov.br/materia/35461'),
('210002534599','https://www.camarasvp.rs.gov.br/proposicoes/Pedidos-de-Providencia/2019/1/20'),
('210002535915','https://www.camarajaguarao.rs.gov.br/proposicoes/Projeto-de-Lei-do-Legislativo/0/1/30'),
('210002534595','https://perola1350.com.br/'),
('210002534591','https://www.miriammarroni.com/'),
('210002534605','https://www.camara.leg.br/deputados/73683/biografia'),
('210002535907','https://www.santanadolivramento.rs.leg.br/institucional/noticias/noticias-20206/rafael/apresentacao-de-projeto-arquitetonico'),
('210002537071','https://www.camaravacaria.rs.gov.br/'),
('210002533912','https://sapl.pelotas.rs.leg.br/parlamentar/'),
]
async def run():
 results=[];now=datetime.now(timezone.utc).isoformat()
 async with async_playwright() as pw:
  browser=await pw.chromium.launch();semaphore=asyncio.Semaphore(3)
  async def inspect(pair):
   async with semaphore:
    cid,url=pair;row={'candidate_id':cid,'url':url,'checked_at':now};page=await browser.new_page()
    try:
     response=await page.goto(url,wait_until='domcontentloaded',timeout=22000)
     await page.wait_for_timeout(1400)
     row.update({'status':response.status if response else None,'title':await page.title(),'final_url':page.url})
     text=await page.locator('body').inner_text(timeout=5000)
     row.update({'text_chars':len(text),'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'reading_text':text[:48000]})
     row['links']=await page.locator('a[href]').evaluate_all('(xs)=>xs.map(a=>({label:a.innerText.slice(0,120),url:a.href})).slice(0,300)')
     lower=text.lower()
     row['access_limitation']='challenge_or_access_block' if any(x in lower for x in ['bot verification','verify you are human','access denied','attention required!']) else 'empty_or_shell' if len(text.strip())<100 else None
    except Exception as e:row['error']=str(e)
    finally:await page.close()
    return row
  results=await asyncio.gather(*(inspect(p) for p in SOURCES));await browser.close()
 Path('/tmp/rs-fed03-deep-reading.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
 (OUT/'deep-source-availability.json').write_text(json.dumps([{k:v for k,v in r.items() if k not in ('reading_text','links')} for r in results],ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'attempted':len(results),'readable_without_detected_challenge':sum(bool(r.get('reading_text')) and not r.get('access_limitation') for r in results)}))
asyncio.run(run())
