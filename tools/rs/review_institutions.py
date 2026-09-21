"""Render public institutional directories. Matching is discovery, not office proof.
No logins, challenge bypasses, contact details or private records are collected.
Short excerpts (<=150 words per URL) allow manual, dated confirmation.
"""
from __future__ import annotations
import hashlib,json,re,time,unicodedata
from datetime import datetime,timezone
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'data/rs';A=ROOT/'docs/rs/review'
def norm(x):return ''.join(c for c in unicodedata.normalize('NFD',x.casefold()) if unicodedata.category(c)!='Mn')
def save(path,x):path.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
TASKS=[
 ('https://sapl.pelotas.rs.leg.br/parlamentar/',['Jurandir','Miriam','Cristina']),
 ('https://sapl.uruguaiana.rs.leg.br/parlamentar/?iframe=1&incluir=0',['Manoela']),
 ('https://ww4.al.rs.gov.br/deputados',['Laura Sito','Valdeci']),
 ('https://cmmontenegro.cittatec.com.br/portal-legislativo/vereadores',['Claudete','Clau']),
 ('https://www.camarafarroupilha.rs.gov.br/',['Fran Bonaci','Francyelle']),
 ('https://www.riogrande.rs.leg.br/',['Juquinha','Rubilar']),
 ('https://www.camaracanoas.rs.gov.br/',['Cris Moraes']),
 ('https://www.camarajaguarao.rs.gov.br/',['Fred']),
 ('https://www.camaralivramento.rs.gov.br/',['Rafael de Castro','Rafa Castro']),
 ('https://www.vacaria.rs.gov.br/',['Fernando Lucena','Fernandinho']),
]
def run():
 output=A/'institutional-directory-review.json'
 if output.exists():return
 audit={'checked_at':datetime.now(timezone.utc).isoformat(),'method':'Public browser rendering; discovery only; manual review required before confirming office','pages':[]}
 with sync_playwright() as p:
  browser=p.chromium.launch();context=browser.new_context()
  for address,needles in TASKS:
   page=context.new_page();item={'url':address,'search_names':needles}
   try:
    response=page.goto(address,wait_until='domcontentloaded',timeout=28000);page.wait_for_timeout(2200)
    text=page.locator('body').inner_text(timeout=8000);item['http_status']=response.status if response else None;item['final_url']=page.url;item['title']=page.title();item['text_sha256']=hashlib.sha256(text.encode()).hexdigest();item['text_length']=len(text)
    # Word budget applies to the entire source URL, not per matched name.
    words=[];matches=[];lines=text.splitlines()
    for i,line in enumerate(lines):
     if any(norm(n) in norm(line) for n in needles):
      matches.append(line.strip()[:180]);chunk=' '.join(lines[max(0,i-2):min(len(lines),i+4)]).split()
      words.extend(chunk[:max(0,150-len(words))])
    item['matched_labels']=list(dict.fromkeys(matches));item['excerpt']=' '.join(words)
    anchors=page.locator('a[href]').evaluate_all('(nodes)=>nodes.map(n=>({label:(n.textContent||" ").trim(),url:n.href}))')
    item['discovered_links']=[a for a in anchors if any(norm(n) in norm(a['label']) for n in needles) or any(s in norm(a['label']) for s in ['vereadores','parlamentares'])][:18]
    if not matches:item['limitation']='No matching name was rendered; not evidence of absence from office.'
    if re.search(r'captcha|verify you are human|just a moment|access denied',text,re.I):item['limitation']='Access challenge encountered; no bypass attempted.'
   except Exception as e:item['error']=str(e)[:500]
   audit['pages'].append(item);page.close()
  browser.close()
 save(output,audit);print(json.dumps(audit,ensure_ascii=False,indent=2))
if __name__=='__main__':run()
