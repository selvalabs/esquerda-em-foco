"""QA estrutural e regressões semânticas explícitas; não certifica verdade política.
PRESERVATION_BASE aceita o SHA da base efetiva do PR. Sem dependências externas.
"""
from __future__ import annotations
from hashlib import sha1, sha256
import json
import os
from pathlib import Path
import subprocess
from build import BASE, ROOT, OUT, PINS, build, load, dump

CHECKS = []

def check(name, passed, detail=None):
    CHECKS.append({'name':name,'passed':bool(passed),'detail':detail})


def git(*args):
    return subprocess.check_output(['git', *args],cwd=ROOT)


def owned(path):
    return path.startswith(('tools/sc_semantic_v2/','data/sc-semantic-v2/')) or path in (
        'docs/SC-FEDERAIS-SEMANTICA-V2-ROUND1.md','.github/workflows/sc-semantic-v2-round1.yml')


def main():
    base = os.environ.get('PRESERVATION_BASE',BASE)
    require_git = git('rev-parse','--show-toplevel').decode().strip()
    check('Execução na raiz do repositório esperado',Path(require_git).resolve()==ROOT)
    before = load('data/sc-federais-topics-v1/matrix.json')
    audits = load('data/sc-semantic-v2/association-audit.json')['associations']
    candidates = load('data/sc-semantic-v2/candidate-content.json')['candidates']
    catalog = load('data/sc-semantic-v2/macrogroups.json')
    source_audit = load('data/sc-semantic-v2/source-review.json')['sources']
    family_audit = load('data/sc-semantic-v2/family-audit.json')['families']
    coverage = load('data/sc-semantic-v2/coverage.json')
    old = {a['association_id']:a for a in before['associations']}
    by_id = {a['association_id']:a for a in audits}
    by_candidate = {c['candidate_id']:c for c in candidates}
    source_ids = {s['source_id'] for s in source_audit}
    eligible = [a for a in audits if a['eligible_v2']]

    changed = []
    protected_count = 0
    for entry in git('ls-tree','-rz',base).split(b'\0'):
        if not entry:
            continue
        meta, name = entry.split(b'\t',1)
        mode, kind, digest = meta.decode().split()
        path = name.decode()
        if owned(path):
            continue
        protected_count += 1
        local = ROOT/path
        if kind!='blob' or not local.exists():
            changed.append(path)
            continue
        data = os.readlink(local).encode() if mode=='120000' else local.read_bytes()
        actual = sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if actual!=digest:
            changed.append(path)
    check('Todos os arquivos preexistentes fora desta auditoria preservados byte a byte',not changed,{'base':base,'files':protected_count,'changed':changed})
    diff = git('diff','--name-only',base,'--').decode().splitlines()
    check('Diff limitado aos arquivos de auditoria autorizados',all(owned(p) for p in diff),diff)
    check('Insumos documentais v1 não alterados',all(sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in PINS.items()))
    check('48 candidaturas com IDs, nomes, partidos e âncoras preservados',len(candidates)==48 and {
        (c['candidate_id'],c['name'],c['party'],c['anchor']) for c in candidates}=={
        (c['candidate_id'],c['name'],c['party'],c['anchor']) for c in before['candidates']})
    check('156 associações únicas e nenhuma omitida',len(audits)==len(by_id)==156 and set(old)==set(by_id))
    check('Todas as 123 associações antes ativas têm decisão',sum(a['eligible_v1'] for a in audits)==123 and all(a['eligible_v1']==old[a['association_id']]['eligible_current_support'] for a in audits))
    check('Toda decisão tem texto, justificativa, fonte e bloco',all(a['match_text'] and a['rationale_and_locator'] and a['source_ids'] and a['section'] for a in audits))
    check('Fontes e claims continuam vinculados à associação correta',all(a['source_ids']==old[a['association_id']]['source_ids'] and a['claim_id']==old[a['association_id']]['claim_id'] and set(a['source_ids'])<=source_ids for a in audits))
    check('52 grupos de afirmações originais contemplados',len({a['claim_id'] for a in audits})==52)
    check('19 lacunas anteriores sem associações fabricadas',sum(not c['association_ids'] for c in candidates)==19 and all(not c['current_macro_ids'] and c['documentation_note'] for c in candidates if not c['association_ids']))
    check('112 associações permanecem elegíveis; 11 reclassificadas; nenhuma promoção automática',len(eligible)==112 and sum(a['eligible_v1'] and not a['eligible_v2'] for a in audits)==11 and not any(a['eligible_v2'] and not a['eligible_v1'] for a in audits))
    check('Elegibilidade vem somente de apoio/prioridade atual reconfirmada',all(a['section']=='pautas' and a['nature'] in {'apoio_atual_a_medida','prioridade_atual_explicita'} and a['all_sources_reconfirmed'] for a in eligible))
    check('29 famílias preservadas e cada uma em um único macrogrupo',len(family_audit)==29 and len({f['id'] for f in family_audit})==29 and sorted(f['id'] for f in family_audit)==sorted(t for g in catalog['groups'] for t in g['family_ids']))
    check('14 macrogrupos propostos sem ativação visual',len(catalog['groups'])==14 and catalog['ui_active'] is False and coverage['filters_v2_active'] is False)
    check('Cultura e relações internacionais não foram fundidas',next(g for g in catalog['groups'] if g['id']=='cultura')['family_ids']==['cultura'] and next(g for g in catalog['groups'] if g['id']=='relacoes-internacionais')['family_ids']==['politica-internacional'])
    check('Contagens dos macrogrupos são pessoas distintas',all(g['current_candidate_count']==len({a['candidate_id'] for a in eligible if a['macro_id']==g['id']}) for g in catalog['groups']))
    check('Macrogrupo não propaga associação a famílias irmãs',all(set(c['current_family_ids'])=={a['family_id'] for a in eligible if a['candidate_id']==c['candidate_id']} for c in candidates))
    check('Nenhum bloco vazio é renderizável e contexto não vira pauta',all(s['items'] and s['summary'] and s['filter_source']==(s['id']=='pautas') and all(i['eligible']==(s['id']=='pautas') for i in s['items']) for c in candidates for s in c['sections']))
    check('Textos de correspondência são frases sem prefixo mecânico',all(not a['match_text'].startswith(('Apoio declarado:','Prioridade declarada:')) for a in audits))
    check('Jú continua em tributação por proposta de impostos, não por declaração de bens',by_id['240002533832-c3--tributacao']['eligible_v2'] and by_id['240002533832-c3--tributacao']['match_text']=='Defende impostos proporcionais à renda e ao patrimônio.')
    check('Gil não recebe tributação por comentário de terceiro',by_candidate['240002537839']['current_family_ids']==['direitos-trabalhistas'])
    check('Ju Andozio não recebe direitos trabalhistas pela biografia em 6×1','direitos-trabalhistas' not in by_candidate['240002533838']['current_family_ids'])
    check('Ana: salário mínimo atual separado de voto relatado sobre 6×1','salário mínimo' in by_id['240002533824-c3--direitos-trabalhistas']['match_text'] and '6×1' not in by_id['240002533824-c3--direitos-trabalhistas']['match_text'] and any('6×1' in i['text'] for s in by_candidate['240002533824']['sections'] if s['id']=='historico' for i in s['items']))
    check('Uczai: requerimento de seminário permanece como atuação',by_id['240002533833-c1--educacao']['section']=='historico' and not by_id['240002533833-c1--educacao']['eligible_v2'])
    check('Nandja: museu iniciado antes mas reafirmado mantém elegibilidade',by_id['240002537841-c1--cultura']['eligible_v2'])
    check('Lirous mantém seis prioridades amplas explicitamente declaradas',len(by_candidate['240002533827']['current_family_ids'])==6)
    check('Material sem período ou de atribuição pendente fica em contexto',all(a['section']=='contexto' and not a['eligible_v2'] for a in audits if a['nature'] in {'periodo_nao_confirmado','atribuicao_conjunta_pendente'}))
    check('Oposição permanece documentada sem virar apoio',sum(a['nature']=='oposicao_atual' for a in audits)==6 and all(not a['eligible_v2'] and a['section']=='posicoes' for a in audits if a['nature']=='oposicao_atual'))
    check('36 fontes com resultado explícito, 35 reconfirmadas e uma limitação',len(source_audit)==36 and sum(s['content_reconfirmed'] for s in source_audit)==35 and coverage['sources_not_reconfirmed']==['240002533820-s1'])
    check('Ivan não é falsamente marcado como fonte reconfirmada ou pauta atual',not by_id['240002533820-c1--moradia-cidades']['all_sources_reconfirmed'] and not by_id['240002533820-c1--moradia-cidades']['eligible_v2'])
    check('Datas de publicação não copiadas automaticamente para eventos',all(a['event_date'] is None for a in audits))
    outputs = sorted(OUT.glob('*.json'))
    outputs = [p for p in outputs if p.name!='qa.json']+[ROOT/'docs/SC-FEDERAIS-SEMANTICA-V2-ROUND1.md']
    hashes = {str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in outputs}
    build()
    check('Reconstrução determinística de todos os dados e do relatório',all(sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items()),hashes)
    result = {'status':'passed' if all(c['passed'] for c in CHECKS) else 'failed',
              'scope':'Dados/modelo editorial; não é QA visual da futura UI, teste em aparelho ou certificação automática das interpretações políticas.',
              'base_commit':base,'checked_commit':git('rev-parse','HEAD').decode().strip(),
              'checks_count':len(CHECKS),'failed_count':sum(not c['passed'] for c in CHECKS),'checks':CHECKS}
    dump(OUT/'qa.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False))
    if result['status']!='passed':
        raise SystemExit(1)


if __name__=='__main__':
    main()
