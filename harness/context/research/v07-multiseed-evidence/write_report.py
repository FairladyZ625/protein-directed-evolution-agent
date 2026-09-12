"""Render completed evidence; never feeds decisions back into the campaign."""
import json
from pathlib import Path
from scipy.stats import binomtest
P=Path(__file__).resolve().parent
S=json.loads((P/'summary.json').read_text())
R=json.loads((P/'results.json').read_text())
C=json.loads((P/'controls.json').read_text())
M=json.loads((P/'manifest.json').read_text())
names={'mean':'纯均值','alternating':'交替 mean/diverse','ucb0.5':'UCB β=0.5','ucb1':'UCB β=1','ucb2':'UCB β=2','ucb3':'UCB β=3','thompson_gaussian':'Gaussian-TS 近似'}
stochastic=('alternating','thompson_gaussian')
deterministic=[m for m in S if m not in stochastic]
successes=[names[m] for m in deterministic if S[m]['hits']]
significant=[names[m] for m in stochastic if S[m]['p_holm']<.05]
strong_wins=all(S[m]['greedy_strong_comparison']['losses']==0 for m in S if m!='mean')
lines=['# v0.7 多 seed 稳健性：固定 AAV 池、固定模型、30 个采集 seed','',
'## 结论优先','',
'**本矩阵推翻“谁都不可靠”的笼统判断：UCB β=3 在固定协议下第三轮确定达峰，strong=128。Greedy仍更适合收集大量strong（166）。**','',
('1. **随机探索配置中，'+('、'.join(significant)+' 的单峰命中率显著高于 1/3。' if significant else '没有配置证明单峰命中率显著高于 1/3。')+'** 使用单侧精确二项检验，并对交替/Gaussian-TS 两项检验做 Holm 校正（α=0.05）。不显著不等于证明真实命中率≤1/3；本次不是等效性检验。'),
('2. **确定性结果：'+('、'.join(successes)+' 在这个固定任务上命中。不能再笼统称“所有配置均靠运气/不能达峰”。' if successes else '纯均值及四个 UCB β 都未命中。')+'** 这些方法不消费采集 RNG；各30条记录实为同一轨迹的重复，不能拿 n=30 宣称跨 seed 统计显著。'),
('3. **Greedy 的 strong 优势'+('在本矩阵全部 seed 上成立。' if strong_wins else '不是对所有配置/seed 都成立。')+'** Greedy 固定 strong='+str(int(S['mean']['strong']['mean']))+'；差值、胜负和完整分布见下表。此结论仅涉及采集 RNG，未检验训练 bootstrap、cold-start 或数据集变化。'),
'4. 本实验全部使用本地真值查表，未调用 LLM/网络、未修改 agent/models/evolution。单峰指 HD>2 **未测池最优8.41620513**，cold-start最大值为9.53645667；不是整个数据集最优，更不是蛋白质真实序列空间的全局最优。','',
'## 单峰命中率及 Wilson 95% CI','',
'| 方法 | 命中 / 30 | 命中率 | Wilson 95% CI | 唯一轨迹数 | p（单侧 >1/3） | Holm p |',
'|---|---:|---:|---|---:|---:|---:|']
for m,s in S.items():
 lo,hi=s['wilson95']; mark='' if m in stochastic else '†'
 p=f"{s['p_greater_one_third']:.6g}" if m in stochastic else '不适用'
 q=f"{s['p_holm']:.6g}" if m in stochastic else '不适用'
 lines.append(f"| {names[m]} | {s['hits']}/30 | {100*s['rate']:.1f}% | [{100*lo:.1f}%, {100*hi:.1f}%]{mark} | {s['unique_trajectories']} | {p} | {q} |")
lines += ['',
'† 按要求列出 n=30 的形式 Wilson 算式值，但确定性重复不满足独立 Bernoulli 抽样解释，**这些 CI 不可用于推断**。固定输入、固定模型且采集不使用 RNG 时，成功/失败是确定结果；改变 seed 不会产生更多独立证据。有效独立轨迹仅1条，也不能估计跨数据集/模型不确定性。',
'交替与 Gaussian-TS 的 CI 是在固定本地模型/候选池/门禁下，对采集 RNG 的条件命中率区间；不是 FLIP 官方优化基准置信区间。没有用旧 seed42 结果增加本次 n，也没有重跑/计入 LLM。','',
'## 六轮终点分布','',
'`cum_top10_max` 是新增288次测量的累计最大 fitness，并非 top10 均值。Q=[最小值,Q1,中位数,Q3,最大值]，样本SD使用 ddof=1。','',
'| 方法 | max 均值 ± SD | max Q | strong 均值 ± SD | strong Q |','|---|---|---|---|---|']
for m,s in S.items():
 a,b=s['maximum'],s['strong']
 aq=', '.join(f'{x:.4f}' for x in a['quantiles']); bq=', '.join(f'{x:g}' for x in b['quantiles'])
 lines.append(f"| {names[m]} | {a['mean']:.4f} ± {a['sd']:.4f} | [{aq}] | {b['mean']:.2f} ± {b['sd']:.2f} | [{bq}] |")
