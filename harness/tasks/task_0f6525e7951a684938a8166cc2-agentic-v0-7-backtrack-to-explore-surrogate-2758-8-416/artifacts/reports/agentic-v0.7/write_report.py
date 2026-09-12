"""Format the final verified matrix without modifying acquisition."""
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
rows=json.loads((OUT/'matrix-summary-final.json').read_text())
assert len(rows)==12
controls=json.loads((OUT/'controls.json').read_text())
by={mode:sorted([r for r in rows if r['mode']==mode],key=lambda r:[42,0,7].index(r['seed']))
    for mode in ('mean','alternating','full','semi')}
hits={m:sum(r['hit_peak'] for r in rs) for m,rs in by.items()}
comparisons=[]
for mode in ('full','semi'):
    differences=[r['max']-ref['max'] for r,ref in zip(by[mode],by['alternating'])]
    comparisons.append(f"{mode.upper()} 相对同 seed 朴素交替：{sum(d>1e-4 for d in differences)}胜/{sum(abs(d)<=1e-4 for d in differences)}平/{sum(d< -1e-4 for d in differences)}负")
lines=['# agentic v0.7：停滞后探索的多 seed 实测', '',
    f"同池、同 surrogate、同 288 预算下，达池内峰次数：纯均值 {hits['mean']}/3，朴素交替 {hits['alternating']}/3，FULL {hits['full']}/3，SEMI {hits['semi']}/3。",
    '；'.join(comparisons)+'（按最终累计最大值）。这些是所测三次轨迹的比较，不能把并列或个别胜出推广成普适优越。',
    '交替策略在 seed42 达峰、seed0/7 未达峰，不能称 seed 稳健。LLM 结果见下表；三次采集 seed 不是独立数据切分，也没有控制网关 LLM 的随机性，不能据此宣称统计显著或普适优势。', '',
    '## 配置 × seed 的完整结果', '', '![同预算多 seed 曲线](comparison.png)', '',
    '| 配置 | seed | 六批 cum_top10_max | strong | 达峰 | 探索批次（1-based） |',
    '|---|---:|---|---:|---|---|']
for m,rs in by.items():
 for r in rs:
    ex=[x['round'] for x in r['rounds'] if x['action'] and
        (x['action'].get('n_explore',0)>0 or x['action'].get('mode') in ('diverse','uncertainty','spread'))]
    lines.append(f"| {m} | {r['seed']} | {r['curve']} | {r['strong']} | {'是' if r['hit_peak'] else '否'} | {ex} |")
lines += ['', '### 保留的非合规预运行（不计入上表）', '',
    '| 预运行 | 已完成批次 | 已花测量预算 | 截止中止累计最优 |',
    '|---|---:|---:|---:|']
for folder in sorted((OUT/'aav').glob('pilot-semi-*')):
    es=[json.loads(x) for x in (folder/'events.jsonl').read_text().splitlines()]
    ms=[e['payload'] for e in es if e['event_type']=='agent.measurements']
    spent=sum(len(m['results']) for m in ms)
    best=round(ms[-1]['top10_max_history'][-1],4) if ms else None
    lines.append(f'| {folder.name} | {len(ms)} | {spent} | {best} |')
