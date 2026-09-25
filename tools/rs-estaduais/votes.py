"""Reuse the audited byte-range reader read-only; write exclusively this edition.
Only RS historical disputes receive RS nominal totals. National candidacies,
other states and vice/supplemental positions are not assigned RS-only votes.
"""
from __future__ import annotations
import importlib.util
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais'
A=ROOT/'docs/rs-estaduais'

def save(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def run():
    utility=ROOT/'tools/rs/votes_ranges.py'
    spec=importlib.util.spec_from_file_location('rs_state_range_reader',utility)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    history=json.loads((D/'history-normalized.json').read_text())
    # The legacy reader requires a history file. Supply only eligible RS rows,
    # then restore the complete record even if collection raises an exception.
    eligible={cid:[h for h in rows if h.get('uf')=='RS' and not str(h.get('office') or '').upper().startswith(('VICE','SUPLENTE','1º SUPLENTE','2º SUPLENTE')) and not h.get('round_note')] for cid,rows in history.items()}
    module.D=D
    module.A=A
    save(D/'history-normalized.json',eligible)
    try:
        module.run()
    finally:
        save(D/'history-normalized.json',history)
    votes=json.loads((D/'votes-official.json').read_text()) if (D/'votes-official.json').exists() else {}
    count=0
    for cid, rows in history.items():
        eligible_keys={(h['year'],h['candidate_id'],h['round']) for h in eligible[cid]}
        for h in rows:
            h['votes']=None
            if (h['year'],h['candidate_id'],h['round']) not in eligible_keys or h['year']>=2026:
                continue
            source=votes.get(str(h['year']),{})
            key=h['candidate_id']+':'+str(h['round'])
            if key in source.get('totals',{}):
                h['votes']=source['totals'][key]
                h['votes_source']=source['source_url']
                h['votes_source_generated_at']=source.get('generated_at')
                h['votes_population']='RS; soma nominal por município/zona e turno; identificador TSE'
                count+=1
    save(D/'history-normalized.json',history)
    save(A/'votes-coverage.json',{'checked_at':datetime.now(timezone.utc).isoformat(),'historical_rows_with_votes':count,'candidates_with_past_votes':sum(any(h.get('votes') is not None for h in rows) for rows in history.values()),'eligible_past_rows':sum(h['year']<2026 for rows in eligible.values() for h in rows),'years':sorted(votes),'reader_source':'tools/rs/votes_ranges.py','reader_sha256':hashlib.sha256(utility.read_bytes()).hexdigest(),'limitation':'Cobertura nominal 2012–2024 quando a fonte permite; não atribui total estadual a disputa presidencial, de outra UF, vice ou suplência. Valor ausente não é zero.'})

if __name__=='__main__':
    run()
