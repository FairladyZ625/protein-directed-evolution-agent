# V0.6 backtrack 对抗分析：先纠正基线归因，再决定 redirect

任务：`task_e2eab881832291e8f8f73f30a4`；2026-09-12；执行分支 `t-analysis`，代码基准 `ccbfce6`。

## 结论与给 CEO / GLM 的建议

1. **否定 CEO 假设的关键前提。** 原报告的“确定性纯 greedy 达 8.4162”实际是 predicted_mean / diverse 交替；本次重放复现 8.4162、strong=151。真正每批均值 top-48 的新消融仅达 **7.8290，strong=166**。不能由原结果推出“探索有毒、纯利用即可达峰”。
2. **v0.5 停滞不是简单漏测当轮高均值。** R4–R6 确实全取均值 top-48；目标却排 #1319 / #1333 / #1217，预测仅约 2.35–2.53。更准确的机制是早期采样改变拟合路径，加上高阶头部排序误差；“走错盆地”只能作比喻，未证明存在独立的序列盆地。
3. **合法达峰路径存在，但本次两类 redirect 均未证明能救回 v0.5。** 交替基线在 R4 的 diverse 批测到均值排名 #1384 的目标。纯均值 redirect 在已有纯利用状态下是重复动作；硬性换构成可能无效或排除有益组合。
4. **明确建议：a 作基础利用策略；b 只作软多样性项，不能作硬排除门。** 若当前已纯利用且停滞，redirect 必须改变采集依据（可将现有不确定性采集作为独立对照），不能只改工具名称。保留 C+A；先纠正基线名称，再由 CEO 预注册纯均值 / 现有交替 / 停滞后切换的等预算消融。此处没有授权或实施产品修改。

## 证据范围与限制

本任务用 **AAV**，不是 GB1：加载器实得 38,265 条、cold-start 10,433、未测池 27,832、门内池 9,533。门禁为 HD≤4 且平均 BLOSUM62≥0。全程只在此池内选点；48×6=288，seed=42。

8.416205 是未测池/门内池最大值；cold-start 最大值却为 **9.536457**。因此“达峰”仅指发现池内最优，不能说超过全部已知实测；停滞检测必须使用新增测量的累计最大值，否则 cold-start incumbent 会造成从第一轮就“永远停滞”。

- v0.4、v0.5 JSONL 的 50 / 25 个事件哈希链本次验证通过，且与 metrics.tool_trace 逐条一致。
- v0.5 / deterministic 可按确定性工具规则恢复批次；各 6 批的 top10 序列及四位分数、累计最大值、strong 命中均与原文件一致。恢复时严格保留 test() 的原池行顺序、精确 CSV 标签和 RNG 消耗。
- 原事件的 test 只存数量/花费/batch_max，list_pool 不存候选，compose 不存候选；**没有完整序列账本**。上述吻合是重放一致性证据，并非与全量原序列逐条核对。
- v0.4 自由 LLM 的手选集合不可恢复：只有各批 top10 的并集 **69/288** 个序列可见，不能伪造完整训练集重拟停滞模型。其最后累计 top10 可从各批 top10 精确恢复；后续精确峰排名、完整簇占比标为 **unverified**。
- v0.4 metrics 实际是 **7 个 test 批次**，大小 `[48,47,48,48,46,42,9]`，不是 6 个等长实验批；调用轮与实验批不能混用。
- 当前 alpha 由一个固定 80/20 split 的 Spearman 选择；不是 docstring 所称留一 RidgeCV，也不是独立于调参的最终测试指标。均值来自全量拟合，方差来自 3 个 bootstrap；本任务不把角色默认的 5-seed 口径套进此模型。

## 1. 停滞机制：头部结构与排名

零基下标与代码一致；下列构成仅用于后验说明，**不是在线指令或硬编码输入**。

