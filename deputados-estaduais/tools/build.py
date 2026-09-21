#!/usr/bin/env python3
"""Independent state build with verified official byte-range archive downloads."""
from pathlib import Path
import runpy
TOOLS=Path(__file__).parent
runpy.run_path(str(TOOLS/'official.py'),run_name='__main__')
runpy.run_path(str(TOOLS/'preview.py'),run_name='__main__')
