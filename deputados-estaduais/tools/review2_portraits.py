#!/usr/bin/env python3
"""Verify each displayed portrait by official member ID and original image hash."""
import hashlib,io,json,re
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image,ImageOps
from http_archive import archive
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'audit/review2'
URL='https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/fotos/foto_cand2026_SC_div.zip'
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 raw=json.loads((OUT/'snapshot/universo-sc-2026.json').read_text());parties={'PT','PCDOB','PV','PSOL','REDE','PDT','PSB','PSTU','UP','PCO'}
 ids={r['SQ_CANDIDATO'] for r in raw if r['SG_PARTIDO'].upper() in parties};old=json.loads((ROOT/'data/portraits.json').read_text());new={};changed=[]
 z,meta=archive(URL)
 with z:
  for member in z.namelist():
   if not re.search(r'\.(jpe?g|png)$',member,re.I):continue
   sid=next((sid for sid in ids if re.search(r'(?<!\d)'+sid+r'(?!\d)',member)),None)
   if not sid:continue
   if sid in new:raise ValueError('Ambiguous official photo members for '+sid)
   source=z.read(member);sha=hashlib.sha256(source).hexdigest()
   image=ImageOps.exif_transpose(Image.open(io.BytesIO(source))).convert('RGB');image.thumbnail((360,450))
   photo={'path':f'assets/portraits/{sid}.webp','source':URL,'archive_member':member,'source_kind':'Arquivo oficial de fotos do TSE','sha256_source':sha,'matched_by':'SQ_CANDIDATO in official archive member','width':image.width,'height':image.height}
   new[sid]=photo
   if sha!=old.get(sid,{}).get('sha256_source'):changed.append(sid)
   target=OUT/'snapshot/portraits';target.mkdir(exist_ok=True)
   image.save(target/f'{sid}.webp','WEBP',quality=84,method=6)
 save(OUT/'snapshot/portraits.json',new)
 report={'checked_at':datetime.now(timezone.utc).isoformat(),'source':meta,'expected':len(ids),'matched':len(new),'missing':sorted(ids-new.keys()),'changed':changed,'passed':set(new)==ids}
 save(OUT/'portraits-audit.json',report)
 print(json.dumps(report,ensure_ascii=False,indent=2))
 if not report['passed']:raise SystemExit('Incomplete official photo join; publication requires review')
if __name__=='__main__':main()
