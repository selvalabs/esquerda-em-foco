"""Bounded read-only source discovery. Excerpts are transient review material.
No credentials are sent to source sites. No login/captcha/paywall is bypassed.
A successful download is not an editorial decision or a confirmed identity.
"""
from __future__ import annotations
import collections, concurrent.futures, hashlib, importlib.util, json, re, urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais';OUT=Path('/tmp/rs-ad3-source-review')
spec=importlib.util.spec_from_file_location('ad3_public_http',ROOT/'tools/rs-estaduais/research.py')
safe=importlib.util.module_from_spec(spec);spec.loader.exec_module(safe)

def fetch(item):
    url,cids=item;result={'url':url,'candidate_ids':sorted(cids),'checked_at':datetime.now(timezone.utc).isoformat(),'read':False,'editorial_verified':False}
    try:
        raw,final,status,mime=safe.read(url,10)
        result.update({'final_url':final,'http_status':status,'content_type':mime,'raw_sha256':hashlib.sha256(raw).hexdigest()})
        if not ('html' in mime or 'text/' in mime):result['outcome']='unsupported_non_html';return result
        soup=BeautifulSoup(raw,'html.parser');title=soup.title.get_text(' ',strip=True) if soup.title else ''
        links=[]
        for a in soup.select('a[href]'):
            target=safe.normalize_url(urllib.parse.urljoin(final,a['href']));label=a.get_text(' ',strip=True)
            if target and re.search(r'propost|biograf|bandeir|plano|programa|trajet|quem|mandato|vereador|deputad|mat[eé]ria|projeto|parlament',label,re.I):links.append({'url':target,'label':label[:120]})
        for n in soup.select('script,style,nav,header,footer,form'):n.decompose()
        body=soup.get_text('\n',strip=True)
        if re.search(r'captcha|verifica.{0,25}rob[oô]|access denied|just a moment|verify you are human',body[:3000]+title,re.I):result['outcome']='access_interstitial';return result
        result['word_count']=len(body.split());result['title']=' '.join(title.split()[:20]);result['relevant_links']=links[:18]
        if result['word_count']<30:result['outcome']='insufficient_readable_text';return result
        result['read']=True;result['outcome']='body_recovered_requires_manual_review'
        # This transient artifact is not committed or published in the site.
        lines=[x for x in body.splitlines() if '@' not in x and not re.search(r'\bCPF\b|CNPJ|doadores|contribui.{0,10}R\$|pix|\(\d{2}\)\s?\d',x,re.I)]
        result['review_text']=' '.join(('\n'.join(lines)).split()[:1400])
    except Exception as exc:result['outcome']='request_failed';result['error_type']=type(exc).__name__;result['http_status']=getattr(exc,'code',None)
    return result

def run():
    records=json.loads((D/'normalized.json').read_text())['candidates'];queue=[c for c in records if not c['pautas']];tasks=collections.defaultdict(set)
    for c in queue:
        urls=[x['url'] for x in c['sites']][:2]
        # Declared public social endpoints; no normalization of opaque handles.
        urls += [x['url'] for x in c['socials'] if 'instagram.com' in x['url']][:1]
        for u in urls:
            if safe.normalize_url(u):tasks[u].add(c['id'])
    extras={
      'https://unidadepopular.org.br/eleicoes/samara':'210002533391',
      'https://www.camararosariodosul.rs.gov.br/atas/sessao_solene/2026/1/0/461':'210002539779',
      'https://www.camararosariodosul.rs.gov.br/proposicoes/Convocacao-/0/1/0/8324':'210002539779',
      'https://periodicos.ufsm.br/kinesis/article/view/48178':'210002533924',
      'https://www.instagram.com/patipeixe02/':'210002544838',
      'https://ww4.al.rs.gov.br/deputados':'210002539810',
      'https://www.pstu.org.br/?s=Patricia+Peixe':'210002544838',
      'https://www.pstu.org.br/?s=Anderson+Silva':'210002544839'}
    for url,cid in extras.items():tasks[url].add(cid)
    OUT.mkdir(parents=True,exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(fetch,sorted(tasks.items())))
    output={'baseline_commit':'b9ec0c352cdc0dc2a77be8ea4cf28469f1c09502','queue_count':len(queue),'url_count':len(results),'sources':results,'automatic_editorial_decisions':False}
    (OUT/'sources.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'queue':len(queue),'urls':len(results),'outcomes':dict(collections.Counter(x['outcome'] for x in results))}))
if __name__=='__main__':run()
