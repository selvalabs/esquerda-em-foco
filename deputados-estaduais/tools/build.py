#!/usr/bin/env python3
"""State-deputy page build; slow historical refresh is an explicit separate step."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('preview.py')),run_name='__main__')
