"""Prepare hashes or verify actual Pages bytes, dependencies and the real 404."""
import argparse,concurrent.futures,hashlib,json,posixpath,time,sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit,unquote
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/global02'))
from core import load,save,indexable_paths
SITE='https://selvalabs.github.io/esquerda-em-foco/'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def prepare():
    import importlib.util
    quality=ROOT/'tools/global05/build.py'
    if quality.is_file():
        spec=importlib.util.spec_from_file_location('eef_global05_head',quality)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.apply(ROOT)
    reg=load(ROOT/'config/editions.json')
    pages=[p.lstrip('/')+'index.html' for p in indexable_paths(reg,'current')]
    pages+=['deputados-estaduais/index.html','404.html']
    paths=pages+['config/editions.json','config/legacy-sc-links.json','config/party-scope-2026.json','sitemap.xml','robots.txt','site.webmanifest','favicon.svg','assets/seo/global-home.png']
    for page in pages:
        s=BeautifulSoup((ROOT/page).read_text(),'html.parser')
        for n in s.select('script[src],link[rel=stylesheet]'):
            value=n.get('src',n.get('href',''));u=urlsplit(value)
            if u.scheme or value.startswith('//'):continue
            target=posixpath.normpath(posixpath.join(posixpath.dirname(page),unquote(u.path)))
            if target.startswith('../'):raise ValueError('Dependency escapes repository: '+target)
            paths.append(target)
    paths=sorted(set(paths))
    missing=[p for p in paths if not (ROOT/p).is_file()]
    if missing:raise FileNotFoundError('Missing required publication files: '+str(missing))
    save(ROOT/'data/global03/publication-files.json',{'schema_version':'1.0.0','files':[{'path':p,'sha256':sha((ROOT/p).read_bytes())} for p in paths]})
def request(item):
    path=item['path'];route=path[:-10] if path.endswith('index.html') else path
    try:
        with urlopen(Request(SITE+route,headers={'User-Agent':'EEF-GLOBAL03-publication-check','Cache-Control':'no-cache'}),timeout=30) as r:
            raw=r.read();code=r.status
        return {'path':path,'status':code,'expected':item['sha256'],'actual':sha(raw),'passed':code==200 and sha(raw)==item['sha256']}
    except Exception as exc:return {'path':path,'passed':False,'error':str(exc)}
def main():
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--out',type=Path);a=p.parse_args()
    if a.prepare:prepare();return
    if not a.out:raise ValueError('--out required')
    a.out.mkdir(parents=True,exist_ok=True);manifest=load(ROOT/'data/global03/publication-files.json');attempts=[]
    for attempt in range(12):
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:result=list(pool.map(request,manifest['files']))
        attempts.append({'attempt':attempt+1,'passed':sum(i['passed'] for i in result),'total':len(result)})
        if all(i['passed'] for i in result):break
        if attempt<11:time.sleep(15)
    missing_url=SITE+'global03-inexistente/arquivo-nao-existe/'
    try:
        with urlopen(missing_url,timeout=30) as r:code=r.status;raw=r.read()
    except HTTPError as exc:code=exc.code;raw=exc.read()
    except Exception as exc:code=0;raw=str(exc).encode()
    notfound={'url':missing_url,'status':code,'passed':code==404 and sha(raw)==sha((ROOT/'404.html').read_bytes()),'actual_sha256':sha(raw)}
    passed=all(i['passed'] for i in result) and notfound['passed']
    save(a.out/'http.json',{'passed':passed,'checked_at':datetime.now(timezone.utc).isoformat(),'attempts':attempts,'files':result,'not_found':notfound})
    print(json.dumps({'passed':passed,'files':len(result),'not_found_status':code}))
    if not passed:raise SystemExit(1)
if __name__=='__main__':main()
