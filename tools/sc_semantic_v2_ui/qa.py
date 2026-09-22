"""QA do frontend v2 e das fronteiras documentais. Sem nova pesquisa política.
PRESERVATION_BASE = base efetiva do PR. CHROMIUM_PATH permite navegador local.
"""
from __future__ import annotations
from collections import Counter
from functools import partial
from hashlib import sha256
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json, os
from pathlib import Path
import subprocess, sys, threading, traceback
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from build import ROOT, OUT, BASE, INPUTS, build, load, normalize_index, COPY_RE
import re

PRESERVATION = os.environ.get('PRESERVATION_BASE', BASE)
SHOTS = Path(os.environ.get('QA_SHOTS', '/tmp/sc-v2-ui-shots'))
SHOTS.mkdir(exist_ok=True, parents=True)
checks=[]

def check(name, ok, detail=None):
    checks.append({'name':name,'passed':bool(ok),'detail':detail})
    if not ok:
        raise AssertionError(name+': '+str(detail))

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)

def allowed(p):
    return p=='index.html' or p in {'assets/pauta-v2.css','assets/pauta-filters-v2.js','assets/sc-federais-filters-v2-data.js','.github/workflows/sc-semantic-v2-ui.yml'} or p.startswith(('tools/sc_semantic_v2_ui/','data/sc-semantic-v2-ui/','docs/SC-FEDERAIS-SEMANTICA-V2-UI','tests/sc_semantic_v2_ui'))

