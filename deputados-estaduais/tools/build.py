#!/usr/bin/env python3
"""State-deputy pipeline; federal files are read-only."""
from pathlib import Path
import runpy
from enrich import run
run()
from research import run as research
research()
renderer = Path(__file__).with_name('render.py')
if renderer.exists():
 runpy.run_path(str(renderer),run_name='__main__')
