from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];p=R/'report.md';s=p.read_text();ki=s.index('<!-- PAGE -->\n## 附录 K.1');li=s.find('<!-- PAGE -->\n## 附录 L.1');math_tail=''
if li>=0:
 math_tail=s[li:ki] if li<ki else s[li:]
 s=s[:min(ki,li)]
else:s=s[:ki]
src=json.loads((R/'evidence/sources.json').read_text())['inputs']
for n,b in enumerate(range(0,len(src),18),1):
 s+='\n<!-- PAGE -->\n## 附录 K.'+str(n)+'　证据文件与原始来源索引\n\n<div class="note">快照路径相对evidence/，原始路径相对仓库；完整SHA-256、编码与版本见sources.json。旧交接保留历史，新解释以原始数据和当前工程交接为准。数据归档是复制既有运行，不是重跑。清洗AAV子集记录原始CSV指纹和过滤代码。</div>\n\n| # | 快照 | 原始来源 |\n|---|---|---|\n'
 for i,z in enumerate(src[b:b+18],b+1):s+=f'| {i} | `{z["snapshot"].removeprefix("evidence/")}` | `{z["path"]}` |\n'
p.write_text(s+math_tail)
print(len(src),'sources across',n,'index pages')
