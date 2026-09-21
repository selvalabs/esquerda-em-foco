"""Confere os bytes servidos pelo Pages; não considera commit como deploy concluído."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT = 'https://selvalabs.github.io/esquerda-em-foco/'
PATHS = ['index.html', 'assets/sc-federais-pautas.css', 'config/topics-v1.json',
         'data/sc-federais-pautas/review.json', 'data/sc-federais-topics-v1/matrix.json',
         'data/sc-federais-topics-v1/coverage.json', 'docs/TOPICS-V1-CONTRACT.md']


def run():
    commit = os.getenv('EXPECTED_SHA') or subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    expected = {p: hashlib.sha256(subprocess.check_output(['git', 'show', f'{commit}:{p}'])).hexdigest() for p in PATHS}
    results = {}
    def probe(path):
        url = ROOT + ('' if path == 'index.html' else path) + '?verify=' + commit
        result = {'path': path, 'url': url, 'expected_sha256': expected[path]}
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'EsquerdaEmFoco-DeploymentCheck/1.0', 'Cache-Control': 'no-cache'})
            with urllib.request.urlopen(request, timeout=20) as response:
                data = response.read()
                result.update({'http_status': response.status, 'actual_sha256': hashlib.sha256(data).hexdigest()})
                result['matched'] = response.status == 200 and result['actual_sha256'] == expected[path]
        except Exception as error:
            result.update({'matched': False, 'error': str(error)[:220]})
        return path, result
    pending = list(PATHS)
    for attempt in range(1, 19):
        with ThreadPoolExecutor(max_workers=4) as executor:
            results.update(dict(executor.map(probe, pending)))
        pending = [p for p in PATHS if not results[p]['matched']]
        print(json.dumps({'attempt': attempt, 'matched': len(PATHS) - len(pending), 'pending': pending}), flush=True)
        if not pending:
            break
        time.sleep(15)
    report = {'status': 'passed' if not pending else 'failed', 'expected_commit': commit,
              'checked_at': datetime.now(timezone.utc).isoformat(), 'files': list(results.values())}
    Path('/tmp/sc-federais-round1-live.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('LIVE_VERIFICATION ' + json.dumps(report, ensure_ascii=False), flush=True)
    return not pending


if __name__ == '__main__':
    sys.exit(0 if run() else 1)
