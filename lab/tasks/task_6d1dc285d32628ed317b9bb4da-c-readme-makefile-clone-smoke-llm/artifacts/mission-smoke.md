# 小规模复现路径(smoke)——笔试题明文要求

## 缺口

试题「三、详细要求 → 代码」明写:**「代码应能在小规模数据集上复现实验流程。」**
本仓现在只有全量入口:`make campaign` 跑真实 149,361 条、四策略三轮,约两分钟以上,
而且需要那份**未提交的 44MB 地形** `data/four_mutations_full_data.csv`。
于是评委 clone 下来**跑不动任何东西**。`Makefile` 里没有任何 smoke / quick 目标。

## 目标

让一个**干净 clone、没有 44MB 地形、没有 ESM 缓存、没有 API key** 的人,
执行一条命令就能把完整实验流程走通一遍(小规模、秒级),并看到真实产物。

## 要做什么

1. **`make smoke`**:端到端跑一遍「数据 → 预测器 → 五角色 Agent → 四策略 campaign」,
   用**内置的小规模合成地形**(不依赖 44MB 文件),预算与轮数都压到秒级。
   产物落一个明确的临时/示例目录,**不要覆盖 `lab/reports/` 下任何已有产物**。
2. **数据缺失时的诚实降级**:若 `data/four_mutations_full_data.csv` 不存在,
   全量入口(`make campaign` 等)必须给出**明确的提示**——说清缺哪个文件、从哪里获得
   (见 `data/README.md`)、以及「可以先跑 `make smoke`」。
   **不许静默失败,也不许假装跑完了。**
3. **README**:在 Setup & run 一节把 `make smoke` 写成**第一个**推荐命令,
   并说明它用的是合成小地形、数字不可与报告中的正式结果比较。
4. **`make test`**:确认它跑的是自包含测试集合(与 `.github/workflows/ci.yml` 里那份一致),
   在没有 44MB 地形时也能绿。

## 硬口径

- smoke 的产物**必须标注是合成小规模数据**,绝不能让人误读成正式实验结果。
  这是诚实性要求:一个跑得通的 demo 不等于论文里的数字。
- 不要为了让 smoke 跑通去改真实实验的默认参数或口径。
- 合成地形要是**确定性的**(固定 seed),这样 smoke 的输出可复现。

## 验收(CEO 亲验)

- 我会在一个**真正干净的 clone** 里(临时目录、不带 `data/`、不带 `features/cache`)
  执行 `make smoke`,它必须成功并产出可见产物。
- 我会把 `data/` 移走后跑 `make test`,必须绿。
- 我会确认 smoke 的产物里带着「合成小规模」的标注。

## 边界

- worktree `.worktrees/t-smoke`(分支 `t-smoke`,基于最新 `origin/main` = `5bf1bcc`)。
- 可动:`Makefile`、`README.md` 的 Setup & run 一节、一个新的 smoke 脚本
  (建议 `scripts/smoke.py` 或 `evolution/smoke.py`,你判断)。
- **不要动** `evolution/campaign.py` 的策略路由与口径、`agent/pipeline.py`、`models/`、
  `knowledge/`、`events/`、`app/demo.py` —— 另有 worker 在飞或刚合入。
  只读复用它们的接口没问题。
- 停止点 = `make smoke` 与 `make test` 都通 + commit。**不 push、不发 PR。**
- 发现 CEO 判断有误就带证据回报并停手。