| 轨迹 | 新增最优构成 | 累计 top10 的结构摘要 | 结论边界 |
|---|---|---|---|
| v0.4 最终 | E2Q/R5A/S17E/T20D，7.8290 | HD3=4、HD4=6；T20E 5/10、S17E 4/10、V18A 4/10 | 并非所有头部都围着单一 incumbent；全已测簇不可恢复 |
| v0.5 最终 | E1D/S17T/R27Q，6.5309 | HD3=7、HD4=3；T20E 5/10、S17E 4/10、V18A 3/10 | incumbent 与真实 top10 分布并不等价 |
| 确定性参考目标 | D0Q/S17E/V18A，8.4162 | 目标所用残基在 LLM 的头部中已有部分覆盖 | 不能以“不同构成”自动推导不同有效盆地 |

下表是 **v0.5 重放状态**，after=已完成实验批数，排名仅在门内未测候选中计算。真值只用于后验定位目标；模型训练仍只用该时刻已测标签。

| after | CV Spearman | 目标均值排名 | 目标预测 | 均值 top48 预测 min / median / max | 下一批纯均值真值 max |
|---:|---:|---:|---:|---|---:|
| 0 | 0.9059 | 426 | 6.3668 | 9.9966 / 10.8867 / 14.4412 | 7.3910 |
| 1 | 0.9003 | 2231 | 2.3829 | 7.0474 / 7.5563 / 9.6537 | 5.7677 |
| 2 | 0.9027 | 2522 | 1.6898 | 5.8788 / 6.2196 / 7.3046 | 6.5309 |
| 3 | 0.9002 | 1319 | 2.5347 | 5.1741 / 5.4387 / 6.0845 | 6.4392 |
| 4 | 0.9043 | 1333 | 2.3506 | 4.8363 / 4.9742 / 5.9966 | 5.6437 |
| 5 | 0.9057 | 1217 | 2.3495 | 4.4932 / 4.7171 / 5.3461 | 6.2620 |
冷启动本次排名是 **#426**，不是历史报告的 #447；保留差异，不把历史数字写成本次结果。当前环境重放的批次指标仍全部吻合。

R1 的 42 exploit + 6 explore 确实漏掉均值 #45 的 7.3910（这是原报告的局部证据）；但本次纯均值完整消融仍未达 8.4162，所以不能把该截断当作解释全部差距的充分原因。v0.5 CV 始终约 0.90，却未反映目标从 #426 跌至 #2231/#2522 的尾部排序错误。R4–R6 不存在未执行纯利用的问题。

v0.4 只能确认混合采集、工具失败及两次 harness 补批；调用 predicted_mean 9 次、其余 19 次不等于实际实验名额比例。其停滞究竟有多少来自利用不足、多少来自预测低估，现有日志无法精确量化。

## 2. 达峰路径与真正的纯均值消融

| 本次运行 | 6 批累计 max 曲线 | 最终 strong |
|---|---|---:|
| v5 | [5.9988, 5.9988, 6.5309, 6.5309, 6.5309, 6.5309] | 163 |
| det | [7.391, 7.391, 7.829, 8.4162, 8.4162, 8.4162] | 151 |
| pure | [7.391, 7.829, 7.829, 7.829, 7.829, 7.829] | 166 |
`det` 的模式为 `[mean, diverse, mean, diverse, mean, diverse]`，diverse=`mean + 3*sqrt(var) + U(0,1)`。R3 后目标均值 **#1384，预测 2.6635**，均值 top48 最低为 5.7858；R4 diverse 实测命中目标。反事实在这个同一状态改取均值 top48，批最大仅 **6.4036**。

这提供了一条实际执行的合法路径，但不证明 v0.5 任意停滞状态在剩余预算内都能到峰，也不证明有必要进行物理式“回溯”。已测标签不应丢弃或退款；backtrack 在此应理解为切换采集策略。不能把参考路径的序列、目标排名或 oracle 成败拿去决定在线切换。

## 3. redirect 对比与敏感性

事先固定两个可计算定义，不宣称等于尚未验收的 GLM 实现：

- **a**：门内未测均值 top48。
- **b-single**：相对新增实测 incumbent 的突变集合 Jaccard 距离 ≥ d，再按均值取48；d∈{0.5,0.75,1.0} 全报，不根据目标表现挑阈值。
- **b-cluster**：相对累计新增 top10，每个候选取到这10个实测点的最小 Jaccard 距离，再施加同一阈值。用于检查“单个最优”是否误代表“簇”。

