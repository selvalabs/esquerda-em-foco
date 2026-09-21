"""Final deterministic presentation pass, run before all validation gates."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2];DEST=ROOT/'rs/deputados-federais';DOC=ROOT/'docs/rs'
def run():
 page=DEST/'index.html';soup=BeautifulSoup(page.read_text(),'html.parser')
 existing=soup.find(id='rs-layout-final')
 if existing:existing.decompose()
 style=soup.new_tag('style',attrs={'id':'rs-layout-final'})
 style.string='''/* Constrain decorative art, rather than hiding overflowing text. */
.party-section{overflow:clip;}
.rs-history-links{white-space:normal;}
.career-votes{font-variant-numeric:tabular-nums;}
.candidate .identity-copy,.candidate-copy,.candidate-links,.career-cell{min-width:0;}
.candidate .social-link:not(:has(svg)){font-size:.64rem;min-width:44px;width:auto;padding:0 8px;}
'''
 soup.head.append(style)
 soup.select_one('.dek').string='Nomes, trajetórias e pautas das candidaturas reunidas neste levantamento. Cada ficha traz suas fontes para que você possa conferir as informações.'
 data=json.loads((DEST/'dados.json').read_text());counts={}
 for c in data['candidates']:counts[c['status']]=counts.get(c['status'],0)+1
 status=[]
 for key,n in sorted(counts.items()):status.append(f'{n} '+('deferidos' if key=='Deferido' and n!=1 else key.lower()))
 soup.select_one('.rs-date').string='Consulta de 21 de setembro de 2026 · '+' · '.join(status)
 result=str(soup).replace('viewbox=','viewBox=');page.write_text(result,encoding='utf-8')
 report_path=DOC/'build-report.json';report=json.loads(report_path.read_text());report['html_sha256']=hashlib.sha256(result.encode()).hexdigest();report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':run()
