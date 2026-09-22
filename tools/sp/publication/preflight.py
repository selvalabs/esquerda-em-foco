"""Read-only publication checks on a committed, simulated merge.
SP_BASE_SHA must name the main commit BEFORE the integration.
Reports are written outside the checkout. No remote writes or source collection.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(os.environ.get('SP_CHECK_OUTPUT', '/tmp/sp-publication-preflight'))
OUT.mkdir(parents=True, exist_ok=True)
BASE = os.environ['SP_BASE_SHA']
if not re.fullmatch(r'[a-f0-9]{40}', BASE):
    raise ValueError('SP_BASE_SHA must be an immutable commit SHA')

def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args], cwd=ROOT)

def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()

def preservation() -> dict:
    entries = git('ls-tree', '-rz', BASE).split(b'\0')
    protected = 0
    mismatches = []
    for entry in entries:
        if not entry:
            continue
        meta, raw_path = entry.split(b'\t', 1)
        mode, kind, oid = meta.decode().split()
        path = raw_path.decode()
        if path in {'index.html', 'sitemap.xml'}:
            continue
        file = ROOT / path
        if mode == '120000':
            raw = os.readlink(file).encode() if file.is_symlink() else b''
        else:
            raw = file.read_bytes() if file.is_file() else b''
        protected += 1
        if blob_sha(raw) != oid:
            mismatches.append(path)
    assert not mismatches, mismatches
    spec = importlib.util.spec_from_file_location('sp_builder', ROOT / 'tools/sp/round_c/build.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    home = (ROOT / 'index.html').read_text(encoding='utf-8')
    old_home = git('show', BASE + ':index.html').decode()
    assert builder.NAV_LINK not in old_home, 'Baseline already contains SP; select pre-integration main'
    assert home.count(builder.NAV_LINK) == 1
    assert home.replace(builder.NAV_LINK, '') == old_home, 'Unbounded homepage change'
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    old_xml = ET.fromstring(git('show', BASE + ':sitemap.xml'))
    new_xml = ET.fromstring((ROOT / 'sitemap.xml').read_bytes())
    def urls(tree):
        return {node.find('s:loc', ns).text: ET.tostring(node) for node in tree.findall('s:url', ns)}
    old_urls, new_urls = urls(old_xml), urls(new_xml)
    assert set(new_urls) - set(old_urls) == {
        'https://selvalabs.github.io/esquerda-em-foco/sp/',
        'https://selvalabs.github.io/esquerda-em-foco/sp/deputados-federais/'
    }
    for url in old_urls:
        old_node = old_xml.find("s:url[s:loc='" + url + "']", ns)
        new_node = new_xml.find("s:url[s:loc='" + url + "']", ns)
        assert [(x.tag, x.text) for x in old_node] == [(x.tag, x.text) for x in new_node]
    allowed = ('sp/', 'data/sp/', 'docs/sp/', 'tools/sp/', 'tests/sp/', 'data/shared/', '.github/workflows/sp-')
    changed = git('diff', '--name-only', BASE, 'HEAD').decode().splitlines()
    unexpected = [p for p in changed if p not in {'index.html', 'sitemap.xml'} and not p.startswith(allowed)]
    assert not unexpected, unexpected
    return {'baseline_main': BASE, 'protected_preexisting_files': protected, 'changed_protected_files': [], 'homepage': 'only_delimited_SP_link', 'sitemap': 'two_SP_entries_only', 'changed_paths': len(changed)}

UNIT_RUNNER = r'''
import json, os, sys, unittest
start, pattern = sys.argv[1:3]
suite = unittest.defaultTestLoader.discover(start, pattern=pattern)
if os.environ.get('SP_TEST_BASE_OVERRIDE'):
    sys.modules['test_product'].BASE = os.environ['SP_TEST_BASE_OVERRIDE']
r = unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps({'tests': r.testsRun, 'failures': [x.id() for x, _ in r.failures], 'errors': [x.id() for x, _ in r.errors], 'skipped': [x.id() for x, _ in r.skipped]}))
'''

def unit(label: str, start: str, pattern: str = 'test*.py', cwd: Path = ROOT, override: bool = False) -> dict:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    if override:
        env['SP_TEST_BASE_OVERRIDE'] = BASE
    result = subprocess.run([sys.executable, '-c', UNIT_RUNNER, start, pattern], cwd=cwd, env=env, text=True, capture_output=True)
    (OUT / (label + '.log')).write_text(result.stderr + '\n' + result.stdout, encoding='utf-8')
    assert result.returncode == 0, label + ': process failure'
    return json.loads(result.stdout.strip().splitlines()[-1])

def node(label: str, path: str) -> dict:
    result = subprocess.run(['node', '--test', path], cwd=ROOT, text=True, capture_output=True)
    (OUT / (label + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
    assert result.returncode == 0, label
    return {k: int(re.search(r'^# ' + k + r' (\d+)$', result.stdout, re.M)[1]) for k in ['tests', 'pass', 'fail']}

def main() -> None:
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'gate': 'BLOCKED', 'baseline_main': BASE, 'simulated_merge': git('rev-parse', 'HEAD').decode().strip(), 'integrated_tree': git('rev-parse', 'HEAD^{tree}').decode().strip(), 'scope': 'Integration and software validation; no new factual or electoral research'}
    try:
        report['preservation'] = preservation()
        report['sp_data'] = unit('sp-data', 'tests/sp/round_c', 'test_product.py', override=True)
        report['sp_filters'] = node('sp-filters', 'tests/sp/round_c/test_filters.cjs')
        report['sc_semantic_filters'] = node('sc-semantic-filters', 'tests/sc_semantic_v2_ui.test.cjs')
        report['scope'] = unit('canonical-scope', 'tests/scope')
        report['rs'] = unit('rs', 'tests/rs')
        for key in ['sp_data', 'scope', 'rs']:
            assert not report[key]['failures'] and not report[key]['errors'] and not report[key]['skipped'], (key, report[key])
        with tempfile.TemporaryDirectory(prefix='sp-main-pr-') as temp:
            baseline_root = Path(temp) / 'repo'
            git('worktree', 'add', '--detach', str(baseline_root), BASE)
            try:
                before = unit('pr-baseline', 'tests/pr', cwd=baseline_root)
                after = unit('pr-integrated', 'tests/pr')
            finally:
                git('worktree', 'remove', '--force', str(baseline_root))
        assert before == after, {'new_PR_regression': {'before': before, 'after': after}}
        assert not before['errors'] and not before['skipped']
        assert set(before['failures']) <= {'test_base.ParanáBase.test_15_sc_rs_unchanged'}, before
        report['pr_regression'] = {'gate': 'BASELINE_EQUIVALENT', 'baseline': before, 'integrated': after, 'note': 'The old PR preservation fixture predates subsequent SC/RS releases. Its failure is retained, not counted as PASS. All preexisting files are independently compared with current main.'}
        report['preservation_after_tests'] = preservation()
        assert not git('diff', '--name-only').decode().strip(), 'Tests or rebuild changed tracked files'
        report['gate'] = 'PASS'
    finally:
        (OUT / 'preflight.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
