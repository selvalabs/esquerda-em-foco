"""Deterministic preparation from the frozen public source snapshot."""
from __future__ import annotations
import collections, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'data/rs';DEST=ROOT/'rs/deputados-federais'
def load(name,default):
    p=D/name
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def text(value): return '' if value is None or str(value) in ('#NE','#NULO','-1','-3') else str(value)
def run():
    records=load('candidates-official.json',[]); ids={r['SQ_CANDIDATO'] for r in records}; groups=collections.defaultdict(dict)
    for r in load('history-official.json',[]):
        cid=r.get('SQ_CANDIDATO_ATUAL');year=int(r['ANO_ELEICAO'])
        if cid not in ids or year>=2026:continue
        key=(year,r['SQ_CANDIDATO'],int(r.get('NR_TURNO') or 1))
        groups[cid][key]={'year':year,'round':key[2],'candidate_id':r['SQ_CANDIDATO'],'election_id':r.get('CD_ELEICAO'),'office':r.get('DS_CARGO'),'place':r.get('NM_UE'),'uf':r.get('SG_UF'),'party':r.get('SG_PARTIDO'),'result':text(r.get('DS_SIT_TOT_TURNO')),'votes':None,'source':'https://dadosabertos.tse.jus.br/dataset/candidatos-2026'}
    profiles=load('profiles-official.json',{})
    for r in records:
        cid=r['SQ_CANDIDATO'];profile=profiles.get(cid,{})
        for h in profile.get('data',{}).get('eleicoesAnteriores',[]):
            year=int(h.get('nrAno') or h.get('ano') or h.get('anoEleicao') or 2026)
            hid=str(h.get('id') or '')
            if year>=2026 or not hid:continue
            matches=[k for k in groups[cid] if k[0]==year and k[1]==hid]
            if matches:
                for k in matches:
                    if h.get('txLink'): groups[cid][k]['profile_url']=h['txLink']
            else:
                cargo=h.get('cargo')
                if isinstance(cargo,dict):cargo=cargo.get('nome') or cargo.get('descricao')
                party=h.get('partido')
                if isinstance(party,dict):party=party.get('sigla')
                groups[cid][(year,hid,1)]={'year':year,'round':1,'candidate_id':hid,'election_id':h.get('idEleicao'),'office':cargo or 'Cargo não informado','place':h.get('local') or 'Local não informado','uf':h.get('sgUf') or 'RS','party':party or h.get('sgPartido') or '', 'result':text(h.get('situacaoTotalizacao')),'votes':None,'profile_url':h.get('txLink'),'source':profile['url']}
        groups[cid][(2026,cid,1)]={'year':2026,'round':1,'candidate_id':cid,'office':'DEPUTADO FEDERAL','place':'RIO GRANDE DO SUL','uf':'RS','party':r['SG_PARTIDO'],'result':'Registro de candidatura; sem resultado eleitoral de 2026','votes':None,'source':'https://dadosabertos.tse.jus.br/dataset/candidatos-2026'}
    votes=load('votes-official.json',{})
    for hs in groups.values():
        for h in hs.values():
            v=votes.get(str(h['year']),{});key=h['candidate_id']+':'+str(h['round'])
            if key in v.get('totals',{}):h['votes']=v['totals'][key];h['votes_source']=v['source_url']
    normalized={cid:sorted(hs.values(),key=lambda h:(h['year'],h['round'],h['candidate_id'])) for cid,hs in groups.items()}
    from review_support import reconcile_history
    normalized=reconcile_history(normalized)
    save(D/'history-normalized.json',normalized)
    editorial=load('editorial.json',{});photos=load('photos-official.json',{});offices=load('offices-verified.json',{})
    audit=[]
    for r in records:
        cid=r['SQ_CANDIDATO'];prior=[h for h in normalized[cid] if h['year']<2026];latest=max(prior,key=lambda h:(h['year'],h['round']),default=None)
        audit.append({'candidate_id':cid,'name':r['NM_URNA_CANDIDATO'],'party':r['SG_PARTIDO'],'official_registration':True,'official_photo':cid in photos,'individual_tse_profile_read':'data' in profiles.get(cid,{}),'historical_disputes':len({(h['year'],h['candidate_id']) for h in prior}),'last_previous_vote_count_available':bool(latest and latest.get('votes') is not None),'current_office_institutionally_confirmed':cid in offices,'editorial_summary_documented':bool(editorial.get(cid,{}).get('pautas')),'editorial_sources':editorial.get(cid,{}).get('sources',[]),'limitations':([] if editorial.get(cid,{}).get('pautas') else ['Síntese de pautas não documentada nesta edição.'])+([] if cid in offices else ['Cargo eletivo atual não confirmado nesta edição.'])})
    save(ROOT/'docs/rs/candidate-audit.json',audit)
    # A predictable social preview; font files remain system dependencies, not distributed assets.
    image=Image.new('RGB',(1200,630),'#f2eadf');draw=ImageDraw.Draw(image)
    def font(size,serif=False):return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf' if serif else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size)
    draw.rectangle((55,56,64,565),fill='#365f4b')
    draw.text((96,65),'ESQUERDA EM FOCO',font=font(26),fill='#365f4b')
    draw.text((96,139),'Rio Grande do Sul',font=font(70,True),fill='#282b27')
    draw.text((98,253),'Deputado(a) Federal',font=font(47,True),fill='#365f4b')
    draw.text((98,340),'ELEIÇÕES 2026',font=font(26),fill='#6b6155')
    draw.line((98,421,1100,421),fill='#b8b1a5',width=2)
    draw.text((98,461),'Cadastro • Histórico • Pautas documentadas • Fontes',font=font(26),fill='#282b27')
    draw.text((98,515),'Consulta independente | Sem ranking de candidaturas',font=font(22),fill='#6b6155')
    assets=DEST/'assets';assets.mkdir(parents=True,exist_ok=True);image.save(assets/'og-rs.png',optimize=True)
    (DEST/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://selvalabs.github.io/esquerda-em-foco/rs/deputados-federais/</loc><lastmod>2026-09-21</lastmod></url></urlset>\n')
if __name__=='__main__':run()
