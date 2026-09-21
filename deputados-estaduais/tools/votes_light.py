"""Read small official result documents. Do not substitute missing totals with zero."""
from pathlib import Path
import concurrent.futures,hashlib,json,re,unicodedata
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'data'; A=ROOT/'audit'
PARTIES={'PCDOB','PDT','PSB','PSOL','PSTU','PT','PV','REDE','UP','PCO'}
def norm(s): return ''.join(c for c in unicodedata.normalize('NFD',str(s).lower()) if unicodedata.category(c)!='Mn')
def save(p,data): Path(p).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def run():
 if (A/'small-results.json').exists(): return
 raw=json.loads((D/'universo-sc-2026.json').read_text()); ids={r['SQ_CANDIDATO'] for r in raw if r['SG_PARTIDO'] in PARTIES}
 history=[r for r in json.loads((D/'historico-sc-2026.json').read_text()) if r['SQ_CANDIDATO_ATUAL'] in ids and int(r['ANO_ELEICAO'])<2026]
 merged=json.loads((D/'votos-historicos.json').read_text()) if (D/'votos-historicos.json').exists() else {}
 groups={}
 for r in history:
  cargo='11' if r['CD_CARGO']=='12' else r['CD_CARGO']; ue=r['SG_UE']; year=r['ANO_ELEICAO']; election=r['CD_ELEICAO']
  key=(year,election,ue,cargo)
  groups.setdefault(key,[]).append(r)
 def fetch(task):
  (year,election,ue,cargo),rows=task
  loc='sc' if ue=='SC' else 'sc'+ue
  fname=f'{loc}-c{int(cargo):04d}-e{int(election):06d}-r.json'
  prefixes=[f'https://resultados.tse.jus.br/oficial/ele{year}/{election}/dados-simplificados/sc/',f'https://resultados.tse.jus.br/oficial/ele{year}/divulgacao/oficial/{election}/dados-simplificados/sc/']
  result={'year':year,'election':election,'unit':ue,'office':cargo,'attempts':[]}; out={}
  for prefix in prefixes:
   url=prefix+fname
   try:
    with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'}),timeout=12) as response: raw=response.read(4000000)
    payload=json.loads(raw); result.update(url=url,sha256=hashlib.sha256(raw).hexdigest(),root_keys=list(payload)[:30] if isinstance(payload,dict) else [])
    entries=[]
    def walk(x,in_candidate_list=False):
     if isinstance(x,dict):
      if ('n' in x or 'nr' in x) and any(v in x for v in ['nv','vap','votos','qtVotosNominais']): entries.append((x,in_candidate_list))
      for k,v in x.items():
       if isinstance(v,(dict,list)): walk(v,in_candidate_list or k.lower() in ['cand','candidatos','candidates'])
     elif isinstance(x,list):
      for y in x: walk(y,in_candidate_list)
    walk(payload)
    result['candidate_entries']=len(entries)
    if entries: result['sample_fields']={k:v for k,v in entries[0][0].items() if not isinstance(v,(dict,list))}
    for r in rows:
     matches=[]
     for entry,candidate_context in entries:
      n=str(entry.get('n',entry.get('nr',''))).lstrip('0'); expected=str(r['NR_CANDIDATO']).lstrip('0')
      if n!=expected: continue
      is_chapa=r['CD_CARGO']=='12'
      public_name=norm(entry.get('nm',entry.get('nome','')))
      expected_names=[norm(r.get('NM_CANDIDATO','')),norm(r.get('NM_URNA_CANDIDATO',''))]
      same_name=public_name and any(public_name==x for x in expected_names)
      same_id=str(entry.get('seq',entry.get('sqcand','')))==r['SQ_CANDIDATO']
      if not (same_name or same_id or (is_chapa and candidate_context)): continue
      value=next((entry[k] for k in ['nv','vap','votos','qtVotosNominais'] if k in entry),None)
      if value is None: continue
      text=str(value).replace('.','').replace(' ','')
      if not re.fullmatch(r'\d+',text): continue
      matches.append((int(text),is_chapa))
     if len(matches)!=1: continue
     total,is_chapa=matches[0]
     key=f"{year}:chapa:{r['SG_UE']}:{r['NR_CANDIDATO']}:{r['NR_TURNO']}" if is_chapa else f"{year}:{r['SQ_CANDIDATO']}:{r['NR_TURNO']}"
     out[key]={'year':year,'candidate_id':r['SQ_CANDIDATO'],'round':r['NR_TURNO'],'votes':total,'source':url,'type':'chapa' if is_chapa else 'nominal','match':'Year, election, office, electoral unit, candidate number, and name or official identifier; vice uses corresponding mayor ticket'}
    result['matched']=len(out)
    if entries: break
   except Exception as e: result['attempts'].append({'url':url,'error':str(e)})
  return out,result
 reports=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
  for found,report in pool.map(fetch,groups.items()):
   merged.update(found); reports.append(report)
   save(D/'votos-historicos.json',merged)
 save(A/'small-results.json',{'documents':reports,'matched_total':len(merged)})
 print('Small official results:',len(merged),'matched totals',flush=True)
if __name__=='__main__': run()
