# AI4S 定向进化 Agent · Worker 仓库手册（所有执行 Agent 预读）

> 这是本仓所有 worker（无论 Codex / GLM / Claude）开工前必须先读的共享上下文。它管**本仓实况与口径**；跨项目纪律见各自角色手册。冷启动 worker 只凭本文件 + 分配到的 `task_plan.md` 就该能开工。

## 0. 一句话背景

这是**明度数智 AI4S 笔试**：一周内做一个「虚拟蛋白质定向进化科学智能体」。硬冻结 **2026-09-13 15:00**。评审看的是：可复现的代码 + 四方法对比 + 诚实的失败分析 + 3–5 页 PDF + 可交互 demo。**不是产品，是笔试**——不要过度工程，把力气花在评分表上。

## 1. 数据事实（不可臆造）

- 数据集：**GB1**（蛋白 G 的 B1 结构域，56 aa），4 个可变位点 V39/D40/G41/V54。来源 Wu et al. 2016 eLife / FLIP benchmark。
- 本地文件：`data/four_mutations_full_data.csv`（约 46 MB，**149,361 行**有效变体 + 表头），列含全长 56aa 序列与 fitness。**已 `.gitignore` 排除，不在版本库**。
- 野生型 WT = `VDGV`，fitness = 1.0；全表最高 fitness = **8.762**（变体 FWAA）；top-1% 均值 ≈ 3.304；非零(>0.01)占比 ≈ 23.1%。
- **组合空间 20⁴ = 160,000，但真值表只有 149,361**，缺 10,639（真实缺数据、找不着）。

## 2. 已锁定口径（decision 台账，违反即打回）

- **D1 提名空间**：四策略的候选提名/评估空间**统一限定在 149,361 个有真值变体内**；缺失 10,639 记为已知局限。任何策略都不得提名到缺真值组合（否则查表 KeyError / 被当 0）。
- **D2 表征**：**ESM-2 650M 本地实时提取**（MPS，1280 维）作 L2 主力；**one-hot**（4×20=80 维）作 L1。**ESM embedding 必须缓存进仓库**，评委无 GPU 也要能复现；保留 one-hot CPU 兜底路径。
- **D3 事件流**：事件流内核属**交付层**（前端过程回放的数据底座 + 可审计链），不是可砍的彩蛋。
- **D4 LLM**：Agent 的 LLM 走**商业 API**（Claude 3.5 Sonnet / GPT-4o / DeepSeek-V3），要求严格产出 Pydantic schema。
- **D5 方案真源**：以 `harness/context/research/AI4S-revision-report.md`（新版）为准；旧 `AI4S-technical-plan.md` 已废弃，冲突时以新版为准。

## 3. 模块地图与文件面（不要越界）

| 方向 | 目录/文件 | 任务 |
|---|---|---|
| 数据+特征 | `data/ evolution/mutations.py features/` | T2 |
| 预测模型 | `models/ reports/`(预测指标) | T3 |
| 事件流内核 | `events/ tests/test_events.py` | T4 |
| 知识库 | `knowledge/` | T5 |
| Agent 流水线 | `agent/` | T6 |
| 闭环对比 | `evolution/campaign.py reports/`(campaign) | T7 |
| 前端 | `app/` | T8 |
| 报告 | `reports/ report/ README.md` | T9 |

已有基础：`evolution/random_baseline.py`（策略①随机基线，导出 `propose_random/simulate/build_report`，供 T7 复用；JSON 契约字段 `round/top10_max/top10_mean/n_hit_nonzero` 保持稳定）。

## 4. 技术栈约定

- Python 3.11+；`.venv` 在仓库根（worktree 里需自行 `python -m venv` 或复用）。
- 数据/建模：pandas、scikit-learn、xgboost、numpy；ESM-2 用 `fair-esm` 或 HuggingFace（device=mps）。
- Agent：**PydanticAI**（不用 LangChain/LangGraph）；LLM 只在 Hypothesis Generator + Scientific Critic 两处出现，且 `output_type=Pydantic schema`。
- 事件流：只用标准库（`hashlib`/`sqlite3`/`json`），不引外部队列/DB 服务。
- 前端：Streamlit 单文件，只读消费产物，严禁写事件流。

## 5. Git / 测试纪律（硬性）

- **独立 worktree + 任务分支**，不占仓库根；base = `main`（当前默认分支）。
- 只改分配给你的文件面；**禁区** = 其他在飞 worker 的文件面 + CI/门禁配置（protected surface）。
- 停止点 = **触碰面的定向测试绿 + 本地 commit**；**不 push、不发 PR、不打标签**（PR 面归 CEO）。
- **禁止跑全量测试矩阵 / `check:local` 全套**（会拖垮 16 核）；只跑 packet 点名的测试文件。
- commit 作者用 `ZeyuLi`；commit message 用 `feat/fix/test/...` 前缀，**不提任何 AI**。
- 阴性对照优先：信一个检测器沉默前，先用阳性对照让它出声（如 shuffle 标签后 Spearman 应塌、篡改事件后 verify 应报错）。

## 6. 输出契约（回报给 CEO）

- 产出**先落盘再汇报**；停手前先 commit。报告分清「完的 / 半截的」。
- 只报有工具证据的事实（真实 runner 输出、磁盘产物、grep 结果），没验证的标 `unverified`。
- 承重观察用 `ha fact record --task <task-id> ...` 晋升（`code-doc-reconciliation` 门要求至少一条 fact）。
- 收口 = 结论 + 依据 + 风险 + 下一步，不转录完整推理。
