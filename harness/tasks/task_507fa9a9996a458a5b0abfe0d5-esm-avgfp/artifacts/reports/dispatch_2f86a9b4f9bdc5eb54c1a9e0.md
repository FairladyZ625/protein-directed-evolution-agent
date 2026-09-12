已完成并提交本地 commit `fe5a1a5`（`feat: add bootstrap uncertainty and harder dataset guards`）。

完成内容：

- `models/train_ladder.py`
  - Ridge 集成改为 5 个确定性 bootstrap 重采样成员。
  - `predict(X)` 继续保持统一 `(mean, var)` 接口。
  - 方差现在具备非平凡分布，可供 UCB 使用。

- `evolution/pool_campaign.py`
  - `fitness_evaluator` 事件新增 `variance_min / variance_mean / variance_max`，便于审计 UCB 是否真正生效。

- `features/esm2.py`
  - ESM embedder 同时支持 GB1 四字符变体和 AAV/avGFP 完整氨基酸序列。
  - 保留原有 GB1 变体展开逻辑。

- `evolution/datasets.py`
  - avGFP loader 不再使用“最长序列”猜测 WT。
  - 要求 CSV 存在显式 WT 行（`mutant` / `mutation` / `mutations` 列值为 `WT` 等）。
  - 增加序列长度、标准氨基酸和 fitness 数值校验。

- 新增 [tests/test_pool_campaign.py](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-harder/tests/test_pool_campaign.py)
  - bootstrap 方差非零；
  - 同 seed 结果可复现；
  - avGFP 显式 WT 解析；
  - ESM 完整序列输入。

- 新增 [harder-findings.md](/Users/lizeyu/Projects/ai4s-directed-evolution-agent/.worktrees/t-harder/artifacts/harder-findings.md)，记录当前真实结论与 blocker。

验证证据：

```text
python -m pytest tests/test_pool_campaign.py -q
3 passed in 2.56s
```

AAV ESM 实跑情况：

1. `fair-esm==2.0.0` 已安装成功。
2. 运行 `python -m evolution.pool_campaign --dataset aav --feature esm2` 时，已进入官方 ESM-2 650M 权重下载：
   `https://dl.fbaipublicfiles.com/fair-esm/models/esm2_t33_650M_UR50D.pt`
3. 下载约 90 秒无进展后中止，因此本轮没有虚报 AAV ESM 指标、事件流或曲线。

avGFP 情况：

- 当前没有 `data/avgfp/avgfp.csv`，因此未运行 avGFP campaign。
- loader 已改为要求真实 ProteinGym CSV 和显式 WT 行。

Harness fact 已记录：

- `F-752A64DF`
- 结论：bootstrap Ridge 产生非平凡且可复现的不确定性；AAV ESM 受 650M 权重下载阻塞，avGFP 受缺失 CSV 阻塞。

未完成 / 下一步：

- 提供或缓存 ESM-2 650M 权重后重跑 AAV ESM。
- 获取 ProteinGym `GFP_AEQVI_Sarkisyan_2016` 数据，放入 `data/avgfp/avgfp.csv`，再运行 avGFP 四策略 campaign。
- 当前尚无本轮证据支持 agent 或 knowledge 优于 greedy；该结论需等待两套 campaign 实际完成后再报告。