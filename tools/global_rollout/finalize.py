"""Apply reviewed source corrections once; production builds never call this helper.
Edits are exact-anchor and idempotent. No research source is modified.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def edit(path,old,new):
 p=ROOT/path;s=p.read_text()
 if new in s:return
 if s.count(old)!=1:raise ValueError('Ambiguous source migration: '+path+' '+old[:60])
 p.write_text(s.replace(old,new,1))
def main():
 p='tools/global_rollout/projection.py'
 edit(p,"a=ev['provenance'][0]['value'];native=a['family_id'];sources=[]", "a=ev['provenance'][0]['value'];native=a['family_id'];sources=[]\n    # Preserve the reviewed atomic wording, not the broader pre-review target.\n    ev['object']=a['match_text']")
 edit(p,"ev['semantic'],a['original_target'],sources", "ev['semantic'],a['match_text'],sources")
 p='tools/global_rollout/build.py'
 edit(p,' parties.append(row)',' parties.append(row);parties.append(el(\'button\',\'Todos os partidos\',type=\'button\',id=\'cqClearParties\',**{\'class\':\'eef-button\',\'disabled\':\'\'}))')
 edit(p,"  save(root/'data/global-rollout/source-hashes.json',{'baseline':BASE,'json_sources':sourcehashes})", "  save(root/'data/global-rollout/source-hashes.json',{'baseline':BASE,'json_sources':sourcehashes})\n  migration=load(root/'data/global-integration/migration-status.json')\n  migration['canonical_rollout']={'version':'1.0.0','issue':56,'baseline':BASE,'publication':'requires_verified_release_not_implied_by_build','editions':reports,'completed_scope':'production_implementation','issue50_implemented':False}\n  save(root/'data/global-integration/migration-status.json',migration)")
 p='assets/global/rollout.js'
 edit(p,"input.value=state.q;$('cqScope').value=state.scope;", "input.value=state.q;$('cqScope').value=state.scope;$('cqClearParties').disabled=!state.parties.length;")
 edit(p," function apply(raw){const next=C.normalize(raw,cfg);if(!same(next,state))window.EEFCollectionUI?.close();state=next;render();return C.copy(state);}", """ function apply(raw){
  const next=C.normalize(raw,cfg);
  if(!same(next,state))window.EEFCollectionUI?.close();
  if(next.scope!==state.scope||!same(next.selectors,state.selectors)){
   document.querySelectorAll('.cc-proof').forEach(proof=>{
    proof.querySelectorAll('[data-cc-evidence]').forEach(li=>li.hidden=false);
    proof.querySelectorAll('[data-cc-topic]').forEach(b=>b.setAttribute('aria-pressed','false'));
    const status=proof.querySelector('.cc-evidence-status');if(status)status.textContent='';
   });
  }
  state=next;render();return C.copy(state);
 }""")
 edit(p," $('eefQueryClear').addEventListener('click',()=>change(C.empty(cfg)));", " $('cqClearParties').addEventListener('click',()=>change({...state,parties:[]}));\n $('eefQueryClear').addEventListener('click',()=>change(C.empty(cfg)));")
 edit(p,"notice(parsed.legacy?'Consulta anterior preservada.","notice(parsed.ignored?.length?'A consulta anterior foi aplicada, mas algum critério não existe nesta edição e foi ignorado.':parsed.legacy?'Consulta anterior preservada.")
 p='tests/global_rollout/verify.py'
 edit(p,"'tools/global03/refresh.py',","'tools/global03/refresh.py','data/global-integration/migration-status.json',")
 edit(p,"  'tools/sp/publication/verify_live.py','tools/sc_semantic_v2_ui/verify_live.py',","  'tools/sp/publication/verify_live.py','tools/sc_semantic_v2_ui/verify_live.py',\n  '.github/workflows/global04-query-maintenance.yml',")
 edit(p,"    if 'current_support' in ev['scopes']:","    if name=='2026-sc-federais':check('SC object is reviewed text '+r['id'],ev['object']==value['match_text'])\n    if 'current_support' in ev['scopes']:")
 edit(p," check('760 published cards',", " newstatus=load(ROOT/'data/global-integration/migration-status.json');newstatus.pop('canonical_rollout')\n check('prior migration history retained',newstatus==load(baseline/'data/global-integration/migration-status.json'))\n check('760 published cards',")
 p='tools/sp/publication/verify_live.py'
 edit(p,'def browser_checks() -> list[dict]:','''def browser_checks() -> list[dict]:
    if 'id="cqData"' in (ROOT/'sp/deputados-federais/index.html').read_text():
        import sys
        sys.path.insert(0,str(ROOT/'tests/global_rollout'))
        import legacy_browser
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            try:return legacy_browser.sp(browser,SITE,OUT,ROWS)
            finally:browser.close()''')
 p='tools/sc_semantic_v2_ui/verify_live.py'
 edit(p,"OUT=Path('/tmp/sc-semantic-v2-ui-live');", "if 'id=\"cqData\"' in (ROOT/ENTRYPOINT).read_text():\n    FILES=list(dict.fromkeys(FILES+[x['path'] for x in json.loads((ROOT/'data/global03/publication-files.json').read_text())['files']]))\nOUT=Path('/tmp/sc-semantic-v2-ui-live');")
 file=ROOT/p;s=file.read_text()
 if "report['browser']=legacy_browser.sc" not in s:
  begin=s.index('        for width in (390,1440):');end=s.index('        browser.close()',begin)
  old=s[begin:end]
  new='''        if 'id="cqData"' in (ROOT/ENTRYPOINT).read_text():
            import sys
            sys.path.insert(0,str(ROOT/'tests/global_rollout'))
            import legacy_browser
            report['browser']=legacy_browser.sc(browser,BASE,OUT)
        else:
'''+''.join('    '+line if line.strip() else line for line in old.splitlines(True))
  file.write_text(s[:begin]+new+s[end:])
if __name__=='__main__':main()
