"""Collect declared public websites for editorial review; never auto-create political claims."""
from __future__ import annotations
import concurrent.futures, hashlib, ipaddress, json, re, socket, urllib.parse, urllib.request
from pathlib import Path
from datetime import datetime, timezone
from bs4 import BeautifulSoup

ROOT = Path('data/rs')
rows = json.loads((ROOT/'candidates-official.json').read_text())
social = json.loads((ROOT/'social-official.json').read_text())
social_hosts = {'instagram.com','facebook.com','youtube.com','youtu.be','tiktok.com','x.com','twitter.com','threads.net','threads.com','kwai.com','linkedin.com','flickr.com','wa.me','api.whatsapp.com','whatsapp.com','t.me','linktr.ee','linktree.com','apoia.se','apoiar.me','queroapoiar.com.br'}
by_id = {r['SQ_CANDIDATO']:r for r in rows}

def normalize(raw):
    value = raw.strip()
    if any(c.isspace() for c in value) or '@' in value.split('/')[0]: return None
    if not re.match(r'^https?://',value,re.I): value='https://'+value
    parts=urllib.parse.urlsplit(value)
    host=(parts.hostname or '').lower()
    if parts.scheme.lower() not in ('http','https') or '.' not in host or parts.username: return None
    if any(host==h or host.endswith('.'+h) for h in social_hosts): return None
    if any(x in host for x in ['apoiar','doacao','vaquinha']): return None
    return urllib.parse.urlunsplit((parts.scheme.lower(),parts.netloc.lower(),parts.path or '/',parts.query,''))

urls={}
for item in social:
    cid=item.get('SQ_CANDIDATO'); url=normalize(item.get('DS_URL',''))
    if cid in by_id and url: urls.setdefault(url,set()).add(cid)

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_public(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def check_public(url):
    parts=urllib.parse.urlsplit(url)
    if parts.scheme not in ('http','https') or parts.username: raise ValueError('Unsafe URL scheme')
    for info in socket.getaddrinfo(parts.hostname,parts.port or 443):
        if not ipaddress.ip_address(info[4][0]).is_global: raise ValueError('Non-public address blocked')

def collect(url):
    result={'url':url,'candidate_ids':sorted(urls[url]),'checked_at':datetime.now(timezone.utc).isoformat()}
    try:
        check_public(url)
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; EsquerdaEmFoco public-source review)'})
        with urllib.request.build_opener(SafeRedirect).open(req,timeout=12) as response:
            raw=response.read(2_000_000)
            result['status']=response.status; result['final_url']=response.geturl()
            encoding=response.headers.get_content_charset() or 'utf-8'
        soup=BeautifulSoup(raw.decode(encoding,errors='replace'),'html.parser')
        result['sha256']=hashlib.sha256(raw).hexdigest(); result['title']=soup.title.get_text(' ',strip=True) if soup.title else ''
        for tag in soup.select('script,style,noscript,form,nav,footer'): tag.decompose()
        result['headings']=[h.get_text(' ',strip=True) for h in soup.select('h1,h2,h3')][:45]
        result['review_text']=soup.get_text('\n',strip=True)[:28000]
        result['links']=[{'text':a.get_text(' ',strip=True)[:180],'url':urllib.parse.urljoin(result['final_url'],a['href'])} for a in soup.select('a[href]') if any(x in a.get_text(' ',strip=True).lower() for x in ['proposta','pauta','história','historia','conheça','quem','luta','bandeira','biografia'])][:25]
    except Exception as exc: result['error']=str(exc)
    return result

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    results=list(pool.map(collect, sorted(urls)))
Path('review-rs').mkdir(exist_ok=True)
Path('review-rs/declared-websites.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
coverage=[]
for cid,r in by_id.items():
    sources=[x for x in results if cid in x['candidate_ids']]
    coverage.append({'id':cid,'name':r['NM_URNA_CANDIDATO'],'declared_website_attempts':len(sources),'readable_websites':sum(bool(x.get('review_text')) for x in sources),'sources':[{k:v for k,v in x.items() if k not in ('review_text','headings','links')} for x in sources]})
Path('review-rs/coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'candidates':len(rows),'declared_websites':len(results),'readable':sum(bool(r.get('review_text')) for r in results)},ensure_ascii=False))
