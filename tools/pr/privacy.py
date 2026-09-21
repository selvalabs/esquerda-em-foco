"""Minimize direct email contacts entered in public social-link fields."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
EMAIL=re.compile(r'[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}',re.I)
def sanitize():
 report_path=ROOT/'docs/pr/privacy.json'
 report=json.loads(report_path.read_text()) if report_path.exists() else {'rule':'Omit direct email-like contacts from public social-link fields; retain source hashes and aggregate redaction counts.','files':{}}
 def rejected(value):return isinstance(value,str) and bool(EMAIL.search(value))
 for filename in ('social-official.json','profiles-official.json'):
  path=ROOT/'data/pr'/filename;data=json.loads(path.read_text());removed=[]
  if filename=='social-official.json':
   removed=[row.get('DS_URL','') for row in data if rejected(row.get('DS_URL'))]
   data=[row for row in data if not rejected(row.get('DS_URL'))]
  else:
   for profile in data.values():
    details=profile.get('data',{});sites=details.get('sites')
    if not isinstance(sites,list):continue
    removed.extend(v for v in sites if rejected(v));details['sites']=[v for v in sites if not rejected(v)]
  previous=report['files'].get(filename,{'removed_value_sha256':[]})
  digests=set(previous['removed_value_sha256']);digests.update(hashlib.sha256(v.encode()).hexdigest() for v in removed)
  report['files'][filename]={'removed_distinct_values':len(digests),'removed_value_sha256':sorted(digests)}
  path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 report_path.parent.mkdir(parents=True,exist_ok=True);report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:v['removed_distinct_values'] for k,v in report['files'].items()}))
if __name__=='__main__':sanitize()
