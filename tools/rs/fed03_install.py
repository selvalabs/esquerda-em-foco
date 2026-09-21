"""Idempotent exact-anchor upgrade; no shared/public non-RS files are edited."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def replace(text,old,new):
    if new in text:return text
    if text.count(old)!=1:raise RuntimeError('Missing or ambiguous upgrade anchor: '+old[:100])
    return text.replace(old,new,1)
def run():
    integration=json.loads((ROOT/'data/rs/fed03/integration-base.json').read_text())
    expected=integration['sc_sha256']
    if hashlib.sha256((ROOT/'index.html').read_bytes()).hexdigest()!=expected:
        raise RuntimeError('SC differs from the explicitly reconciled upstream baseline; rebaseline required')
    try:
        pinned=subprocess.check_output(['git','show',integration['upstream_commit']+':index.html'],cwd=ROOT,stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:pinned=None
    if pinned is not None and hashlib.sha256(pinned).hexdigest()!=expected:raise RuntimeError('Pinned SC baseline hash mismatch')
    path=ROOT/'tools/rs/review_support.py';text=path.read_text(encoding='utf-8')
    text=replace(text,' for cid,e in editorial.items():',' from fed03_support import extend_editorial\n extend_editorial(editorial,offices)\n for cid,e in editorial.items():')
    text=replace(text,' return histories',' from fed03_support import extend_history\n return extend_history(histories)')
    text=replace(text,'def finalize(records):','def _finalize_round_two(records):')
    wrapper='\ndef finalize(records):\n from fed03_support import finalize_round_three\n return finalize_round_three(records,_finalize_round_two)\n'
    if wrapper not in text:text+=wrapper
    compile(text,str(path),'exec');path.write_text(text,encoding='utf-8')
    path=ROOT/'tests/rs/test_review.py';text=path.read_text(encoding='utf-8')
    text=text.replace('docs/rs/review/final-report.json','docs/rs/fed03/final-report.json').replace('docs/rs/review/candidate-matrix.json','docs/rs/fed03/candidate-matrix.json')
    text=replace(text,"self.public['schema_version'],2","self.public['schema_version'],3")
    text=replace(text,"counts['verified_nominal'],276","counts['verified_nominal'],277")
    # Current upstream no longer hard-codes the number of unresolved records.
    # The exact five remaining records are asserted by the round-three tests.
    compile(text,str(path),'exec');path.write_text(text,encoding='utf-8')
    path=ROOT/'tests/rs/test_build.py';text=path.read_text(encoding='utf-8')
    text=replace(text,"'www.camarajaguarao.rs.gov.br'}","'www.camarajaguarao.rs.gov.br','www.santanadolivramento.rs.leg.br'}")
    old='7bbb7a78f2cb9b5ec8844e0abf7be1cb16d7b248f9aa22a0bdd2686493212642'
    text=replace(text,old,expected)
    compile(text,str(path),'exec');path.write_text(text,encoding='utf-8')
    path=ROOT/'tools/rs/qa.py';text=path.read_text(encoding='utf-8')
    text=replace(text,old,expected)
    compile(text,str(path),'exec');path.write_text(text,encoding='utf-8')
    print('RS-FED-03 installed on reconciled canonical scope; prior evidence and all other fronts preserved.')
if __name__=='__main__':run()
