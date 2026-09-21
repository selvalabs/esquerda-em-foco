"""Public source inspection. Full reading extracts are artifact-only, gitignored."""
from __future__ import annotations
import hashlib,json,re,unicodedata
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,urljoin
from urllib.request import Request,urlopen
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data'; A=ROOT/'audit'
INSTITUTIONS=[
 'https://www.alesc.sc.gov.br/deputados/',
 'https://www.alesc.sc.gov.br/agencia/?s=Marquito',
 'https://www.alesc.sc.gov.br/agencia/?s=Carolline',
 'https://www.cmf.sc.gov.br/vereadores',
 'https://www.cmsj.sc.gov.br/vereadores',
 'https://www.cmc.sc.gov.br/vereadores',
 'https://camarablu.sc.gov.br/quem-sao/',
 'https://www.camaragaspar.sc.gov.br/vereadores',
 'https://www.camaracamboriu.sc.gov.br/vereadores',
 'https://www.balneariocamboriu.sc.leg.br/vereadores',
 'https://www.camaratimbo.sc.gov.br/vereadores',
 'https://www.cvi.sc.gov.br/vereadores',
]
BLOCK=['instagram.com','facebook.com','youtube.com','youtu.be','tiktok.com','twitter.com','x.com','wa.me','whatsapp.com','t.me','telegram','kwai','threads','linkedin','insagram.com','queroapoiar.com.br']

def norm(s): return ''.join(c for c in unicodedata.normalize('NFD',s.lower()) if unicodedata.category(c)!='Mn')
def read(task):
 url,kind,ids=task
 out={'url':url,'kind':kind,'candidate_ids':ids}
 try:
  with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=18) as r:
   raw=r.read(2000000); final=r.url; status=r.status
  soup=BeautifulSoup(raw,'html.parser')
  for n in soup(['script','style','noscript','svg']): n.decompose()
  text=soup.get_text(' ',strip=True)
  out.update(status=status,final_url=final,sha256=hashlib.sha256(raw).hexdigest(),title=soup.title.get_text(' ',strip=True) if soup.title else '',text=text[:100000])
  out['links']=[{'label':a.get_text(' ',strip=True)[:120],'url':urljoin(final,a['href'])} for a in soup.select('a[href]') if a.get_text(' ',strip=True)][:220]
 except Exception as e: out['error']=str(e)
 return out

def run():
 if (A/'source-extracts.json').exists(): return
 candidates=json.loads((D/'recorte-sc-2026.json').read_text())
 ids={r['SQ_CANDIDATO'] for r in candidates}
 tasks={u:('institution',[]) for u in INSTITUTIONS}
 for r in json.loads((D/'redes-sc-2026.json').read_text()):
  if r['SQ_CANDIDATO'] not in ids: continue
  u=r['DS_URL'].strip()
  if any(h in u.lower() for h in BLOCK): continue
  if u.upper()==u: u=u.lower()
  if not re.match(r'^https?://',u,re.I): continue
  parts=urlsplit(u); u=urlunsplit((parts.scheme.lower(),parts.netloc.lower(),parts.path,parts.query,''))
  if u not in tasks: tasks[u]=('declared_site',[])
  tasks[u][1].append(r['SQ_CANDIDATO'])
 tasks['https://jeanvolpato.com.br/']=('candidate_site',[])
 with ThreadPoolExecutor(max_workers=6) as pool:
  result=list(pool.map(read,[(u,k,ids) for u,(k,ids) in tasks.items()]))
 follow=[]
 terms=['guesser','jumeri','paulinho','piccoli','fabricio','hilda','cica','volpato','dionisio','sater','camas','gui pereira','sarda','marquito']
 for page in result:
  if page['kind']!='institution': continue
  for link in page.get('links',[]):
   if any(t in norm(link['label']) for t in terms) and urlsplit(link['url']).hostname==urlsplit(page.get('final_url',page['url'])).hostname:
    if link['url'] not in tasks:
     tasks[link['url']]=('institution_profile',[]); follow.append((link['url'],'institution_profile',[]))
 with ThreadPoolExecutor(max_workers=6) as pool: result.extend(pool.map(read,follow[:45]))
 (A/'source-extracts.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 public=[{k:v for k,v in r.items() if k not in ['text','links']} for r in result]
 (A/'source-checks.json').write_text(json.dumps(public,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Sources read:',len(result),'accessible:',sum('text'in r for r in result),flush=True)
if __name__=='__main__': run()