lines += ['', '这三条轨迹因代码未强制 SEMI 停滞前纯利用而中止；按动作轨迹发现合同违例后修正，未根据峰命中选择参数或筛除较差结果。全部事件、状态与 stdout 保留。']
lines += ['', '四个任务参照点：纯均值 7.829、交替 seed42 8.4162 均在本轮复现；历史 v0.4 LLM=7.829/strong108、v0.5 B=6.5309/strong163 来自指定旧报告，本轮未重跑，不能冒充本轮证据。v0.6 未运行、未修改。', '',
 '## 固定条件与实现', '',
 '实际任务数据是 AAV，而非角色手册的 GB1：38,265 条，HD≤2 cold-start 10,433，HD>2 池 27,832；沿用 HD≤4 且平均 BLOSUM62≥0 后门内 9,533。48×6=288，12 条正式轨迹均核验六批各48、候选互不重复、预测与测量账本一致、事件链完整。oracle 仍为 CSV 真值查表。',
 'EpistasisRidgePredictor 与 v0.5 完全相同：28aa one-hot，训练频次筛列、二阶稀疏交互、固定 80/20 split 选 alpha、全量训练均值、三个 bootstrap 模型给方差。没有改成角色默认的五模型，也没有改门禁、数据池或 oracle。该 CV 参与 alpha 选择，不能称独立最终评估。',
 '保留 C（异常结构化、长度/字符校验、原样暂存后测试）及 A（实时 CV 透传）。v0.7 默认纯 predicted_mean；FULL 由 LLM 选择时机与比例。SEMI 在此之前强制每轮全均值利用；在新增测量累计最优连续两批不升后，要求每轮整批探索直到改善，LLM 选择方法；直接 test 也不能绕过这条采集规则。旧 v0.5 的高CV/末轮利用比例下限仅保留在 legacy 模式。',
 '探索固定为 diverse=mean+3√var+U(0,1)、uncertainty=var 降序、spread=10n 个 UCB 候选中贪心最大化归一化 UCB 加最小 Hamming 距离。spread 距离参考已测 top10 与本批已选点，仅软加分，无额外排除门。beta=3、shortlist=10n、停滞 patience=2 全在运行前锁定，没有按峰身份/排名/结果调参。',
 'FULL/SEMI prompt 使用“高整体 CV 仍可能低估稀有高值”的一般假设，没有提供 7.8/8.416 数值、目标序列或 #2758 身份提示。固定冷启动与 bootstrap；seed42/0/7 只影响候选工具共享 RNG，不影响 LLM 随机性。随机 diverse 预览也消耗该 RNG，因此同一个数值 seed 不表示各策略共享相同随机候选流。`preregistration.md` 与 `scheduling-note.md` 记录设计和并行调度。初始 SEMI 错误允许停滞前混合探索，已保留三条中止预运行并仅修正该阶段约束；正式 SEMI 重跑前通过30项测试；最终又补上离线 fallback 阶段回归，31项通过。三个实跑/最终源码快照及哈希均保留，详见 implementation-correction.md。FULL 与参照路径及 prompt 未变。', '',
 '## 达峰机制与排名勘误', '',
 f"本轮后验 cold-start 峰均值排名 **#{controls['cold_peak_mean_rank']}**，不是合同的 #2758；与指定 Astra 实测 #426 一致。cold-start 最大值 {controls['cold_max']:.6f} 高于池内峰 {controls['pool_peak']:.6f}，故停滞只看新增测量累计最优。这里的‘达峰’是发现池内最优，绝不是超过全部已知测量。", '',
 '| 命中轨迹 | 实验批次 | 采集 | 当轮门内均值排名 |',
 '|---|---:|---|---:|']
for r in rows:
 for x in r['rounds']:
  for rank in x['peak_ranks']:
   lines.append(f"| {r['run']} | {x['round']} | {x['action']['mode']} ({x['driver']}) | {rank} |")
lines += ['', '交替 seed42 的达峰批次为第4批 diverse；目标预测均值2.663489、方差7.946871、均值排名#1384，确实由探索捞到利用 top48 之外的候选。SEMI seed0 在第6批强制 diverse 命中同一峰，当轮均值排名#124、预测4.495092、方差3.865298，仍在纯均值 top48 之外。它在第1、5轮还调用了 diverse 预览并消耗共享 RNG；没有同轨迹确定性 backtrack 对照，不能把命中唯一归因于 LLM 选择方法的优越性。全部已测点的 pre-test rank/mean/var 均先记录，后再记录精确查表标签；目标身份只用于 post-hoc 对齐，不反馈给采集。', '',
 '## LLM 与工具证据', '',
 '实际解析并请求的网关模型 ID 为 `claude-sonnet-5`，来自 `agent/llm.py` 的配置，不使用 CLI 的旧硬编码默认名。此为请求 ID；网关背后的物理模型身份未独立验证。每条运行保留模型事件、每轮摘要、工具选择、错误/补批和全部测量账本。', '',
 '| 轨迹 | 模型 | tool error | round error | harness 补批 | fallback |',
 '|---|---|---:|---:|---:|---:|']
for r in rows:
 if r['mode'] in ('full','semi'):
  e=r['errors'];lines.append(f"| {r['run']} | {r['model']} | {e['agent.tool.error']} | {e['agent.llm.round_error']} | {e['agent.llm.no_test']} | {e['agent.llm.fallback']} |")
