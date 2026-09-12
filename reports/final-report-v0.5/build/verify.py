from pathlib import Path
import json,re,hashlib
import fitz
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'report.md').read_text(); main=s.split('<!-- REFERENCES -->')[0]
assert re.findall(r'^## ([1-8]) ',main,re.M)==list('12345678')
refs=set()
for group in re.findall(r'(?<!!)\[([0-9,]+)\]',main): refs.update(map(int,group.split(',')))
assert refs==set(range(1,31)),refs
bib=json.loads((ROOT/'evidence/bibliography-audit.json').read_text())['entries']
assert len(bib)==30 and all(r['entry'] in s and r['url'] in s for r in bib)
fig_nums=re.findall(r'!\[图 ([1-5])',main);assert fig_nums==list('12345'),fig_nums
for f in re.findall(r'!\[.*?\]\((.*?)\)',main):assert (ROOT/f).is_file(),f
assert '### 7.6 研究者角色与预测器角色的区分' in main
assert '不应跳过任务验证' in main and '无工具猜测候选适应度' in main
assert '8.416205-7.828968' in main
assert all(v in main for v in ['71.31%','71.88%','9.536457','8.416205','2.100777','NA'])
g=json.loads((ROOT/'evidence/gb1_summary.json').read_text())['summary']
for k in g:
 for v in g[k]['cum_top10_max_curve']: assert f'{v:.6f}' in main
 assert str(g[k]['total_beneficial_hits']) in main
layout=json.loads((ROOT/'evidence/layout-check.json').read_text())
assert all(not p['bad'] and all(i['ok'] for i in p['images']) for p in layout),layout
html=BeautifulSoup((ROOT/'scientific_report_v0.5_two_column.html').read_text(),'html.parser')
assert len(html.select('figure'))==5
assert not [t for t in html.select('td') if not t.get_text(strip=True)]
assert not html.select('merror')
assert not html.select('span.math') # pandoc falls back to this on invalid math
pdf=fitz.open(ROOT/'scientific_report_v0.5_two_column.pdf')
assert len(pdf)==12
for p in pdf:
 assert p.get_text().strip()
 # 12 mm is safely inside the 18 mm authored body margins.
 for block in p.get_text('dict')['blocks']:
  if 'lines' not in block: continue
  for line in block['lines']:
   for span in line['spans']:
    x0,y0,x1,y1=span['bbox']
    assert x0>=33 and x1<=p.rect.width-33,(p.number,span['text'])
# Fixed local source snapshots are retained and tied to the input manifests.
for row in json.loads((ROOT/'evidence/sources.json').read_text()):
 copy=ROOT/'evidence'/Path(row['path']).name
 assert hashlib.sha256(copy.read_bytes()).hexdigest()==row['sha256']
result={'pages':len(pdf),'chapters':8,'references':30,'figures':5,'empty_table_cells':0,'layout_overflows':0,'user_researcher_rationale':'section 7.6','checks':'source snapshots, GB1 values, AAV source table retained, image paths, math rendering, text bounds','experiments_rerun':False}
(ROOT/'evidence/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
