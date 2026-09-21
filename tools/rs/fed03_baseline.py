"""Reference SC bytes from Git, never from the potentially modified working file.
A current checkout may contain independently published SC updates. RS tests must
preserve those exact bytes rather than require an obsolete historical SC version.
"""
from __future__ import annotations
import hashlib,subprocess
from pathlib import Path

def expected_sc_sha256(root: Path) -> str:
    try:
        raw=subprocess.check_output(['git','show','HEAD:index.html'],cwd=root,stderr=subprocess.PIPE)
    except (OSError,subprocess.CalledProcessError) as exc:
        raise RuntimeError('Preservation checks require the full Git checkout; the delivery ZIP contains the prebuilt RS page.') from exc
    if not raw:raise RuntimeError('Empty SC baseline from current Git commit')
    return hashlib.sha256(raw).hexdigest()
