"""Match the reviewed local contract outputs, not merely two identical CI runs."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
expected=json.loads((Path(__file__).parent/'expected.json').read_text())
for path,sha in expected.items():
    if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=sha:raise SystemExit('Reviewed output differs: '+path)
print(json.dumps({'reviewed_outputs':len(expected),'passed':True}))