候选集合和排名只使用序列、已测标签和预测；选完才查未测真值。几何距离不是功能盆地的实证定义。

**v0.5 停滞前后的一步 b-cluster 结果**；overlap 为与 a 的交集，目标 eligible 仅后验检查：

| after | d | batch max | strong | overlap /48 | 目标 eligible |
|---:|---:|---:|---:|---:|---|
| 3 | 0.5 | 6.4392 | 27 | 47 | True |
| 3 | 0.75 | 6.4392 | 27 | 39 | False |
| 3 | 1.0 | 4.2623 | 17 | 15 | False |
| 4 | 0.5 | 5.6437 | 29 | 47 | True |
| 4 | 0.75 | 5.7024 | 28 | 35 | False |
| 4 | 1.0 | 4.9733 | 17 | 14 | False |
| 5 | 0.5 | 6.2620 | 27 | 48 | True |
| 5 | 0.75 | 4.9733 | 24 | 42 | False |
| 5 | 1.0 | 5.3254 | 18 | 14 | False |
b-single 在 after3/4/5、d=0.5 或0.75 时与 a **48/48 完全相同**；d=1 时交集47/45/46，下一批 max 为6.4392/5.7024/6.2620。b-cluster 的目标最近距离均为 **0.6**，所以 d≥0.75 会把目标硬排除。两种 b 都没有在这些单批中命中目标；不能因为空间距离更大就声称更接近峰。

**剩余预算内续跑**：after3 是提前介入敏感性，不满足“连续2批不提升”；after5 是该检测器首次触发，余48预算。这里只重拟并继续这些代理规则，不调用商业 LLM。

| 从 after 开始 | 规则 | 剩余批累计 max | 最终 strong | 命中目标 |
|---:|---|---|---:|---|
| 3 | mean | [6.5309, 6.5309, 6.5309] | 163 | False |
| 3 | hop0.5 | [6.5309, 6.5309, 6.5309] | 163 | False |
| 3 | hop0.75 | [6.5309, 6.5309, 6.5309] | 163 | False |
| 3 | hop1.0 | [6.5309, 6.5309, 6.5309] | 161 | False |
| 5 | mean | [6.5309] | 163 | False |
| 5 | hop0.5 | [6.5309] | 163 | False |
| 5 | hop0.75 | [6.5309] | 163 | False |
| 5 | hop1.0 | [6.5309] | 162 | False |
**判据裁定建议**：本地证据不支持 a 或硬 b 有稳定达峰优势。a 适合作可审计的基础采集；b 应限于软排序/预算内多样性，并检查实际 batch overlap，避免把相同批次包装成 redirect。对已连续纯利用的状态，优先验证不确定性采集或采集函数切换；目前已有交替成功对照，但没有多 seed 优势证明，不能直接宣告 UCB 普遍最优。

## 4. V0.6 full / semi 的预期与验收

本 read-set 未提供 full/semi 的最终实现定义，**没有读取并发 worktree 或运行 V0.6**。以下是有条件预测，不是正式结果：

- 若 semi 是确定性停滞触发、随后纯均值 top48，且此前沿用 v0.5：预计继续停在6.5309。本次 after5 剩一批的 a 已验证这种退化；工具名称改变不会改变候选。
- 若 full 让 LLM 自主触发/选择构成跳转：不能预报精确峰值；预计对触发时机、距离定义及实际替换名额敏感。距离松时可能与 semi 无差，距离强时可能排除共享的有益构成。若 full/semi 实际角色定义不同，应按采集行为重新映射，不能用名称套结果。
- 两变体都应同时报告：新增已测累计峰/strong、触发时剩余预算、切换前后候选交集、均值与不确定性摘要、重复/门禁率、实际测试序列与精确标签。CV 高不等于尾部已校准；还应追踪逐批预测误差与排序表现（建议，未在产品实现）。
- **异议**：暂停把“纯均值 redirect”或“硬换构成”当作已获证实的修复。先修正成功基线的科学归因，再由 CEO 决定后续等预算对照；当前证据不支持以 LLM backtrack 自主性宣称增益。

