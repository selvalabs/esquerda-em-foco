"""Disponibilidade técnica, não validação automática do conteúdo da fonte.
Não acessa contas privadas. Redes já lidas em navegador conservam o registro manual.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import urllib.error
import urllib.request
from urllib.parse import urlsplit

ROOT = Path('data/sc-federais-pautas')
records = json.loads((ROOT / 'review.json').read_text(encoding='utf-8'))['candidates']
sources = {s['url']: s for r in records for s in r['sources']}


def probe(item: tuple[str, dict]) -> dict:
    url, source = item
    row = {'url':url, 'consulted_at':source['consulted_at'], 'editorial_access':source['access']}
    host = urlsplit(url).netloc.lower()
    if host.endswith(('instagram.com','facebook.com')) and source.get('verification_run'):
        return {**row, 'status':'leitura_publica_renderizada_registrada', 'verification_run':source['verification_run'], 'note':'Não repetida automaticamente para evitar bloqueios por frequência. A leitura de autoria/legenda está registrada na revisão.'}
    try:
        request = urllib.request.Request(url, method='HEAD', headers={'User-Agent':'EsquerdaEmFoco-SourceCheck/1.0'})
        with urllib.request.urlopen(request, timeout=12) as response:
            return {**row, 'status':'respondeu', 'http_status':response.status, 'final_url':response.url}
    except urllib.error.HTTPError as error:
        kind = 'nao_localizado_nesta_verificacao' if error.code in (404,410) else 'acesso_limitado_ou_metodo_nao_aceito'
        return {**row, 'status':kind, 'http_status':error.code, 'final_url':error.url}
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return {**row, 'status':'indisponivel_nesta_verificacao', 'error':str(error)[:240]}


with ThreadPoolExecutor(max_workers=6) as executor:
    rows = list(executor.map(probe, sorted(sources.items())))
result = {
    'checked_at':datetime.now(timezone.utc).isoformat(),
    'purpose':'Disponibilidade técnica das URLs, separada da leitura editorial já realizada.',
    'caveats':['HEAD pode ser bloqueado mesmo quando a página abre no navegador.', 'Resposta HTTP 200 não confirma identidade nem conteúdo.', '403, 429, login ou timeout não provam inexistência de propostas.', 'Respostas 404/410 exigem reconferência humana antes de publicar.'],
    'url_count':len(rows),
    'needs_recheck':[r['url'] for r in rows if r['status']=='nao_localizado_nesta_verificacao'],
    'results':rows
}
(ROOT / 'link-check.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'checked':len(rows), 'needs_recheck':result['needs_recheck']}, ensure_ascii=False))
