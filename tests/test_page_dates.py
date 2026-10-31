import importlib.util,tempfile,unittest,datetime,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('dates',ROOT/'scripts/update_page_dates.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
class Dates(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);d.ROOT=self.root;d.STATE=self.root/'page-updates.json';d.BASE={}
  (self.root/'assets').mkdir();(self.root/'assets/common.css').write_text('body{color:black}');(self.root/'assets/photo.svg').write_text('<svg/>')
  page='<html><head><link rel="stylesheet" href="assets/common.css"><script type="application/ld+json">{"@type":"WebPage","dateModified":"2026-10-23","datePublished":"2026-01-02"}</script></head><body><p>資料確認日 2026年10月23日</p><footer></footer></body></html>'
  (self.root/'index.html').write_text(page);(self.root/'profile.html').write_text(page)
 def tearDown(self):self.temp.cleanup()
 def test_repeated_stamp_stable(self):
  d.stamp('index.html','2026-10-30T20:05:37Z');a=(self.root/'index.html').read_bytes();h=d.fingerprint('index.html')[0];d.stamp('index.html','2026-10-30T20:05:37Z');self.assertEqual(a,(self.root/'index.html').read_bytes());self.assertEqual(h,d.fingerprint('index.html')[0])
 def test_dates_do_not_make_new_source(self):
  d.stamp('index.html','2026-10-30T01:00:00Z');h=d.fingerprint('index.html')[0];d.stamp('index.html','2026-10-30T02:00:00Z');self.assertEqual(h,d.fingerprint('index.html')[0])
 def test_content_only_affects_target(self):
  a=d.fingerprint('index.html')[0];b=d.fingerprint('profile.html')[0];p=self.root/'index.html';p.write_text(p.read_text().replace('<body>','<body><p>new</p>'));self.assertNotEqual(a,d.fingerprint('index.html')[0]);self.assertEqual(b,d.fingerprint('profile.html')[0])
 def test_shared_css_affects_both(self):
  a=d.fingerprint('index.html')[0];b=d.fingerprint('profile.html')[0];(self.root/'assets/common.css').write_text('body{color:red}');self.assertNotEqual(a,d.fingerprint('index.html')[0]);self.assertNotEqual(b,d.fingerprint('profile.html')[0])
 def test_image_dependency(self):
  p=self.root/'index.html';p.write_text(p.read_text().replace('<body>','<body><img src="assets/photo.svg">'));a=d.fingerprint('index.html')[0];(self.root/'assets/photo.svg').write_text('<svg>changed</svg>');self.assertNotEqual(a,d.fingerprint('index.html')[0])
 def test_publication_and_research_preserved(self):
  d.stamp('index.html','2026-10-30T20:05:37Z');s=(self.root/'index.html').read_text();self.assertIn('"datePublished":"2026-01-02"',s);self.assertIn('資料確認日 2026年10月23日',s)
 def test_jst_boundary(self):
  self.assertEqual(d.iso('2026-10-30T20:05:37Z'),'2026-10-31T05:05:37+09:00')
 def test_missing_timezone_rejected(self):
  with self.assertRaises(ValueError):d.iso('2026-10-30T20:05:37')
 def test_future_rejected(self):
  with self.assertRaises(ValueError):d.iso('2099-01-01T00:00:00+09:00')
 def test_noncontent_files_ignored(self):
  a=d.fingerprint('index.html')[0];(self.root/'README.md').write_text('build again');self.assertEqual(a,d.fingerprint('index.html')[0])
if __name__=='__main__':unittest.main()