lines += ['', '表中补批包含代测已暂存候选与 harness 自行选样两类，`matrix-summary-final.json` 的逐批 driver 区分二者。FULL seed0 第5轮由 harness 代测 LLM 已暂存的 spread 批，第6轮由 harness 纯均值补批取得6.5309。SEMI seed7 第6轮未提名/测试，harness 按强制探索规则用默认 diverse 自行补批。FULL seed42 第4轮只分析未测试；harness 随后的纯均值补批把累计最优从7.391推至7.829。该最终极值不能全部归因于 LLM 自主探索。其 uncertainty/spread/diverse 采集本次未捕获池内峰。',
 'FULL seed42 的第一轮原始摘要错误地用 cold-start incumbent 判断“没有新纪录”，并把轮前空 history 描述为轮后状态。尽管 prompt 已区分两种指标，LLM 解释仍可出错；代码主指标和停滞状态以新增测量为准。保留该错误，不把自然语言摘要当数值证据。', '',
 '## 验证', '',
 '真实定向 runner：`31 passed in 3.58s`（最终实现；阶段修正为30 passed in 3.29s，初始版本为29 passed in 3.67s）。测试文件为新增 `test_auto_researcher_explore.py` 及合同指定 compose/gate/epistasis 三文件；没有跑全量 suite 或 CI。测试涵盖持续上升不误触发、平台触发/恢复、SEMI 停滞后不能通过直接纯利用绕过约束、FULL 末轮自由探索、三种探索可纳入低均值排名且高方差候选、未测标签任意替换不改变首批候选/预测，以及 gate-safe 满批去重、SEMI 禁止提前探索且改善后恢复利用。',
 f"真实 AAV cold-start 正/阴性对照：CV Spearman={controls['cv']:.9f}，shuffle CV={controls['shuffle_cv']:.9f}（alpha={controls['shuffle_alpha']}）。因模型仅选择固定验证 split 上的最佳 alpha，此处只证明置乱信号消失，不等于全数据泛化保证。",
 '复现（单线程；请使用空输出目录，runner 拒绝覆盖任何已有实验）：', '',
 '```bash',
 'OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=. .venv/bin/python harness/reports/agentic-v0.7/run_matrix.py --controls',
 'PYTHONPATH=. .venv/bin/python harness/reports/agentic-v0.7/summarize.py',
 'PYTHONPATH=. .venv/bin/python -m pytest tests/test_auto_researcher_explore.py tests/test_auto_researcher_compose.py tests/test_auto_researcher_gate.py tests/test_epistasis_surrogate.py -q',
 '```', '',
 '## 产物、风险与下一步', '',
 '`matrix-summary-final.json` 给出每配置×seed 的曲线、strong、命中、探索/强制轮次、逐批最佳候选预测排名及错误计数；`aav/<配置>-seed<seed>/metrics.json` 与 `events.jsonl` 保留完整原始证据。`manifest-final.json` 记录数据/源码/runner 哈希、版本、模型与预算；报告及这些工件通过 Harness artifact/doc sync 提交，不进入公共代码 commit。',
 '早期已登记的 `matrix-summary.json` / `manifest.json` 保留为归档版本；最终汇总使用 `matrix-summary-final.json`，仅修正 SEMI seed7 末轮 harness 自行选样的归因，实验数值不变。',
 '承重事实：F-AFE22C14（六条参照与阴性对照）；F-B5AE4DDE（12条正式轨迹、达峰机制与最终比较）。',
 '限制：单一 AAV 数据集、三个采集 seed、LLM 随机性未控、网关模型身份未独立核验、CV 不是尾部排序校准。没有运行 v0.6、GB1、ESM 路径或全量 CI。即使某 LLM 轨迹打平或超过交替，也只能说该次策略有效，不能分离更多工具选择、时机和模型随机性的贡献。',
 '交付前已 fetch origin/main；其 be62937 历史与任务 v0.5 基线没有共同祖先，无法安全 rebase。保留任务指定基线，不强拼历史；需 CEO 处理分支基线，并做 answer-agnostic 语义验收与独立 review/consent。',
 '下一步应预注册更多采集 seed/LLM 重复，以及相同触发规则的确定性 explore 对照，以区分时机、探索算子和 LLM 决策的贡献；本任务不再根据本轮峰命中调参。', '']
(OUT/'report.md').write_text('\n'.join(lines))