lines += ['','`strong` 阈值沿用产品：全部38,265条 clean 数据 fitness 的90%分位数 **2.615913579904**（仅用于事后评估，不进入采集/训练选择）；计数包含阈值相等项，不含 cold-start。','',
'| Greedy 减去对照的 strong | 平均差 | 差值范围 | Greedy 胜/平/负 | 单侧 sign-test p | Holm p（随机方法） |','|---|---:|---|---|---:|---:|']
ps=sorted((S[m]['greedy_strong_comparison']['sign_test_p'],m) for m in stochastic)
adj={};prev=0
for i,(p,m) in enumerate(ps):
 prev=max(prev,min(1,(2-i)*p));adj[m]=prev
for m in S:
 if m=='mean': continue
 a=S[m]['greedy_strong_comparison']; q=a['delta']['quantiles']
 p=f"{a['sign_test_p']:.6g}" if m in stochastic else '不适用'
 h=f'{adj[m]:.6g}' if m in stochastic else '不适用'
 lines.append(f"| {names[m]} | {a['delta']['mean']:.2f} | [{q[0]:g}, {q[-1]:g}] | {a['wins']}/{a['ties']}/{a['losses']} | {p} | {h} |")
lines += ['', 'sign test 去掉平局，检验 Greedy 在随机轨迹上 strong 更高的概率是否>1/2；不等于均值差的检验。同编号 seed 用于配对记账，不声称不同策略消费了同一随机候选流。','',
'## 固定协议及 answer-agnostic 边界','',
'- 数据：AAV clean=38,265；cold-start HD≤2=10,433；HD>2 池=27,832；HD≤4 且平均 BLOSUM62≥0 后门内=9,533。每轮48、共6轮，所有配置完全相同。',
'- 模型：原始 EpistasisRidgePredictor；训练频次过滤one-hot列、二阶交互、稀疏标准化；固定80/20 split random_state=0，alpha∈{1,10,100,300}按 held-out Spearman选择；全已测数据拟合均值，bootstrap种子0/1/2共3模型提供方差。沿用v0.7而非角色通用5模型。CV用于选参，不是独立最终泛化评估。',
'- mean=预测均值；交替第1/3/5批 mean、第2/4/6批 mean+3√var+U(0,1)；UCB=mean+β√var，β=0.5/1/2/3全部报告，不择优删配置。',
'- Gaussian-TS=每轮每个剩余候选独立采样 mean+√var·N(0,1)，按样本值选48。仅是边际高斯 Thompson 近似，忽略候选间后验相关性；不是严格的后验函数采样，也不宣称方差校准。',
'- 与v0.7同口径，seed0..29仅控制采集随机数，cold-start、CV及bootstrap固定。diverse消耗整个剩余池长度的随机数；按产品 test() 的原池行顺序追加训练批，保留默认argsort的并列排序规则。',
'- select()只接收方法/轮次/mean/var/门禁/RNG，无fitness或峰身份参数；训练只接收cold-start及先前已提名的标签。每轮先确定提名；账本保留当时预测及后续查表真值，峰值由audit事后读取。没有使用目标序列/坐标/排名调参。',
'- 固定模型下，相同有序训练行ID复用精确预测缓存；所有210条配置×seed都实际执行六轮提名，缓存不改变训练/提名规则。3个单线程进程仅分担调度。',
'- 初始单进程调度试跑在完成任何完整轨迹前中止，仅改为三进程；原stdout/manifest保留于scheduling-pilot。没有按试跑峰值修改任何策略参数。','',
'## 本轮工具证据','',
f"- 正/阴性对照：cold-start CV Spearman={C['cv']:.9f}；shuffle CV={C['shuffle_cv']:.9f}，满足>0.8与绝对值<0.1断言。",
f"- 未修改产品 runner 独立重跑 seed42 交替：max={C['reference_seed42']['cum_top10_max']:.6f}、strong={C['reference_seed42']['strong']}；六批累计max、最终strong及逐批top10序列和分数全部一致。该seed42不进入30seed统计。",
'- UCB β=3 的另一路 DataFrame 实现不读预测缓存，重新拟合六次，六批288个候选与完整真值逐条一致，再次第三批达峰，终点strong=128；见ucb3-uncached.log。',
'- `run.py --verify-only` 从逐批真值账本重算全部统计；`audit.py` 逐批从缓存预测和RNG重建提名，并逐条对照oracle、去重、门禁和预算；真实runner输出见verification.log/audit.log。',
'- audit.py实际输出：verified_rounds=1260、verified_nominations=60480，全部候选重建及查表核对通过。Wilson公式0..30命中的31种情况均与SciPy内置实现一致。',
'- runner实际输出：verified trials=210、nominations=60480、seconds=1977.4；其unique_fits=5仅是父进程新增拟合计数，三个worker的拟合另记在worker日志中。',
'- 未修改产品代码/数据：manifest内SHA256前后逐项一致；git产品差异为空。只跑本任务分析与断言，未跑pytest全量矩阵或CI。',
f"- 环境 Python {M['python']} / numpy {M['numpy']} / scipy {M['scipy']} / sklearn {M['sklearn']}；执行基线 `{M['commit']}`。",
f"- 数据SHA256：`{next(v for k,v in M['hashes'].items() if k.endswith('full_data.csv'))}`。",
f"- 实跑runner SHA256：`{next(v for k,v in M['hashes'].items() if k.endswith('run.py'))}`。",'',
'复现：在本代码基线从仓库根运行（已有目录拒绝覆盖；另建目录并复制run.py可重跑）：','',
'```bash',
'OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=. .venv/bin/python harness/context/research/v07-multiseed-evidence/run.py',
'PYTHONPATH=. .venv/bin/python harness/context/research/v07-multiseed-evidence/run.py --verify-only',
'PYTHONPATH=. .venv/bin/python harness/context/research/v07-multiseed-evidence/audit.py',
'```','',
'证据目录：[v07-multiseed-evidence](v07-multiseed-evidence/)：run.py、audit.py、verify_ucb3.py、protocol.md、manifest.json、210份trials、results.json、summary.json、controls.json、reference-seed42.json、runner/worker日志及预测cache。报告与本地证据不强制加入公共代码仓。','',
'## 每个 seed 的终点（max / strong）','',
'| seed | mean | alternating | UCB0.5 | UCB1 | UCB2 | UCB3 | Gaussian-TS |','|---:|---|---|---|---|---|---|---|']
by={(r['method'],r['seed']):r for r in R}
for seed in range(30):
 vals=[f"{by[m,seed]['cum_top10_max']:.4f}/{by[m,seed]['strong']}" for m in names]
 lines.append('| '+str(seed)+' | '+' | '.join(vals)+' |')
