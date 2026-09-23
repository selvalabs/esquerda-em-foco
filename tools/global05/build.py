"""Finalize public-head metadata and asset revisions without rewriting card HTML.
Called by publication.py --prepare, after whichever editorial renderer was used.
No research dates, candidate text, taxonomy or source associations are changed.
"""
from __future__ import annotations
import argparse,hashlib,html,json,posixpath,re
from pathlib import Path
from urllib.parse import parse_qsl,urlsplit,urlunsplit,urlencode
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
SITE='https://selvalabs.github.io/esquerda-em-foco/'
BASELINE='4a3300005fafbf85e13c4a61e763db1496924348'

def public_pages(root:Path)->list[str]:
    reg=json.loads((root/'config/editions.json').read_text())
    return ['index.html']+[s['path'].lstrip('/')+'index.html' for s in reg['states']]+[e['entrypoint'] for e in reg['editions'] if e['publication_status']=='published']+['deputados-estaduais/index.html','404.html']

def finalize(text:str,page:str,root:Path)->str:
    def revision(m:re.Match)->str:
        value=html.unescape(m[3]);u=urlsplit(value)
        if u.scheme or u.netloc or not u.path.endswith(('.js','.css')):return m[0]
        path=posixpath.normpath(posixpath.join(posixpath.dirname(page),u.path))
        f=(root/path).resolve()
        if not f.is_relative_to(root.resolve()) or not f.is_file():raise ValueError('Missing local asset: '+page+': '+value)
        query=[(k,v) for k,v in parse_qsl(u.query,keep_blank_values=True) if k!='v']
        query.append(('v',hashlib.sha256(f.read_bytes()).hexdigest()[:12]))
        current=urlunsplit(('', '',u.path,urlencode(query),u.fragment))
        return m[1]+'='+m[2]+html.escape(current,quote=True)+m[2]
    text=re.sub(r'\b(href|src)=([\"\'])([^\"\']+)\2',revision,text)
    # Parse only the head for inspection. Keep the original document bytes outside
    # the attribute substitutions and the added metadata; no DOM reserialization.
    head=re.search(r'<head\b[^>]*>(.*?)</head\s*>',text,re.S|re.I)
    if not head:raise ValueError('Missing head: '+page)
    d=BeautifulSoup(head[1],'html.parser');extra=[]
    if not d.select_one('meta[property="og:site_name"]'):
        extra.append('<meta property="og:site_name" content="Esquerda em foco"/>')
    if not d.select_one('meta[property="og:image"]'):
        for key,value in [('og:image',SITE+'assets/seo/global-home.png'),('og:image:width','1200'),('og:image:height','630'),('og:image:alt','Esquerda em foco — estados, candidaturas e fontes — 2026')]:
            extra.append('<meta property="'+key+'" content="'+html.escape(value,quote=True)+'"/>')
    if not d.select_one('meta[name="twitter:card"]'):
        extra.append('<meta name="twitter:card" content="summary_large_image"/>')
    if extra:
        # The rollout removes and appends its own assets on every generation.
        # Insert new metadata before that block, using the same serialization as
        # the renderer, so the next complete build does not reorder these tags.
        marker=re.search(r'<(?:link|script)\b[^>]*\bdata-global-rollout=',head[1],re.I)
        insertion=head.start(1)+marker.start() if marker else head.end(1)
        metadata=''.join(str(BeautifulSoup(tag,'html.parser').find()) for tag in extra)
        text=text[:insertion]+metadata+text[insertion:]
    return text

def apply(root:Path=ROOT,write:bool=True)->dict:
    root=Path(root);changed=[];pages=public_pages(root)
    for page in pages:
        p=root/page;old=p.read_text();new=finalize(old,page,root)
        if old!=new:
            changed.append(page)
            if write:p.write_text(new)
    return {'pages_checked':len(pages),'changed_pages':changed,'research_changed':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
    result=apply(write=not a.check);print(json.dumps(result))
    if a.check and result['changed_pages']:raise SystemExit(1)
