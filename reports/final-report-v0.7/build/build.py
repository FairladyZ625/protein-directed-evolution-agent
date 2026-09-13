from pathlib import Path
import subprocess,json,re,base64
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/'report.md').read_text()
refs=json.loads((ROOT/'evidence/bibliography-audit.json').read_text())['entries']
if '<!-- REFERENCES -->' not in src:
 text='\n<!-- PAGE -->\n<!-- REFERENCES -->\n## 参考文献\n\n::: {.refs}\n'
 for r in refs:
  doi=r['url'].split('doi.org/')[-1] if 'doi.org/' in r['url'] else None
  label='DOI: '+doi if doi else '会议原文'
  text+=f"\n[{r['main_id']}] {r['entry']} [{label}]({r['url']})\n"
 text+='\n:::\n';src+=text;(ROOT/'report.md').write_text(src)
css='''
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
html,body { margin:0; padding:0; background:white; color:#243243; }
body { font-family:"Songti SC","STSong",serif; font-size:11pt; line-height:1.72; }
.page { width:210mm; height:297mm; padding:18mm 18mm 19mm; position:relative; break-after:page; background:white; }
.page:last-child {break-after:auto;}
.running {position:absolute;top:8mm;left:18mm;right:18mm;display:flex;justify-content:space-between;font-family:"Helvetica Neue",sans-serif;font-size:7.2pt;letter-spacing:.02em;color:#798797;border-bottom:.4pt solid #dfe5eb;padding-bottom:2mm;}
.footer {position:absolute;bottom:8mm;left:18mm;right:18mm;display:flex;justify-content:space-between;font:7.3pt "Helvetica Neue",sans-serif;color:#798797;}
.content { height:260mm; }
h1 {font-size:21pt;line-height:1.5;font-weight:700;text-align:center;margin:8mm 0 3mm;color:#1b2e43;}
.metadata {text-align:center;font-size:9pt;line-height:1.7;margin-bottom:6mm;color:#607080;font-family:"Helvetica Neue","Songti SC",sans-serif;}
a {color:#306e80;text-decoration:none;}
h2 {font-size:13pt;line-height:1.35;color:#213a4e;margin:0 0 4mm;padding-bottom:2mm;border-bottom:.7pt solid #8099aa;}
h3 {font-size:10.6pt;line-height:1.4;color:#356575;margin:4mm 0 2.2mm;break-after:avoid;}
h3:first-child {margin-top:0;}
p {margin:0 0 2.8mm;text-align:justify;word-break:normal;overflow-wrap:break-word;}
.cols {column-count:2;column-gap:8mm;column-fill:balance;margin-top:4mm;}
.cols h2 {font-size:12pt;}
.cols p {orphans:2;widows:2;}
.abstract {font-size:9.5pt;line-height:1.68;border-top:1pt solid #557a87;border-bottom:.5pt solid #d9e2e7;padding:3.5mm 0 1mm;margin:3mm 0 5mm;}
strong {font-weight:700;color:#223e51;}
figure {margin:2mm 0 4mm;break-inside:avoid;}
figure img {display:block;width:100%;height:auto;max-height:90mm;object-fit:contain;background:white;}
figcaption {font-size:9pt;line-height:1.55;text-align:justify;margin-top:2.2mm;color:#506172;}
.table-title {font-size:9.4pt;font-weight:700;margin:4mm 0 1.8mm;color:#263f51;}
table {width:100%;border-collapse:collapse;font-size:9pt;line-height:1.45;margin:0 0 2mm;border-top:1pt solid #426174;border-bottom:1pt solid #426174;font-variant-numeric:tabular-nums;}
th {font-weight:600;background:#f0f4f6;border-bottom:.5pt solid #a7b8c4;}
th,td {padding:2.1mm 2.2mm;text-align:left;vertical-align:middle;}
tbody tr+tr {border-top:.3pt solid #e0e7ec;}
.note {font-size:8pt;line-height:1.55;color:#63717e;margin:1.5mm 0 3mm;}
.sequence {font:8.4pt "Menlo",monospace;white-space:nowrap;padding:2.5mm 0;color:#305c70;}
code {font-family:"Menlo",monospace;font-size:8pt;overflow-wrap:anywhere;}
math {font-family:"STIX Two Math","STIXGeneral",serif;font-size:.96em;}
math[display="block"] {margin:2mm 0;}
.refs {column-count:2;column-gap:8mm;font-family:"Times New Roman",serif;font-size:8.1pt;line-height:1.3;}
.refs p {margin-bottom:2.1mm;text-align:left;break-inside:avoid;overflow-wrap:anywhere;}
.refs a {font-size:8pt;}
.page[data-page="1"] h1 {margin:2mm 0 2mm;font-size:20pt;line-height:1.35;}
.page[data-page="1"] .metadata {margin-bottom:3mm;}
.page[data-page="1"] .abstract {margin:2mm 0 3mm;padding-top:2mm;}
.page[data-page="1"] figure img {max-height:80mm;}
.page[data-page="1"] .cols {margin-top:2mm;}
.page[data-page="1"] figure {margin-bottom:2mm;}
.page.appendix {font-size:10.4pt;line-height:1.65;}
.page.alpha-full figure img {max-height:130mm;}
.page.source-index table {font-size:8.4pt;table-layout:fixed;}
.page.source-index td {padding-top:1.1mm;padding-bottom:1.1mm;}
.page.source-index th:first-child {width:6%;}
.page.source-index th:nth-child(2) {width:34%;}
.page.source-index th:nth-child(3) {width:60%;}
.page.source-index code {font-size:7.5pt;line-height:1.4;overflow-wrap:anywhere;}
td {padding-top:1.65mm;padding-bottom:1.65mm;}
@media screen {body {background:#e8edf0;padding:12px 0;} .page {margin:0 auto 18px;box-shadow:0 2px 8px #0001;} }
'''
chunks=src.split('<!-- PAGE -->');pages=[]
for i,c in enumerate(chunks,1):
 conversion=subprocess.run(['pandoc','--from=markdown+fenced_divs+raw_html','--to=html5','--mathml'],input=c,text=True,capture_output=True,check=True)
 if 'Could not convert TeX' in conversion.stderr: raise RuntimeError(conversion.stderr)
 html=conversion.stdout
 soup=BeautifulSoup(html,'html.parser')
 for img in soup.find_all('img'):
  if img.parent.name=='p':
   fig=soup.new_tag('figure'); img.parent.replace_with(fig); fig.append(img)
   cap=soup.new_tag('figcaption'); cap.string=img.get('alt',''); fig.append(cap)
 if '证据文件与原始来源索引' in c:
  for table in soup.find_all('table'):
   cols=table.find_all('col')
   for col,width in zip(cols,['6%','34%','60%']): col['style']='width: '+width
 html=str(soup)
 kind='appendix' if '## 附录' in c else ('references' if '<!-- REFERENCES -->' in c else 'main')
 extra=' alpha-full' if 'fs1_alpha_full.png' in c else (' source-index' if '证据文件与原始来源索引' in c else '')
 running='SUPPLEMENTARY MATERIAL' if kind=='appendix' else 'RESEARCH REPORT'
 # Embed project images so the HTML is a portable, offline artifact.
 def emb(m):
  rel=m.group(1); f=ROOT/rel
  if not f.exists(): return m.group(0)
  typ='image/svg+xml' if f.suffix=='.svg' else 'image/png'
  return 'src="data:'+typ+';base64,'+base64.b64encode(f.read_bytes()).decode()+'"'
 html=re.sub(r'src="(figures/[^\"]+)"',emb,html)
 pages.append(f'<section class="page {kind}{extra}" data-page="{i}"><div class="running"><span>CONTROLLED DIRECTED EVOLUTION</span><span>{running}</span></div><main class="content">{html}</main><div class="footer"><span>Zeyu Li · 2026</span><span>{i} / {len(chunks)}</span></div></section>')
out='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>受控科学智能体研究报告 v0.7</title><style>'+css+'</style></head><body>'+''.join(pages)+'</body></html>'
(ROOT/'scientific_report_v0.7_two_column.html').write_text(out)
print('Built HTML pages:',len(chunks))
