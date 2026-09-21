#!/usr/bin/env python3
"""State page build; no federal modifications."""
from pathlib import Path
import runpy
TOOLS=Path(__file__).parent
runpy.run_path(str(TOOLS/'votes_light.py'),run_name='__main__')
runpy.run_path(str(TOOLS/'preview.py'),run_name='__main__')
