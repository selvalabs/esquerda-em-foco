"""Prova de publicação por HTTP/SHA-256 e interação no Pages.
Nenhum contato é acessado; não há clique de envio em aplicativos externos.
"""
from __future__ import annotations
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlsplit,parse_qs
import json,os,subprocess,time
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
BASE='https://selvalabs.github.io/esquerda-em-foco/'
FILES=['index.html','assets/editorial-selected.css','assets/selecionados.js','assets/selecionados-core.js','assets/pauta-filters-editorial.js',
       'assets/pauta-filter-core.js','assets/pauta-filters.css','assets/pauta-v2.css','assets/sc-federais-filters-v2-data.js',
       'data/sc-selected-ui/manifest.json','data/sc-editorial-selected-r1/editorial.json','data/sc-semantic-v2-ui/payload.json']
OUT=Path('/tmp/eef-selected-live');OUT.mkdir(parents=True,exist_ok=True)
SHA=os.environ.get('GITHUB_SHA') or subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
report={'status':'pending','expected_commit':SHA,'files':[],'browser':[],'scope':'Publicação estática e interação Chromium no endereço público. Sem envio por WhatsApp, aparelho físico ou leitor de tela real.'}
try:
    for attempt in range(1,25):
        rows=[]
        for file in FILES:
            expected=sha256((ROOT/file).read_bytes()).hexdigest()
            url=BASE+('' if file=='index.html' else file)+'?verify='+SHA
            row={'path':file,'expected_sha256':expected,'matched':False}
            try:
                with urlopen(Request(url,headers={'User-Agent':'EEF-PublicationCheck/3','Cache-Control':'no-cache'}),timeout=15) as response:
                    actual=sha256(response.read()).hexdigest()
                    row.update(http_status=response.status,actual_sha256=actual,matched=response.status==200 and actual==expected)
            except Exception as e:row['error']=str(e)[:200]
            rows.append(row)
        report['files']=rows
        print(json.dumps({'attempt':attempt,'matched':sum(x['matched'] for x in rows),'total':len(rows)}),flush=True)
        if all(x['matched'] for x in rows):break
        time.sleep(10)
    if not all(x['matched'] for x in report['files']):raise RuntimeError('A versão servida ainda não corresponde ao commit esperado')
    with sync_playwright() as p:
        browser=p.chromium.launch()
        for width in [390,1440]:
            context=browser.new_context(viewport={'width':width,'height':900},locale='pt-BR',reduced_motion='reduce')
            page=context.new_page();errors=[];requests=[]
            page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
            page.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='selvalabs.github.io' else r.abort())
            page.goto(BASE+'?verify='+SHA,wait_until='networkidle')
            page.wait_for_function('document.documentElement.classList.contains("eef-selected-ready")')
            page.add_style_tag(content='html{scroll-behavior:auto!important}')
            count=page.locator('article.candidate').count()
            if count!=48 or page.locator('[data-eef-paragraph]').count()!=67:raise RuntimeError('Cards ou redação publicados não correspondem à integração')
            nav=page.locator('#eefSelectedNav')
            if not nav.evaluate('(e)=>{const r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));}'):raise RuntimeError('Atalho da navbar sobreposto')
            selected=['240002533824','240002533818']
            for cid in selected:page.locator(f'[data-eef-toggle="{cid}"]').click()
            if width<=980:page.locator('#pautaOpen').click()
            page.locator('[data-pauta-topic="saude"]').click()
            if width<=980:
                page.keyboard.press('Escape');page.wait_for_function('!document.getElementById("pautaDialog").open && document.activeElement.id==="pautaOpen"')
            initial_filtered=page.locator('.party-section .candidate:not([hidden])').count()
            if initial_filtered!=10:raise RuntimeError('Filtro Saúde alterou seu conjunto documentado')
            nav.click()
            if page.locator('#eefReaderHost .candidate').get_attribute('data-tse-id')!=selected[0]:raise RuntimeError('A coleção não manteve a ordem de seleção')
            page.locator('#eefReaderHost .eef-source-ref').first.click()
            page.wait_for_function('document.getElementById("pauta-contexto-240002533824").open')
            bounds=page.locator('#eefCollection').bounding_box()
            if bounds['y']<0 or bounds['y']+bounds['height']>901:raise RuntimeError('Diálogo saiu do viewport ao navegar a uma fonte')
            page.locator('#eefReaderHost h3').scroll_into_view_if_needed()
            page.screenshot(path=str(OUT/f'{width}-reader.png'))
            page.locator('#eefNext').click()
            if page.locator('#eefReaderHost .candidate').get_attribute('data-tse-id')!=selected[1] or not page.locator('#eefReaderHost .pauta-v2-gap').is_visible():raise RuntimeError('Ficha sem pauta filtrável não pôde ser consultada na coleção')
            page.locator('#eefShareCollection').click()
            link=page.locator('#eefShareUrl').input_value();fragment=parse_qs(urlsplit(link).fragment)
            if fragment.get('selecionados')!=[','.join(selected)] or fragment.get('ficha')!=[selected[1]]:raise RuntimeError('Link não conserva conjunto e ficha aberta')
            wa=page.locator('#eefWhatsapp').get_attribute('href')
            if urlsplit(wa).netloc!='wa.me' or not parse_qs(urlsplit(wa).query)['text'][0].endswith(link):raise RuntimeError('Texto do WhatsApp não contém o link exato')
            if width==390:page.screenshot(path=str(OUT/'390-share.png'))
            page.keyboard.press('Escape');page.wait_for_function('!document.getElementById("eefShareDialog").open && document.activeElement.id==="eefShareCollection"')
            page.locator('#eefCollectionClose').click();page.wait_for_function('!document.documentElement.classList.contains("eef-collection-open")')
            if page.locator('.party-section .candidate:not([hidden])').count()!=initial_filtered:raise RuntimeError('Retorno perdeu o estado do filtro')
            recipient=browser.new_context(viewport={'width':width,'height':900},locale='pt-BR',reduced_motion='reduce')
            other=recipient.new_page();other.on('pageerror',lambda e:errors.append(str(e)))
            other.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='selvalabs.github.io' else r.abort())
            other.goto(link,wait_until='networkidle');other.wait_for_function('document.getElementById("eefCollection").open')
            if other.locator('#eefSelectedNav [data-eef-count]').text_content()!='2' or other.locator('#eefReaderHost .candidate').get_attribute('data-tse-id')!=selected[1]:raise RuntimeError('Um novo navegador não reconstruiu a coleção publicada')
            if other.locator('article.candidate').count()!=48 or other.locator('#eefReaderHost .candidate').count()!=1:raise RuntimeError('Fichas duplicadas ou omitidas no destino')
            overflow=other.evaluate('document.documentElement.scrollWidth>innerWidth')
            stored=other.evaluate('localStorage.length+sessionStorage.length')
            if errors or overflow or stored:raise RuntimeError(str({'errors':errors,'overflow':overflow,'stored':stored}))
            if any('/api/metrics/' in r for r in requests):raise RuntimeError('Métricas foram indevidamente ativadas')
            report['browser'].append({'width':width,'candidate_count':count,'paragraphs':67,'selected':len(selected),
                'single_card_reader':True,'source_anchor_in_viewport':True,'whatsapp_link_valid':True,'recipient_collection_restored':True,
                'filter_preserved_on_return':True,'js_errors':errors,'overflow':overflow,'storage_entries':stored,
                'external_message_sent':False})
            context.close();recipient.close()
        browser.close()
    report['status']='passed'
except Exception as e:report.update(status='failed',error=str(e));raise
finally:
    report['checked_at']=datetime.now(timezone.utc).isoformat()
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PUBLICATION '+json.dumps(report,ensure_ascii=False),flush=True)
