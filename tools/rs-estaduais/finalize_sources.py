"""Merge reviewed additions without erasing evidence added in a later phase.

A null input records an earlier knowledge gap, not an instruction to delete a
subsequently reviewed field. Conflicting nonempty text still fails explicitly.
Deletions or substantive corrections require their own reviewed migration.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais'
A=ROOT/'docs/rs-estaduais'

def read(path,default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def apply(base,additions,ids):
    allowed={'reviewed','checked_at','pautas','pautas_type','biography','sources','activities_append'}
    retained=[]
    for cid,patch in additions.items():
        if cid not in ids or set(patch)-allowed:
            raise ValueError('Unknown candidature or editorial fields: '+cid)
        if patch.get('reviewed') is not True or not patch.get('checked_at') or not patch.get('sources'):
            raise ValueError('Incomplete review evidence: '+cid)
        target=base.setdefault(cid,{})
        for field in ('pautas','biography'):
            if patch.get(field) is not None and target.get(field) and target[field]!=patch[field]:
                raise ValueError('Conflicting reviewed text must be resolved explicitly: '+cid+' '+field)
        for key,value in patch.items():
            if value is None and target.get(key) is not None:
                retained.append({'candidate_id':cid,'field':key,'reason':'Earlier null input does not erase a later reviewed value'})
                continue
            if key in ('sources','activities_append'):
                destination='activities' if key=='activities_append' else 'sources'
                existing=target.setdefault(destination,[])
                signatures={json.dumps(x,sort_keys=True,ensure_ascii=False) for x in existing}
                for item in value:
                    token=json.dumps(item,sort_keys=True,ensure_ascii=False)
                    if token not in signatures:
                        existing.append(item);signatures.add(token)
            else:
                target[key]=value
    return retained

def run():
    additions=read(D/'editorial-additions.json',{})
    base=read(D/'editorial.json',{})
    ids={r['SQ_CANDIDATO'] for r in read(D/'candidates-official.json',[])}
    retained=apply(base,additions,ids)
    save(D/'editorial.json',base)
    save(A/'editorial-merge.json',{'input':'data/rs-estaduais/editorial-additions.json','input_sha256':hashlib.sha256((D/'editorial-additions.json').read_bytes()).hexdigest() if additions else None,'reviewed_records':sum(bool(e.get('reviewed')) for e in base.values()),'policy_summaries':sum(bool(e.get('pautas')) for e in base.values()),'institutional_activity_records':sum(bool(e.get('activities')) for e in base.values()),'retained_later_fields':retained,'method':'Reviewed additive merge. Earlier nulls do not erase later evidence. Nonempty conflicts still fail. Sources and acts deduplicate across re-runs.'})

if __name__=='__main__':run()
