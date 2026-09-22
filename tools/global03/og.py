"""Generate the site's OG card with local browser fonts; no font files exported."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
markup='''<!doctype html><meta charset="utf-8"><style>*{box-sizing:border-box}body{margin:0;width:1200px;height:630px;background:#f3eadc;color:#1c2829;padding:58px 68px;font-family:Georgia,serif}.top{display:flex;justify-content:space-between;border-bottom:1px solid #cdbfae;padding-bottom:22px;font:15px Arial,sans-serif;letter-spacing:2px;text-transform:uppercase}.marks{display:inline-flex;gap:8px;margin-right:18px}.marks i{width:12px;height:12px;border-radius:50%;background:#c47b98}.marks i:nth-child(2){background:#486f5c}.marks i:nth-child(3){background:#527ea3}h1{font-size:105px;line-height:.92;letter-spacing:-5px;font-weight:400;margin:42px 0 28px}em{color:#486f5c}.foot{font:22px/1.5 Arial,sans-serif;border-top:1px solid #cdbfae;padding-top:24px;margin-top:28px}.note{position:absolute;right:68px;top:216px;max-width:330px;font-size:29px;line-height:1.4;border-left:1px solid #cdbfae;padding-left:30px}</style><div class="top"><span><span class="marks"><i></i><i></i><i></i></span>Caderno eleitoral</span><span>2026</span></div><h1>Esquerda<br><em>em foco.</em></h1><div class="note">Candidaturas,<br>trajetórias e fontes<br>para consulta.</div><div class="foot">Escolha um estado. Conheça a edição.</div>'''
with sync_playwright() as p:
    options={'executable_path':os.environ['EEF_CHROMIUM']} if os.environ.get('EEF_CHROMIUM') else {}
    b=p.chromium.launch(headless=True,**options);page=b.new_page(viewport={'width':1200,'height':630},device_scale_factor=1)
    page.set_content(markup);page.screenshot(path=str(ROOT/'assets/seo/global-home.png'));b.close()
