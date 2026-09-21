#!/usr/bin/env python3
"""Independent state build; all outputs stay in deputados-estaduais/."""
from pathlib import Path
import runpy
TOOLS=Path(__file__).parent
runpy.run_path(str(TOOLS/'review_patch.py'),run_name='__main__')
import official
from http_archive import archive
official.archive = archive
official.run()
runpy.run_path(str(TOOLS/'reconcile.py'),run_name='__main__')
runpy.run_path(str(TOOLS/'preview.py'),run_name='__main__')
runpy.run_path(str(TOOLS/'data_gate.py'),run_name='__main__')
