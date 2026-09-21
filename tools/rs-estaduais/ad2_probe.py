"""Read-only A-D.2 inspection; outputs are temporary review artifacts, not facts.
Only public source pages and explicitly projected electoral fields are retained.
No login, posting, form submission, registry mutation or automatic office/policy
assignment occurs. Failed retrievals remain failures, not negative conclusions.
"""
from __future__ import annotations
import concurrent.futures
import hashlib
import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/rs-estaduais'
OUT=Path('/tmp/rs-ad2-probe')
SOURCES=[
'https://www.camaracq.rs.gov.br/vereador/joao-pedro-grill-3395',
'https://camarasa.rs.gov.br/vereador/gilberto-corazza',
'https://www.camarataquara.rs.gov.br/camara/membros/show/12',
'https://www.camarasapiranga.rs.gov.br/camara/membros/show/12',
'https://www.al.rs.gov.br/deputados/ListadeDeputados.aspx',
'https://ww4.al.rs.gov.br/deputados',
'https://sapl.saojeronimo.rs.leg.br/parlamentar/42',
'https://www.camarapoa.rs.gov.br/vereadores',
'https://www.saogabriel.rs.gov.br/noticias/prefeita-em-exercicio-sandra-weber-recebe-vereador-ladisle-teixeira-que-comunica-conquista-de-retroescavadeira-para-a-agricultura',
'https://bancodeleis.unale.org.br/spl/consulta-producao.aspx?autor=848',
'https://www.instagram.com/p/DcBrIp3pKWQ/',
'https://www.instagram.com/samaragarcia.up/',
]

def now():return datetime.now(timezone.utc).isoformat()
def save(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location('rs_ad2_public_safety',ROOT/'tools/rs-estaduais/research.py')
    safe=importlib.util.module_from_spec(spec);spec.loader.exec_module(safe)
    records=json.loads((DATA/'normalized.json').read_text())['candidates']
    tasks=[]
    for c in records:
        for h in c['history']:
            if h['year']>=2026 or h.get('votes') is not None or str(h.get('votes_status','')).startswith('not_applicable'):continue
            match=re.search(r'#/candidato/(\d+)/(\d+)/([^/]+)/(\d+)',h.get('profile_url',''))
            if not match:continue
            year,election,unit,cid=match.groups()
            url=f'https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura/buscar/{year}/{unit}/{election}/candidato/{cid}'
            tasks.append((c['id'],c['name'],h,url))
    def historical(task):
        current,name,history,url=task
        result={'current_candidate_id':current,'name':name,'history_context':{k:history.get(k) for k in ['candidate_id','year','round','office','uf','electoral_unit','result','round_note']},'url':url,'checked_at':now()}
        try:
            raw,final,status,mime=safe.read(url,22);obj=json.loads(raw)
            if str(obj.get('id'))!=str(history['candidate_id']):raise ValueError('Historical TSE ID mismatch')
            allowed=['id','nomeCompleto','nomeUrna','numero','cargo','eleicao','partido','descricaoSituacao','descricaoTotalizacao','descricaoSituacaoCandidato','candidatoApto','isCandidatoInapto','nomeMunicipio','uf','localCandidatura']
            public={k:obj[k] for k in allowed if k in obj}
            public.update({k:v for k,v in obj.items() if re.search('voto|turno',k,re.I) and isinstance(v,(str,int,float,bool,type(None)))})
            result.update({'read':True,'http_status':status,'source_sha256':hashlib.sha256(raw).hexdigest(),'schema_keys':list(obj),'data':public})
        except Exception as exc:result.update({'read':False,'error':str(exc)})
        return result
    def page(url):
        result={'url':url,'checked_at':now()}
        try:
            raw,final,status,mime=safe.read(url,18)
            soup=BeautifulSoup(raw,'html.parser')
            if re.search(r'access denied|verify you are human|just a moment|acesso negado',soup.get_text(' ',strip=True)[:1800],re.I):raise ValueError('Access/interstitial page is not source content')
            result.update({'http_status':status,'final_url':final,'source_sha256':hashlib.sha256(raw).hexdigest(),'title':soup.title.get_text(' ',strip=True) if soup.title else ''})
            for x in soup.select('script,style,nav,header,footer,form'):x.decompose()
            main=soup.select_one('main,article,#content,.conteudo') or soup
            lines=[re.sub(r'\s+',' ',s).strip() for s in main.get_text('\n',strip=True).splitlines()]
            lines=[s for s in lines if s and '@' not in s and not re.search(r'telefone|celular|endereço|cnpj|cpf|doadores|arrecad|gabinete:|nascimento',s,re.I)]
            result['review_text']=' '.join(' '.join(lines).split()[:500])
            result['links']=[{'label':a.get_text(' ',strip=True)[:100],'url':a['href']} for a in soup.select('a[href]') if re.search('mandato|legislatura|projeto|matéria|materia|comiss|proposi|João Pedro|Grill|Corazza|Massena|Rita|Mônica',a.get_text(' ',strip=True),re.I)][:35]
            result['read']=bool(result['review_text'])
        except Exception as exc:result.update({'read':False,'error':str(exc)})
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        historicals=list(pool.map(historical,tasks))
        pages=list(pool.map(page,SOURCES))
    save(OUT/'historical-details.json',historicals)
    save(OUT/'public-pages.json',pages)
    print(json.dumps({'historical_attempts':len(historicals),'historical_read':sum(x['read'] for x in historicals),'pages_attempted':len(pages),'pages_read':sum(x['read'] for x in pages)}))

if __name__=='__main__':run()
