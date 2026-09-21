#!/usr/bin/env python3
"""One-time, hash-pinned transport of reviewed UTF-8 state files, never exec.
The transfer directory is removed after complete verification. Readable sources
are committed only after the normal build, isolation and browser gates pass.
"""
from __future__ import annotations
import base64
import hashlib
import json
import lzma
import os
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[2]
STATE = REPO / 'deputados-estaduais'
TRANSFER = STATE / '.review2-transfer'
EXPECTED_RAW = '3c398c1e2d360c11a5cda5a861730e3367d6ef986616c2e31ef21efbb949e3c2'
ALLOWED = {
 'deputados-estaduais/.gitignore', 'deputados-estaduais/README.md',
 'deputados-estaduais/tools/build.py', 'deputados-estaduais/tools/qa.py',
 'deputados-estaduais/tools/render.py', 'deputados-estaduais/tools/review2_build.py',
 'deputados-estaduais/tools/review2_qa.py', 'deputados-estaduais/tools/review2_sources.py',
 'deputados-estaduais/tools/review2_votes.py', 'deputados-estaduais/ui/app.js',
 'deputados-estaduais/ui/state.css', 'deputados-estaduais/editorial/review2.json',
 'deputados-estaduais/audit/review2/web-research.json',
}

def digest(value: bytes) -> str:
 return hashlib.sha256(value).hexdigest()

def main() -> None:
 manifest = json.loads((TRANSFER / 'manifest.json').read_text(encoding='utf-8'))
 assert manifest['encoding'] == 'base64+xz+utf8-json'
 assert manifest['raw_sha256'] == EXPECTED_RAW
 assert set(manifest['files']) == ALLOWED
 assert len(manifest['parts']) == 8
 parts = []
 for i, part in enumerate(manifest['parts'], 1):
  assert part['file'] == f'part-{i:02}.txt'
  value = (TRANSFER / part['file']).read_bytes()
  assert len(value) == part['length'] and digest(value) == part['sha256'], part['file']
  parts.append(value)
 compressed = base64.b64decode(b''.join(parts), validate=True)
 assert len(compressed) == 48488 and digest(compressed) == manifest['compressed_sha256']
 raw = lzma.decompress(compressed, memlimit=128 * 1024 * 1024)
 assert len(raw) == 422961 and digest(raw) == EXPECTED_RAW
 payload = json.loads(raw.decode('utf-8'))
 assert set(payload) == ALLOWED
 staged = []
 for rel, text in payload.items():
  assert isinstance(text, str)
  path = PurePosixPath(rel)
  assert not path.is_absolute() and '..' not in path.parts and path.parts[0] == 'deputados-estaduais'
  destination = (REPO / rel).resolve()
  assert destination.is_relative_to(STATE.resolve())
  value = text.encode('utf-8')
  assert digest(value) == manifest['files'][rel], rel
  if rel.endswith('.py'): compile(text, rel, 'exec')
  if rel.endswith('.json'): json.loads(text)
  staged.append((destination, value))
 # All members and Python syntax are checked before any destination is changed.
 for destination, value in staged:
  destination.parent.mkdir(parents=True, exist_ok=True)
  temporary = destination.with_name(destination.name + '.review2-transfer-tmp')
  temporary.write_bytes(value)
  os.replace(temporary, destination)
 for old in STATE.glob('review2-patch.*.txt'):
  assert old.is_file() and not old.is_symlink()
  old.unlink()
 for part in manifest['parts']: (TRANSFER / part['file']).unlink()
 (TRANSFER / 'manifest.json').unlink()
 TRANSFER.rmdir()
 print(f'Verified {len(staged)} state-only files; raw SHA-256 {EXPECTED_RAW}', flush=True)

if __name__ == '__main__': main()
