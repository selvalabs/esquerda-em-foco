"""Valida vínculos e protótipo, não equivalência política automática.
Navegador testa leitura individual; compartilhamento e clipboard são simulados.
PRESERVATION_BASE aponta para a base efetiva do PR.
"""
from __future__ import annotations
from functools import partial
from hashlib import sha1, sha256
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json,os,subprocess,threading,traceback
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
from build import ROOT,OUT,PREVIEW,BASE,PINS,load,build,dump

CHECKS=[]
PRESERVATION=os.environ.get('PRESERVATION_BASE',BASE)
SHOTS=Path('/tmp/eef-editorial-selected-shots');SHOTS.mkdir(parents=True,exist_ok=True)

def check(name,ok,detail=None):
    CHECKS.append({'name':name,'passed':bool(ok),'detail':detail})
    if not ok:raise AssertionError(name+': '+str(detail))

def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)

def own(path):
    return path.startswith(('tools/sc_editorial_selected/','data/sc-editorial-selected-r1/','docs/SC-EDITORIAL-SELECTED')) or path in ('.github/workflows/sc-editorial-selected-round1.yml','tests/sc_editorial_selected.test.cjs')

def static():
    changed=[];count=0
    for entry in git('ls-tree','-rz',PRESERVATION).split(b'\0'):
        if not entry:continue
        meta,raw=entry.split(b'\t',1);mode,kind,digest=meta.decode().split();path=raw.decode()
        if own(path):continue
        count+=1;p=ROOT/path
        if not p.exists():changed.append(path);continue
        data=os.readlink(p).encode() if mode=='120000' else p.read_bytes()
        actual=sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if actual!=digest:changed.append(path)
    check('Todos os arquivos preexistentes, incluindo index e assets, preservados',not changed,{'base':PRESERVATION,'files':count,'changed':changed})
    data=load('data/sc-editorial-selected-r1/editorial.json')
    model=load('data/sc-semantic-v2/candidate-content.json')['candidates']
    locations=load('data/sc-editorial-selected-r1/paragraph-locations.json')['associations']
    associations=load('data/sc-semantic-v2/association-audit.json')['associations']
    original={c['candidate_id']:c for c in model}
    check('48 fichas representadas uma vez',len(data['candidates'])==48 and len({c['candidate_id'] for c in data['candidates']})==48)
    items_seen=[]
    for c in data['candidates']:
        old=original[c['candidate_id']]
        check(c['name']+': identificação e elegibilidade preservadas',all(c[k]==old[k] for k in ['candidate_id','name','party','anchor','association_ids','current_macro_ids','current_family_ids','has_current_defended_pautas']))
        check(c['name']+': mesmos blocos e limitações', [s['id'] for s in c['sections']]==[s['id'] for s in old['sections']] and c['retained_limitations']==old['sources_and_context']['previous_limitations'])
        if not c['sections']:check(c['name']+': lacuna sem pauta inventada',bool(c['gap_text']) and not c['association_ids'])
        for section in c['sections']:
            original_section=next(s for s in old['sections'] if s['id']==section['id'])
            old_items={i['item_id']:i for i in original_section['items']}
            linked=[]
            for p in section['paragraphs']:
                linked+=p['item_ids'];items_seen+=p['item_ids']
                check(p['paragraph_id']+': fontes e associações exatas',set(p['source_ids'])=={sid for iid in p['item_ids'] for sid in old_items[iid]['source_ids']} and set(p['association_ids'])=={aid for iid in p['item_ids'] for aid in old_items[iid]['association_ids']})
            check(c['name']+': nenhum item omitido em '+section['id'],len(linked)==len(set(linked))==len(old_items) and set(linked)==set(old_items))
    check('145 itens preservados nos 39 blocos',len(items_seen)==len(set(items_seen))==145 and sum(len(c['sections']) for c in data['candidates'])==39)
    check('156 associações com localizador sem alterar a evidência',len(locations)==156 and all(locations[a['association_id']]['exact_evidence']==a['match_text'] and locations[a['association_id']]['eligible_v2']==a['eligible_v2'] and locations[a['association_id']]['evidence_source_ids']==a['source_ids'] for a in associations))
    check('112 elegibilidades mantidas',sum(v['eligible_v2'] for v in locations.values())==112)
    for source in data['sources'].values():
        check(source['source_id']+': rótulo não inventa data',('sem data original informada' in source['caption'])==(source['publication_date'] is None))
    by={c['candidate_id']:c for c in data['candidates']}
    def section(cid,key):return next(s for s in by[cid]['sections'] if s['id']==key)
    check('Atuação registrada não sugere apenas mandato anterior',all(s['title']=='Atuação registrada' for c in data['candidates'] for s in c['sections'] if s['id']=='historico'))
    check('Aviso de Ivan permanece junto da atuação', 'não pôde ser reconferida' in section('240002533820','historico')['notice'])
    check('Atribuição e limites do voto permanecem junto de Ana Paula Lima','próprio mandato' in section('240002533824','historico')['notice'] and 'votação nominal' in section('240002533824','historico')['notice'])
    check('Contextos sem período/autoria conservam aviso próximo',all(s['notice'] for c in data['candidates'] for s in c['sections'] if s['id']=='contexto'))
    check('Coleção não habilita comparação nem produção',data['comparison_enabled'] is False and data['production_enabled'] is False)
    check('Inputs sem alteração',all(sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in PINS.items()))
    paths=[p for p in OUT.glob('*.json') if p.name!='qa.json']+[PREVIEW/'index.html',PREVIEW/'LEIA-ME.txt',ROOT/'docs/SC-EDITORIAL-SELECTED-ROUND1.md']
    hashes={str(p):sha256(p.read_bytes()).hexdigest() for p in paths};build()
    check('Compilação determinística',all(sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items()))
    unit=subprocess.run(['node','--test','tests/sc_editorial_selected.test.cjs'],cwd=ROOT,capture_output=True,text=True)
    (OUT/'unit-tests.txt').write_text(unit.stdout+unit.stderr,encoding='utf-8')
    check('Suíte de núcleo e links aprovada',unit.returncode==0,unit.stdout[-1600:]+unit.stderr)
    return data

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def browser(data):
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(PREVIEW)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}/'
    a='240002533818';b='240002533824';ju='240002533832'
    launch={'executable_path':os.environ['CHROMIUM_PATH']} if os.environ.get('CHROMIUM_PATH') else {}
    mock="""window.__copied=[];window.__shareCalls=[];window.__clipReject=false;window.__shareResult='cancel';Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async v=>{if(window.__clipReject)throw Error('denied');window.__copied.push(v);}}});Object.defineProperty(navigator,'share',{configurable:true,value:async v=>{window.__shareCalls.push(v);if(window.__shareResult==='cancel')throw new DOMException('cancel','AbortError');}});Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>true});"""
    with sync_playwright() as p:
        browser=p.chromium.launch(**launch)
        try:
            for width in [320,360,390,430,768,1024,1440]:
                label=str(width)+'px: '
                ctx=browser.new_context(viewport={'width':width,'height':900},locale='pt-BR',reduced_motion='reduce',has_touch=width<=430)
                ctx.add_init_script(mock)
                page=ctx.new_page();errors=[];requests=[]
                page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
                page.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='127.0.0.1' else r.abort())
                page.goto(base,wait_until='networkidle')
                check(label+'Lista contém 48 fichas',page.locator('#roster .roster-row').count()==48)
                check(label+'Sem overflow inicial',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                for cid in [a,b,ju]:page.locator(f'#roster [data-action="toggle"][data-id="{cid}"]').click()
                check(label+'Seleção explícita de três fichas',page.locator('#selectedViewBtn [data-selection-count]').inner_text()=='3')
                page.locator('#nameSearch').fill('Ana Paula Lima')
                check(label+'Busca de nomes não apaga seleção',page.locator('#roster .roster-row').count()==1 and page.locator('#selectedViewBtn [data-selection-count]').inner_text()=='3')
                page.locator('#selectedViewBtn').click()
                check(label+'Uma ficha por vez, na ordem de seleção',page.locator('.reader-card').count()==1 and page.locator('.reader-card').get_attribute('data-candidate-id')==a)
                page.locator('#next').click()
                check(label+'Navegação abre a segunda ficha sem comparação',page.locator('.reader-card').count()==1 and page.locator('.reader-card').get_attribute('data-candidate-id')==b and page.locator('#pager').inner_text()=='Ficha 2 de 3')
                title=page.locator('[data-section="historico"] h4').text_content()
                warning=page.locator('[data-section="historico"] .warning').text_content()
                check(label+'Pautas e atuação mantêm títulos e ressalvas',title=='Atuação registrada' and 'votação nominal' in warning,{'title':title,'warning':warning})
                check(label+'Fontes por parágrafo são legíveis',page.locator('.citations a').count()>0 and 'sem data original informada' in page.locator('.citations a').first.inner_text())
                if width in [320,390,1440]:
                    page.locator('#activeName').scroll_into_view_if_needed();page.screenshot(path=str(SHOTS/f'{width}-leitura.png'))
                page.locator('[data-action="share-single"]').click()
                check(label+'Link individual usa âncora publicada',page.locator('#shareUrl').input_value()==data['site_base']+'#candidato-'+b)
                wa=page.locator('#whatsappLink').get_attribute('href')
                check(label+'WhatsApp sem telefone imposto',wa.startswith('https://wa.me/?text=') and 'phone=' not in wa)
                page.locator('#copyLink').click();page.wait_for_function('document.getElementById("shareStatus").textContent.includes("Link copiado")')
                check(label+'Cópia confirmada por adapter',len(page.evaluate('window.__copied'))==1 and 'Link copiado' in page.locator('#shareStatus').inner_text())
                page.locator('#nativeShare').click();page.wait_for_function('document.getElementById("shareStatus").textContent.includes("cancelado")')
                check(label+'Cancelar não dispara cópia nem envio alternativo',len(page.evaluate('window.__copied'))==1 and 'cancelado' in page.locator('#shareStatus').inner_text())
                page.evaluate('window.__clipReject=true');page.locator('#copyLink').click();page.wait_for_function('document.activeElement.id==="shareUrl"')
                check(label+'Falha de cópia oferece seleção manual',page.evaluate('document.activeElement.id==="shareUrl"') and 'Não foi possível copiar' in page.locator('#shareStatus').inner_text())
                page.evaluate('window.__clipReject=false;window.__shareResult="ok"');page.locator('#nativeShare').click();page.wait_for_function('document.getElementById("shareStatus").textContent.includes("Confirme o envio")')
                check(label+'Handoff não é descrito como mensagem enviada','Confirme o envio' in page.locator('#shareStatus').inner_text())
                page.keyboard.press('Escape');page.wait_for_function('!document.getElementById("shareDialog").open && document.activeElement.dataset.action==="share-single"')
                check(label+'Escape devolve foco ao acionador',page.evaluate('document.activeElement.dataset.action==="share-single"'))
                page.locator('#shareCollection').click()
                collection_url=page.locator('#shareUrl').input_value()
                check(label+'Link de teste conserva conjunto no fragmento', '#selecionados=' in collection_url and 'edicao=sc-federais' in collection_url)
                check(label+'Coleção da prévia não é enviada como recurso publicado',page.locator('#whatsappLink').is_hidden() and page.locator('#nativeShare').is_hidden() and page.locator('#shareWarning').is_visible())
                if width==320:page.screenshot(path=str(SHOTS/'320-compartilhar.png'))
                page.keyboard.press('Escape');page.wait_for_function('!document.getElementById("shareDialog").open')
                page.locator('#backToList').click()
                check(label+'Retorno conserva busca da lista',page.locator('#nameSearch').input_value()=='Ana Paula Lima')
                page.goto(collection_url,wait_until='networkidle')
                page.wait_for_function('document.querySelector(".reader-card")?.dataset.candidateId==="240002533824" && !document.getElementById("readingView").hidden')
                check(label+'Link reconstrói coleção e ficha ativa',page.locator('#selectedViewBtn [data-selection-count]').inner_text()=='3' and page.locator('.reader-card').get_attribute('data-candidate-id')==b)
                page.evaluate("location.hash='#selecionados=999999999999&v=1&edicao=sc-federais'");page.wait_for_function('document.getElementById("notice").textContent.includes("preservada")')
                check(label+'Link inválido preserva a seleção',page.locator('#selectedViewBtn [data-selection-count]').inner_text()=='3' and 'preservada' in page.locator('#notice').inner_text())
                page.locator('.reader-card [data-action="toggle"]').click()
                check(label+'Remover ficha ativa abre outra sem perder coleção',page.locator('#selectedViewBtn [data-selection-count]').inner_text()=='2' and page.locator('.reader-card').get_attribute('data-candidate-id')==ju)
                page.locator('#clearCollection').click();page.locator('#cancelClear').click();page.wait_for_function('!document.getElementById("clearDialog").open')
                check(label+'Cancelar limpeza conserva coleção',page.locator('#selectedViewBtn [data-selection-count]').inner_text()=='2')
                page.locator('#clearCollection').click();page.locator('#confirmClear').click();page.wait_for_function('!document.getElementById("clearDialog").open')
                check(label+'Limpar mostra estado vazio sem ficha fantasma',page.locator('#selectedEmpty').is_visible() and page.locator('.reader-card').count()==0)
                # Force a fresh document, not just a hash change, for the independent 48-item case.
                page.goto(base+'?case=all',wait_until='networkidle')
                page.evaluate("[...document.querySelectorAll('#roster [data-action=toggle]')].forEach(b=>b.click())")
                page.locator('#selectedViewBtn').click()
                check(label+'48 selecionados, só uma ficha em leitura',page.locator('#selectedViewBtn [data-selection-count]').inner_text()=='48' and page.locator('.reader-card').count()==1)
                page.locator('#next').focus();page.keyboard.press('Enter')
                check(label+'Navegação por teclado',page.locator('#pager').inner_text()=='Ficha 2 de 48')
                if width==390:
                    active=page.locator('.reader-card').get_attribute('data-candidate-id')
                    page.set_viewport_size({'width':1440,'height':900});page.set_viewport_size({'width':390,'height':900})
                    check('Mudança de largura preserva ficha e coleção',page.locator('.reader-card').get_attribute('data-candidate-id')==active and page.locator('#selectedViewBtn [data-selection-count]').inner_text()=='48')
                    page.locator('.reader-card').dispatch_event('pointerdown',{'pointerType':'touch','clientX':260,'clientY':220})
                    page.locator('.reader-card').dispatch_event('pointerup',{'pointerType':'touch','clientX':90,'clientY':224})
                    check('Gesto horizontal simulado avança a leitura',page.locator('#pager').inner_text()=='Ficha 3 de 48')
                check(label+'Sem persistência, cookies ou requisições de seleção',page.evaluate('localStorage.length===0&&sessionStorage.length===0&&document.cookie===""') and all(urlsplit(u).hostname=='127.0.0.1' and '#' not in u for u in requests))
                page.reload(wait_until='networkidle')
                check(label+'Recarregar sem link esvazia seleção',page.locator('#selectedViewBtn [data-selection-count]').inner_text()=='0')
                check(label+'Sem erros JS ou overflow',not errors and page.evaluate('document.documentElement.scrollWidth<=innerWidth'),errors)
                ctx.close()
            ctx=browser.new_context(java_script_enabled=False);page=ctx.new_page();page.goto(base)
            check('Prévia sem JavaScript apresenta orientação e link real',page.locator('noscript').is_visible());ctx.close()
        finally:browser.close();server.shutdown()

def main():
    try:
        data=static();browser(data)
    except Exception as e:
        CHECKS.append({'name':'Execução','passed':False,'detail':str(e),'trace':traceback.format_exc()})
    result={'status':'passed' if all(c['passed'] for c in CHECKS) else 'failed','base_commit':PRESERVATION,'checked_commit':git('rev-parse','HEAD').decode().strip(),
        'checks_count':len(CHECKS),'failed_count':sum(not c['passed'] for c in CHECKS),'checks':CHECKS,
        'scope':'Estrutura e prévia Chromium em sete larguras. Web Share e clipboard simulados; WhatsApp não recebeu mensagens. Sem aparelho físico ou leitor de tela real. Não é QA da integração de produção.'}
    dump(OUT/'qa.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False))
    if result['status']!='passed':
        print(json.dumps([c for c in CHECKS if not c['passed']],ensure_ascii=False));raise SystemExit(1)

if __name__=='__main__':main()
