"""Migrate the explicit GLOBAL-02 root-phase assumptions, then build.
Both historical and global-root phases remain covered. Bootstrap is idempotent.
"""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
CHANGES=[('assets/global/core.js', "if (phase === 'next' && path === '/')", "if ((phase === 'next' || registry.root_mode === 'global_home') && path === '/')"),
('tests/global02/core.test.cjs', "assert.equal(C.resolveRoute(registry,base,base,'current').edition_id,'2026-sc-federais');", "if(registry.root_mode==='global_home')assert.equal(C.resolveRoute(registry,base,base,'current').kind,'home');else assert.equal(C.resolveRoute(registry,base,base,'current').edition_id,'2026-sc-federais');")]
for path,old,new in CHANGES:
    p=ROOT/path;text=p.read_text()
    if new in text:continue
    if text.count(old)!=1:raise RuntimeError('Unexpected foundation source: '+path)
    p.write_text(text.replace(old,new,1))
subprocess.run([sys.executable,str(ROOT/'tools/global03/build.py'),*sys.argv[1:]],check=True)
