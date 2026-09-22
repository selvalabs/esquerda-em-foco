"""QA estrutural e de navegador. Não avalia candidaturas nem envia mensagens.
SHARE/clipboard são simulados. Chromium local pode ser indicado por CHROMIUM_PATH.
"""
from __future__ import annotations
from functools import partial
from hashlib import sha1,sha256
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json,os,subprocess,threading,traceback
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from build import ROOT,OUT,BASE,INPUTS,build,load,normalize

CHECKS=[]
PRESERVATION=os.environ.get('PRESERVATION_BASE',BASE)
ART=Path('/tmp/eef-selected-qa');ART.mkdir(parents=True,exist_ok=True)

def check(name,ok,detail=None):
    CHECKS.append({'name':name,'passed':bool(ok),'detail':detail})
    if not ok:raise AssertionError(name+': '+str(detail))

def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)

def owned(p):
    return p=='index.html' or p.startswith(('tools/sc_selected_ui/','tools/sc_editorial_selected/','data/sc-selected-ui/','data/sc-editorial-selected-r1/','docs/SC-EDITORIAL-SELECTED')) or p in ['.github/workflows/sc-selected-ui.yml','.github/workflows/sc-editorial-selected-round1.yml','tests/sc_editorial_selected.test.cjs','assets/editorial-selected.css','assets/selecionados.js','assets/selecionados-core.js','assets/pauta-filters-editorial.js']

def static():
    current=(ROOT/'index.html').read_text();prior=git('show',PRESERVATION+':index.html').decode()
    check('HTML fora das áreas editoriais e controles autorizados preservado',normalize(current)==normalize(prior))
    changed=[];total=0
    for entry in git('ls-tree','-rz',PRESERVATION).split(b'\0'):
        if not entry:continue
        meta,p=entry.split(b'\t',1);mode,kind,h=meta.decode().split();p=p.decode()
        if owned(p):continue
        total+=1;local=ROOT/p
        if not local.exists():changed.append(p);continue
        content=os.readlink(local).encode() if mode=='120000' else local.read_bytes()
        if sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()!=h:changed.append(p)
    check('Demais frentes e arquivos preexistentes preservados byte a byte',not changed,{'files':total,'base':PRESERVATION,'changed':changed})
    s=BeautifulSoup(current,'html.parser');old=BeautifulSoup(prior,'html.parser')
    cards={c['data-tse-id']:c for c in s.select('article.candidate')};oldcards={c['data-tse-id']:c for c in old.select('article.candidate')}
    check('48 fichas com mesmas identidades',len(cards)==48 and set(cards)==set(oldcards))
    for cid,c in cards.items():
        for selector in ['.candidate-head','.candidate-links','.career-band']:
            check(cid+' preserva '+selector,str(c.select_one(selector))==str(oldcards[cid].select_one(selector)))
    for selector in ['.masthead','.persistent-footer']:
        check(selector+' preservado',str(s.select_one(selector))==str(old.select_one(selector)))
    before_nav=old.select_one('#siteNav');after_nav=s.select_one('#siteNav');after_nav.select_one('#eefSelectedNav').decompose()
    check('Links antigos da navbar preservados',[a.get('href') for a in before_nav.select('a')]==[a.get('href') for a in after_nav.select('a')])
    data=load('data/sc-editorial-selected-r1/editorial.json')
    for c in data['candidates']:
        card=cards[c['candidate_id']]
        for section in c['sections']:
            block=card.select_one('[data-pauta-section="'+section['id']+'"]')
            check(c['name']+' título '+section['id'],block.select_one('h4').get_text()==section['title'])
            for p in section['paragraphs']:
                item=block.select_one('[data-eef-paragraph="'+p['paragraph_id']+'"]')
                check(p['paragraph_id']+' texto e vínculos exatos',item.select_one('.pauta').get_text()==p['text'] and set(item.get('data-eef-associations','').split())==set(p['association_ids']) and {a['href'].replace('#pauta-fonte-','') for a in item.select('.eef-source-ref')}==set(p['source_ids']))
            if section['notice']:check(c['name']+' ressalva preservada',section['notice'] in block.get_text())
        if c['gap_text']:check(c['name']+' lacuna explícita',c['gap_text'] in card.get_text())
        for note in c['retained_limitations']:check(c['name']+' limitação original',note in card.get_text())
    ids=[el['id'] for el in s.select('[id]')]
    check('IDs únicos; âncoras legadas preservadas',len(ids)==len(set(ids)) and {x['id'] for x in old.select('[id]')}<=set(ids))
    check('Âncoras locais resolvem',all(a['href']=='#' or a['href'][1:] in ids for a in s.select('a[href^="#"]')))
    check('Fontes e elegibilidade v2 preservadas',all((ROOT/p).read_bytes()==git('show',PRESERVATION+':'+p) for p in ['data/sc-semantic-v2/association-audit.json','data/sc-semantic-v2-ui/payload.json','config/topics-v1.json']))
    check('Núcleo de seleção publicado idêntico ao aprovado',(ROOT/'assets/selecionados-core.js').read_bytes()==(ROOT/'tools/sc_editorial_selected/selection-core.cjs').read_bytes())
    paths=['index.html','assets/selecionados-core.js','assets/pauta-filters-editorial.js','data/sc-selected-ui/manifest.json']
    hashes={p:sha256((ROOT/p).read_bytes()).hexdigest() for p in paths};build()
    check('Recompilação idêntica',all(sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items()))
    for js in ['assets/selecionados-core.js','assets/selecionados.js','assets/pauta-filters-editorial.js']:
        r=subprocess.run(['node','--check',js],cwd=ROOT,capture_output=True,text=True);check('Sintaxe '+js,r.returncode==0,r.stderr)
    r=subprocess.run(['node','--test','tests/sc_editorial_selected.test.cjs'],cwd=ROOT,capture_output=True,text=True)
    (ART/'unit-tests.txt').write_text(r.stdout+r.stderr);check('12 testes do núcleo, URLs e compartilhamento',r.returncode==0,r.stdout[-800:])
    return data

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*a):pass

