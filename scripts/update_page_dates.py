#!/usr/bin/env python3
"""Stamp an explicitly verified page-change date; never advance dates on build."""
import argparse,datetime,hashlib,json,re,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'page-updates.json'
ORIGIN='https://djnaoyaman.github.io/sanreikotaiyoku/'
JST=datetime.timezone(datetime.timedelta(hours=9))
BASE={}
def pages():return sorted(p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*.html') if '.git' not in p.parts)
def iso(value):
 d=datetime.datetime.fromisoformat(value)
 if d.tzinfo is None:raise ValueError('Explicit timezone required')
 if d>datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(minutes=5):raise ValueError('Future date')
 return d.astimezone(JST).isoformat(timespec='seconds')
def normalize(s):
 s=re.sub(r'<!-- page-update:start -->.*?<!-- page-update:end -->','',s,flags=re.S)
 s=re.sub(r'<meta name="page-modified"[^>]*>','',s)
 s=re.sub(r'<script type="application/ld\+json" data-page-update>.*?</script>','',s,flags=re.S)
 return re.sub(r'("dateModified"\s*:\s*")[^"]+',r'\1@DATE@',s)
def blob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def asset(path):
 p=ROOT/path
 if p.is_file():return blob(p.read_bytes())
 if path in BASE:return BASE[path]
 raise ValueError('Missing referenced asset: '+path)
def dependencies(path,text):
 found=set();queue=[(ORIGIN+path,text)]
 while queue:
  base,s=queue.pop()
  refs=re.findall(r'(?:src|href|content)=["\']([^"\']+)["\']',s)+re.findall(r'url\(["\']?([^\)"\']+)',s)
  refs+=re.findall(r'["\']((?:\.?\.?/)*assets/[^"\'\s]+\.(?:css|js|svg|png|webp|jpe?g|woff2?))["\']',s)
  for ref in refs:
   u=urllib.parse.urlsplit(urllib.parse.urljoin(base,ref))
   if u.netloc!='djnaoyaman.github.io' or not u.path.startswith('/sanreikotaiyoku/'):continue
   p=urllib.parse.unquote(u.path.removeprefix('/sanreikotaiyoku/'))
   if Path(p).suffix.lower() not in ['.css','.js','.svg','.png','.jpg','.jpeg','.webp','.woff','.woff2','.ico']:continue
   if p in found:continue
   found.add(p)
   if p.endswith('.css') and (ROOT/p).exists():queue.append((ORIGIN+p,(ROOT/p).read_text()))
 return sorted(found)
def fingerprint(path):
 s=normalize((ROOT/path).read_text());deps=dependencies(path,s)
 payload={'html':hashlib.sha256(s.encode()).hexdigest(),'assets':{p:asset(p) for p in deps}}
 return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest(),payload['assets']
def stamp(path,value):
 value=iso(value);d=datetime.datetime.fromisoformat(value);label=d.strftime('%Y年%m月%d日 %H:%M JST');p=ROOT/path;s=p.read_text()
 block='<!-- page-update:start --><span class="page-updated" style="display:block;font-size:.75rem;line-height:1.7;margin:.75rem 0;letter-spacing:.02em">ページ更新：<time datetime="'+value+'">'+label+'</time></span><!-- page-update:end -->'
 if '<!-- page-update:start -->' in s:s=re.sub(r'<!-- page-update:start -->.*?<!-- page-update:end -->',lambda _:block,s,flags=re.S)
 else:
  # Existing general page-update labels are replaced; research/profile verification dates stay untouched.
  patterns=[r'<small class="updated">更新 <time[^>]*>.*?</time></small>',r'<span>更新 <time[^>]*>.*?</time></span>']
  placed=False
  for pat in patterns:
   if re.search(pat,s,re.S):s=re.sub(pat,lambda _:block,s,count=1,flags=re.S);placed=True;break
  if not placed:
   end='</footer>' if '</footer>' in s else '</body>';s=s.replace(end,block+'\n'+end,1)
 s=re.sub(r'("dateModified"\s*:\s*")[^"]+',lambda m:m[1]+value,s)
 meta='<meta name="page-modified" content="'+value+'">'
 if 'name="page-modified"' in s:s=re.sub(r'<meta name="page-modified"[^>]*>',lambda _:meta,s)
 else:s=s.replace('</head>',meta+'\n</head>',1)
 if '"dateModified"' not in s:
  schema={'@context':'https://schema.org','@type':'WebPage','url':ORIGIN+path,'inLanguage':'ja','dateModified':value}
  s=s.replace('</head>','<script type="application/ld+json" data-page-update>'+json.dumps(schema,ensure_ascii=False)+'</script>\n</head>',1)
 p.write_text(s)
def sitemap(data):
 # Keep the existing sitemap route set; quiz result pages retain their existing indexing policy.
 import xml.etree.ElementTree as ET
 p=ROOT/'sitemap.xml';tree=ET.parse(p);ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
 for row in tree.findall('s:url',ns):
  url=row.find('s:loc',ns).text;rel=urllib.parse.urlsplit(url).path.removeprefix('/sanreikotaiyoku/') or 'index.html'
  if rel not in data['pages']:raise ValueError('Unknown sitemap route: '+url)
  m=row.find('s:lastmod',ns)
  if m is None:m=ET.SubElement(row,'{'+ns['s']+'}lastmod')
  m.text=data['pages'][rel]['modified']
 ET.register_namespace('',ns['s']);tree.write(p,encoding='utf-8',xml_declaration=True)
def check():
 data=json.loads(STATE.read_text());assert set(data['pages'])==set(pages()),'Route set changed'
 for path,e in data['pages'].items():
  s=(ROOT/path).read_text();value=iso(e['modified']);assert re.findall(r'<meta name="page-modified" content="([^"]+)">',s)==[value],path+' meta'
  b=re.search(r'<!-- page-update:start -->(.*?)<!-- page-update:end -->',s,re.S);assert b and 'datetime="'+value+'"' in b[1],path+' visible'
  assert re.findall(r'"dateModified"\s*:\s*"([^"]+)"',s) and all(v==value for v in re.findall(r'"dateModified"\s*:\s*"([^"]+)"',s)),path+' JSONLD'
  assert fingerprint(path)[0]==e['source_sha256'],path+' content/assets changed: explicitly stamp verified date'
 import xml.etree.ElementTree as ET
 ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
 for row in ET.parse(ROOT/'sitemap.xml').findall('s:url',ns):
  rel=urllib.parse.urlsplit(row.find('s:loc',ns).text).path.removeprefix('/sanreikotaiyoku/') or 'index.html';assert row.find('s:lastmod',ns).text==data['pages'][rel]['modified'],rel+' lastmod'
 print('PASS: '+str(len(data['pages']))+' page dates and referenced asset fingerprints')
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--check',action='store_true');a.add_argument('--date');a.add_argument('--all',action='store_true');a.add_argument('--paths',nargs='+');a.add_argument('--baseline-tree',help='Initial source export only; CI never uses this fallback');args=a.parse_args()
 global BASE
 if args.baseline_tree:BASE={x['path']:x['sha'] for x in json.loads(Path(args.baseline_tree).read_text())['tree'] if x['type']=='blob'}
 if args.check:return check()
 if not args.date or not (args.all or args.paths):a.error('Explicit --date plus --all/--paths required')
 value=iso(args.date);data=json.loads(STATE.read_text()) if STATE.exists() else {'schema':1,'timezone':'Asia/Tokyo','pages':{}}
 for path in pages() if args.all else args.paths:
  if path not in pages():a.error('Unknown route '+path)
  stamp(path,value);h,deps=fingerprint(path);data['pages'][path]={'modified':value,'source_sha256':h,'dependencies':deps}
 STATE.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');sitemap(data);check()
if __name__=='__main__':main()
