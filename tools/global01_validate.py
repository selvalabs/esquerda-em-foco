"""Validate GLOBAL-01 deliverables against frozen git objects and actual observations.

Uses only the standard library and git. Does not rebuild, edit, fetch political
sources, or publish any edition. The observation artifact is supplied explicitly.
Example: python tools/global01_validate.py --raw-observations /tmp/raw --out /tmp/qa.json
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/global-integration'
ALLOWED = {
    'docs/GLOBAL-CANONICAL-AUDIT.md', 'docs/GLOBAL-CANONICAL-DECISIONS.md',
    'docs/GLOBAL-CANONICAL-GAPS.md',
    'data/global-integration/current-editions.json',
    'data/global-integration/evidence-index.json',
    'data/global-integration/capability-matrix.json',
    'data/global-integration/qa.json',
    'tools/global01/observe.py', 'tools/global01_validate.py',
    '.github/workflows/global01-audit.yml', '.github/workflows/global01-deliverables.yml',
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args], cwd=ROOT, stderr=subprocess.PIPE)


def blob(ref: str, path: str) -> bytes:
    return git('show', f'{ref}:{path}')


class Cards(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str | None] = []
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == 'article' and 'candidate' in (attrs_dict.get('class') or '').split():
            self.ids.append(attrs_dict.get('id'))
        if tag == 'script' and attrs_dict.get('src'):
            self.scripts.append(str(attrs_dict['src']).split('?', 1)[0])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw-observations', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    checks: list[dict] = []

    def check(name: str, result: bool, detail=None) -> None:
        checks.append({'check': name, 'passed': bool(result), 'detail': detail})

    inventory = read_json(DATA / 'current-editions.json')
    index = read_json(DATA / 'evidence-index.json')
    matrix = read_json(DATA / 'capability-matrix.json')
    qa = read_json(DATA / 'qa.json')
    refs = inventory['refs']
    evidence = {e['id']: e for e in index['evidence']}
    columns = matrix['edition_columns']
    check('refs_are_consistent', refs == index['refs'] == qa['refs'])
    check('seven_unique_editions', len(columns) == len(set(columns)) == 7)
    check('inventory_matches_matrix_order', columns == [e['edition_id'] for e in inventory['editions']])
    check('unique_evidence_ids', len(evidence) == len(index['evidence']))
    paths_seen = set()
    for eid, entry in evidence.items():
        for path in entry['paths']:
            data = blob(refs[entry['ref']], path)
            check(f'evidence:{eid}:{path}', bool(data))
            paths_seen.add((entry['ref'], path))
    rows = matrix['capabilities']
    check('33_unique_capabilities', len(rows) == len({r['id'] for r in rows}) == 33)
    check('231_observed_cells', sum(len(r['states']) for r in rows) == 231)
    states = set(matrix['status_definitions'])
    decisions = {'adopt', 'adapt', 'edition-specific', 'do-not-globalize'}
    for row in rows:
        prefix = row['id']
        check(f'{prefix}:states', len(row['states']) == 7 and set(row['states']) <= states)
        check(f'{prefix}:observations', len(row['observations']) == 7 and all(row['observations']))
        check(f'{prefix}:decision', row['decision'] in decisions)
        check(f'{prefix}:evidence', bool(row['sources']) and set(row['sources'] + row['donor']) <= set(evidence))
        check(f'{prefix}:complete', all(row.get(k) for k in ['area', 'name', 'basis', 'strength', 'risk', 'target', 'dependencies', 'migration_test']))
    raw = args.raw_observations
    observations = read_json(raw / 'browser-audit.json')
    static = {e['edition']: e for e in read_json(raw / 'static-inventory.json')}
    hashes = read_json(raw / 'source-file-hashes.json')
    tests = (raw / 'node-tests.txt').read_text(encoding='utf-8')
    for ed in inventory['editions']:
        ref = refs[ed['ref']]
        source = blob(ref, ed['entrypoint'])
        parsed = Cards()
        parsed.feed(source.decode('utf-8'))
        check(f'{ed["edition_id"]}:hash', hashlib.sha256(source).hexdigest() == ed['html_sha256'] == static[ed['edition_id']]['sha256'])
        check(f'{ed["edition_id"]}:size', len(source) == ed['html_bytes'])
        check(f'{ed["edition_id"]}:cards', len(parsed.ids) == len(set(parsed.ids)) == ed['html_cards'] and all(parsed.ids))
        check(f'{ed["edition_id"]}:status', (ed['publication_status'] == 'branch_only') == (ed['ref'] == 'rs_branch'))
        for runtime in ed['effective_runtime']:
            if not runtime.startswith('inline:'):
                check(f'{ed["edition_id"]}:runtime:{runtime}', bool(blob(ref, runtime)))
    for key, expected in [('passed', qa['observations']['passed']), ('failed', qa['observations']['failed'])]:
        check(f'browser_summary:{key}', observations[key] == expected)
    check('browser_check_count', len(observations['checks']) == qa['observations']['checks'])
    failed = [c for c in observations['checks'] if not c['passed']]
    check('SP_gap_not_hidden', len(failed) == 1 and failed[0]['edition'] == 'sp-federais' and failed[0]['check'] == 'hidden_candidate_anchor_reveals' and qa['findings'][0]['fixed_in_this_round'] is False)
    check('no_claim_of_live_recheck', 'nova conferência HTTP do site público' in qa['not_performed'])
    for key, expected in [('tests', 47), ('pass', 47), ('fail', 0), ('skipped', 0)]:
        match = re.search(rf'^# {key} (\d+)\s*$', tests, re.MULTILINE)
        check(f'actual_node_tap:{key}', bool(match) and int(match.group(1)) == expected)
    for ref_key, expected in [('main', 1638), ('rs_branch', 674)]:
        tracked = git('ls-tree', '-r', '--name-only', refs[ref_key]).decode().splitlines()
        check(f'{ref_key}:manifest_count', len(tracked) == len(hashes[ref_key]) == expected)
        mismatches = [p for p in tracked if hashlib.sha256(blob(refs[ref_key], p)).hexdigest() != hashes[ref_key].get(p)]
        check(f'{ref_key}:full_source_manifest', not mismatches, mismatches)
    for ref_key, path, field, expected in [
        ('main', 'config/topics-v1.json', 'topics', 29),
        ('main', 'data/rs/topics.json', 'topics', 28),
        ('main', 'data/pr/taxonomy.json', 'themes', 25),
        ('main', 'data/sp/round-c/product.json', 'taxonomy', 30),
    ]:
        value = json.loads(blob(refs[ref_key], path))
        check(f'taxonomy:{path}', len(value[field]) == expected)
    product = json.loads(blob(refs['main'], 'data/sp/round-c/product.json'))
    directions = Counter(c['direction'] for r in product['records'] for c in r['claims_2026'])
    check('SP_semantics_claim_directions', dict(directions) == {'apoio_ou_prioridade': 18, 'proposta': 75, 'atuacao': 9}, dict(directions))
    site = ET.fromstring(blob(refs['main'], 'sitemap.xml'))
    urls = [urlsplit(e.text or '').path.removeprefix('/esquerda-em-foco') or '/' for e in site.iter() if e.tag.endswith('}loc')]
    check('root_sitemap_inventory', urls == inventory['global_findings']['root_sitemap_entries'], urls)
    main_paths = set(git('ls-tree', '-r', '--name-only', refs['main']).decode().splitlines())
    check('no_SP_state_or_registry_in_baseline', not ({'sp/deputados-estaduais/index.html', 'config/editions.json'} & main_paths))
    for name in ['GLOBAL-CANONICAL-AUDIT.md', 'GLOBAL-CANONICAL-DECISIONS.md', 'GLOBAL-CANONICAL-GAPS.md']:
        doc = ROOT / 'docs' / name
        text = doc.read_text(encoding='utf-8')
        check(f'doc:{name}:substantive', len(text) > 3000)
        for link in re.findall(r'\]\(([^)]+)\)', text):
            if not link.startswith(('http://', 'https://', '#')):
                check(f'doc:{name}:link:{link}', (doc.parent / link.split('#', 1)[0]).resolve().is_file())
    changed = git('diff', '--name-status', refs['main'], 'HEAD').decode().splitlines()
    unexpected = [line for line in changed if line.split('\t')[-1] not in ALLOWED or line.split('\t')[0] != 'A']
    check('audit_only_additions_no_existing_file_changed', not unexpected, unexpected)
    report = {
        'head_sha': git('rev-parse', 'HEAD').decode().strip(), 'refs': refs,
        'checks': checks, 'passed': sum(c['passed'] for c in checks),
        'failed': sum(not c['passed'] for c in checks), 'evidence_paths_verified': len(paths_seen),
        'capabilities': len(rows), 'edition_cells': sum(len(r['states']) for r in rows),
        'changed_paths': changed,
        'meaning': 'Validação do pacote documental; não corrige o finding SP nem certifica conteúdo político.',
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'checks'}, ensure_ascii=False, indent=2))
    for entry in checks:
        if not entry['passed']:
            print('FAILED:', json.dumps(entry, ensure_ascii=False))
    raise SystemExit(1 if report['failed'] else 0)


if __name__ == '__main__':
    main()
