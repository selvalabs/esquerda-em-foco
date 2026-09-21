#!/usr/bin/env python3
"""Independent state build. Use bounded downloads for the official archive reader."""
from pathlib import Path
import runpy
import official
from http_archive import archive
# The data parser accepts the same (ZipFile, provenance) interface from this adapter.
official.archive = archive
official.run()
runpy.run_path(str(Path(__file__).with_name('preview.py')),run_name='__main__')
