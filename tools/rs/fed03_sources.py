"""Retrieve public HTML for editorial reading; never assigns political topics.
Only availability metadata is committed. Temporary text goes to the CI artifact,
not to public site data. PDFs and oversized payloads are not parsed here.
"""
from __future__ import annotations
import concurrent.futures, hashlib, json, urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]; D=ROOT/'data/rs'; OUT=ROOT/'docs/rs/fed03'; OUT.mkdir(parents=True,exist_ok=True)
NOW=datetime.now(timezone.utc).isoformat()
EXTRA={
 '210002535914':['https://www.geledes.org.br/a-mocao-de-recomendacao-ao-governador-do-estado-para-a-recriacao-da-secretaria-de-politicas-para-mulheres/'],
 '210002535915':['https://www.camarajaguarao.rs.gov.br/proposicoes/Projeto-de-Lei-do-Legislativo/0/1/30','https://www.camarajaguarao.rs.gov.br/camara/membros/show/30'],
 '210002535925':['https://www.pelotas.rs.leg.br/noticia/projeto-de-lei-da-vereadora-cristina-oliveira-pretende-proibir-a-venda-de-fogos-barulhentos-em-pelotas/d125d448f92447eca27325ba89a15509','https://sapl.pelotas.rs.leg.br/parlamentar/69'],
 '210002533912':['https://sapl.pelotas.rs.leg.br/parlamentar/'],
 '210002535907':['https://sapl.santanadolivramento.rs.leg.br/parlamentar/46'],
}
def main():
 records=json.loads((D/'normalized.json').read_text())['candidates'];targets={t['id'] for t in json.loads((D/'rs-fed-03-targets.json').read_text())['targets']}
 pairs={(c['id'],s['url']) for c in records if c['id'] in targets for s in c.get('sites',[]) if urllib.parse.urlsplit(s['url']).hostname}
 pairs.update((cid,u) for cid,urls in EXTRA.items() for u in urls)
 def collect(pair):
  cid,address=pair;result={'candidate_id':cid,'url':address,'checked_at':NOW}
  try:
   req=urllib.request.Request(address,headers={'User-Agent':'Mozilla/5.0 (compatible; public source audit)','Accept':'text/html'})
   with urllib.request.urlopen(req,timeout=18) as response:
    raw=response.read(2000001);ctype=response.headers.get('Content-Type','');result.update({'status':response.status,'final_url':response.geturl(),'content_type':ctype})
   if len(raw)>2000000:raise ValueError('Size limit reached')
   if b'%PDF' in raw[:8] or 'pdf' in ctype:raise ValueError('PDF requires separate visual review')
   soup=BeautifulSoup(raw,'html.parser');result['sha256']=hashlib.sha256(raw).hexdigest();result['title']=soup.title.get_text(' ',strip=True) if soup.title else ''
   for tag in soup.select('script,style,nav,header,footer,noscript'):tag.decompose()
   main=soup.select_one('main') or soup.select_one('article') or soup
   text=main.get_text('\n',strip=True);result['text_chars']=len(text)
   result['reading_text']=text[:60000]
   result['discovered_links']=[{'text':a.get_text(' ',strip=True)[:150],'url':urllib.parse.urljoin(address,a['href'])} for a in main.select('a[href]')][:250]
  except Exception as exc:result['error']=str(exc)
  return result
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(collect,sorted(pairs)))
 metadata=[{k:v for k,v in r.items() if k not in ('reading_text','discovered_links')} for r in rows]
 (OUT/'source-availability.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
 Path('/tmp/rs-fed03-source-reading.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'attempted':len(rows),'readable':sum('reading_text' in r for r in rows),'note':'Availability is not identity confirmation or editorial acceptance.'}))
if __name__=='__main__':main()
