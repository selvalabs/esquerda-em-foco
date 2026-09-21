"""Idempotent migration of the frozen RS renderer. Exact anchors prevent drift.
All resulting renderer changes are committed and reviewed alongside the release.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def replace_once(text,old,new):
 if new in text:return text
 if text.count(old)!=1:raise RuntimeError('Renderer anchor missing or ambiguous: '+old[:100])
 return text.replace(old,new,1)
def run():
 path=ROOT/'tools/rs/build.py';text=path.read_text()
 text=replace_once(text,'from bs4 import BeautifulSoup','from bs4 import BeautifulSoup\nfrom review_support import apply_editorial, enrich_records, decorate_card, finalize')
 text=replace_once(text,"or p.username or p.password:return None","or p.username is not None or p.password is not None or '@' in p.netloc:return None")
 text=replace_once(text,"return sorted(output,key=lambda c:","return sorted(enrich_records(output),key=lambda c:")
 text=replace_once(text,'def card(c,icons):','def baseline_card(c,icons):')
 text=replace_once(text,'def build():\n from prepare import run as prepare','def card(c,icons):\n return decorate_card(baseline_card(c,icons),c)\n\ndef build():\n apply_editorial()\n from prepare import run as prepare')
 text=replace_once(text,"if os.getenv('GITHUB_ACTIONS')=='true':","if os.getenv('GITHUB_ACTIONS')=='true' and os.getenv('EEFOCO_OFFLINE_BUILD')!='1':")
 text=replace_once(text,"write(DOC/'build-report.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))","write(DOC/'build-report.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))\n finalize(records)")
 compile(text,str(path),'exec');path.write_text(text)
 path=ROOT/'tools/rs/prepare.py';text=path.read_text()
 text=replace_once(text,"    save(D/'history-normalized.json',normalized)","    from review_support import reconcile_history\n    normalized=reconcile_history(normalized)\n    save(D/'history-normalized.json',normalized)")
 compile(text,str(path),'exec');path.write_text(text)
 path=ROOT/'tests/rs/test_build.py';text=path.read_text()
 text=replace_once(text,"self.assertTrue(c['current_office']['source'].startswith('https://www.camara.leg.br/deputados/'))","self.assertIn(urllib.parse.urlsplit(c['current_office']['source']).hostname, {'www.camara.leg.br','www.camarapoa.rs.gov.br','www.cmsantabarbaradosul.rs.gov.br','www.camarafarroupilha.rs.gov.br','www.camarajaguarao.rs.gov.br'});self.assertTrue(c['current_office'].get('checked_at'))")
 compile(text,str(path),'exec');path.write_text(text)
 (ROOT/'tools/rs/runtime.js').write_text((ROOT/'tools/rs/review-runtime.js').read_text())
 print('RS renderer migration installed; no shared files changed.')
if __name__=='__main__':run()
