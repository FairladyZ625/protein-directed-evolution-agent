# v0.7 多 seed 稳健性:证据包

本目录是 agentic v0.7(AAV 30-seed 采集稳健性矩阵)的**完整证据包**,
`lab/context/research/v07-multiseed-robustness.md` 里的每个数字都出自这里。

## 为什么它单独存在

2026-09-12 CEO 盘点发现:v0.7 这一版**没有 `lab/reports/agentic-v0.7/` 数据文件夹**
(`t-v07` 相对 `t-v05` 只新增了 `agent/auto_researcher.py` 与一个测试文件),而它的
机器可读证据**整个目录 134MB 都处于 git 未跟踪状态**,只存在于 worktree `t-astra-seeds`
的文件系统里——那个 worktree 一删数据就永久丢失。本目录是把其中 336KB 的证据文件
(去掉 128MB 的 `cache/` 派生缓存)纳入版本控制的结果。

## 内容

| 文件 | 是什么 |
|---|---|
| `protocol.md` | 实验协议:固定 AAV 池、固定模型、30 个采集 seed |
| `run.py` | 产出矩阵的脚本(复现入口) |
| `verify_ucb3.py` | UCB β=3 达峰结论的独立复核脚本 |
| `results.json` | 全矩阵原始结果(78KB) |
| `summary.json` | 汇总统计 |
| `reference-seed42.json` | seed42 参照轨迹全量记录(55KB) |
| `controls.json` | 对照:CV 0.905917 vs shuffle-label CV 0.013438(阴性对照成立) |
| `ucb3-uncached-verification.json` | 绕开缓存的 UCB β=3 复核 |
| `delivery-checks.json` / `governance.log` / `audit.log` | 交付检查与治理留痕 |
| `worker-{0,1,2}.log` / `runner.log` / `verification.log` | 三个并行 worker 与复核的原始日志 |

## 口径限制(来自 `v07-multiseed-robustness.md`,不得在引用时省略)

- 这 30 个 seed 是**同一轨迹的确定性重复**:这些方法不消费采集 RNG。
  因此 **n=30 的 Wilson 置信区间不可用于统计推断**,有效独立轨迹只有 1 条。
  文档里列出 CI 是为了满足形式要求,并已显式标注不可用。
- 全程使用**本地真值查表**,未调用 LLM/网络。
- 「峰」指 **HD>2 未测池内的最优 8.41620513**,cold-start 最大值为 9.53645667;
  既不是整个数据集的最优,更不是蛋白真实序列空间的全局最优。

## 未纳入版本控制的部分

`cache/`(128MB,302 个子目录)是派生的预测缓存,不入库。`run.py` 在缓存缺失时会重算;
`ucb3-uncached-verification.json` 就是绕开缓存重算的复核结果,用来证明结论不依赖缓存。
