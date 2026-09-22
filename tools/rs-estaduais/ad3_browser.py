"""Run the existing functional browser suite against AD3, into new report paths."""
from __future__ import annotations
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
A=ROOT/'docs/rs-estaduais/ad3'
def module(name,filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/'tools/rs-estaduais'/filename)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj

def run():
    A.mkdir(parents=True,exist_ok=True)
    basic=module('ad3_basic_browser','qa.py');basic.A=A;basic.run()
    disclosure=module('ad3_disclosure_browser','close_ad2_browser.py');disclosure.DOC=A
    temporary=A/'ad2-close';temporary.mkdir(exist_ok=True)
    disclosure.run()
    source=temporary/'browser-closure.json'
    if source.exists():source.replace(A/'browser-disclosures.json')
    temporary.rmdir()
if __name__=='__main__':run()
