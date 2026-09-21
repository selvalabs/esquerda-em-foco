"""Leitura pontual, sem login, para revisão humana. Nunca atribui pautas automaticamente.
O conteúdo não é inserido no site nem persistido na base editorial.
"""
from __future__ import annotations
import json
from playwright.sync_api import sync_playwright

URLS = [
    'https://nandjaxokleng.com.br/',
    'https://www.jessicamichels.com.br/',
    'https://doe.la/profjuandozio',
    'https://www.giovanamondardo.com.br/',
    'http://www.drarosana4321.com.br/',
    'http://www.guaraci4343.com.br/',
]
with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(locale='pt-BR', ignore_https_errors=False)
    for url in URLS:
        page = context.new_page()
        try:
            response = page.goto(url, wait_until='domcontentloaded', timeout=35000)
            page.wait_for_timeout(2500)
            text = page.locator('body').inner_text(timeout=10000)
            links = page.locator('a[href]').evaluate_all("els => els.map(a => ({text:a.innerText.trim(),url:a.href})).filter(a => a.text)")
            print('PUBLIC_PAGE ' + json.dumps({'url':url, 'final_url':page.url, 'status':response.status if response else None, 'title':page.title(), 'text':text[:22000], 'links':links[:55]}, ensure_ascii=False), flush=True)
        except Exception as e:
            print('PUBLIC_PAGE ' + json.dumps({'url':url, 'error':str(e)[:700]}, ensure_ascii=False), flush=True)
        finally:
            page.close()
    browser.close()