## 5. 验证、复现与未验证项

仅运行下列只读分析；无产品修改、无 pytest/CI、无外部文献或 API 请求。持续上升/恢复不触发、平台触发、历史不足不触发，以及真实 AAV cold-start shuffle 阴性对照均在 runner 中断言/输出：
`{"kind": "control", "rising": false, "plateau": true, "too_short": false, "recovery": false, "v5_triggers": [5, 6]}`
`{"kind": "shuffle_control", "cv": 0.01343817714646941, "alpha": 300.0}`
执行环境：Python3.13.2 / numpy2.5.3 / scipy1.18.1 / sklearn1.9.0。精确原始数据与脚本哈希如下（版本差异可能影响细部排名）：
- `data/aav/full_data.csv` SHA256 `520c7c6545e61d3c23b41616fbb6afe3396c3ca11da1fe14ead92846dfeffa77`
- `.analysis-tmp/diagnose.py` SHA256 `f3819e93a3e2ddcd1bc294a9ac80d2fd6cedb223e3ef0e3be32a4e29e4f49829`
- `.analysis-tmp/cluster_check.py` SHA256 `883edac463d92331c26c8df907f67e354052ca4073c83cf68a3972278b9df886`
- `harness/reports/agentic-v0.4/aav/agentic.metrics.json` SHA256 `3f1fb10ba36a18287156f6e8dd52abb4d03a993d8c8656b87802ec49a3724612`
- `harness/reports/agentic-v0.4/aav/deterministic.metrics.json` SHA256 `41ae9945a401c0d047c7b6bd81738f96e953fa638bc55c5b22d1cae7e0e144b0`
- `harness/reports/agentic-v0.5/aav/agentic.metrics.json` SHA256 `a718c0b063bae3630812b606bfed5112556d595c08655f7e1bea89ee221d65ee`
将附录两段分别保存到 `.analysis-tmp/diagnose.py` 与 `.analysis-tmp/cluster_check.py`，在本任务代码基准与数据环境运行（目录若不存在先 mkdir）：
```bash
mkdir -p .analysis-tmp
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=. .venv/bin/python .analysis-tmp/diagnose.py > .analysis-tmp/runner.log 2>&1
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=. .venv/bin/python .analysis-tmp/cluster_check.py > .analysis-tmp/cluster.log 2>&1
```
每个数字来自上述脚本的 audit/data/recorded/state/replay/summary/rescue/cluster_hop/control/shuffle_control 输出；不依赖不可访问的临时脚本，完整代码随文保存。原始 stdout 与 JSON 本机保留在 `.analysis-tmp/`。

风险：单 dataset/seed；后验代理对照不能作为独立确认试验；不证明全地形盆地；v0.4 完整已测集、V0.6 full/semi 正式结果、多 seed 泛化均 unverified。未验证 ESM、GB1 或其他产品面。

交付前 `git fetch origin main` 成功；最新 origin/main=`be62937a8b7a7bc3e6e9e7d67fba33e67e8f3bc2`，`git merge-base HEAD origin/main` 无输出、exit1，仓库非 shallow。**没有共同祖先，不能按常规安全 rebase**；未强行拼接历史，证据仍基于任务声明 v0.5 分叉。需要 CEO 处理基线历史。Harness 文档与临时证据不进入公共代码提交；本地提交只记录交付检查点。