lines += ['','## 风险、未验证项与下一步','',
'只有一个固定AAV池、一个cold-start和一套固定模型bootstrap，结果不能硬化成“任何算法都不可靠”或跨蛋白质的普遍结论；Gaussian-TS也不能代表所有Thompson实现。greedy的strong优势与单峰成功率是不同目标，须分别陈述。',
'历史v0.7三seed矩阵、v06-backtrack-analysis及frontier-landscape-synthesis仅提供本地背景；未重跑旧LLM轨迹，未联网复核外部论文，未验证GB1/ESM/训练随机性变化。FLIP-AAV原生是回归基准，本项目池式优化协议不等于官方全局优化评测。',
'下一步：若要测跨训练随机性的稳健性，应另行预注册统一的bootstrap/CV/cold-start扰动，并对全部方法共用扰动，不根据本轮峰身份选择模型/特征/β。若只想收集大量strong，按上述strong差值结果决策；若追单峰，应报告预算与条件命中率，保留失败轨迹。',
'治理交接：本worktree未注册Harness，专属canonical task-id未提供；事实晋升与task-bound doc sync未完成，不能声称已提交/通过完成门。按无联网约束未fetch；本地origin/main与任务基线无共同祖先，未强行rebase。见handoff.json及governance.log；待owner提供task绑定/处理基线历史后补交。']
out=P.parent/'v07-multiseed-robustness.md'
assert len(lines)<=300
out.write_text('\n'.join(lines)+'\n')
print(json.dumps({'report':str(out),'lines':len(lines)}))
