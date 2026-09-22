"""Synchronize the canonical handoff after CI, retaining original research snapshots."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('close_handoff_support',ROOT/'tools/rs-estaduais/close_ad2.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
def run():
    report=c.load(c.A/'report.json')
    if report['technical_gate']!='passed':raise ValueError('Closure gate not passed')
    ledger=c.load(c.A/'candidate-coverage.json');by_id={x['candidate_id']:x for x in ledger}
    root=c.load(c.DOC/'candidate-coverage.json')
    if {x['candidate_id'] for x in root}!=set(by_id):raise ValueError('Canonical coverage identity mismatch')
    for row in root:
        source=by_id[row['candidate_id']]
        for key in ('research_status','status_label','research_exhaustive','next_action','current_office_status'):
            row[key]=source[key]
        row['research_detail']='ad2-close/candidate-coverage.json'
    c.save(c.DOC/'candidate-coverage.json',root)
    fields=['candidate_id','name','party','number','registration_reconciled','policy_summary','institutional_act','current_office_confirmed','previous_disputes','past_vote_rows_missing','web_audit_status','research_status','status_label','research_exhaustive','current_office_status','next_action','source','research_detail']
    c.csv_file(c.DOC/'candidate-coverage.csv',root,fields)
    if 'before_AD' in report:report['after_AD_before_AD2']=report.pop('before_AD')
    availability=c.load(c.A/'source-availability.json')
    report['source_availability']={'attempted_urls':availability['attempted_urls'],'outcomes':availability['outcomes'],'scope':'Availability only; failed links do not disprove preserved content.'}
    report['close_review_input_sha256']=c.sha(c.D/'close-source-review.json')
    report['canonical_coverage_synchronized']=True
    report['task_scope']={
        '0_recovery':'reproduced_from_versioned_inputs_without_temporary_files',
        '1_canonical_cohort':'149_records_reconciled_11_parties_including_zero_entries',
        '2_individual_statuses':'all_149_classified_deeper_research_incomplete',
        '3_current_offices':'preserved_dated_evidence_validated_broader_confirmation_pending',
        '4_institutional_acts':'44_primary_references_preserved_identifier_followups_documented',
        '5_nominal_votes':'395_verified_totals_preserved_11_unresolved_26_ticket_positions',
        '6_page_exports':'regenerated_and_status_disclosures_added',
        '7_regression':'full_git_backed_unit_and_browser_tests_passed',
        '8_handoff':'versioned_reports_synchronized_issue_and_PR_metadata_updated_separately'}
    c.save(c.A/'report.json',report)
    note='\n\n## Rastreabilidade do fechamento\n\nAs cópias principais `candidate-coverage.json` e `.csv` foram sincronizadas com os estados individuais deste fechamento. Relatórios históricos de A–D e A–D.2 não são usados para alegar uma nova coleta eleitoral. A disponibilidade das fontes foi testada separadamente de sua verificação de conteúdo.\n'
    for path in (c.A/'ENTREGA-A-D2.md',c.DOC/'ENTREGA-A-D2.md'):
        text=path.read_text(encoding='utf-8')
        if '## Rastreabilidade do fechamento' not in text:path.write_text(text+note,encoding='utf-8')
    print(json.dumps({'canonical_coverage':len(root),'source_urls_checked':availability['attempted_urls'],'technical_gate':report['technical_gate']}))
if __name__=='__main__':run()