## 附录 A：主 runner（实跑源码）
```python
import json, hashlib, copy
from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from evolution.datasets import load_aav
from agent.auto_researcher import _gate_variants, _compose_batch_indices, _adaptive_exploit_ratio, _enforce_exploit_floor
from models.train_ladder import EpistasisRidgePredictor
from knowledge.validators import load_rules
from events.store import _event_hash
OUT=Path('.analysis-tmp'); records=[]
def emit(kind, **kw):
    row=dict(kind=kind, **kw); records.append(row)
    print(json.dumps(row, ensure_ascii=False), flush=True)
    (OUT/'results.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
reps={k:json.loads(Path(p).read_text()) for k,p in {
 'v4':'harness/reports/agentic-v0.4/aav/agentic.metrics.json',
 'det':'harness/reports/agentic-v0.4/aav/deterministic.metrics.json',
 'v5':'harness/reports/agentic-v0.5/aav/agentic.metrics.json'}.items()}
for version in ['v0.4','v0.5']:
    p=Path(f'harness/reports/agentic-{version}/aav/agentic.events.jsonl')
    es=[json.loads(x) for x in p.read_text().splitlines()]; prev=''
    for i,e in enumerate(es,1):
        body={k:e[k] for k in ['seq','ts','event_type','round_id','strategy','actor','payload']}
        assert e['seq']==i and e['prev_hash']==prev and e['hash']==_event_hash(prev,body)
        prev=e['hash']
    assert [dict(event_type=e['event_type'],actor=e['actor'],payload=e['payload']) for e in es]==reps['v4' if version=='v0.4' else 'v5']['tool_trace']
    emit('audit',version=version,events=len(es),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),chain=True,trace_equal=True)
spec=load_aav();df=spec.df; seq=df.seq.to_numpy(); y=df.fitness.to_numpy(); X=spec.feature_fn(seq.tolist())
cold=np.flatnonzero(df.hd.to_numpy()<=2); initial=np.flatnonzero(df.hd.to_numpy()>2)
b=load_rules()['blosum62']
def blosum(a,c):return 4 if a==c else b.get(a,{}).get(c,b.get(c,{}).get(a,0))
allowed,_=_gate_variants(seq[initial].tolist(),wt=spec.wt,max_hd=4,blosum_min=0.,blosum_fn=blosum)
gates=set(allowed); gateidx=np.array([i for i in initial if seq[i] in gates]); strong=float(np.quantile(y,.9))
# Diagnostic target is chosen AFTER policy definition from the observed reference result.
peakseq=max((v for r in reps['det']['rounds'] for v in r['top10']),key=lambda v:v[1])[0]
peak=int(np.flatnonzero(seq==peakseq)[0])
def mutations(s):return frozenset(f'{w}{i}{a}' for i,(w,a) in enumerate(zip(spec.wt,s)) if w!=a)
mut=[mutations(s) for s in seq]
def jdist(i,j):return 1-len(mut[i]&mut[j])/max(1,len(mut[i]|mut[j]))
def cluster(tested):
    ids=sorted(tested,key=lambda i:-y[i])[:10]
    return dict(best=float(y[ids[0]]),best_mutations=sorted(mut[ids[0]]),top10_mutations=Counter(m for i in ids for m in mut[i]).most_common(8),top10_hd=Counter(int(df.iloc[i].hd) for i in ids),peak_distance=float(jdist(peak,ids[0])))
emit('data',n=len(df),cold=len(cold),pool=len(initial),gated=len(gateidx),cold_max=float(y[cold].max()),pool_max=float(y[initial].max()),gate_max=float(y[gateidx].max()),peak_gate=peakseq in gates,peak_mutations=sorted(mut[peak]),strong_threshold=strong)
for key in ['v4','det','v5']:
    rep=reps[key]; known=list(dict.fromkeys(s for r in rep['rounds'] for s,f in r['top10']))
    emit('recorded',run=key,batches=[r['n_nominated'] for r in rep['rounds']],curve=rep['summary']['cum_top10_max_curve'],list_modes=[e['payload']['by'] for e in rep['tool_trace'] if e['event_type']=='agent.tool.list_pool'],known_tested=len(known),cluster=cluster([int(np.flatnonzero(seq==s)[0]) for s in known]))
def fit(measured,pool):
    model=EpistasisRidgePredictor().fit(X[measured],y[measured]);mean,var=model.predict(X[pool]);return model,mean,var
def acquire(mode,mean,var,pool,tested,rng,roundno,model):
    eligible=np.array([j for j,i in enumerate(pool) if seq[i] in gates]);order=eligible[np.argsort(-mean[eligible],kind='stable')]
    if mode=='adaptive':
        ratio,_=_enforce_exploit_floor(_adaptive_exploit_ratio(model.val_spearman,roundno,6),model.val_spearman,roundno,6)
        local,_,_=_compose_batch_indices(mean,var,eligible_indices=eligible,exploit_ratio=ratio,n=48,rng=rng)
    elif mode=='alternating' and roundno%2==0:
        scores=mean+3*np.sqrt(np.maximum(var,0))+rng.random(len(pool)); order=np.argsort(-scores)
        local=[j for j in order if seq[pool[j]] in gates][:48]
    elif mode.startswith('hop') and tested:
        # A declared proxy for composition hop, not a claim about GLM's implementation.
        anchor=max(tested,key=lambda i:y[i]); threshold=float(mode[3:])
        far=[j for j in order if jdist(pool[j],anchor)>=threshold]
        local=far[:48]
    else:local=order[:48]
    assert len(local)==48
    return np.array([pool[j] for j in local],dtype=int)
def diagnostic(run,rnd,model,mean,var,pool,tested):
    eligible=np.array([j for j,i in enumerate(pool) if seq[i] in gates]);order=eligible[np.argsort(-mean[eligible],kind='stable')]
    loc={int(pool[j]):int(j) for j in range(len(pool))};rank=next((r for r,j in enumerate(order,1) if pool[j]==peak),None)
    opts={}
    for mode in ['mean','hop0.5','hop0.75','hop1.0']:
        picks=acquire(mode,mean,var,pool,tested,np.random.default_rng(42),rnd+1,model)
        opts[mode]=dict(max=float(y[picks].max()),strong=int(sum(y[picks]>=strong)),mean_pred=float(mean[[loc[i] for i in picks]].mean()),overlap_mean=int(len(set(picks)&set(pool[order[:48]]))),contains_peak=peak in picks)
    emit('state',run=run,after_batch=rnd,spent=len(tested),alpha=model._alpha,cv=model.val_spearman,peak_rank=rank,peak_pred=float(mean[loc[peak]]) if peak in loc else None,top48_pred_quantiles=np.quantile(mean[order[:48]],[0,.5,1]).tolist(),cluster=cluster(tested) if tested else None,redirect=opts)
cache={}; states={}
for run,mode in [('v5','adaptive'),('det','alternating'),('pure','mean')]:
    measured=cold.tolist();pool=initial.copy();tested=[];rng=np.random.default_rng(42);curve=[]
    for rnd in range(1,7):
        key=tuple(measured)
        if key not in cache:cache[key]=fit(measured,pool)
        model,mean,var=cache[key]
        if run=='v5' or run=='det':diagnostic(run,rnd-1,model,mean,var,pool,tested)
        picks=acquire(mode,mean,var,pool,tested,rng,rnd,model)
        # test() preserves pool row order, not acquisition ranking order.
        rows=[int(i) for i in pool if i in set(picks)];tested+=rows;measured+=rows;pool=np.array([i for i in pool if i not in set(picks)])
        curve.append(round(float(y[tested].max()),4));status=None
        if run in reps:
            r=reps[run]['rounds'][rnd-1]
            actual=[[str(seq[i]),round(float(y[i]),4)] for i in sorted(rows,key=lambda i:-y[i])[:10]]
            assert actual==r['top10'],(run,rnd,'top10 mismatch',actual,r['top10'])
            assert curve[-1]==r['cum_top10_max']
            assert int(sum(y[tested]>=strong))==r['cum_n_strong']
            status='top10/curve/strong match'
        states[run,rnd]=(measured.copy(),pool.copy(),tested.copy())
        emit('replay',run=run,batch=rnd,max=curve[-1],batch_max=float(y[rows].max()),cv=model.val_spearman,verified=status,peak_in_batch=peak in rows)
    emit('summary',run=run,curve=curve,strong=int(sum(y[tested]>=strong)))
# Counterfactual rescue: switch after two unchanged batches (v5 after batch5), plus
# earlier post-best batch3 for explicit budget/trigger sensitivity. No oracle in selection.
for start in [3,5]:
    for mode in ['mean','hop0.5','hop0.75','hop1.0']:
        measured,pool,tested=copy.deepcopy(states['v5',start]);curve=[]
        for rnd in range(start+1,7):
            key=tuple(measured)
            if key not in cache:cache[key]=fit(measured,pool)
            model,mean,var=cache[key]
            picks=acquire(mode,mean,var,pool,tested,np.random.default_rng(42),rnd,model)
            rows=[int(i) for i in pool if i in set(picks)];tested+=rows;measured+=rows;pool=np.array([i for i in pool if i not in set(picks)])
            curve.append(round(float(y[tested].max()),4))
        emit('rescue',start=start,mode=mode,curve=curve,final=float(y[tested].max()),strong=int(sum(y[tested]>=strong)),peak_tested=peak in tested)
# Stagnation defined on NEW campaign measurements; cold-start incumbent is excluded.
def stalled(curve,patience=2,eps=0.0):return len(curve)>=patience+1 and max(curve[-patience:])<=curve[-patience-1]+eps
emit('control',rising=stalled([1,2,3,4]),plateau=stalled([1,2,2,2]),too_short=stalled([2,2]),recovery=stalled([1,1,2]),v5_triggers=[i for i in range(1,7) if stalled(reps['v5']['summary']['cum_top10_max_curve'][:i])])
assert not stalled([1,2,3,4]) and stalled([1,2,2,2]) and not stalled([2,2]) and not stalled([1,1,2])
# Label-shuffle control of the actual AAV cold-start held-out signal.
shuffled=y[cold].copy();np.random.default_rng(42).shuffle(shuffled)
null=EpistasisRidgePredictor().fit(X[cold],shuffled)
emit('shuffle_control',cv=null.val_spearman,alpha=null._alpha)
```

