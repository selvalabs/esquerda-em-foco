"""Audit each candidate's declared public sources; never infer agendas from party.
Source availability is distinct from editorial verification. Authentication-only
social pages are recorded as declared links, not treated as read evidence.
"""
from __future__ import annotations
import concurrent.futures
import hashlib
import ipaddress
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais'
A=ROOT/'docs/rs-estaduais'
SOCIAL=('instagram.com','facebook.com','fb.com','youtube.com','youtu.be','tiktok.com','x.com','twitter.com','threads.net','threads.com','bsky.app','kwai.com','wa.me','whatsapp.com','telegram.me','t.me')
SHORTENERS=('bit.ly','tinyurl.com','linktr.ee','linktree.com','queroapoiar.com.br','apoia.se')

def stamp():return datetime.now(timezone.utc).isoformat()
def save(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def load(path,default):return json.loads(path.read_text()) if path.exists() else default
def host_is(host,domains):return any(host==d or host.endswith('.'+d) for d in domains)
def normalize_url(value):
    value=str(value or '').strip()
    try:
        parts=urllib.parse.urlsplit(value)
        host=(parts.hostname or '').lower()
        if parts.scheme.lower() not in ('https','http') or parts.username or parts.password or not host or '.' not in host or re.search(r'\s',value) or parts.port not in (None,80,443):return None
        if host.endswith(('.local','.internal','.localhost')) or host in ('localhost','metadata.google.internal'):return None
        try:
            if not ipaddress.ip_address(host).is_global:return None
        except ValueError:pass
        return urllib.parse.urlunsplit((parts.scheme.lower(),host.encode('idna').decode('ascii'),parts.path or '/',parts.query,''))
    except (ValueError,UnicodeError):return None

def public_address(address):
    parsed=urllib.parse.urlsplit(address)
    for item in socket.getaddrinfo(parsed.hostname,parsed.port or (443 if parsed.scheme=='https' else 80),type=socket.SOCK_STREAM):
        if not ipaddress.ip_address(item[4][0]).is_global:raise ValueError('Non-public destination rejected')

class PublicRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not normalize_url(newurl):raise ValueError('Unsafe redirect')
        public_address(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def read(address,timeout=12):
    address=normalize_url(address)
    if not address:raise ValueError('Invalid public URL')
    public_address(address)
    opener=urllib.request.build_opener(PublicRedirect())
    request=urllib.request.Request(address,headers={'User-Agent':'Mozilla/5.0 (compatible; EsquerdaEmFoco/1.0; public information audit)','Accept':'text/html,application/json,text/javascript,*/*;q=0.5'})
    with opener.open(request,timeout=timeout) as response:
        raw=response.read(3_000_001)
        if len(raw)>3_000_000:raise ValueError('Oversized page')
        return raw,response.geturl(),response.status,response.headers.get('Content-Type','')

def audit_page(address):
    try:
        raw,final,status,mime=read(address)
        soup=BeautifulSoup(raw,'html.parser')
        title=soup.title.get_text(' ',strip=True) if soup.title else ''
        links=[]
        for a in soup.select('a[href]'):
            target=normalize_url(urllib.parse.urljoin(final,a.get('href','')))
            if target and (urllib.parse.urlsplit(target).hostname==urllib.parse.urlsplit(final).hostname):
                text=a.get_text(' ',strip=True)
                if re.search(r'biograf|trajet|quem|propost|projet|mandato|sobre|pautas',text,re.I):links.append({'label':text[:100],'url':target})
        description=soup.find('meta',attrs={'name':'description'})
        # Retain a small evidence locator, not copied campaign prose.
        locator=' '.join((title+' '+(description.get('content','') if description else '')).split()[:22])
        return {'url':address,'final_url':final,'http_status':status,'content_type':mime,'sha256':hashlib.sha256(raw).hexdigest(),'title':title[:180],'locator':locator,'relevant_links':links[:12],'checked_at':stamp(),'read':True,'editorial_verified':False}
    except Exception as exc:
        return {'url':address,'read':False,'error':str(exc),'checked_at':stamp(),'editorial_verified':False}

def formatting_reconciliation():
    audit=load(A/'reconciliation.json',{})
    remaining=[];formats=[]
    for row in audit.get('identity_mismatches',[]):
        differences=row.get('mismatches',[])
        same=lambda value:re.sub(r'[^\w]+',' ',str(value),flags=re.UNICODE).strip()
        if differences and all(x['field']=='civil_name' and same(x['api'])==same(x['csv']) for x in differences):
            formats.append({**row,'classification':'punctuation_or_whitespace_only','identity_basis':'Identificador TSE, número, partido e cargo concordantes; mesmas palavras do nome civil após normalizar pontuação/espaços.'})
            for check in audit.get('identity_checks',[]):
                if check['candidate_id']==row['candidate_id']:
                    check['identity_fields_match']=True
                    check['formatting_difference']=True
        else:remaining.append(row)
    audit['source_format_differences']=formats
    audit['identity_mismatches']=remaining
    audit['formatting_reviewed_at']=stamp()
    save(A/'reconciliation.json',audit)

def discovery():
    path=A/'institutional-discovery.json'
    if path.exists():return
    pages=[]
    for address in ['https://ww4.al.rs.gov.br/','https://ww4.al.rs.gov.br/deputados']:
        try:
            raw,final,status,mime=read(address,20)
            soup=BeautifulSoup(raw,'html.parser')
            item={'url':address,'final_url':final,'sha256':hashlib.sha256(raw).hexdigest(),'checked_at':stamp(),'options':[{'value':o.get('value'),'label':o.get_text(' ',strip=True)} for o in soup.select('option')],'links':[{'url':urllib.parse.urljoin(final,a['href']),'label':a.get_text(' ',strip=True)[:100]} for a in soup.select('a[href]') if re.search(r'deput|parlament|api',a['href']+a.get_text(),re.I)],'scripts':[]}
            for script in soup.select('script'):
                src=script.get('src')
                target=urllib.parse.urljoin(final,src) if src else None
                if target and (not urllib.parse.urlsplit(target).hostname.endswith('al.rs.gov.br') or any(k in target for k in ('jquery','bootstrap','core/assets','google'))):continue
                text=script.get_text()
                if src:
                    try:text=read(target,10)[0].decode('utf-8',errors='replace')
                    except Exception as exc:item['scripts'].append({'url':target,'error':str(exc)});continue
                # API/request fragments only, not unrelated application code.
                matches=[m.group(0) for m in re.finditer(r'.{0,180}(?:[Dd]eputad|[Pp]arlament|https?://|[Aa]pi/|ajax|[Ff]etch\().{0,280}',text)]
                if matches:item['scripts'].append({'url':target,'sha256':hashlib.sha256(text.encode()).hexdigest(),'request_fragments':matches[:90]})
            pages.append(item)
        except Exception as exc:pages.append({'url':address,'error':str(exc),'checked_at':stamp()})
    save(path,{'pages':pages})

def run():
    formatting_reconciliation()
    records=load(D/'candidates-official.json',[])
    profiles=load(D/'profiles-official.json',{})
    social=load(D/'social-official.json',[])
    previous=load(D/'web-research.json',{})
    def candidate(row):
        cid=row['SQ_CANDIDATO']
        if previous.get(cid,{}).get('version')==1:return cid,previous[cid]
        declared=profiles.get(cid,{}).get('data',{}).get('sites',[])+[x.get('DS_URL','') for x in social if x.get('SQ_CANDIDATO')==cid]
        valid=sorted({normalize_url(x) for x in declared if normalize_url(x)})
        social_links=[u for u in valid if host_is(urllib.parse.urlsplit(u).hostname,SOCIAL)]
        own=[u for u in valid if not host_is(urllib.parse.urlsplit(u).hostname,SOCIAL+SHORTENERS)]
        selected=[];seen=set()
        for u in own:
            host=urllib.parse.urlsplit(u).hostname
            if host not in seen:selected.append(u);seen.add(host)
        pages=[audit_page(u) for u in selected[:2]]
        return cid,{'version':1,'candidate_id':cid,'checked_at':stamp(),'source_of_links':profiles.get(cid,{}).get('url'),'declared_link_count':len(declared),'valid_links':valid,'social_links':social_links,'invalid_link_count':sum(normalize_url(x) is None for x in declared),'websites':pages,'research_status':'public_website_read_needs_editorial_review' if any(x['read'] for x in pages) else 'declared_social_links_only' if social_links else 'no_readable_declared_website','editorial_verified':False,'limitation':'Disponibilidade de links não comprova pautas, autenticidade de cada publicação, atividade de mandato ou ausência de atuação. Nenhum login foi contornado.'}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        output=dict(pool.map(candidate,records))
    save(D/'web-research.json',output)
    save(A/'web-research-coverage.json',{'checked_at':stamp(),'candidates_audited':len(output),'with_valid_declared_links':sum(bool(x['valid_links']) for x in output.values()),'with_readable_website':sum(any(p['read'] for p in x['websites']) for x in output.values()),'invalid_declared_links':sum(x['invalid_link_count'] for x in output.values()),'read_does_not_equal_editorial_verification':True})
    discovery()

if __name__=='__main__':run()
