"""Protect both the research baseline and pre-existing recovery-report refreshes.

Before AD3's incremental workflow existed, its research-script commits triggered
an older recovery workflow. That bot refreshed five historical report files but
kept the recorded cohort, summaries and page bytes unchanged. The incremental
build must preserve the state it actually inherited, not erase those updates or
mistake them for a new AD3 mutation. Other editions retain the original baseline.
"""
from __future__ import annotations
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESEARCH_BASELINE = 'b9ec0c352cdc0dc2a77be8ea4cf28469f1c09502'
RECOVERY_DISABLED_COMMIT = '30ea4203e176433e1cdc1e4308cfc76e829f83c8'
HISTORICAL_DIRECTORY = 'docs/rs-estaduais/ad2-close'
OTHER_PROTECTED = (
    'index.html', 'deputados-estaduais', 'rs/deputados-federais',
    'data/rs', 'tools/rs', 'assets', 'server', 'sitemap.xml', 'config',
)
EXPECTED_PREEXISTING_CHANGES = {
    HISTORICAL_DIRECTORY + '/recovery-audit.json',
    HISTORICAL_DIRECTORY + '/report.json',
    HISTORICAL_DIRECTORY + '/reproducibility.json',
    HISTORICAL_DIRECTORY + '/scope-reconciliation.json',
    HISTORICAL_DIRECTORY + '/source-availability.json',
}
UNCHANGED_REPORT_FIELDS = (
    'after_closure', 'research_status_counts', 'unit_tests', 'browser_checks',
    'html_sha256', 'technical_gate', 'editorial_gate',
)


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(['git', *args], cwd=ROOT)


def validate_preserved_metrics(original: dict, inherited: dict) -> None:
    for field in UNCHANGED_REPORT_FIELDS:
        if original.get(field) != inherited.get(field):
            raise ValueError('Recovery refresh changed a substantive field: ' + field)


def audit() -> dict:
    subprocess.run(
        ['git', 'merge-base', '--is-ancestor', RESEARCH_BASELINE, RECOVERY_DISABLED_COMMIT],
        cwd=ROOT, check=True, capture_output=True,
    )
    changed = set(git_bytes(
        'diff', '--name-only', RESEARCH_BASELINE, RECOVERY_DISABLED_COMMIT,
        '--', HISTORICAL_DIRECTORY,
    ).decode().splitlines())
    if changed != EXPECTED_PREEXISTING_CHANGES:
        raise ValueError('Unexpected historical changes before incremental AD3: ' + repr(sorted(changed)))
    report_path = HISTORICAL_DIRECTORY + '/report.json'
    original = json.loads(git_bytes('show', RESEARCH_BASELINE + ':' + report_path))
    inherited = json.loads(git_bytes('show', RECOVERY_DISABLED_COMMIT + ':' + report_path))
    validate_preserved_metrics(original, inherited)
    checks = []
    for path in OTHER_PROTECTED + (HISTORICAL_DIRECTORY,):
        reference = RECOVERY_DISABLED_COMMIT if path == HISTORICAL_DIRECTORY else RESEARCH_BASELINE
        subprocess.run(
            ['git', 'diff', '--exit-code', reference, '--', path],
            cwd=ROOT, check=True, capture_output=True,
        )
        checks.append({'path': path, 'baseline_commit': reference, 'unchanged': True})
    evidence = []
    for path in sorted(changed):
        old = git_bytes('show', RESEARCH_BASELINE + ':' + path)
        found = git_bytes('show', RECOVERY_DISABLED_COMMIT + ':' + path)
        if (ROOT / path).read_bytes() != found:
            raise ValueError('Incremental AD3 modified an inherited recovery report: ' + path)
        evidence.append({
            'path': path, 'research_baseline_sha256': hashlib.sha256(old).hexdigest(),
            'inherited_sha256': hashlib.sha256(found).hexdigest(),
            'preserved_byte_for_byte': True,
        })
    return {
        'passed': True, 'research_baseline': RESEARCH_BASELINE,
        'historical_preservation_baseline': RECOVERY_DISABLED_COMMIT,
        'protected_checks': checks, 'preexisting_historical_changes': evidence,
        'substantive_recovery_metrics_unchanged': True,
        'historical_tests_still_run_at_original_baseline': RESEARCH_BASELINE,
        'reason': 'O workflow antigo atualizou metadados e disponibilidade de fontes antes de ser desativado. A edição incremental preserva esses arquivos como os recebeu; a comparação das demais frentes permanece no baseline original.',
    }


if __name__ == '__main__':
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
