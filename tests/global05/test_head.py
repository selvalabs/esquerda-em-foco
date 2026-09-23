"""Deterministic metadata finalization, with synthetic non-political fixtures."""
import hashlib,html,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('global05',ROOT/'tools/global05/build.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class Head(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'assets').mkdir();(self.root/'assets/test.js').write_text('const value=1;');(self.root/'assets/test.css').write_text('body{display:block}')
 def document(self,extra='',body='<main><h1>Texto original</h1></main>'):return '<html><head><title>Título original</title>'+extra+'</head><body>'+body+'</body></html>'
 def test_missing_share_metadata_added(self):
  s=module.finalize(self.document(),'index.html',self.root);self.assertIn('property="og:image"',s);self.assertIn('summary_large_image',s)
 def test_existing_share_image_preserved(self):
  s=module.finalize(self.document('<meta property="og:image" content="https://example.org/image.png"/>'),'index.html',self.root);self.assertIn('https://example.org/image.png',s);self.assertEqual(s.count('property="og:image"'),1)
 def test_title_and_body_preserved(self):
  s=self.document(body='<main><article id="a" data-x="1"><p>Texto &amp; fonte.</p></article></main>');result=module.finalize(s,'index.html',self.root);self.assertEqual(s.split('<body>')[1],result.split('<body>')[1]);self.assertIn('<title>Título original</title>',result)
 def test_second_pass_identical(self):
  s=module.finalize(self.document('<script src="assets/test.js?v=old"></script>'),'index.html',self.root);self.assertEqual(s,module.finalize(s,'index.html',self.root))
 def test_revision_matches_bytes(self):
  s=module.finalize(self.document('<script src="assets/test.js?v=old"></script>'),'index.html',self.root);self.assertIn('v='+hashlib.sha256((self.root/'assets/test.js').read_bytes()).hexdigest()[:12],s)
 def test_other_query_parameters_and_fragment_preserved(self):
  s=module.finalize(self.document('<script src="assets/test.js?variant=compact&amp;v=old#part"></script>'),'index.html',self.root);self.assertIn('variant=compact&amp;v=',s);self.assertIn('#part',s)
 def test_relative_asset_resolution(self):
  s=module.finalize(self.document('<script src="../../assets/test.js"></script>'),'sc/deputados-federais/index.html',self.root);self.assertIn('../../assets/test.js?v=',s)
 def test_external_script_not_rewritten(self):
  src='<script src="https://example.org/a.js?v=external"></script>';self.assertIn(src,module.finalize(self.document(src),'index.html',self.root))
 def test_non_executable_link_not_rewritten(self):
  body='<main><a href="sources.json?v=historical">Fonte</a></main>';self.assertIn(body,module.finalize(self.document(body=body),'index.html',self.root))
 def test_missing_asset_rejected(self):
  with self.assertRaises(ValueError):module.finalize(self.document('<script src="assets/absent.js"></script>'),'index.html',self.root)
 def test_escaping_repository_rejected(self):
  with self.assertRaises(ValueError):module.finalize(self.document('<script src="../outside.js"></script>'),'index.html',self.root)
 def test_metadata_precedes_regenerated_rollout_assets(self):
  value=self.document('<link data-global-rollout="asset" rel="stylesheet" href="assets/test.css"/>')
  result=module.finalize(value,'index.html',self.root)
  self.assertLess(result.index('property="og:image"'),result.index('data-global-rollout'))
 def test_missing_head_rejected(self):
  with self.assertRaises(ValueError):module.finalize('<body>Missing</body>','index.html',self.root)
if __name__=='__main__':unittest.main()
