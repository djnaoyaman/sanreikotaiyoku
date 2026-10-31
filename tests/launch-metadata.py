"""Check the public navigation aid and custom Pages error document."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import re,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
BASE='/sanreikotaiyoku/'
class Document(HTMLParser):
    def __init__(self):super().__init__();self.tags=[]
    def handle_starttag(self,tag,attrs):self.tags.append((tag,dict(attrs)))
source=(ROOT/'404.html').read_text();doc=Document();doc.feed(source)
assert ('html',{'lang':'ja'}) in doc.tags
assert len([1 for t,a in doc.tags if t=='h1'])==1
assert any(t=='meta' and a.get('name')=='robots' and a.get('content')=='noindex' for t,a in doc.tags)
assert not any(t=='script' or (t=='meta' and a.get('http-equiv','').lower()=='refresh') for t,a in doc.tags)
assert not any(t=='link' and a.get('rel')=='canonical' for t,a in doc.tags)
assert any(t=='nav' and a.get('aria-label') for t,a in doc.tags)
for tag,attrs in doc.tags:
    url=attrs.get('href') or attrs.get('src')
    if not url:continue
    assert url.startswith(BASE),url
    target=ROOT/(url.removeprefix(BASE) or 'index.html')
    assert target.is_file(),target
assert 'sanrei-wordmark.svg' in source and '酸冷交代浴' in source
assert not any('404' in (e.text or '') for e in ET.parse(ROOT/'sitemap.xml').iter())
llms=(ROOT/'llms.txt').read_text()
assert llms.startswith('# 酸冷交代浴\n') and '三冷' not in llms
links=re.findall(r'\]\((https://[^)]+)\)',llms)
assert len(links)==5 and len(links)==len(set(links))
for link in links:
    u=urlparse(link);assert u.netloc=='djnaoyaman.github.io' and u.path.startswith(BASE)
    assert not u.query and not u.fragment
    assert (ROOT/(u.path.removeprefix(BASE) or 'index.html')).is_file(),link
assert '個別研究の結果を、酸冷交代浴全体の健康効果や、すべての人に共通する感触の保証として扱っていません。' in llms
assert '個別研究の結果を、酸冷交代浴全体の健康効果や、すべての人に共通する感触の保証として扱っていません。' in (ROOT/'index.html').read_text()
print('PASS: Japanese noindex 404, project-absolute existing navigation/assets, no redirect/scripts, sitemap exclusion, five llms links and existing research boundary')