MOCK="""window.__copied=[];window.__shared=[];window.__shareMode='cancel';window.__copyFail=false;Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async s=>{if(__copyFail)throw Error('denied');__copied.push(s);}}});Object.defineProperty(navigator,'share',{configurable:true,value:async d=>{__shared.push(d);if(__shareMode==='cancel')throw new DOMException('cancel','AbortError');}});Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>true});"""

def browser(data):
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
    url=f'http://127.0.0.1:{server.server_port}/'
    launches={'executable_path':os.environ['CHROMIUM_PATH']} if os.environ.get('CHROMIUM_PATH') else {}
    a='240002533824';b='240002533832';gap='240002533818'
    payload=load('data/sc-semantic-v2-ui/payload.json')
    expected=lambda topics,mode='any':{c['id'] for c in payload['candidates'] if (all(t in c['topicIds'] for t in topics) if mode=='all' else any(t in c['topicIds'] for t in topics))}
    with sync_playwright() as p:
        browser=p.chromium.launch(**launches)
        try:
            for width in [320,360,390,430,768,1024,1440]:
                prefix=str(width)+'px: ';ctx=browser.new_context(viewport={'width':width,'height':900},locale='pt-BR',reduced_motion='reduce')
                ctx.add_init_script(MOCK);page=ctx.new_page();errors=[];requests=[]
                page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
                page.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='127.0.0.1' else r.abort())
                page.goto(url,wait_until='networkidle');page.wait_for_function('document.documentElement.classList.contains("eef-selected-ready")')
                page.add_style_tag(content='html{scroll-behavior:auto!important}')
                visible=lambda:page.locator('.party-section .candidate:not([hidden])').evaluate_all('(els)=>els.map(e=>e.dataset.tseId)')
                order=visible();check(prefix+'48 fichas e controles acessíveis',len(order)==48 and page.locator('#eefSelectedNav').is_visible())
                check(prefix+'Sem overflow inicial',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                page.locator('#eefSelectedNav').click();check(prefix+'Coleção vazia sem ficha fantasma',page.locator('#eefCollectionEmpty').is_visible() and page.locator('#eefReaderHost .candidate').count()==0)
                page.locator('#eefCollectionClose').click();page.wait_for_function('!document.documentElement.classList.contains("eef-collection-open")')
                for cid in [a,gap,b]:page.locator('[data-eef-toggle="'+cid+'"]').click()
                check(prefix+'3 selecionados sem modificar URL ou ordem',page.locator('#eefSelectedNav [data-eef-count]').inner_text()=='3' and not page.url.split('#')[1:] and visible()==order)
                def open_filters():
                    if width<=980:page.locator('#pautaOpen').click()
                def close_filters():
                    if width<=980:
                        page.keyboard.press('Escape');page.wait_for_function('!document.getElementById("pautaDialog").open && document.activeElement.id==="pautaOpen"')
                open_filters();page.locator('[data-pauta-topic="saude"]').click();close_filters()
                check(prefix+'Filtro mantido com busca independente',set(visible())==expected(['saude']))
                page.locator('#searchInput').fill('impostos proporcionais')
                check(prefix+'Busca e filtro combinam',visible()==[b])
                before_scroll=page.evaluate('scrollY')
                page.locator('#eefSelectedNav').click()
                check(prefix+'Ficha selecionada oculta abre no leitor',page.locator('#eefReaderHost .candidate').get_attribute('data-tse-id')==a and page.locator('article.candidate').count()==48)
                check(prefix+'Nenhuma duplicação de IDs',page.evaluate('(()=>{const ids=[...document.querySelectorAll("[id]")].map(e=>e.id);return ids.length===new Set(ids).size;})()'))
                check(prefix+'Ressalva de atuação visível',page.locator('#eefReaderHost [data-pauta-section="historico"] .eef-editorial-notice').is_visible())
                page.locator('#eefNext').click();check(prefix+'Lacuna individual acessível',page.locator('#eefReaderHost .candidate').get_attribute('data-tse-id')==gap and page.locator('#eefReaderHost .pauta-v2-gap').is_visible())
                page.locator('#eefNext').click();check(prefix+'Ordem explícita da coleção',page.locator('#eefReaderHost .candidate').get_attribute('data-tse-id')==b and page.locator('#eefPager').inner_text()=='Ficha 3 de 3')
                # Source anchors resolve in the original card without leaving the reader.
                page.locator('#eefReaderHost .eef-source-ref').first.click();page.wait_for_function('document.getElementById("pauta-contexto-240002533832").open')
                check(prefix+'Fonte abre no leitor, sem limpar filtros',page.locator('#eefCollection').is_visible() and page.locator('#searchInput').input_value()=='impostos proporcionais')
                if width in [320,390,1440]:
                    page.locator('#eefReaderHost h3').scroll_into_view_if_needed();page.screenshot(path=str(ART/f'{width}-reader.png'))
                page.locator('#eefShareCollection').click()
                link=page.locator('#eefShareUrl').input_value();parsed=parse_qs(urlsplit(link).fragment)
                check(prefix+'Link público contém IDs e ordem',parsed['selecionados']==[','.join([a,gap,b])] and parsed['ficha']==[b] and urlsplit(link).query=='')
                wa=page.locator('#eefWhatsapp').get_attribute('href')
                check(prefix+'WhatsApp codificado sem destinatário',urlsplit(wa).netloc=='wa.me' and parse_qs(urlsplit(wa).query)['text'][0].endswith(link) and 'phone=' not in wa)
                page.locator('#eefCopy').click();page.wait_for_function('document.getElementById("eefShareStatus").textContent.includes("Link copiado")')
                check(prefix+'Cópia confirmada',page.evaluate('window.__copied').pop()==link)
                page.locator('#eefNativeShare').click();page.wait_for_function('document.getElementById("eefShareStatus").textContent.includes("cancelado")')
                check(prefix+'Cancelamento sem envio/cópia automática',len(page.evaluate('window.__copied'))==1 and len(page.evaluate('window.__shared'))==1)
                page.evaluate('window.__copyFail=true');page.locator('#eefCopy').click();page.wait_for_function('document.activeElement.id==="eefShareUrl"');check(prefix+'Fallback manual de cópia',page.locator('#eefShareUrl').is_visible())
                page.evaluate('window.__copyFail=false;window.__shareMode="ok"');page.locator('#eefNativeShare').click();page.wait_for_function('document.getElementById("eefShareStatus").textContent.includes("Confirme o envio")')
                if width==320:page.screenshot(path=str(ART/'320-share.png'))
                page.keyboard.press('Escape');page.wait_for_function('!document.getElementById("eefShareDialog").open && document.activeElement.id==="eefShareCollection"')
                check(prefix+'Escape fecha só compartilhamento',page.locator('#eefCollection').is_visible())
                page.locator('#eefCollectionClose').click();page.wait_for_function('!document.documentElement.classList.contains("eef-collection-open")')
                check(prefix+'Retorno preserva busca, filtros e 48 nós',page.locator('#searchInput').input_value()=='impostos proporcionais' and visible()==[b] and page.locator('article.candidate').count()==48)
                page.locator('#searchInput').fill('');open_filters();page.locator('[data-pauta-clear]').click();close_filters()
                check(prefix+'Ordem da listagem integral restaurada',visible()==order)
                # Simulate recipient with a fresh document, not only a hash assignment.
                page.goto(url+'?recipient=1'+urlsplit(link).fragment.join(['#','']),wait_until='networkidle')
                page.wait_for_function('document.getElementById("eefCollection").open')
                check(prefix+'Destinatário reconstrói coleção completa',page.locator('#eefSelectedNav [data-eef-count]').inner_text()=='3' and page.locator('#eefReaderHost .candidate').get_attribute('data-tse-id')==b)
                page.locator('#eefReaderHost [data-eef-toggle]').click()
                check(prefix+'Remover aberta mantém demais',page.locator('#eefSelectedNav [data-eef-count]').inner_text()=='2' and page.locator('#eefReaderHost .candidate').count()==1)
                page.locator('#eefClearCollection').click();page.locator('#eefCancelClear').click();page.wait_for_function('!document.getElementById("eefConfirm").open')
                check(prefix+'Cancelar limpeza conserva coleção',page.locator('#eefSelectedNav [data-eef-count]').inner_text()=='2')
                page.locator('#eefClearCollection').click();page.locator('#eefConfirmClear').click();page.wait_for_function('!document.getElementById("eefConfirm").open')
                check(prefix+'Limpar restaura todos os nós e foco',page.locator('#eefReaderHost .candidate').count()==0 and page.locator('article.candidate').count()==48 and page.locator('#eefCollectionEmpty').is_visible())
                page.keyboard.press('Escape');page.wait_for_function('!document.getElementById("eefCollection").open')
                page.goto(url+'?case=all',wait_until='networkidle')
                page.evaluate('[...document.querySelectorAll("[data-eef-toggle]")].forEach(b=>b.click())')
                page.locator('#eefSelectedNav').click();check(prefix+'48 selecionados com uma ficha por vez',page.locator('#eefSelectedNav [data-eef-count]').inner_text()=='48' and page.locator('#eefReaderHost .candidate').count()==1)
                page.locator('#eefNext').focus();page.keyboard.press('ArrowRight');check(prefix+'Teclado avança',page.locator('#eefPager').inner_text()=='Ficha 2 de 48')
                page.locator('#eefShareCollection').click();full=page.locator('#eefShareUrl').input_value()
                check(prefix+'Todas as 48 cabem no link',len(parse_qs(urlsplit(full).fragment)['selecionados'][0].split(','))==48 and len(urlsplit(full).fragment)<4096)
                page.keyboard.press('Escape');page.wait_for_function('!document.getElementById("eefShareDialog").open')
                if width==390:
                    active=page.locator('#eefReaderHost .candidate').get_attribute('data-tse-id')
                    page.set_viewport_size({'width':1440,'height':900});page.set_viewport_size({'width':390,'height':900})
                    check('Breakpoint mantém coleção e ficha',page.locator('#eefReaderHost .candidate').get_attribute('data-tse-id')==active and page.locator('#eefSelectedNav [data-eef-count]').inner_text()=='48')
                page.evaluate("location.hash='#selecionados=999999999999&v=1&edicao=sc-federais'");page.wait_for_function('document.getElementById("eefSelectionStatus").textContent.includes("preservada")')
                check(prefix+'URL inválida não esvazia seleção',page.locator('#eefSelectedNav [data-eef-count]').inner_text()=='48')
                page.keyboard.press('Escape');page.wait_for_function('!document.documentElement.classList.contains("eef-collection-open")')
                check(prefix+'Sem storage ou coleta de seleção',page.evaluate('localStorage.length===0&&sessionStorage.length===0&&document.cookie===""') and not any('/api/metrics/' in r or '#selecionados=' in r for r in requests))
                page.goto(url+'?case=end',wait_until='networkidle')
                check(prefix+'Nova visita sem fragmento não mantém seleção',page.locator('#eefSelectedNav [data-eef-count]').inner_text()=='0')
                check(prefix+'Sem erros ou overflow',not errors and page.evaluate('document.documentElement.scrollWidth<=innerWidth'),errors)
                ctx.close()
            # Feature failures do not remove editorial content or break existing filters.
            for missing in ['selecionados-core.js','selecionados.js','pauta-filters-editorial.js']:
                ctx=browser.new_context(viewport={'width':390,'height':900});page=ctx.new_page()
                page.route('**/*',lambda r:r.abort() if missing in r.request.url or urlsplit(r.request.url).hostname!='127.0.0.1' else r.continue_())
                page.goto(url,wait_until='networkidle')
                check('Falha '+missing+' conserva 48 fichas',page.locator('article.candidate:not([hidden])').count()==48)
                if missing!='pauta-filters-editorial.js':check('Falha '+missing+' oculta Selecionados',not page.locator('#eefSelectedNav').is_visible())
                page.locator('#searchInput').fill('Caren');check('Falha '+missing+' conserva busca',page.locator('#candidato-240002533828').is_visible())
                ctx.close()
            ctx=browser.new_context(java_script_enabled=False);page=ctx.new_page();page.goto(url)
            check('Sem JS: texto e fontes preservados, controles ocultos',page.locator('article.candidate').count()==48 and page.locator('[data-eef-paragraph]').count()==67 and not page.locator('#eefSelectedNav').is_visible());ctx.close()
        finally:browser.close();server.shutdown()

def main():
    try:data=static();browser(data)
    except Exception as e:CHECKS.append({'name':'Execução','passed':False,'detail':str(e),'trace':traceback.format_exc()})
    result={'status':'passed' if all(x['passed'] for x in CHECKS) else 'failed','base_commit':PRESERVATION,'checked_commit':git('rev-parse','HEAD').decode().strip(),
            'checks_count':len(CHECKS),'failed_count':sum(not x['passed'] for x in CHECKS),'checks':CHECKS,
            'scope':'Preservação, vínculos e interação Chromium. Web Share/clipboard simulados; nenhuma mensagem enviada; sem aparelho físico ou leitor de tela real.'}
    dump(OUT/'qa.json',result);print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False))
    if result['status']!='passed':
        print(json.dumps([x for x in CHECKS if not x['passed']],ensure_ascii=False));raise SystemExit(1)

if __name__=='__main__':main()
