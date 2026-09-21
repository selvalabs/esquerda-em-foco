"""Generate a factual audit trail; no network and no inferred campaign positions."""
from pathlib import Path
import collections, hashlib, json, urllib.parse
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'data/rs';A=ROOT/'docs/rs/review'
def load(p,default=None):return json.loads(p.read_text()) if p.exists() else default
def save(p,value):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run():
 from review_support import apply_editorial
 apply_editorial()
 from build import normalize_records
 records,_=normalize_records();ids={c['id'] for c in records}
 searches={r['id']:r['queries'] for r in load(D/'review-searches.json',{})['entries']}
 assert set(searches).issubset(ids)
 profiles=load(D/'profiles-official.json',{});http={r['url']:r for r in load(A/'source-http-review.json',[])}
 institutional=load(A/'institutional-directory-review.json',{}).get('pages',[])
 log={};bad=[]
 for c in records:
  cid=c['id'];profile=profiles[cid]
  sources=[{'url':profile['url'],'purpose':'electoral_registration','checked_at':profile['checked_at'],'sha256':profile.get('sha256'),'not_evidence_of_policy':True}]
  for s in c['editorial_sources']:
   entry={'url':s['url'],'purpose':'editorial_document','label':s['label'],'period':s.get('period','Período indicado no texto'),'source_type':s.get('source_type','Source type recorded in original editorial research')}
   if s['url'] in http:entry['http_availability_check']=http[s['url']]
   sources.append(entry)
  if c.get('current_office'):sources.append({'url':c['current_office']['source'],'purpose':'institutional_office_confirmation','checked_at':c['current_office'].get('checked_at')})
  for site in c['sites']:
   if site['url'] in http:sources.append({'url':site['url'],'purpose':'declared_site_availability_only','http_availability_check':http[site['url']],'not_evidence_of_policy':True})
  log[cid]={'id':cid,'name':c['name'],'checked_at':'2026-09-21','queries':searches.get(cid,[]),'sources':sources,'summary_documented':bool(c['pautas']),'biography_documented':bool(c.get('biography')),'current_office_confirmed':bool(c.get('current_office')),'current_office_search_exhaustive':False,'remaining_editorial_gap':None if c['pautas'] else 'As fontes consultadas não sustentam uma síntese individual de pautas ou atuação. Isso não significa ausência de propostas.','method_limit':'Busca, cadastro eleitoral e disponibilidade HTTP não comprovam, isoladamente, apoio a uma pauta ou exercício de mandato.'}
  for value in c['invalid_declared_urls']:
   v=value.strip();lower=v.lower()
   reason='malformed_or_incomplete_address'
   if v.startswith('@'):reason='handle_without_verified_platform'
   elif '@' in v and '://' not in v:reason='contact_address_not_a_public_profile_url'
   elif any(ch.isspace() for ch in v):reason='text_or_spaces_in_address'
   elif lower.startswith('https:') and not lower.startswith('https://'):reason='malformed_scheme'
   bad.append({'id':cid,'name':c['name'],'declared_value_sha256':hashlib.sha256(value.encode()).hexdigest(),'disposition':'not_rendered','reason':reason,'replacement':None,'replacement_note':'Nenhum canal foi inferido. Só substituir com comprovação individual.','checked_at':'2026-09-21'})
 save(D/'review-search-log.json',log)
 save(A/'declared-links-review.json',{'method':'Revisão sintática e de segurança de todos os endereços rejeitados; valores originais não reproduzidos neste relatório. Bloqueios HTTP não são classificados como links inexistentes.','count':len(bad),'records':bad,'source_http_checks':len(http),'verified_replacements':0})
 save(A/'research-log-summary.json',{'candidate_count':len(records),'individual_registry_checks':len(profiles),'with_recorded_individual_queries':len(searches),'with_editorial_documents':sum(bool(c['editorial_sources']) for c in records),'with_summary':sum(bool(c['pautas']) for c in records),'with_biography':sum(bool(c.get('biography')) for c in records),'invalid_declared_values_reviewed':len(bad),'source_availability_checks':len(http),'all_offices_exhaustively_verified':False,'note':'Todas as fichas possuem controle. Isso não significa que todas as lacunas editoriais tenham sido preenchidas.'})
 print('Research audit:',len(log),'candidate records;',len(searches),'individual query registers;',len(bad),'rejected declarations reviewed.')
if __name__=='__main__':run()
