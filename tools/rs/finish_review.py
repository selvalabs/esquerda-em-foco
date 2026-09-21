"""Idempotent completion of RS-FED-02; never writes outside RS files.
The published SC baseline is deliberately different from the older visual template.
"""
from pathlib import Path
import json, subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='810a7896b3355254d50852761a41bae31ce3f567'
OLD='4b7f82c4e8dc95e54ec3e3be2a9954f81d06b0edceb530e900aebe68cd2c36ea'
CURRENT='7bbb7a78f2cb9b5ec8844e0abf7be1cb16d7b248f9aa22a0bdd2686493212642'
APPLY='''def apply_editorial():
 # Rebuild from frozen inputs, not from the output of a previous build.
 editorial=load(D/'editorial-baseline.json',{})
 if not editorial:raise RuntimeError('Run upgrade_review.py first')
 offices=load(D/'offices-baseline.json',{})
 changes=load(D/'review-editorial.json',{});extra=load(D/'review-addendum.json',{})
 ids={r['SQ_CANDIDATO'] for r in load(D/'candidates-official.json',[])}
 for cid,topics in changes.get('existing_topic_assignments',{}).items():
  assert cid in ids and editorial.get(cid,{}).get('pautas'),cid
  entry=editorial[cid];sources=sorted(s['url'] for s in entry['sources'])
  entry['topics']=[{'id':topic,'sources':sources} for topic in topics]
  entry.setdefault('summary_kind','documented_mixed')
 for change in changes.get('entries',[])+extra.get('entries',[]):
  cid=change['id'];assert cid in ids,cid
  assert safe_url(change['url']),change['url']
  entry=editorial.setdefault(cid,{'sources':[]})
  for field in ('pautas','biography','summary_kind'):
   if field in change:entry[field]=change[field]
  if 'pautas' in change:entry['topics']=[]
  if change.get('replace_sources'):entry['sources']=[]
  source={'url':change['url'],'label':change['label'],'source_type':change['source_type'],'checked_at':DATE,'period':change.get('period','Período indicado no texto da ficha')}
  entry['sources']=[s for s in entry.get('sources',[]) if s['url']!=change['url']]+[source]
  existing={t['id']:t for t in entry.get('topics',[])}
  for topic in change.get('topics',[]):
   assert topic in TOPICS,topic
   old=existing.get(topic,{'id':topic,'sources':[]});old['sources']=sorted(set(old['sources']+[change['url']]));existing[topic]=old
  entry['topics']=sorted(existing.values(),key=lambda x:x['id']);entry['checked_at']=DATE
  if change.get('limitation'):entry['source_limitation']=change['limitation']
  elif change.get('replace_sources'):entry.pop('source_limitation',None)
  if change.get('office'):
   assert change['source_type']=='institutional'
   offices[cid]={'label':change['office'],'source':change.get('office_source',change['url']),'checked_at':DATE,'confirmation':'Diretório institucional consultado; não inferido do resultado eleitoral.'}
 for cid,e in editorial.items():
  e['sources']=sorted(e['sources'],key=lambda s:s['url'])
  for topic in e.get('topics',[]):
   assert topic['id'] in TOPICS and topic['sources']
   assert set(topic['sources']).issubset({s['url'] for s in e['sources']})
 save(D/'editorial.json',editorial);save(D/'offices-verified.json',offices)
 save(D/'topics.json',{'version':1,'checked_at':DATE,'rule':'Vocabulário documental, sem novos filtros nesta rodada. Fontes e período são específicos por candidatura. Registros históricos não estabelecem apoio atual nem compromisso de campanha de 2026.','topics':TOPICS})
'''
def run():
 for original,dest in [('data/rs/editorial.json','data/rs/editorial-baseline.json'),('data/rs/offices-verified.json','data/rs/offices-baseline.json')]:
  p=ROOT/dest
  if not p.exists():p.write_bytes(subprocess.check_output(['git','show',BASE+':'+original],cwd=ROOT))
 # Runtime stays byte-identical to the published edition: no new filter controls.
 (ROOT/'tools/rs/runtime.js').write_bytes(subprocess.check_output(['git','show',BASE+':tools/rs/runtime.js'],cwd=ROOT))
 p=ROOT/'tools/rs/review_support.py';text=p.read_text()
 a=text.index('def apply_editorial():');b=text.index('\ndef reconcile_history',a);text=text[:a]+APPLY+text[b:]
 marker=" if c.get('topics'):\n  box=soup.new_tag"
 if marker in text:
  a=text.index(marker);b=text.index(" if c.get('source_limitation'):",a);text=text[:a]+text[b:]
 marker=" controls=soup.new_tag('section'"
 if marker in text:
  a=text.index(marker);b=text.index(" note=soup.new_tag",a)
  text=text[:a]+" css=soup.new_tag('style',attrs={'id':'rs-review-styles'});css.string='.rs-vote-note{display:block;margin-top:3px}.rs-review-note{line-height:1.6}.rs-source-limitation{margin-top:10px}'\n soup.head.append(css)\n"+text[b:]
 text=text.replace('A seleção por temas inclui apenas associações com fontes e não exclui propostas que ainda não foram documentadas aqui.','Os temas foram organizados na base estruturada, sem alterar os filtros da interface. Não há atualização em tempo real.')
 if "journal=load(D/'review-search-log.json'" not in text:
  text=text.replace(" A.mkdir(parents=True,exist_ok=True);soup=", " A.mkdir(parents=True,exist_ok=True);journal=load(D/'review-search-log.json',{});soup=")
  text=text.replace("'remaining_editorial_work':None", "'research_record':journal.get(c['id'],{}),'remaining_editorial_work':None")
  text=text.replace("'with_biography':biography_count", "'with_biography':biography_count,'with_documented_policy_or_action':sum(bool(c['pautas']) and c.get('summary_kind')!='trajectory' for c in records),'trajectory_only_summaries':sum(bool(c['pautas']) and c.get('summary_kind')=='trajectory' for c in records),'research_log_entries':len(journal),'new_filter_ui':False")
  text=text.replace("'registry_profile_rechecked':True", "'registry_profile_rechecked':bool(load(D/'profiles-official.json',{}).get(c['id'],{}).get('checked_at','').startswith(DATE))")
 compile(text,str(p),'exec');p.write_text(text)
 # Correct the regression reference without changing any SC bytes.
 for name in ['tests/rs/test_build.py','tools/rs/qa.py']:
  p=ROOT/name;p.write_text(p.read_text().replace(OLD,CURRENT))
 p=ROOT/'tests/rs/test_review.py';text=p.read_text()
 if ' def test_filters_accessible' in text:
  a=text.index(' def test_filters_accessible');b=text.index(' def test_raw_bad_addresses',a)
  text=text[:a]+''' def test_no_new_filter_ui(self):
  self.assertIsNone(self.soup.select_one('#partyFilter'));self.assertIsNone(self.soup.select_one('#topicFilters'));self.assertIsNone(self.soup.select_one('.rs-topics'));self.assertFalse(self.report['new_filter_ui'])
 def test_research_log_population(self):
  log=json.loads((ROOT/'data/rs/review-search-log.json').read_text());self.assertEqual({c['id'] for c in self.cs},set(log))
  for row in log.values():self.assertTrue(row.get('queries') or row.get('sources'))
'''+text[b:]
 compile(text,str(p),'exec');p.write_text(text)
 print('Stable RS editorial inputs installed; existing UI and current SC baseline preserved.')
if __name__=='__main__':run()
