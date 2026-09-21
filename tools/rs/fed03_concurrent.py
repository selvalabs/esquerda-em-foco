"""Idempotent compatibility migration for the explicitly reconciled 111-record scope.
No political content is inferred. It preserves the frozen original 63 research targets.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def patch(text,old,new):
    if new in text:return text
    if text.count(old)!=1:raise RuntimeError('Concurrent migration anchor mismatch: '+old[:120])
    return text.replace(old,new,1)
def run():
    base=json.loads((ROOT/'data/rs/fed03/integration-base.json').read_text())
    assert base['current_population']==111 and base['original_population']==107
    assert len(base['added_records'])==4 and not base['removed_ids']
    path=ROOT/'tools/rs/fed03_support.py';text=path.read_text(encoding='utf-8')
    old="    save(A/'final-report.json',report);save(A/'candidate-matrix.json',matrix);save(A/'research-log.json',research)"
    new="""    integration=load(I/'integration-base.json')
    incoming={r['SQ_CANDIDATO'] for r in integration['added_records']}
    if incoming & target_ids or not incoming <= set(byid):raise ValueError('Concurrent records not preserved independently')
    report.update({'original_population':integration['original_population'],'concurrent_added_records':integration['added_records'],'concurrent_population_baseline':integration['upstream_commit'],'original_targets_remaining_policy_gaps':sum(not r['policy_or_action_documented'] for r in matrix if r['target_this_round']),'concurrent_added_policy_gaps':sum(not r['policy_or_action_documented'] for r in matrix if r['id'] in incoming),'concurrent_added_vote_gaps':sum(len(r['unresolved_nominal_rows']) for r in matrix if r['id'] in incoming),'scope_expansion_preserved':True})
    for row in matrix:
        if row['id'] in incoming:row['research_outcome']='incoming_triage_only_not_original_target'
    save(A/'incoming-triage.json',load(I/'incoming-triage.json'))
    save(A/'final-report.json',report);save(A/'candidate-matrix.json',matrix);save(A/'research-log.json',research)"""
    text=patch(text,old,new)
    text=patch(text,'Text/source presence and temporal-attribution review for all 107; substantive new-source research for the 63 targets. Previously published sources were not all independently reopened.','Text/source presence and temporal-attribution review of the reconciled dataset; substantive new-source research for the original 63 targets. Four concurrently added records received initial triage only. Previously published sources were not all independently reopened.')
    text=patch(text,'CSV eleitoral reconciliado; 107 consultas de perfil individual bloqueadas (HTTP 403). Não foram contabilizadas como reconferidas.','CSV eleitoral reconciliado para 111 registros; 111 consultas de perfil individual bloqueadas (HTTP 403). Não foram contabilizadas como reconferidas. A ampliação de 107 para 111 veio de correção de recorte no main; os quatro novos registros foram preservados e triados separadamente.')
    text=patch(text,'As cinco ausências nominais não foram transformadas em zero.','As cinco ausências nominais não foram transformadas em zero. Além dos dois conflitos de identidade do lote original, há três lacunas de votação vindas dos quatro cadastros acrescentados pelo main. As pendências editoriais são 43 dos alvos originais e quatro recém-incorporadas.')
    compile(text,str(path),'exec');path.write_text(text,encoding='utf-8')
    path=ROOT/'tests/rs/test_fed03.py';text=path.read_text(encoding='utf-8')
    pairs=[("self.report['without_summary'],42","self.report['without_summary'],46"),("self.report['without_policy_or_action'],43","self.report['without_policy_or_action'],47"),("len(validate_registry()),107","len(validate_registry()),111"),("self.report['registry_csv_reconciled'],107","self.report['registry_csv_reconciled'],111"),("self.report['profile_access_failures'],107","self.report['profile_access_failures'],111"),("'not_verified':2,'not_applicable':21,'not_yet_held':107","'not_verified':5,'not_applicable':21,'not_yet_held':111")]
    for old,new in pairs:text=patch(text,old,new)
    marker="if __name__=='__main__':unittest.main()"
    extra=""" def test_concurrent_scope_and_original_targets_are_separate(self):
  incoming={'210002533907','210002538975','210002533903','210002538974'}
  self.assertTrue(incoming <= set(self.by));self.assertEqual(len(self.cs),111)
  self.assertEqual(self.report['original_targets_remaining_policy_gaps'],43)
  self.assertEqual(self.report['concurrent_added_policy_gaps'],4)
  self.assertEqual(self.report['concurrent_added_vote_gaps'],3)
  matrix=read('docs/rs/fed03/candidate-matrix.json')
  for row in matrix:
   if row['id'] in incoming:self.assertFalse(row['target_this_round']);self.assertEqual(row['research_outcome'],'incoming_triage_only_not_original_target')
if __name__=='__main__':unittest.main()"""
    text=patch(text,marker,extra);compile(text,str(path),'exec');path.write_text(text,encoding='utf-8')
    print('Concurrent scope accounted separately; exact regression expectations updated from the official preserved population.')
if __name__=='__main__':run()