def static_tests():
    old=git('show',f'{PRESERVATION}:index.html').decode()
    current=(ROOT/'index.html').read_text()
    check('HTML fora dos blocos editoriais/filtros preservado',normalize_index(old)==normalize_index(current))
    paths=git('ls-tree','-r','--name-only',PRESERVATION).decode().splitlines()
    protected=[p for p in paths if not allowed(p)]
    changed=[p for p in protected if not (ROOT/p).is_file() or (ROOT/p).read_bytes()!=git('show',f'{PRESERVATION}:{p}')]
    check('Outras frentes e todos os insumos preservados byte a byte',not changed,{'base':PRESERVATION,'files':len(protected),'changed':changed})
    current_soup,old_soup=BeautifulSoup(current,'html.parser'),BeautifulSoup(old,'html.parser')
    check('Navbar, hero, trajetória e rodapé preservados',all(str(current_soup.select_one(sel))==str(old_soup.select_one(sel)) for sel in ('#siteNav','.persistent-footer','.masthead')))
    old_cards={x['data-tse-id']:x for x in old_soup.select('article.candidate')}
    new_cards={x['data-tse-id']:x for x in current_soup.select('article.candidate')}
    check('48 identidades e âncoras preservadas',len(new_cards)==48 and set(old_cards)==set(new_cards))
    for cid in new_cards:
        for selector in ('.candidate-head','.candidate-links','.career-band'):
            check(f'{cid} preserva {selector}',str(new_cards[cid].select_one(selector))==str(old_cards[cid].select_one(selector)))
    data=load('data/sc-semantic-v2-ui/payload.json')
    manifest=load('data/sc-semantic-v2-ui/manifest.json')
    audit=load('data/sc-semantic-v2/association-audit.json')['associations']
    models=load('data/sc-semantic-v2/candidate-content.json')['candidates']
    by_aid={a['association_id']:a for a in audit}
    observed=[]
    for c in data['candidates']:
        for m in c['matches']:
            a=by_aid[m['associationId']]
            check('Correspondência exata '+m['associationId'],a['eligible_v2'] and a['candidate_id']==c['id'] and a['macro_id']==m['topicId'] and a['family_id']==m['familyId'] and a['match_text']==m['text'] and a['source_ids']==m['sourceIds'])
            observed.append(m['associationId'])
    check('Exatamente 112 associações aprovadas, sem 11 reclassificadas',len(observed)==112 and len(set(observed))==112 and set(observed)=={a['association_id'] for a in audit if a['eligible_v2']})
    check('13 filtros amplos/14 grupos/29 famílias; 19 pessoas elegíveis',len(data['topics'])==13 and len(data['families'])==29 and sum(bool(c['matches']) for c in data['candidates'])==19 and manifest['no_current_matches']==['relacoes-internacionais'])
    for c in models:
        card=new_cards[c['candidate_id']]
        sections=card.select('[data-pauta-section]')
        check(c['name']+': blocos corretos, sem vazio', [x['data-pauta-section'] for x in sections]==[s['id'] for s in c['sections']])
        for s in c['sections']:
            paragraph=card.select_one(f'[data-pauta-section="{s["id"]}"] .pauta-v2-copy')
            copy=BeautifulSoup(str(paragraph),'html.parser');[a.decompose() for a in copy.select('a')]
            check(c['name']+': texto aprovado '+s['id'],copy.get_text(' ',strip=True)==s['summary'])
        expected_items={i['item_id']:i for s in c['sections'] for i in s['items']}
        actual_items=card.select('[data-evidence-item]')
        check(c['name']+': evidências por bloco acessíveis',len(actual_items)==len(expected_items) and all(i['data-evidence-item'] in expected_items for i in actual_items))
    ids=[x['id'] for x in current_soup.select('[id]')]
    check('IDs únicos e links legados preservados',len(ids)==len(set(ids)) and {x['id'] for x in old_soup.select('[id]')}<=set(ids))
    check('Todas as âncoras locais resolvem',all(a['href']=='#' or a['href'][1:] in set(ids) for a in current_soup.select('a[href^="#"]')))
    check('Runtime v1 não carregado; versão v2 exclusiva',not current_soup.select('script[src^="assets/pauta-filters.js"],script[src^="assets/sc-federais-filters-data.js"]') and len(current_soup.select('script[src^="assets/pauta-filters-v2.js"]'))==1)
    check('Modelo v1 e modelos auditados não reescritos',all((ROOT/p).read_bytes()==git('show',f'{PRESERVATION}:{p}') for p in INPUTS))
    for name in ('pauta-filter-core.js','pauta-filters-v2.js','sc-federais-filters-v2-data.js'):
        p=subprocess.run(['node','--check',str(ROOT/'assets'/name)],capture_output=True,text=True)
        check('Sintaxe JavaScript '+name,p.returncode==0,p.stderr)
    paths=['index.html','assets/pauta-filters-v2.js','assets/sc-federais-filters-v2-data.js','data/sc-semantic-v2-ui/payload.json','data/sc-semantic-v2-ui/manifest.json']
    hashes={p:sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
    build()
    check('Build idempotente',all(sha256((ROOT/p).read_bytes()).hexdigest()==v for p,v in hashes.items()))
    unit=subprocess.run(['node','--test','tests/sc_semantic_v2_ui.test.cjs'],cwd=ROOT,capture_output=True,text=True)
    (OUT/'unit-tests.txt').write_text(unit.stdout+unit.stderr)
    check('Suíte independente de combinações aprovada',unit.returncode==0,unit.stdout[-1200:]+unit.stderr)
    return data,audit

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

def browser_tests(data,audit):
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    url=f'http://127.0.0.1:{server.server_port}/'
    def expected(topics,mode='any',ids=None):
        by={c['id']:set() for c in data['candidates']}
        for a in audit:
            if a['eligible_v2']: by[a['candidate_id']].add(a['macro_id'])
        return {cid for cid,own in by.items() if (not topics or (all(t in own for t in topics) if mode=='all' else any(t in own for t in topics))) and (ids is None or cid in ids)}
    def visible(page):
        return page.locator('.candidate:not([hidden])').evaluate_all('(els)=>els.map(e=>e.dataset.tseId)')
    def allow_local(route):
        route.continue_() if urlsplit(route.request.url).hostname=='127.0.0.1' else route.abort()
    launch={'executable_path':os.environ['CHROMIUM_PATH']} if os.environ.get('CHROMIUM_PATH') else {}
    with sync_playwright() as p:
        browser=p.chromium.launch(**launch)
        try:
            for width in (320,360,390,430,768,1024,1440):
                label=f'{width}px: '
                ctx=browser.new_context(viewport={'width':width,'height':900},locale='pt-BR',reduced_motion='reduce')
                page=ctx.new_page(); errors=[];requests=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('request',lambda r:requests.append(r.url));page.route('**/*',allow_local)
                page.goto(url,wait_until='networkidle');page.wait_for_function('Boolean(window.EEFTopicFilters)')
                page.add_style_tag(content='html{scroll-behavior:auto!important}')
                order=visible(page)
                check(label+'48 fichas e 13 botões',len(order)==48 and page.locator('[data-pauta-topic]').count()==13)
                check(label+'Sem overflow inicial',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                if width>980:
                    check(label+'Sidebar abaixo dos partidos e rolável',page.locator('#pautaPanel').is_visible() and page.locator('.rail').evaluate('(e)=>getComputedStyle(e).overflowY==="auto" && e.clientHeight<innerHeight'))
                else:
                    check(label+'Painel fechado inicialmente',not page.locator('#pautaPanel').is_visible() and page.locator('#pautaOpen').is_visible())
                def open_panel():
                    if width<=980 and not page.locator('#pautaDialog').is_visible():
                        page.locator('#pautaOpen').click();page.wait_for_function('document.getElementById("pautaDialog").open')
                def close_panel():
                    if page.locator('#pautaDialog').is_visible():
                        page.keyboard.press('Escape');page.wait_for_function('!document.getElementById("pautaDialog").open');page.wait_for_timeout(30)
                def choose(topic):
                    open_panel();page.locator(f'[data-pauta-topic="{topic}"]').click()
                def verify(topics,mode='any'):
                    exp=expected(topics,mode)
                    check(label+'Resultado '+mode+' '+','.join(topics),set(visible(page))==exp)
                    check(label+'Ordem diária mantida',visible(page)==[cid for cid in order if cid in exp])
                    counts=page.locator('[data-pauta-topic]').evaluate_all('(els)=>Object.fromEntries(els.map(e=>[e.dataset.pautaTopic,Number(e.querySelector(".pauta-chip__count").textContent)]))')
                    check(label+'Contagem por pessoa não muda com seleção',counts=={t['id']:t['count'] for t in data['topics']})
                choose('economia-estado');verify(['economia-estado']);close_panel()
                ju=page.locator('#candidato-240002533832 .pauta-match')
                check(label+'Tributação mostra frase concreta correta',ju.is_visible() and 'Defende impostos proporcionais à renda e ao patrimônio.' in ju.inner_text() and 'Apoio declarado:' not in ju.inner_text())
                check(label+'Atuação de Drag não vaza para Economia/Estado','240002537831' not in visible(page))
                choose('economia-estado');choose('saude');verify(['saude'])
                choose('educacao-infancia-juventude');verify(['saude','educacao-infancia-juventude'])
                page.locator('input[value="all"]').check();verify(['saude','educacao-infancia-juventude'],'all')
                if width<=980:
                    page.locator('#pautaShowResults').focus();page.keyboard.press('Tab')
                    check(label+'Tab permanece no diálogo',page.evaluate('document.getElementById("pautaDialog").contains(document.activeElement)'))
                    page.locator('#pautaClose').focus();page.keyboard.press('Shift+Tab')
                    check(label+'Shift+Tab permanece no diálogo',page.evaluate('document.getElementById("pautaDialog").contains(document.activeElement)'))
                    page.screenshot(path=str(SHOTS/f'{width}-painel.png'));close_panel()
                    check(label+'Escape devolve foco',page.evaluate('document.activeElement.id==="pautaOpen"'))
                    open_panel();check(label+'Seleção preservada ao reabrir',page.locator('[data-pauta-topic="saude"]').get_attribute('aria-pressed')=='true');close_panel()
                else:
                    page.locator('#candidaturas').scroll_into_view_if_needed();page.screenshot(path=str(SHOTS/f'{width}-filtros.png'))
                page.locator('#searchInput').fill('caren')
                check(label+'Busca + AND',visible(page)==['240002533828'])
                page.locator('#searchInput').fill('zzz-inexistente')
                check(label+'Estado vazio',not visible(page) and page.locator('#pautaEmpty').is_visible())
                page.locator('#pautaEmpty [data-pauta-reset="topics"]').click()
                check(label+'Limpar pautas preserva busca',page.locator('#searchInput').input_value()=='zzz-inexistente' and not visible(page))
                page.locator('#pautaEmpty [data-pauta-reset="all"]').click()
                check(label+'Limpar tudo restaura todas na mesma ordem',visible(page)==order)
                choose('trabalho-renda');close_panel()
                ana=page.locator('#candidato-240002533824')
                check(label+'Histórico de 6×1 separado do motivo trabalhista', 'salário mínimo' in ana.locator('.pauta-match').inner_text() and '6×1' not in ana.locator('.pauta-match').inner_text() and '6×1' in ana.locator('[data-pauta-section="historico"]').inner_text())
                page.locator('#pautaActiveList button').click()
                check(label+'Remoção individual restaura lista',visible(page)==order)
                choose('saude');close_panel()
                page.evaluate("location.hash='#candidato-240002533818'");page.wait_for_function('!document.getElementById("candidato-240002533818").hidden')
                check(label+'Link revela ficha sem pauta e informa limpeza',len(visible(page))==48 and page.locator('#pautaNotice').is_visible())
                page.evaluate("location.hash='#pauta-fonte-240002533832-s1'");page.wait_for_function('document.getElementById("pauta-contexto-240002533832").open')
                check(label+'Fonte numerada abre contexto e foca destino',page.evaluate('document.activeElement.id==="pauta-fonte-240002533832-s1"'))
                page.evaluate('window.scrollTo(0,1500)');page.wait_for_timeout(40)
                check(label+'Navbar sticky',abs(page.locator('#siteNav').bounding_box()['y'])<=1)
                if width<=760:
                    page.locator('#siteNavMenu').click();check(label+'Hambúrguer preservado',page.locator('#siteNavMenu').get_attribute('aria-expanded')=='true')
                    page.keyboard.press('Escape')
                check(label+'Sem preferências persistidas ou enviadas',page.evaluate('localStorage.length===0&&sessionStorage.length===0&&document.cookie===""') and not any('/api/metrics/' in u for u in requests))
                check(label+'Sem erro ou overflow após interação',not errors and page.evaluate('document.documentElement.scrollWidth<=innerWidth'),errors)
                if width in (390,1440):
                    page.evaluate("location.hash='#candidato-240002533824'");page.wait_for_timeout(100)
                    page.screenshot(path=str(SHOTS/f'{width}-blocos.png'))
                    page.evaluate("location.hash='#candidato-240002533832'");page.wait_for_timeout(100)
                    page.screenshot(path=str(SHOTS/f'{width}-tributacao.png'))
                if width==390:
                    choose('saude')
                    page.set_viewport_size({'width':1440,'height':900});page.wait_for_function('!document.getElementById("pautaDialog").open')
                    check('Breakpoint preserva painel e seleção',page.locator('#pautaPanel').count()==1 and page.locator('#pautaSidebarHost [data-pauta-topic="saude"]').get_attribute('aria-pressed')=='true')
                    page.set_viewport_size({'width':390,'height':900});open_panel();page.mouse.click(3,3);page.wait_for_function('!document.getElementById("pautaDialog").open')
                    check('Toque fora fecha painel',not page.locator('#pautaDialog').is_visible())
                    open_panel();page.locator('#pautaShowResults').click();page.wait_for_function('!document.getElementById("pautaDialog").open')
                    check('Ver resultados foca uma ficha',page.evaluate('document.activeElement.matches(".candidate")'))
                ctx.close()
            # Real-day rotation relation, rather than regenerating a claimed ranking.
            orders=[]
            for day in ('2026-09-21T15:00:00Z','2026-09-22T15:00:00Z'):
                ctx=browser.new_context(viewport={'width':1440,'height':900})
                ctx.add_init_script("{const D=Date;window.Date=class extends D{constructor(...a){super(...(a.length?a:['"+day+"']));}static now(){return new D('"+day+"').getTime();}};}")
                page=ctx.new_page();page.route('**/*',allow_local);page.goto(url,wait_until='networkidle')
                orders.append(page.locator('.party-section').evaluate_all('(els)=>els.map(e=>({party:e.dataset.partySection,ids:[...e.querySelectorAll(".candidate")].map(c=>c.dataset.tseId)}))'))
                ctx.close()
            check('Rotação avança um partido por dia', [x['party'] for x in orders[1]]==[x['party'] for x in orders[0][1:]+orders[0][:1]])
            zero={x['party']:x['ids'] for x in orders[0]}
            check('Rotação avança uma candidatura em cada partido',all(x['ids']==zero[x['party']][1:]+zero[x['party']][:1] for x in orders[1]))
            for scenario in ('no-js','no-data','no-runtime','wrong-version'):
                ctx=browser.new_context(java_script_enabled=scenario!='no-js',viewport={'width':390,'height':900})
                page=ctx.new_page()
                def route_handler(route):
                    u=route.request.url
                    if scenario=='wrong-version' and 'sc-federais-filters-v2-data.js' in u:
                        route.fulfill(content_type='application/javascript',body='window.EEF_SC_FEDERAIS_FILTERS_V2={schemaVersion:"1.0.0"};')
                    elif (scenario=='no-data' and 'sc-federais-filters-v2-data.js' in u) or (scenario=='no-runtime' and 'pauta-filters-v2.js' in u): route.abort()
                    else: allow_local(route)
                page.route('**/*',route_handler);page.goto(url,wait_until='networkidle')
                check(scenario+': 48 fichas e controles de filtro ocultos',len(visible(page))==48 and not page.locator('#pautaToolbar').is_visible())
                check(scenario+': conteúdo v2 disponível sem runtime',page.locator('[data-pauta-section="historico"]').count()>0)
                if scenario!='no-js':
                    page.locator('#searchInput').fill('caren');check(scenario+': busca original funciona','240002533828' in visible(page))
                ctx.close()
        finally:
            browser.close();server.shutdown()

def main():
    try:
        data,audit=static_tests();browser_tests(data,audit)
    except Exception as e:
        checks.append({'name':'Execução','passed':False,'detail':str(e),'trace':traceback.format_exc()})
    result={'status':'passed' if all(c['passed'] for c in checks) else 'failed','base_commit':PRESERVATION,
            'checked_commit':git('rev-parse','HEAD').decode().strip(),'checks_count':len(checks),'failed_count':sum(not c['passed'] for c in checks),
            'checks':checks,'scope':'Modelo v2, preservação e Chromium; fontes/imagens externas bloqueadas. Não certifica interpretações políticas nem teste em aparelho físico ou leitor de tela real.'}
    (OUT/'qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False))
    if result['failed_count']:
        print(json.dumps([c for c in checks if not c['passed']],ensure_ascii=False));sys.exit(1)

if __name__=='__main__': main()
