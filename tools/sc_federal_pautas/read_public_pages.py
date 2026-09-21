"""Inspeção pontual de páginas públicas; não atribui pautas automaticamente."""
from __future__ import annotations
import json
from playwright.sync_api import sync_playwright

URLS = [
    'https://2026.votelgbt.org/candidatura/99',
    'https://doe.la/samarapsol',
    'https://www.instagram.com/p/DcwXrbvvqo7/',
    'https://www.instagram.com/jordanasanz/',
]
with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(locale='pt-BR')
    for url in URLS:
        page = context.new_page()
        try:
            response = page.goto(url, wait_until='domcontentloaded', timeout=25000)
            page.wait_for_timeout(2000)
            text = page.locator('body').inner_text(timeout=8000)
            start = text.find('Prioridades')
            excerpt = text[start:start+1500] if start >= 0 else text[:2500]
            print('PUBLIC_PAGE ' + json.dumps({'url':url, 'final_url':page.url, 'status':response.status if response else None, 'title':page.title(), 'review_excerpt':excerpt}, ensure_ascii=False), flush=True)
        except Exception as e:
            print('PUBLIC_PAGE ' + json.dumps({'url':url, 'error':str(e)[:400]}, ensure_ascii=False), flush=True)
        finally:
            page.close()
    browser.close()
