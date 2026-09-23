"""D5 operational metadata reconciliation. Never changes claims, HTML or runtimes.
Historical stage contracts remain intact; readiness is not research completeness.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,subprocess
from collections import Counter
from pathlib import Path
from bs4 import BeautifulSoup
import jsonschema
ROOT=Path(__file__).resolve().parents[2]
BASE='8a36b2a47a893746ea528646ff0bb40d6a2d9101'
REPORT='data/global-integration/reconciliation.json'
DOC='docs/GLOBAL-04-RECONCILIATION.md'
OLD_MUTABLE={'config/editions.json','data/global-integration/migration-status.json','data/global03/publication-files.json','tests/global_rollout/verify.py'}
NEW_ALLOWED={REPORT,DOC,'tools/global_reconciliation/reconcile.py','tests/global_reconciliation/test_contract.py','.github/workflows/global-reconciliation.yml','.github/workflows/reconciliation-prepare.yml'}
SCOPES=('current_support','documented_topic','legacy_context')
COMMON=('A01','A02','A03','A04','D01','D02','D06','D07','D08','D09','C01','C02','C03','E02','E04','I01','I02','I03','I04','I05','Q01','Q03','Q05')
LABELS={'registration':'Registro','aptitude':'Aptidão','mandate':'Mandato','history':'Histórico','region':'Localidade'}
LIMITS={
 'registration':'Status filtrável somente quando estruturado; o contexto original permanece na ficha.',
 'aptitude':'Aptidão não é deduzida do nome do status cadastral.',
 'mandate':'Sem confirmação não significa ausência; registro institucional, licença e declaração são distintos.',
 'history':'Não coletado não é estreia; zero, null e não aplicável são distintos.',
 'region':'Atuação com fonte, não residência ou base eleitoral presumida.'}
REASONS={
 'A01':'Catálogo único, separando publicação, pesquisa e capacidades.',
 'A02':'Shell e seletor de edição comuns, contexto atual explícito.',
 'A03':'Home geral e quatro hubs; edições em preparação não são publicadas.',
 'A04':'Identidade contextual ano/UF/cargo/candidatura e links antigos preservados.',
 'D01':'Termos normalizados em campos declarados; busca não classifica pautas.',
 'D02':'Multisseleção partidária por OU, combinada às demais dimensões.',
 'D03':'Disponibilidade de cadastro, mandato e histórico detalhada por dimensão.',
 'D04':'Localidade opcional somente com vínculo de atuação e fonte.',
 'D05':'Vínculos por recorte de evidência; cobertura não significa pesquisa completa.',
 'D06':'Qualquer/Todos, contagem distinta por candidatura e estado vazio explicado.',
 'D07':'39 temas e 16 grupos; equivalência e relação de escopo são distintas.',
 'D08':'Consulta v2, importação v1/dialetos antigos, compartilhamento explícito.',
 'D09':'Rotação diária e alfabética, sem relevância política.',
 'C01':'Cargo, UF, ano e identificação; desconhecidos explicitados.',
 'C02':'Mandato e histórico contextualizados, sem nova confirmação externa.',
 'C03':'Composição comum preserva textos, subtítulos, fontes e lacunas.',
 'E01':'Afirmação individual onde existente; fonte da síntese mantém sua granularidade.',
 'E02':'Publicação, consulta, pesquisa e redação distintas; datas ausentes explícitas.',
 'E03':'Motivo do filtro aponta a evidência pertinente e permite restaurar contexto.',
 'E04':'Origem e limites visíveis; falta de material não significa ausência de posição.',
 'E05':'Variantes/correções conservam formatos de origem; sem ressuscitar alegações.',
 'E06':'Exports de origem preservados; este round não cria export público único.',
 'I01':'Coleção manual ordenada, isolada por eleição/UF/cargo, sem persistência global.',
 'I02':'Leitor move a ficha original, não clone com IDs repetidos.',
 'I03':'Link e rascunho de compartilhamento; nenhum envio real é alegado.',
 'I04':'Link de ficha oculta suspende filtros e permite restaurar a consulta.',
 'I05':'Estado no documento, chave opaca no histórico, sem preferências persistentes.',
 'Q01':'Painel progressivo, ordem visual e larguras verificados no rollout.',
 'Q02':'Foco/noJS testados; auditoria global de acessibilidade permanece na #44.',
 'Q03':'Refresh das seis edições e renovação de proveniência; pesquisas independentes.',
 'Q04':'Rotas/canonical preservados; revisão global de SEO permanece na #44.',
 'Q05':'Evidência vinculada ao commit e gates de preservação/rebuild/publicação.',
 'N01':'Não globalizar hardcodes, inferências, ranking ou preferências persistentes.'}

def load(p):return json.loads(Path(p).read_text())
def enc(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def require(ok,message):
 if not ok:raise ValueError(message)
def base_bytes(path,baseline_root=None):
 if baseline_root:return (Path(baseline_root)/path).read_bytes()
 return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)

def states(cfg):
 dims={d['id']:d for d in cfg['dimensions']};any_theme=any(cfg['available'][s] for s in SCOPES)
 result={k:'ready' for k in COMMON}
 result.update(D03='ready' if all(dims[k]['state']=='ready' for k in ('registration','mandate','history')) else 'partial',
  D04=dims['region']['state'],D05='ready' if any_theme else 'blocked_data',
  E01='ready' if cfg['available']['documented_topic'] else 'edition_specific',
  E03='ready' if any_theme else 'blocked_data',E05='edition_specific',E06='edition_specific',
  Q02='partial',Q04='partial',N01='edition_specific')
 return result

def inspect(root,edition,old):
 raw=(root/edition['entrypoint']).read_bytes();doc=BeautifulSoup(raw,'html.parser')
 cfg=json.loads(doc.select_one('#cqData').get_text());eid=edition['edition_id'];cards=doc.select('article.candidate')
 require(cfg['edition_id']==eid,'Wrong edition identity '+eid)
 require(len(cfg['topics'])==39 and len(cfg['groups'])==16,'Taxonomy drift '+eid)
 require(len(cards)==len(cfg['records']),'Card count drift '+eid)
 require(len({c['id'] for c in cards})==len(cards),'Duplicate identity '+eid)
 require({c['id'] for c in cards}=={'candidato-'+r['id'] for r in cfg['records']},'Different identity sets '+eid)
 for selector in ('#eefQueryTools','#cqPanel','#eefQueryShareDialog','#eefCollection'):
  require(len(doc.select(selector))==1,'Duplicate/missing '+selector+' '+eid)
 for selector in ('.cc-context','.cc-transparency'):
  require(len(doc.select('article.candidate '+selector))==len(cards),'Missing context '+eid)
 for d in cfg['dimensions']:
  node=doc.select_one('#cq-'+d['id'])
  require(node is not None and node.has_attr('disabled')==(d['state']!='ready'),'Control/state mismatch '+eid+':'+d['id'])
  require([o['value'] for o in node.select('option')][1:]==[o['value'] for o in d['options']],'Option mismatch '+eid)
 counts={s:sum(any(s in ev['scopes'] for ev in r['evidence']) for r in cfg['records']) for s in SCOPES}
 for scope in SCOPES:
  require(sorted(cfg['available'][scope])==sorted({v['topic'] for r in cfg['records'] for v in r['evidence'] if scope in v['scopes']}),'Scope mismatch '+eid)
 dims=[]
 for d in cfg['dimensions']:
  values=Counter(r[d['id']] for r in cfg['records'])
  dims.append({'id':d['id'],'state':d['state'],'values':dict(sorted(values.items())),
   'options':d['options'],'limitation':LIMITS[d['id']],
   'blocking_reason':d['reason'] if d['state']!='ready' else None})
 current=states(cfg);require(set(current)==set(REASONS),'Incomplete capability mapping')
 rows=[]
 for key,value in sorted(current.items()):
  disposition='implemented' if value=='ready' else 'pending_global05' if key in ('Q02','Q04') else 'edition_specific' if value=='edition_specific' else 'documented_data_limit'
  rows.append({'id':key,'state':value,'disposition':disposition,'reason':REASONS[key],
   'previous_state':old['capabilities'][key]['state'],'followup_issue':44 if disposition=='pending_global05' else None})
 return {'edition_id':eid,'entrypoint':edition['entrypoint'],'html_sha256':sha(raw),'cards':len(cards),
  'topics':39,'groups':16,'dimensions':dims,'capabilities':rows,
  'scopes':{s:{'state':'ready' if cfg['available'][s] else 'blocked_data','available_topics':cfg['available'][s],
   'candidacies_with_association':counts[s],
   'reason':'Vínculos revisados neste recorte, sem alegar pesquisa completa.' if counts[s] else 'Sem vínculo revisado neste recorte; não significa ausência de posição.'} for s in SCOPES},
  'evidence_panels':len(doc.select('article.candidate .cc-proof')),
  'research_status':edition['research'],'snapshot':edition['snapshot']}

def document(report):
 lines=['# GLOBAL-04D5 · reconciliação final','',f'Baseline do produto: `{BASE}`. Issue #57; mãe #43; epic #39.','',
  '## Conclusão','',
  'As seis edições têm a mesma composição funcional. Diferenças de cobertura não significam seis sistemas de interface. O encerramento funcional não conclui pesquisas editoriais, a #44 ou a #50. Fechar a issue somente depois do gate público de metadados.','',
  '## Matriz operacional','',
  '| Edição | Fichas | Temas: atual / documentado / contexto | Registro | Aptidão | Mandato | Histórico | Localidade |',
  '|---|---:|---|---|---|---|---|---|']
 for r in report['rows']:
  ds={d['id']:('Disponível' if d['state']=='ready' else 'Sem base estruturada') for d in r['dimensions']}
  themes=' / '.join(str(len(r['scopes'][s]['available_topics'])) for s in SCOPES)
  lines.append('| '+r['edition_id']+' | '+str(r['cards'])+' | '+themes+' | '+' | '.join(ds[k] for k in LABELS)+' |')
 lines += ['',
  'Os totais temáticos contam conceitos com vínculos existentes, não candidaturas aptas ou mérito. As contagens por candidatura no JSON não devem ser somadas entre recortes.','',
  'SC Estadual conserva textos e fontes, mas não tem matriz temática individual revisada. Painel de fonte não autoriza associação candidato→tema. RS/PR mantêm contexto; SP mantém documentação temática; SC Federal tem os três recortes. Localidades com atuação documentada existem somente no PR nesta baseline.','',
  '## Divergências e decisões','',
  '- A01/A02/A03 e outras capacidades do catálogo operacional ainda carregavam estados da auditoria inicial. Foram reconciliadas; o inventário histórico não foi reescrito.',
  '- O campo `reason` do payload D4 é fallback para controle desabilitado, não diagnóstico de bloqueio quando a dimensão está ready. O relatório D5 separa `blocking_reason` de `limitation` sem mudar o runtime.',
  '- E01 conserva granularidade: afirmação individual em SC Federal/SP; síntese inteira ou fontes narrativas nas demais. Nenhum vínculo frase→fonte foi inventado.',
  '- E05/E06 são específicos de origem: correções e exports legados não foram substituídos por formatos públicos únicos. O modelo interno comum não é alegado como export público novo. Versões substituídas não são reintroduzidas como posições vigentes.',
  '- Q02/Q04 permanecem parciais para a #44. Foco/noJS e bytes já testados não equivalem a certificação integral de acessibilidade ou SEO.',
  '- Identidade é por candidatura/eleição/UF/cargo, não pessoa universal. #50 não foi implementada.','',
  '## Preservação e manutenção','',
  'Este round modifica catálogo de capacidades, status de migração, hash desse catálogo no manifesto e o teste que reconhece o fechamento D5. Páginas, JS/CSS, textos, fontes, fotos, associações e snapshots permanecem byte a byte iguais ao rollout. O teste protege todos os demais arquivos preexistentes.','',
  'O gerador D5 é determinístico. baseline/lot/editions no status conservam o contexto do lote 02; canonical_rollout registra D4; reconciliation é o fechamento atual. As 33 capacidades têm estado, justificativa e disposição no JSON. Nova pesquisa exige nova baseline, não restaurar este snapshot sobre conteúdo posterior.','',
  '## Evidências e publicação','',
  'Evidência D4 preservada: run 35844058016, artefato 10742911162, SHA-256 25994b1eaf8619d57af4ec163462b86eb116febaa4d857c59ff0b08a637e2a52. Não é execução D5. O workflow D5 registra testes, preservação e verificação pública próprios no artefato e na issue/PR.','',
  'Antes do merge, HTTP usa o manifesto da baseline publicada. Depois do merge, usa o novo manifesto, incluindo o catálogo reconciliado. Nunca exigir um hash ainda não publicado nem aceitar catálogo antigo como aprovação pós-merge.','',
  'A #43 pode fechar após a #57; o epic #39 só depois da #44. Sem pesquisa externa nova, mensagem WhatsApp real, preferências persistentes ou teste em aparelho físico.','']
 return '\n'.join(lines)

def outputs(baseline_root=None):
 reg=json.loads(base_bytes('config/editions.json',baseline_root));before=copy.deepcopy(reg)
 historical=json.loads(base_bytes('data/global-integration/migration-status.json',baseline_root));rows=[]
 for e in reg['editions']:
  if e['publication_status']!='published':continue
  old=next(x for x in before['editions'] if x['edition_id']==e['edition_id']);row=inspect(ROOT,e,old);rows.append(row)
  for c in row['capabilities']:e['capabilities'][c['id']]={'state':c['state'],'semantic':None,'audit_ref':'GLOBAL-04D5:'+c['id']}
  for scope in SCOPES:e['capabilities'][scope]={'state':row['scopes'][scope]['state'],'semantic':scope,'audit_ref':'GLOBAL-04D5:'+scope}
  e['migration']['reconciliation']='GLOBAL-04D5'
 jsonschema.validate(reg,load(ROOT/'config/editions.schema.json'))
 require(len(rows)==6 and sum(r['cards'] for r in rows)==760,'Published scope changed: renew baseline explicitly')
 for e in reg['editions']:
  old=next(x for x in before['editions'] if x['edition_id']==e['edition_id'])
  require(e['research']==old['research'] and e['snapshot']==old['snapshot'],'Research metadata changed')
  if e['publication_status']!='published':require(e==old,'Unpublished edition changed')
 report={'schema_version':'1.0.0','issue':57,'parent_issue':43,'baseline':BASE,
  'meaning':'Functional migration, not research completeness or GLOBAL-05 certification.',
  'capability_count':33,'edition_count':6,'cards':760,'rows':rows,
  'historical_registry_sha256':sha(base_bytes('config/editions.json',baseline_root)),
  'historical_migration_sha256':sha(base_bytes('data/global-integration/migration-status.json',baseline_root)),
  'unpublished':[e['edition_id'] for e in reg['editions'] if e['publication_status']!='published'],
  'deferred':[{'issue':44,'scope':'QA global, SEO, acessibilidade técnica e compatibilidade'},
              {'issue':50,'scope':'Caderno multi-edição posterior, não implementado'}],
  'product_evidence':{'commit':BASE,'run':35844058016,'artifact':10742911162,
   'artifact_sha256':'25994b1eaf8619d57af4ec163462b86eb116febaa4d857c59ff0b08a637e2a52',
   'scope':'Existing D4 evidence, not a new D5 run; D5 records its own artifact.'},
  'historical_sources':['data/global-integration/capability-matrix.json','data/global-integration/filter-capabilities.json'],
  'no_public_html_or_runtime_changes':True,'research_refetched':False}
 migration=copy.deepcopy(historical);migration['whole_issue_completed']=True
 migration['reconciliation']={'issue':57,'baseline':BASE,'report':REPORT,'scope':'functional_migration',
  'historical_top_level_scope':'baseline/lot/editions describe lot 02; canonical_rollout describes D4; reconciliation is current closure.',
  'previous_whole_issue_completed':historical['whole_issue_completed'],
  'global05_issue':44,'global05_completed':False,'issue50_implemented':False,
  'publication':'Product verified at D4 commit; D5 metadata must pass public verification before issue closure.'}
 manifest=json.loads(base_bytes('data/global03/publication-files.json',baseline_root))
 for item in manifest['files']:
  if item['path']=='config/editions.json':item['sha256']=sha(enc(reg).encode())
 return {'config/editions.json':enc(reg),'data/global-integration/migration-status.json':enc(migration),
  'data/global03/publication-files.json':enc(manifest),REPORT:enc(report),DOC:document(report)}

def preservation():
 names=subprocess.check_output(['git','ls-tree','-rz','--name-only',BASE],cwd=ROOT).decode().split('\0');protected=[]
 for path in filter(None,names):
  if path in OLD_MUTABLE:continue
  expected=base_bytes(path)
  require((ROOT/path).is_file() and (ROOT/path).read_bytes()==expected,'Unexpected change '+path);protected.append(path)
 changes=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT).decode().splitlines()
 require(set(changes)<=OLD_MUTABLE|NEW_ALLOWED,'Changes outside scope '+str(set(changes)-OLD_MUTABLE-NEW_ALLOWED))
 old=json.loads(base_bytes('data/global-integration/migration-status.json'));new=load(ROOT/'data/global-integration/migration-status.json')
 restored=copy.deepcopy(new);restored.pop('reconciliation');restored['whole_issue_completed']=old['whole_issue_completed']
 require(restored==old,'Historical migration data rewritten')
 return {'passed':True,'baseline':BASE,'protected_original_files':len(protected),'allowed_original_changes':sorted(OLD_MUTABLE),'actual_changes':changes}

def main():
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--build',action='store_true');g.add_argument('--check',action='store_true')
 p.add_argument('--baseline-root',type=Path);p.add_argument('--verify',action='store_true');p.add_argument('--out',type=Path);a=p.parse_args();expected=outputs(a.baseline_root)
 for path,content in expected.items():
  if a.build:(ROOT/path).parent.mkdir(parents=True,exist_ok=True);(ROOT/path).write_text(content)
  else:require((ROOT/path).read_text()==content,'Stale reconciliation '+path)
 report={'passed':True,'generated_files':len(expected),'edition_capability_cells':198,'cards':760}
 if a.verify:report['preservation']=preservation()
 if a.out:a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(enc(report))
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
