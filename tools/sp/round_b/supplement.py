"""Recover the initial profile-parser error and retry institutional sources.
No electoral record from Round A is overwritten. All sources are read-only.
"""
from __future__ import annotations
import concurrent.futures, json
from pathlib import Path
from collect import OUT, json_get, now, write, fold

def run():
    marker=OUT/'supplement.json'
    if marker.exists():
        print('Frozen supplementary collection already present.'); return
    candidates=json.loads(Path('data/sp/normalized.json').read_text())['candidates']
    report={'started_at':now(),'errors':[],'attempts':[], 'correction':'The initial DivulgaCand probe raised KeyError on an absent optional field. This is a parser error, not evidence that the official endpoint is unavailable.'}
    details={}
    def detail(c):
        url='https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura/buscar/2026/SP/20322002026/candidato/'+c['id']
        try:
            obj,meta=json_get(url,timeout=20,retries=2)
            identity=str(obj.get('id'))==c['id'] and fold(obj.get('nomeCompleto',''))==fold(c['full_name'])
            allowed=['id','nomeUrna','nomeCompleto','numero','descricaoSituacao','descricaoTotalizacao','descricaoSituacaoComplementar','fotoUrl','stReeleicao','ocupacao']
            public={k:obj[k] for k in allowed if k in obj and isinstance(obj[k],(str,int,float,bool,type(None)))}
            public['source']=meta; public['identity_verified']=identity
            if not identity: public['error']='identity_mismatch_or_missing_fields'
            return c['id'],public
        except Exception as exc: return c['id'],{'source_url':url,'retrieved_at':now(),'error':str(exc),'identity_verified':False}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for cid,record in pool.map(detail,candidates): details[cid]=record
    write(OUT/'divulgacand-profiles.json',details)
    report['divulgacand']={'attempted':len(details),'identity_verified':sum(d.get('identity_verified',False) for d in details.values()),'errors':sum('error' in d for d in details.values()),'initial_attempt_preserved':'divulgacand-checks.json'}
    print('DivulgaCand '+json.dumps(report['divulgacand']),flush=True)
    listing=[]; pages=[]
    for start in ['https://dadosabertos.camara.leg.br/api/v2/deputados?siglaUf=SP&itens=100', 'https://dadosabertos.camara.leg.br/api/v2/deputados?itens=100']:
        try:
            url=start; temporary=[]; meta_pages=[]
            while url:
                body,meta=json_get(url,timeout=45,retries=1); meta_pages.append(meta)
                temporary.extend(x for x in body['dados'] if x.get('siglaUf')=='SP')
                url=next((l['href'] for l in body.get('links',[]) if l.get('rel')=='next'),None)
                if len(meta_pages)>10: raise ValueError('unexpected pagination')
            listing=temporary; pages=meta_pages; report['attempts'].append({'url':start,'status':'success'}); break
        except Exception as exc:
            report['attempts'].append({'url':start,'status':'failed','error':str(exc)})
    profiles=[]; matches={}
    def deputy(d):
        try:
            obj,meta=json_get(d['uri'],timeout=25,retries=1); x=obj['dados']; s=x.get('ultimoStatus',{})
            return {'id':str(x['id']),'nomeCivil':x.get('nomeCivil'),'nome':s.get('nome'),'nomeEleitoral':s.get('nomeEleitoral'),'situacao':s.get('situacao'),'condicaoEleitoral':s.get('condicaoEleitoral'),'dataSituacao':s.get('data'),'siglaUf':s.get('siglaUf'),'siglaPartido':s.get('siglaPartido'),'redeSocial':x.get('redeSocial',[]),'urlWebsite':x.get('urlWebsite'),'source':meta,'public_url':'https://www.camara.leg.br/deputados/'+str(x['id'])}
        except Exception as exc:return {'id':str(d['id']),'source_url':d['uri'],'error':str(exc)}
    if listing:
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool: profiles=list(pool.map(deputy,listing))
        for c in candidates:
            found=[p for p in profiles if p.get('nomeCivil') and fold(p['nomeCivil'])==fold(c['full_name'])]
            if len(found)==1: matches[c['id']]={'identity_method':'exact_normalized_civil_name','profile':found[0]}
            elif len(found)>1:report['errors'].append({'kind':'ambiguous_camara_identity','id':c['id']})
    write(OUT/'camara-retry-public.json',profiles); write(OUT/'camara-retry-matches.json',matches)
    report['camara']={'pages':pages,'listing':len(listing),'profiles_success':sum('error' not in p for p in profiles),'exact_matches':len(matches),'limitation':'No match is not evidence of never having exercised a mandate. Use exact civil-name match; no fuzzy association.'}
    report['completed_at']=now();write(marker,report)
    print(json.dumps({'divulgacand':report['divulgacand'],'camara':report['camara'],'errors':report['errors']},ensure_ascii=False,indent=2))
if __name__=='__main__':run()
