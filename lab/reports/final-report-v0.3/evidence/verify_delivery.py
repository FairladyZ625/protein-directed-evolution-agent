#!/usr/bin/env python3
"""Validate the delivered text, citation sets, source-backed GB1 export and mirrors."""
import csv
import hashlib
import json
import re
from pathlib import Path

base = Path(__file__).resolve().parents[1]
titles = ['背景与问题定义','数据集介绍','适应度预测模型','LLM Agent 设计','知识增强方法','虚拟定向进化实验结果','失败案例分析','改进建议与未来拓展']
main = (base / 'report.md').read_text()
assert re.findall(r'^## (\d+) (.+)$', main, re.M) == [(str(i+1), s) for i,s in enumerate(titles)]
assert len(re.findall(r'^## ',main,re.M)) == 8
print('PASS: exact eight numbered official sections')
for name, count in [('report.md',30),('supplementary_thinking_report.md',16)]:
    p=base/name; text=p.read_text(); body, refs=text.split('### 参考文献')
    cited=list(map(int,re.findall(r'\[(\d+)\]',body)))
    listed=list(map(int,re.findall(r'^\[(\d+)\]',refs,re.M)))
    assert listed == list(range(1,count+1))
    assert list(dict.fromkeys(cited)) == listed
    assert set(cited) == set(listed)
    assert len(re.findall(r'^\[\d+\] .+\[(?:J|C)\]',refs,re.M)) == count
    assert not any(t in body for t in ['震撼','史诗级','断层式碾压','恐慌式','认知暗物质','一击贯穿'])
    print(f'PASS: {name} {count}/{count} references; first-appearance order; unique entries')
    print(f'STAT: {name}: Han={len(re.findall("[\\u4e00-\\u9fff]",text))}; nonspace={len(re.sub(chr(92)+"s","",text))}; bytes={len(p.read_bytes())}; sha256={hashlib.sha256(p.read_bytes()).hexdigest()}')
for i in range(1,6):
    assert main.count(f'<!-- FIGURE_{i}_START -->') == 1
    assert main.count(f'<!-- FIGURE_{i}_END -->') == 1
print('PASS: five paired figure anchors and captions (rendering not tested)')
rows=list(csv.DictReader((base/'evidence/gb1_top10.csv').open()))
assert len(rows)==120
summary=json.loads((base/'evidence/gb1_summary.json').read_text())
for strategy in summary['summary']:
    cumulative=[]; best=float('-inf')
    for t in range(1,4):
        group=[r for r in rows if r['strategy']==strategy and int(r['round'])==t]
        assert len(group)==10 and [int(r['rank']) for r in group]==list(range(1,11))
        best=max(best,max(float(r['fitness']) for r in group)); cumulative.append(best)
    assert cumulative==summary['summary'][strategy]['cum_top10_max_curve']
assert round(7937/11130*100,2)==71.31
assert round(6852/9533*100,2)==71.88
assert round(8.41620513-7.828968,4)==0.5872
print('PASS: 120 GB1 Top-10 rows reconstruct all four max curves; denominators and gap recomputed')
refs=json.loads((base/'evidence/bibliography-audit.json').read_text())['entries']
assert len(refs)==30
for r in refs:
    assert (base/'evidence'/r['metadata_file']).is_file()
print('PASS: 30 bibliography metadata records present (existence is not full-text validation)')
for root in [Path('/Users/lizeyu/Projects/ai4s-directed-evolution-agent/reports/final-report-v0.3'),Path('/Users/lizeyu/Projects/ai4s-directed-evolution-agent/lab/reports/final-report-v0.3'),Path('/Users/lizeyu/Projects/protein-directed-evolution-agent/reports/final-report-v0.3')]:
    for name in ['report.md','supplementary_thinking_report.md']:
        assert (root/name).read_bytes()==(base/name).read_bytes(),(root,name)
print('PASS: both report bytes identical across worker, canonical authored copy, and both report mirrors')
print('UNVERIFIED: campaign reruns, wet lab, ESM retraining, full CI, figure rendering, PDF pagination')
