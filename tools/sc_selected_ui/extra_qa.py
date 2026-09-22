"""Regressões adicionais da integração, sem pesquisa nem envio externo."""
from __future__ import annotations
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json,os,threading,traceback
from pathlib import Path
from playwright.sync_api import sync_playwright
from urllib.parse import urlsplit
from build import ROOT,OUT,load,dump

checks=[]
ART=Path('/tmp/eef-selected-qa');ART.mkdir(parents=True,exist_ok=True)
def check(name,ok,detail=None):
    checks.append({'name':name,'passed':bool(ok),'detail':detail})
    if not ok:raise AssertionError(name+': '+str(detail))
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*a):pass

def run():
    payload=load('data/sc-semantic-v2-ui/payload.json')
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    url=f'http://127.0.0.1:{server.server_port}/'
    ju='240002533832';ana='240002533824';gap='240002533818'
    def exp(topics,mode):
        return {c['id'] for c in payload['candidates'] if (all(t in c['topicIds'] for t in topics) if mode=='all' else any(t in c['topicIds'] for t in topics))}
    launch={'executable_path':os.environ['CHROMIUM_PATH']} if os.environ.get('CHROMIUM_PATH') else {}
    with sync_playwright() as p:
        browser=p.chromium.launch(**launch)
        try:
            for width in [320,360,390,430,768,1024,1440]:
                prefix=f'{width}px: '
                page=browser.new_page(viewport={'width':width,'height':900},reduced_motion='reduce',locale='pt-BR')
                page.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='127.0.0.1' else r.abort())
                page.goto(url,wait_until='networkidle');page.wait_for_function('document.documentElement.classList.contains("eef-selected-ready")')
                page.add_style_tag(content='html{scroll-behavior:auto!important}')
                nav=page.locator('#eefSelectedNav')
                check(prefix+'Atalho da navbar não está sob outro elemento',nav.evaluate('(e)=>{const r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));}'))
                if width in [768,1440]:page.screenshot(path=str(ART/f'{width}-navbar.png'))
                order=page.locator('.party-section .candidate').evaluate_all('(els)=>els.map(e=>e.dataset.tseId)')
                def visible():return set(page.locator('.party-section .candidate:not([hidden])').evaluate_all('(els)=>els.map(e=>e.dataset.tseId)'))
                def open_filters():
                    if width<=980:page.locator('#pautaOpen').click()
                def close_filters():
                    if width<=980:
                        page.keyboard.press('Escape');page.wait_for_function('!document.getElementById("pautaDialog").open && document.activeElement.id==="pautaOpen"')
                for cid in [ju,gap]:page.locator(f'[data-eef-toggle="{cid}"]').click()
                open_filters()
                for topic in ['saude','trabalho-renda']:page.locator(f'[data-pauta-topic="{topic}"]').click()
                check(prefix+'OR preserva conjunto documentado',visible()==exp(['saude','trabalho-renda'],'any'))
                page.locator('input[name="pauta-mode"][value="all"]').check()
                check(prefix+'AND preserva conjunto documentado',visible()==exp(['saude','trabalho-renda'],'all'))
                close_filters()
                check(prefix+'Ficha oculta continua selecionada',page.locator('#eefSelectedNav [data-eef-count]').text_content()=='2' and ju not in visible())
                saved_scroll=page.evaluate('scrollY')
                nav.click();page.wait_for_function('document.getElementById("eefCollection").open')
                check(prefix+'Uma ficha original, mesmo fora do AND',page.locator('#eefReaderHost .candidate').get_attribute('data-tse-id')==ju)
                page.locator('#eefReaderHost .eef-source-ref').first.click()
                page.wait_for_function('document.getElementById("pauta-contexto-240002533832").open')
                box=page.locator('#eefCollection').bounding_box()
                check(prefix+'Dialog permanece no viewport ao abrir fonte',box['y']>=0 and box['y']+box['height']<=901,box)
                check(prefix+'Fechar continua acessível após navegar às fontes',page.locator('#eefCollectionClose').evaluate('(e)=>{const r=e.getBoundingClientRect();return r.y>=0 && r.bottom<=innerHeight && e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));}'))
                page.locator('#eefReaderHost h3').scroll_into_view_if_needed()
                if width in [320,390,1440]:page.screenshot(path=str(ART/f'{width}-reader-final.png'))
                page.locator('#eefCollectionClose').click();page.wait_for_function('!document.documentElement.classList.contains("eef-collection-open")')
                check(prefix+'Retorno conserva AND e rolagem',visible()==exp(['saude','trabalho-renda'],'all') and abs(page.evaluate('scrollY')-saved_scroll)<=2)
                nav.click();page.locator('#eefOpenFull').click()
                page.wait_for_function('!document.getElementById("eefCollection").open && !document.getElementById("candidato-240002533832").hidden')
                page.wait_for_function('!document.documentElement.classList.contains("eef-collection-open")')
                check(prefix+'Ir à ficha revela destino e mantém coleção',page.locator('#eefSelectedNav [data-eef-count]').text_content()=='2' and ju in visible() and page.locator('#pautaNotice').is_visible())
                open_filters();page.locator('[data-pauta-topic="economia-estado"]').click();close_filters()
                check(prefix+'Indicações do filtro permanecem recolhidas',page.locator('#candidato-'+ju+' .eef-filter-note').count()>0 and page.locator('#candidato-'+ju+' .eef-filter-note[open]').count()==0)
                notes=page.locator('#candidato-'+ju+' .eef-filter-note')
                for d in notes.all():d.locator('summary').click()
                texts=page.locator('#candidato-'+ju+' .eef-filter-exact').evaluate_all('(els)=>els.map(e=>e.firstChild.textContent.trim())')
                expected_texts={m['text'] for c in payload['candidates'] if c['id']==ju for m in c['matches'] if m['topicId']=='economia-estado'}
                check(prefix+'Registros exatos do motivo do filtro preservados',set(texts)==expected_texts,{'actual':texts,'expected':sorted(expected_texts)})
                page.locator('#searchInput').fill('zz-sem-registro')
                check(prefix+'Estado vazio não apaga selecionados',not visible() and page.locator('#eefSelectedNav [data-eef-count]').text_content()=='2')
                page.locator('#pautaEmpty [data-pauta-reset="all"]').click()
                check(prefix+'Limpar busca/filtros restaura ordem',page.locator('.party-section .candidate:not([hidden])').evaluate_all('(els)=>els.map(e=>e.dataset.tseId)')==order)
                if width<=760:
                    page.locator('#siteNavMenu').click();check(prefix+'Hambúrguer permanece utilizável',page.locator('#siteNavMenu').get_attribute('aria-expanded')=='true');page.keyboard.press('Escape')
                page.evaluate('window.scrollTo(0,1800)')
                check(prefix+'Navbar continua fixa',abs(page.locator('#siteNav').bounding_box()['y'])<=1)
                footer=page.locator('.persistent-footer').bounding_box();bar=page.locator('#eefSelectionBar').bounding_box()
                check(prefix+'Barra de seleção não cobre rodapé',bar['y']+bar['height']<=footer['y']+1)
                check(prefix+'Sem overflow final',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                page.close()
            daily=[]
            for day in ['2026-09-21T15:00:00Z','2026-09-22T15:00:00Z']:
                ctx=browser.new_context(viewport={'width':1440,'height':900})
                ctx.add_init_script("{const D=Date;window.Date=class extends D{constructor(...a){super(...(a.length?a:['"+day+"']));}static now(){return new D('"+day+"').getTime();}};}")
                page=ctx.new_page();page.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='127.0.0.1' else r.abort());page.goto(url,wait_until='networkidle')
                daily.append(page.locator('.party-section').evaluate_all('(els)=>els.map(e=>({party:e.dataset.partySection,ids:[...e.querySelectorAll(".candidate")].map(c=>c.dataset.tseId)}))'));ctx.close()
            check('Rotação diária de partidos preservada',[d['party'] for d in daily[1]]==[d['party'] for d in daily[0][1:]+daily[0][:1]])
            before={d['party']:d['ids'] for d in daily[0]}
            check('Rotação diária de fichas preservada',all(d['ids']==before[d['party']][1:]+before[d['party']][:1] for d in daily[1]))
        finally:browser.close();server.shutdown()

if __name__=='__main__':
    try:run()
    except Exception as e:checks.append({'name':'Execução','passed':False,'detail':str(e),'trace':traceback.format_exc()})
    report={'status':'passed' if all(c['passed'] for c in checks) else 'failed','checks_count':len(checks),'failed_count':sum(not c['passed'] for c in checks),'checks':checks,'scope':'Regressões de layout, navegação e conjuntos de filtros; não avaliação ou comparação de candidaturas.'}
    dump(OUT/'extra-qa.json',report);print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False))
    if report['status']!='passed':print(json.dumps([c for c in checks if not c['passed']],ensure_ascii=False));raise SystemExit(1)
