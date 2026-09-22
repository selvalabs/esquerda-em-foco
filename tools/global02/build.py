"""Build a non-published integration rehearsal, never replace the repository root.
The rehearsal uses real immutable pages, a minimal home/hub harness, canonical
SC routes and a client-side legacy bridge. GLOBAL-03 owns the public home design.
"""
from __future__ import annotations
import argparse
import html
import json
import posixpath
import re
import shutil
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from core import ROOT, load, validate, require, url, shell, sitemap, metadata, save


def rebase_page(text: str, source: str, base: str) -> str:
    soup=BeautifulSoup(text,'html.parser')
    directory=posixpath.dirname(source)
    def resolve(value):
        if not value or value.startswith(('#','//')) or urlsplit(value).scheme:
            return value
        p=urlsplit(value)
        path=posixpath.normpath(posixpath.join(directory,p.path))
        require(not path.startswith('../'), 'Asset escapes site root')
        out=base+path.lstrip('./')
        if value.endswith('/') and not out.endswith('/'):out+='/'
        if p.query:out+='?'+p.query
        if p.fragment:out+='#'+p.fragment
        return out
    for n in soup.select('[href],[src],[poster]'):
        for key in ('href','src','poster'):
            if n.has_attr(key):n[key]=resolve(n[key])
    for n in soup.select('style,[style]'):
        key='style' if n.has_attr('style') else None
        text=n[key] if key else n.get_text()
        text=re.sub(r'url\(([\'"]?)([^)\'\"]+)\1\)',lambda m:'url("'+resolve(m[2])+'")',text)
        if key:n[key]=text
        else:n.string=text
    return str(soup).replace('viewbox=','viewBox=')


def decorate(text: str, registry: dict, base: str, e: dict) -> str:
    soup=BeautifulSoup(text,'html.parser')
    for n in soup.select('.eef-global-shell, [data-global02]'):n.decompose()
    css=soup.new_tag('link',rel='stylesheet',href=base+'assets/global/shell.css');css['data-global02']='';soup.head.append(css)
    js=soup.new_tag('script',src=base+'assets/global/shell.js',defer='');js['data-global02']='';soup.body.append(js)
    nav=BeautifulSoup(shell(registry,base,e['edition_id'],'next'),'html.parser').div
    # Insert once before the local navigation. Do not duplicate its IDs or controls.
    soup.body.insert(0,nav)
    canonical=soup.select_one('link[rel="canonical"]')
    if canonical:canonical['href']=metadata(e,base,'next')['canonical']
    for n in soup.select('meta[property="og:url"]'):n['content']=metadata(e,base,'next')['canonical']
    robots=soup.select_one('meta[name="robots"]')
    if robots:robots['content']='noindex,nofollow'
    else:soup.head.append(soup.new_tag('meta',attrs={'name':'robots','content':'noindex,nofollow'}))
    return str(soup).replace('viewbox=','viewBox=')


def harness(registry: dict, base: str, title: str, content: str, *, bridge=False) -> str:
    head='<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">'
    head+='<title>'+html.escape(title)+'</title><link rel="stylesheet" href="'+base+'assets/global/shell.css">'
    body=shell(registry,base,None,'next')+'<main style="max-width:70rem;margin:24px auto;padding:0 16px"><h1>'+html.escape(title)+'</h1>'+content+'</main>'
    body+='<script defer src="'+base+'assets/global/shell.js"></script>'
    if bridge:
        fixtures=load(ROOT/'config/legacy-sc-links.json')
        data=json.dumps({'fixtures':fixtures,'base':base},ensure_ascii=False).replace('</','<\\/')
        body+='<script src="'+base+'assets/global/core.js"></script><script type="application/json" id="global-legacy-data">'+data+'</script>'
        body+='''<script>(function(){const d=JSON.parse(document.getElementById('global-legacy-data').textContent);function bridge(){const target=EEFGlobal.legacyRootTarget(location.hash,d.fixtures,d.base);if(target)location.replace(target);}addEventListener('hashchange',bridge);bridge();})();</script>'''
    return '<!doctype html><html lang="pt-BR"><head>'+head+'</head><body>'+body+'</body></html>'


def build(out: Path, base: str) -> dict:
    require(out.resolve()!=ROOT and ROOT not in out.resolve().parents,'Rehearsal output must be outside repository')
    registry=load(ROOT/'config/editions.json');validate(registry);url(base,'/')
    out.mkdir(parents=True,exist_ok=True)
    # Copy only existing public directories, never the unpublished RS branch.
    for name in ['assets','deputados-estaduais','rs','pr','sp']:
        shutil.copytree(ROOT/name,out/name,dirs_exist_ok=True)
    for name in ['favicon.svg','site.webmanifest','.nojekyll']:
        if (ROOT/name).exists():shutil.copyfile(ROOT/name,out/name)
    results=[]
    for e in registry['editions']:
        if e['publication_status']!='published':continue
        old=(ROOT/e['entrypoint']).read_text(encoding='utf-8')
        content=rebase_page(old,e['entrypoint'],base)
        content=decorate(content,registry,base,e)
        dest=out/e['canonical_path'].lstrip('/')/'index.html';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(content,encoding='utf-8')
        srcdoc=BeautifulSoup(old,'html.parser');dstdoc=BeautifulSoup(content,'html.parser')
        before=[(n['id'],n.get_text(' ',strip=True)) for n in srcdoc.select('article.candidate')]
        after=[(n['id'],n.get_text(' ',strip=True)) for n in dstdoc.select('article.candidate')]
        require(before==after,'Card identity/text changed during routing '+e['edition_id'])
        results.append({'edition_id':e['edition_id'],'cards_preserved':len(before),'path':e['canonical_path']})
    for state in registry['states']:
        items=[]
        for e in registry['editions']:
            if e['state']!=state['code']:continue
            label=html.escape(e['office_label'])
            items.append('<p><a href="'+url(base,e['canonical_path'])+'">'+label+'</a></p>' if e['publication_status']=='published' else '<p>'+label+' — em preparação, sem publicação.</p>')
        p=out/state['path'].lstrip('/')/'index.html';p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(harness(registry,base,'Validação · '+state['name'],''.join(items)))
    root_content='<p>Ambiente técnico de validação da GLOBAL-02. A home pública é a próxima etapa.</p><p><a href="'+url(base,'/sc/deputados-federais/')+'">Acessar SC · Deputados federais</a></p>'
    (out/'index.html').write_text(harness(registry,base,'Validação da navegação global',root_content,bridge=True))
    target=url(base,'/sc/deputados-estaduais/')
    # Alias keeps fragment on client; no meta refresh that loses the fragment.
    alias='<p>Esta edição tem um novo endereço. <a id="global-alias" href="'+target+'">Acessar SC · Deputados estaduais</a></p>'
    alias+='<script>(function(){const u=new URL(document.getElementById("global-alias").href);u.hash=location.hash;u.search=location.search;location.replace(u.href);})();</script>'
    (out/'deputados-estaduais/index.html').write_text(harness(registry,base,'Endereço da edição SC',alias))
    (out/'404.html').write_text(harness(registry,base,'Página não encontrada','<p>Use a navegação por estado e cargo para encontrar a edição.</p>'))
    (out/'sitemap.xml').write_text(sitemap(registry,base,'next'))
    (out/'robots.txt').write_text('User-agent: *\nDisallow: /\n')
    return {'publication':'rehearsal_only','editions':results,'root_replaced_in_repository':False}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--base',required=True);args=p.parse_args()
    result=build(args.out,args.base);save(args.out.parent/(args.out.name+'-report.json'),result)
