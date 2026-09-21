"""Importa a revisão pinada sem substituir o index atual nem outras frentes.
Uso: python tools/sc_federal_taxonomy/prepare.py
Os arquivos importados mantêm a proveniência do round de pesquisa anterior.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

SOURCE = 'c2ce0d44f64c72c5949d373fa210d9144948d310'
INTEGRATION_BASE = '38e66f643048a00f15a70d6f7be3a69e83cf4c23'
OUT = Path('data/sc-federais-topics-v1')
PREFIXES = ('data/sc-federais-pautas/', 'tools/sc_federal_pautas/')
EXACT = ('assets/sc-federais-pautas.css', 'docs/SC-FEDERAIS-PAUTAS-METODO.md',
         'docs/SC-FEDERAIS-PAUTAS-RESULTADOS.md', 'docs/SC-FEDERAIS-PAUTAS-TAXONOMIA.md')


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args])


def run() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = git('ls-tree', '-r', '--name-only', SOURCE).decode().splitlines()
    imported = {}
    for path in paths:
        if not (path.startswith(PREFIXES) or path in EXACT):
            continue
        data = git('show', f'{SOURCE}:{path}')
        target = Path(path)
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        imported[path] = hashlib.sha256(data).hexdigest()
    assert all(Path(path).exists() for path in EXACT)
    spec = importlib.util.spec_from_file_location('review_builder', 'tools/sc_federal_pautas/build_review.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    baseline, records = module.compile_records()
    module.update_site(records)
    module.write_reports(baseline, records)
    index = Path('index.html')
    text = index.read_text(encoding='utf-8')
    old = 'A taxonomia para os futuros filtros continua em revisão e nenhum filtro por pauta foi ativado nesta etapa.'
    new = 'Os temas foram organizados em uma taxonomia documental. Os filtros por pauta ainda não estão ativos; sua implementação será uma etapa separada.'
    assert old in text
    index.write_text(text.replace(old, new, 1), encoding='utf-8')
    provenance = {
        'schema_version': '1.0.0', 'research_commit': SOURCE,
        'research_date': '2026-09-21', 'integration_base_commit': INTEGRATION_BASE,
        'method': 'reaplicacao_dos_blocos_editoriais_no_index_atual',
        'old_index_copied': False, 'imported_source_sha256': imported,
        'note': 'A proveniência é do round de pesquisa. O QA desta integração está em integration-qa.json, não no qa.json histórico importado.'
    }
    (OUT / 'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'imported_files': len(imported), 'candidates': len(records), 'filters_active': False}))


if __name__ == '__main__':
    run()