## 附录 B：簇距离敏感性 runner（实跑源码）
```python
from pathlib import Path
# Reuse the exact loaders and policies, but keep this evidence in a separate file.
source=Path('.analysis-tmp/diagnose.py').read_text().split('cache={}; states={}')[0]
source=source.replace("OUT=Path('.analysis-tmp'); records=[]", "OUT=Path('.analysis-tmp/cluster'); OUT.mkdir(exist_ok=True); records=[]")
exec(compile(source,'diagnose_definitions','exec'))
measured=cold.tolist();pool=initial.copy();tested=[];rng=np.random.default_rng(42)
for rnd in range(1,7):
    model,mean,var=fit(measured,pool)
    picks=acquire('adaptive',mean,var,pool,tested,rng,rnd,model)
    if rnd>=4:
        anchors=sorted(tested,key=lambda i:-y[i])[:10]
        eligible=np.array([j for j,i in enumerate(pool) if seq[i] in gates])
        order=eligible[np.argsort(-mean[eligible],kind='stable')]
        dist=np.array([min(jdist(i,a) for a in anchors) for i in pool])
        for threshold in [.5,.75,1.]:
            local=np.array([j for j in order if dist[j]>=threshold][:48]); chosen=pool[local]
            emit('cluster_hop',after_batch=rnd-1,threshold=threshold,n=len(chosen),max=float(y[chosen].max()),mean_pred=float(mean[local].mean()),overlap_mean=int(len(set(chosen)&set(pool[order[:48]]))),strong=int(sum(y[chosen]>=strong)),peak_distance=float(dist[np.flatnonzero(pool==peak)[0]]),peak_eligible=bool(dist[np.flatnonzero(pool==peak)[0]]>=threshold),peak_tested=peak in chosen)
    rows=[int(i) for i in pool if i in set(picks)]
    actual=[[str(seq[i]),round(float(y[i]),4)] for i in sorted(rows,key=lambda i:-y[i])[:10]]
    assert actual==reps['v5']['rounds'][rnd-1]['top10']
    tested+=rows;measured+=rows;pool=np.array([i for i in pool if i not in set(picks)])
```
