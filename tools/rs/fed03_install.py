"""Idempotent exact-anchor upgrade; no shared/public non-RS files are edited."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def replace(text,old,new):
    if new in text:return text
    if text.count(old)!=1:raise RuntimeError('Missing or ambiguous upgrade anchor: '+old[:100])
    return text.replace(old,new,1)
def run():
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
    text=replace(text,"counts['not_verified'],8","counts['not_verified'],2")
    compile(text,str(path),'exec');path.write_text(text,encoding='utf-8')
    path=ROOT/'tests/rs/test_build.py';text=path.read_text(encoding='utf-8')
    text=replace(text,"'www.camarajaguarao.rs.gov.br'}","'www.camarajaguarao.rs.gov.br','www.santanadolivramento.rs.leg.br'}")
    compile(text,str(path),'exec');path.write_text(text,encoding='utf-8')
    print('RS-FED-03 installed; previous reports and other fronts untouched.')
if __name__=='__main__':run()
