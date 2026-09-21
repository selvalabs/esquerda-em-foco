"""Leitura sem autenticação. Comentários e recomendações não são evidência autoral."""
from __future__ import annotations
import json
from playwright.sync_api import sync_playwright
URLS = [
'https://www.instagram.com/reel/Dcv7pi0uAG5/',
'https://www.facebook.com/marisouzalicerce/videos/queremos-vida-al%C3%A9m-do-trabalho-amanh%C3%A3-2-de-setembro-a-pec-2212019-que-prop%C3%B5e-o-f/1370510858564894/',
'https://www.facebook.com/marisouzalicerce/posts/vai-ter-cotistas-nas-universidades-de-sc-simas-cotas-raciais-s%C3%A3o-pol%C3%ADticas-p%C3%BAbli/1076336738413269/',
'https://www.instagram.com/reel/DcJUGGsvNJl/',
'https://www.instagram.com/reel/DcOtSLkz0o3/',
'https://www.instagram.com/reel/DWpJm7ZAr_P/',
'https://www.instagram.com/p/DdcRCR0hanD/',
'https://www.instagram.com/p/DcUJ6RklF3U/',
'https://www.instagram.com/reel/DbjQRqTBgQO/',
'https://www.facebook.com/camasao50/posts/a-extrema-direita-tem-um-projeto-de-medo-na-educa%C3%A7%C3%A3o-de-santa-catarinamas-o-thia/1619164642931346/'
]
with sync_playwright() as p:
    browser = p.chromium.launch()
    for url in URLS:
        context = browser.new_context(locale='pt-BR')
        page = context.new_page()
        try:
            response = page.goto(url, wait_until='domcontentloaded', timeout=20000)
            page.wait_for_timeout(1500)
            text = page.locator('body').inner_text(timeout=6000)
            print('AUTHORSHIP_CHECK ' + json.dumps({'url':url, 'final_url':page.url, 'status':response.status if response else None, 'title':page.title(), 'review_excerpt':text[:4000]}, ensure_ascii=False), flush=True)
        except Exception as e:
            print('AUTHORSHIP_CHECK ' + json.dumps({'url':url, 'error':str(e)[:300]}, ensure_ascii=False), flush=True)
        finally:
            context.close()
    browser.close()
