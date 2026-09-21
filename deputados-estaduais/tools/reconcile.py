"""Project a verified ticket total onto its corresponding lead-candidate record."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'data'
votes=json.loads((D/'votos-historicos.json').read_text())
history=json.loads((D/'historico-sc-2026.json').read_text())
changes=[]
for h in history:
 if int(h['ANO_ELEICAO'])>=2026 or h['CD_CARGO'] not in ['3','11']: continue
 key=f"{h['ANO_ELEICAO']}:{h['SQ_CANDIDATO']}:{h['NR_TURNO']}"
 ticket=f"{h['ANO_ELEICAO']}:chapa:{h['SG_UE']}:{h['NR_CANDIDATO']}:{h['NR_TURNO']}"
 record=votes.get(ticket)
 if key in votes or not record or record['candidate_id']!=h['SQ_CANDIDATO']: continue
 votes[key]={**record,'type':'nominal','derived_from':ticket,'reconciliation':'Same official lead candidate identifier, year, round, electoral unit and number. The corresponding vice retains the shared-ticket label.'}
 changes.append({'key':key,'ticket_key':ticket,'source':record['source']})
(D/'votos-historicos.json').write_text(json.dumps(votes,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'audit/reconciliation.json').write_text(json.dumps({'method':'Exact identifier reconciliation, not a vote estimate','changes':changes},ensure_ascii=False,indent=2),encoding='utf-8')
print('Lead-candidate records reconciled:',len(changes))
