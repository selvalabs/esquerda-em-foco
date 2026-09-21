"""Read-only legislative evidence collector. No policy positions inferred here."""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, json, time, urllib.parse, urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
API='https://dadosabertos.camara.leg.br/api/v2/'
def now():return datetime.now(timezone.utc).isoformat()
def get(url):
 errors=[]
 for attempt in range(2):
  try:
   req=urllib.request.Request(url,headers={'Accept':'application/json','User-Agent':'EsquerdaEmFoco evidence audit'})
   with urllib.request.urlopen(req,timeout=25) as response:raw=response.read(5_000_001)
   if len(raw)>5_000_000:raise ValueError('Response exceeds bound')
   return {'url':url,'checked_at':now(),'sha256':hashlib.sha256(raw).hexdigest(),'data':json.loads(raw)}
  except Exception as exc:errors.append(str(exc));time.sleep(1)
 return {'url':url,'checked_at':now(),'errors':errors}
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
 collection={'generated_at':now(),'selection':'PEC 221/2019, conjunto das votações disponíveis para revisão; votação de mérito e requerimentos permanecem separados.','responses':{}}
 sources={'proposition':API+'proposicoes/2233802','proposition_votes':API+'proposicoes/2233802/votacoes','plenary_day':API+'votacoes?dataInicio=2026-05-27&dataFim=2026-05-27&siglaOrgao=PLEN&itens=100&ordem=ASC&ordenarPor=dataHoraRegistro'}
 for key,url in sources.items():collection['responses'][key]=get(url)
 vote_ids=set()
 for key in ('proposition_votes','plenary_day'):
  for v in collection['responses'][key].get('data',{}).get('dados',[]):
   if v.get('id') and str(v.get('data','')).startswith('2026-05-27'):vote_ids.add(str(v['id']))
 # Max 60 vote objects, explicit bounded review set, no claim of a full mandate inventory.
 requests={}
 for vid in sorted(vote_ids)[:60]:
  requests[vid+':detail']=API+'votacoes/'+urllib.parse.quote(vid)
  requests[vid+':votes']=API+'votacoes/'+urllib.parse.quote(vid)+'/votos'
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for key,response in zip(requests,pool.map(get,requests.values())):collection['responses'][key]=response
 current=json.loads((ROOT/'data/pr/camara-records.json').read_text())
 for cid,c in current.items():
  collection['responses'][cid+':current']=get(API+'deputados/'+str(c['deputy_id']))
 (out/'legislative-evidence.json').write_text(json.dumps(collection,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'vote_ids':len(vote_ids),'responses':len(collection['responses']),'errors':sum('errors' in r for r in collection['responses'].values())}))
if __name__=='__main__':main()
