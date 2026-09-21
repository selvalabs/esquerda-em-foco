"""Idempotent exact-anchor upgrade; no shared/public non-RS files are edited."""
import hashlib
from pathlib import Path
from fed03_baseline import expected_sc_sha256
ROOT=Path(__file__).resolve().parents[2]
def replace(text,old,new):
    if new in text:return text
    if text.count(old)!=1:raise RuntimeError('Missing or ambiguous upgrade anchor: '+old[:100])
    return text.replace(old,new,1)
def install_sc_reference(text):
    expr='expected_sc_sha256(ROOT)'
    if expr not in text:
        old_hashes=('7bbb7a78f2cb9b5ec8844e0abf7be1cb16d7b248f9aa22a0bdd2686493212642','8a9bdffb2ad20a53857c0ac3fd4d02ce9980e10dd162235479971f4e63ffe2f5')
        matches=["'"+h+"'" for h in old_hashes if "'"+h+"'" in text]
        if len(matches)!=1:raise RuntimeError('Known preservation assertion not found')
        text=replace(text,matches[0],expr)
    return text

def run():
    if hashlib.sha256((ROOT/'index.html').read_bytes()).hexdigest()!=expected_sc_sha256(ROOT):
        raise RuntimeError('SC working tree differs from checked-out Git commit; do not overwrite it')
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
    compile(text,str(path),'exec');path.write_text(text,encoding='utf-8')
    path=ROOT/'tests/rs/test_build.py';text=path.read_text(encoding='utf-8')
    text=replace(text,"'www.camarajaguarao.rs.gov.br'}","'www.camarajaguarao.rs.gov.br','www.santanadolivramento.rs.leg.br'}")
    text=replace(text,'from bs4 import BeautifulSoup',"from bs4 import BeautifulSoup\nimport sys\nsys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/rs'))\nfrom fed03_baseline import expected_sc_sha256")
    text=install_sc_reference(text);compile(text,str(path),'exec');path.write_text(text,encoding='utf-8')
    path=ROOT/'tools/rs/qa.py';text=path.read_text(encoding='utf-8')
    text=replace(text,'from playwright.sync_api import sync_playwright','from playwright.sync_api import sync_playwright\nfrom fed03_baseline import expected_sc_sha256')
    text=install_sc_reference(text);compile(text,str(path),'exec');path.write_text(text,encoding='utf-8')
    print('RS-FED-03 installed; preservation assertions reference the current Git commit, never the working copy.')
if __name__=='__main__':run()
