# AI4S 笔试四天冲刺技术方案

> 面向蛋白质定向进化的科学智能体 · 明度数智笔试
> 候选人：李泽宇 · 2026-09-10（周四）定稿
> 交付：2026-09-13（周日）· PDF 报告 3-5 页 + GitHub 代码 + 可交互 demo

---

## 0. 一页总纲：这份方案凭什么赢

**考官要的不是蛋白质专家，是"能把科研流程拆成可控 Agent 系统"的架构师。** 题目考核重点最后三条（Agent 流程化、知识规则引入、失败分析）和能力条款全部指向系统工程，而非生物知识。蛋白质知识零基础不是短板——把领域知识外置成**结构化规则库**，恰好是明度面试官自己正在做的事（SOP schema 拆解）。

三条设计主轴，全部来自 9/5 技术面面试官原话：

1. **"可控的小积木块，不要大模型自由发挥"** → Agent 是约束化积木：LLM 只在 Pydantic schema 边界内填空，突变组合/校验/评估全部是确定性代码。过程可以 LLM 辅助，**产出必须严格合规**（面试官总结原话）。
2. **"可审计、可回放、防篡改、入库"**（医药合规要求）→ 复刻 Harness Anything 精简内核：append-only 事件流 + SQLite 投影 + 轮次快照，Agent 每一步推理可回放。题目要求"展示推理过程/失败案例/可回放"——事件流天然对口，这不是凑出来的功能，是我开源项目的核心机制移植。
3. **GMP audit trail 同构** → 报告里直接写："事件流 ≈ 医药行业审计追踪：append-only、时间戳、可重放、单写路"。让面试官看到我懂他们的行业约束。

**务实底线**：CPU-only、零模型下载、4 天可交付。所有选型都有降级路径，砍单顺序预先定义（见 §4.5）。

---

## 1. 技术选型

### 1.1 数据集：GB1（蛋白 G B1 结构域，IgG 结合活性）—— 主线，不摇摆

| 项 | 决定 | 理由 |
|---|---|---|
| 数据集 | **GB1 two_vs_many split**（FLIP benchmark） | 题目点名；规模适中（55k 变体可下采样）；突变格式规整（位点+替换氨基酸）；two_vs_many split 天然模拟"训练只见 1-2 点突变、实验要推 3-4 点突变"的真实定向进化外推场景——这个 split 的科学叙事直接写进报告 |
| 来源 | GitHub `J-SNACKKB/FLIP` splits（gb1 目录，csv 直接下载） | 已验证可获取；同时 microsoft/protein-uq 仓库有同源备份 |
| WT 序列 | GB1 野生型 56 aa（PDB 2GB1 / FLIP 仓库内含） | 序列短 = embedding 快、demo 展示友好 |
| 任务定义 | 提高 IgG-Fc 结合 fitness（GB1 滴度测定值，已 log 变换） | 对位题目"提高结合能力" |
| 下采样 | 全量 55k → 训练池采样 5k + 虚拟实验查询池保留 50k | CPU 训练 30 秒内一轮，支持多次迭代调试 |
| 备胎 | FLIP AAV（插入突变型，格式稍复杂）；β-lactamase（ProteinGym 子集） | 仅当 GB1 下载失败才切换，不提前投入 |

**"已完成实验 / 未知候选"场景构造**（题目 1d）：训练池 = 模拟已完成的第 0 轮实验（按 mutation count 分层抽样，保证 1/2/3/4 点突变都有覆盖）；查询池 = 虚拟湿实验库（Agent 提名的变体在这里查真值，查不到的用适应度模型 oracle 兜底并标注）。

### 1.2 蛋白质表征：不下载大模型，用"预提取 + 轻量"双轨

| 路线 | 内容 | 定位 |
|---|---|---|
| A（主线） | **FLIP 官方预提取的 ESM-2 embedding**（仓库提供直接下载，CSV/npz） | 零 GPU、零下载模型，论文可引（FLIP 原文 baseline 即此路线） |
| B（对照） | One-hot + 氨基酸理化特征（疏水性/电荷/体积/极性，5 维 AAindex 精选） | 报告里的"无 PLM"对照组，也喂给知识规则库 |
| C（备胎） | `esm2_t6_8M`（8M 参数，CPU 可跑）transformers 本地推理 | 仅当 A 下载失败；150M 都不碰 |

**叙事点**：FLIP2 论文（2026）结论"简单模型经常打平或超过微调 PLM"——报告引用此结论支撑轻量路线的合理性，把资源约束转成"我读过 benchmark 最新结论"的加分项。

### 1.3 适应度预测模型：baseline 梯子 + 不确定性

| 层级 | 模型 | 指标预期（FLIP 论文 two_vs_many 参考） |
|---|---|---|
| L1 | One-hot + Ridge | Spearman ~0.2-0.4（弱基线，必须有，衬托 L2） |
| L2 | ESM-2 emb + Ridge / XGBoost | Spearman ~0.4-0.6（主力） |
| L3 | ESM-2 emb + MLP（sklearn，2 隐层） | 与 L2 互有胜负，都保留 |
| 不确定性 | **Deep Ensemble（L2/L3 各 5 个种子）→ 预测方差** | 加分项"不确定性估计"最省事实现：GP 拟合 5k 样本太慢，ensemble 方差 5 倍训练成本仍然分钟级；主动选择用 UCB 分数 |

评估指标（题目 2）：Spearman（主）、Pearson、MSE、**Top-k 命中率**（k=10/50：预测 top-k 里真值进入全库 top-1% 的比例——这是定向进化真正关心的指标，报告重点讲）。

### 1.4 Agent 框架：自研约束化 loop，不用 LangChain

- **形态**：Python 单进程 loop（`while not done: perceive → reason(act) → validate → execute → log`），Pydantic 定义每个角色的输入输出 schema，LLM 只负责 schema 边界内的结构化填空（function calling / JSON mode）。
- **心智模型**：π Agent SDK 同款（面试官亲口确认我熟练）——系统 prompt 注入 → 推理 → tool calling JSON → 运行时抽出来执行 → 结果回填 → 下一轮。代码里注释直接写明这个对应关系。
- **LLM provider**：OpenAI 兼容接口抽象层（`llm.py` 一个 `call(messages, schema)` 函数），可切 GLM/GPT/Claude——对位我的多 runtime 调度经验。默认 GLM（当前环境即可用），成本每轮 < ¥1。
- **为什么不用 LangChain**（报告写、面试也说）：题目明说"不要求复杂框架"；LangChain 的自由度正是明度不要的"大模型自由发挥"；自研 loop 让每一步可埋点、可校验、可回放——这是事件流的前提。

### 1.5 审计内核：精简版事件流（Harness Anything 机制移植）

```
events.jsonl          # append-only 事件流（唯一事实源）
  ├─ round.started / agent.thought / tool.called / tool.result
  ├─ proposal.validated / proposal.rejected(+理由) / oracle.queried
  └─ decision.made(chose=X, rejected=[Y,Z]+理由) / round.completed
sqlite 投影            # 事件流物化 → 查询"第2轮为什么推荐 39V→I"
replay.py             # 输入 round_id → 按时间序重放全部事件 → 渲染推理时间线
```

约 150 行代码。这是**差异化命门**：题目要求展示推理过程（3.d.iv）与失败案例（2.vii），别人靠打印 log，我靠可查询、可重放的事件存储——且直接对位明度 GMP audit trail 需求。

### 1.6 前端 demo：Streamlit 单页

输入 WT 序列（预填 GB1）→ 一键跑 3 轮虚拟进化 → 展示：① 每轮 Top-k 突变卡片（含推荐理由）② fitness 逐轮曲线（4 方法对比）③ **事件流时间线回放组件**（点击任一轮展开 Agent 推理步骤）④ 位点热力图。备选 Gradio；皮肤找开源 Streamlit 模板（我有 Copilot 类项目前端经验，外壳不是风险点）。

### 1.7 技术栈清单

```
Python 3.11 / pandas / numpy / scikit-learn / xgboost / pydantic / networkx(轻量图谱)
streamlit / matplotlib / biopython(仅序列工具)
LLM: OpenAI 兼容 API（GLM 默认，可切）
数据: FLIP GB1（J-SNACKKB/FLIP github）
硬件: 全程 CPU，笔记本即可
```

---

## 2. 模块拆解（对位题目六大任务）

### M1 数据层 `data/`（题目任务一）

- `download_gb1.py`：拉取 FLIP splits + 预提取 embedding，校验 SHA，注明来源（题目 3.a.⚠️ 要求注明外部资源）
- `mutations.py`：突变解析（`39V` → 位点 39、WT 残基 V、替换残基）；序列重建（WT + 突变列表 → 变体序列）；Biopython 校验非法氨基酸/终止密码子——**知识规则的第一个执行点**
- `pools.py`：构造三个池——`train_pool`（已完成的第 0 轮实验，分层抽样 5k）、`query_pool`（虚拟湿实验库）、`holdout`（最终评估，Agent 全程不可见）
- 产出：数据统计图（fitness 分布 × 突变数）、split 表

### M2 适应度模型 `models/`（题目任务二）

- `baselines.py`：L1/L2/L3 梯子，统一接口 `fit(pool) → predict(variants) → (mean, var)`
- `uncertainty.py`：deep ensemble 方差 + UCB 主动选择分数
- `evaluate.py`：Spearman/Pearson/MSE/Top-k 命中率，输出指标表 + 预测-真值散点图
- **Agent 友好接口设计**（我的 SDK 封装经验直接复用）：predict 的报错不是裸 traceback，而是结构化错误——`{error: "变体含非法残基 X", hint: "检查突变位点 39 是否超出 WT 长度 56", valid_range: [1,56]}`——**报错即指引**，写进报告作为 Agent 工具设计原则

### M3 科学智能体 `agent/`（题目任务三，核心）

五角色对位题目 3.c，但每一块都是"积木"——LLM 的自由度被 schema 和校验器双层圈死：

| 角色 | 实现 | LLM 参与度 | 积木约束 |
|---|---|---|---|
| Data Analyst | 纯代码：池统计、位点收益分析（每位点 top 变体 vs WT 的 Δfitness）、突变谱系聚类 | 0%（确定性工具） | 输出固定 schema 的 `SiteReport` |
| Hypothesis Generator | LLM 读 `SiteReport` + 知识库检索结果，产出假设列表 | 高（这是 LLM 该干的） | Pydantic `Hypothesis{site, from_aa, to_aa, rationale, rule_refs[]}`；rationale 必须引用规则 ID，否则校验拒绝 |
| Mutation Designer | 纯代码组合器：单点/双点/多点组合生成、去重、预算控制 | 0% | 突变数 ≤4、禁 Pro/Gly 入螺旋区（规则库）、历史优质单点优先组合 |
| Fitness Evaluator | M2 模型调用 + 不确定性 | 0% | (mean, var) 结构化返回 |
| Scientific Critic | 规则校验器（代码）+ LLM 复核（低温度）：合理性、多样性、组合冲突（上位性风险） | 中 | 每条提名必须有 `{score, rule_check_passed, critic_note}` 三件套才可进入推荐 |

- `loop.py`：主循环（感知→假设→设计→评估→批评→提名→记事件）
- `llm.py`：provider 抽象（1.4）
- **约束化的可视化表达**：报告放一张图——"LLM 自由区（着色）vs 确定性积木区（灰色）"，LLM 只在假设生成和 critic 复核两处出现。这张图就是面试官"笼子里的大模型"的直观版

### M4 知识增强 `knowledge/`（题目任务四）

**三层结构——直接同构明度 SOP 多级 schema 拆解**（这是命中面试官审美的关键设计，报告里明说）：

| 层 | 内容 | 同构 |
|---|---|---|
| 业务级 schema（科学规则层） | `rules.yaml`：① 氨基酸性质表（20aa × 疏水/电荷/体积/极性）② BLOSUM62 分级（保守/半保守/激进替换）③ 突变数上限 4 ④ 禁引入终止/非常见 aa ⑤ 单轮突变数递增策略（探索期允许 4 点，收敛期 ≤2）⑥ 历史优质单点优先组合 | SOP 业务级 schema（"放桌上不超 10 分钟"） |
| 实现级 schema（校验器层） | `validators.py`：每条规则的确定性检查函数，拒绝时返回结构化错误 + 指引（报错即指引） | SOP 实现级 schema（YOLO/DINO 检测实现） |
| port 机制（可替换评估器） | `FitnessEvaluatorPort`：接口固定，实现可换 Ridge/XGB/MLP/ensemble——选哪个模型是配置不是代码 | 面试官原话 port："检查在不在是一个 port，YOLO/DINO 来 fill" |

- 轻量知识图谱（加分项）：networkx 三元组（`AA–has_property–Hydrophobic`、`Mutation–occurs_at–Position`、`Mutation–improves–Fitness`、`Variant–contains–Mutation`），CSV 存储，demo 里渲染查询结果。**不上 neo4j**——4 天期限里任何运维负担都是自杀
- **消融开关** `--no-knowledge`：跑同一循环，对比有/无知识增强的提名差异（题目 4.f 硬性要求）

### M5 虚拟定向进化 `evolution/`（题目任务五）

- `campaign.py`：DBTL 循环
  - **实验预算叙事**：每轮 96 变体（96 孔板——药物行业面试官秒懂的隐喻，报告就用这个表述）
  - 轮 0：train_pool 即已完成实验
  - 轮 N：Agent 提名 → 模型打分 → 选 96 → 虚拟湿实验（query_pool 查真值，未命中用 ensemble oracle 并标注 `source=model`）→ 回流 train_pool → 重训模型 → 下一轮
  - 共 3 轮（题目要求 2-3 轮，做满 3 轮）
- `strategies.py`：**四策略对比**（题目 5.c 硬性要求，也是报告主图）
  1. 随机突变（基线）
  2. 适应度模型直接推荐（greedy top-96 by mean）
  3. LLM Agent 推荐（无知识库）
  4. 知识增强 LLM Agent 推荐（完整版）
  - 主指标：每轮 top-10 真实 fitness 的最大值与均值（"这一轮实验最好的孔有多好"）；辅指标：Top-k 命中率、位点集中度
- 主动学习加分项：策略 4 内部用 UCB（mean + λ·√var）平衡开发/探索，报告单列一节

### M6 展示层 `app/` + 报告（题目任务六）

- Streamlit 四区布局（1.6）
- PDF 报告 3-5 页，**章节逐字对位题目 3.a.i–viii**：背景与问题定义 / 数据集 / 适应度模型 / Agent 设计（含 LLM 自由区图）/ 知识增强（含三层 schema 同构表）/ 虚拟实验结果（四策略主图）/ **失败案例分析** / 改进建议
- 失败案例从事件流里直接捞（`proposal.rejected` + 推荐后 fitness 下降的轮次），三选一深挖：① 上位性误判（单点都好、组合崩）② 外推失败（two_vs_many 的 3-4 点突变区模型塌方）③ LLM 幻觉提名被校验器拦截的实例——第 ③ 类是"积木约束生效"的正面证据，面试最爱
- 报告末节讨论题目灵魂拷问（"Agent 是否真学到科学家思维"）：用消融数据回答——预期策略 3 与 2 差距小（LLM 增益有限），策略 4 与 3 差距来自规则而非推理；**诚实结论：当前 Agent 的价值是"把科学家流程结构化"，不是"复现科学家直觉"**。这个自省本身就是面试官想要的答案（考核重点最后一条）

### GitHub 仓库结构

```
ai4s-directed-evolution-agent/
├── README.md            # 环境/数据来源/运行命令/主要结果表（题目 3.b.c）
├── data/                # 下载脚本 + 缓存（不入库，.gitignore）
├── knowledge/           # rules.yaml + 图谱 csv + validators
├── models/  agent/  evolution/  app/
├── events/              # 事件流样例（入库，供面试官直接翻看）
├── reports/report.pdf
└── Makefile             # make data / train / campaign / demo 四命令复现
```

---

## 3. 差异化叙事：五张牌，每张对位面试官原话

面试官 9/5 的提问路径 = 他们的关注排序：**schema 设计 → 事件流/审计 → 可控性 → provider 抽象**。方案五张牌严格按此排序打出：

**牌 1 · 事件流审计内核**（对位原话："不光是事件流……要审计、被记录、防篡改、可回放""GMP audit trail"）
- 每个推荐方案冻结时算内容哈希写入事件（`proposal.frozen{hash}`）——对应"每个环节都要冻结、签名"
- 报告措辞：*"事件流是执行的表达；推荐方案的哈希冻结是产出的签名。这套机制在医药行业叫 audit trail，在我的开源项目 Harness Anything 里叫 WAL + 事件溯源。"*
- demo 里时间线回放组件让面试官亲手点——可回放不是报告里的一句话，是能摸的

**牌 2 · 约束化积木 = SOP schema 同构**（对位原话："可控的小积木块""过程可以随意，产出必须严格合规""多级 schema 拆解 + port"）
- M4 三层结构直接照着面试官描述的 SOP 架构搭：业务级规则（科学约束）→ 实现级校验器（代码）→ port（可替换评估器）
- 报告措辞：*"知识库不是 prompt 里的一段文字，而是一组多级 schema：科学规则层声明'什么合法'，校验器层执行'拦下什么'，port 层允许评估器像换 YOLO/DINO 一样换模型。LLM 在两处受控出现，其余全是确定性积木。"*
- 这一牌的效果：面试官看报告目录的瞬间就认出这是他们的思路——**同构感 > 一切技术炫技**

**牌 3 · Agent 友好的工具封装**（对位我工业建模 SDK 经验：切面拦截/报错即指引/动态上下文注入）
- M2 的结构化报错 + hint；M3 校验器拒绝时返回"它不能做什么 + 能做什么列表"——和我在工业 SDK 里做的动态上下文注入是同一件事
- 报告单列一小节"Tool Ergonomics"：Agent 的成功率一半取决于工具的报错设计

**牌 4 · Provider 抽象 = 多 runtime 经验**（对位原话："Py 的这套 loop 你看过吗"——他考过 loop 细节）
- `llm.py` 的 OpenAI 兼容抽象 + 报告架构图注明"LLM 可换 provider，循环结构不变"——多 runtime 调度经验的微缩展示
- 面试若追问 loop 细节，代码里注释就是标准答案（system prompt 注入 → reasoning → tool call 抽取 → 执行 → 回填 → 终止检测）

**牌 5 · 决策留痕的失败分析**（对位题目 2.vii + 我的 fact/decision/task 三元语）
- 事件流里每个 `decision.made` 记录 chose/rejected + 理由——失败分析不是事后回忆，是查询留痕
- 报告措辞：*"我选择了什么、拒绝了什么、为什么——这是我的开源 harness 里 decision 实体的最小实现。"*

**叙事红线**（反面清单）：
- 绝不吹"Agent 学到了科学家思维"——题目末问就是在钓这个，用消融数据给诚实答案
- 绝不堆 LangChain/LangGraph 名词——面试官明确反感应框架味
- 绝不隐瞒外部资源：FLIP 数据、预提取 embedding、LLM 辅助全部在报告声明（题目明文要求，也是医药合规气质的展示）
- 蛋白知识点到为止：报告里的生物学表述（GB1 功能、BLOSUM 含义、上位性）以 FLIP/教材口径为准，不自由发挥

---

## 4. 四天开发计划

### 4.0 里程碑定义

- **M-Thu**：数据管线全通，第一张图出炉
- **M-Fri**：模型指标表定稿（含不确定性）
- **M-Sat**：四策略 3 轮虚拟实验全通 + 事件流可回放 ← **最重的关卡**
- **M-Sun**：demo + 报告 + 提交，15:00 冻结

### 4.1 周四晚（9/10，~3h）：数据层 + 骨架

- [ ] GitHub 建仓（私有，周日交前转公开），初始化目录结构 + README 骨架
- [ ] `download_gb1.py`：FLIP splits + 预提取 embedding 下载、校验、缓存（**今晚必须完成——数据风险前置清零**，失败立即启动备胎 AAV/ProteinGym）
- [ ] `mutations.py` + `pools.py`：解析、分层抽样、三池构造
- [ ] 出图：fitness 分布 × 突变数直方图（报告图 1 直接用）
- [ ] venv + requirements.txt 冻结

### 4.2 周五（9/11，全天）：模型梯子 + 知识库

- 上午：L1 one-hot Ridge → L2 ESM+Ridge → L2.5 XGBoost，统一接口；`evaluate.py` 指标全家桶
- 下午：L3 MLP + 5-seed ensemble 方差；holdout 上定稿指标表（报告表 1）
- 晚上：`rules.yaml`（氨基酸性质表 + BLOSUM 分级 + 全部规则）+ `validators.py` 校验器 + 三元组图谱 CSV
- 验收：`make train` 一键复现；指标表截图进调研文件夹

### 4.3 周六（9/12，全天）：Agent + 事件流 + 虚拟实验 ← 关键日

- 上午：`events.py` 事件流内核（append-only + sqlite 投影 + replay，~150 行）+ `llm.py` provider 层
- 下午：M3 五角色积木 + `loop.py` 主循环；先跑通**策略 3**（无知识库 LLM Agent）单轮
- 晚上：`campaign.py` 四策略 × 3 轮全部跑通；`replay.py` 验证可回放；主图（四策略 fitness 逐轮曲线）出炉
- 风险预案：LLM API 不稳 → 降级为"假设生成用检索规则拼接 + LLM 离线批产"模式（提前把 Hypothesis Generator 的 prompt 缓存成离线响应文件）；时间爆 → 策略 3 的轮次降到 2 轮

### 4.4 周日（9/13）：demo + 报告 + 提交

- 上午：Streamlit 四区 demo（外壳周五晚找好模板）；录制 2 分钟演示视频（防 demo 环境翻车）
- 中午：写报告（Markdown → PDF，LaTeX 模板或 Typora 导出；3-5 页卡上限用信息密度填，不注水）；失败案例从事件流捞取定稿 3 例
- 14:00：README 完整化（环境/来源/命令/结果表）；仓库转公开；最终检查清单：报告八章节对位 ✓ 外部资源声明 ✓ 复现命令跑一遍 ✓ 事件流样例入库 ✓
- **15:00 硬冻结**：之后只改错别字。提交渠道按笔试通知执行

### 4.5 砍单顺序（预定义，执行时不犹豫）

1. 知识图谱可视化砍掉（CSV + demo 表格展示保底）→ 图谱三元组本身保留（题目加分项点名）
2. GP 不确定性 → 已用 ensemble 替代（等效加分）
3. demo 降级为"录屏 + 事件流翻页静态页"
4. 策略对比从 3 轮降到 2 轮（题目下限）
5. **永不砍**：事件流回放、失败案例分析、四策略对比、外部资源声明——前两个是差异化命门，后两个是题目硬性要求

---

## 5. 风险登记簿

| 风险 | 概率 | 缓解 |
|---|---|---|
| FLIP 下载失败 | 低 | 双仓库源（J-SNACKKB/FLIP + protein-uq）+ AAV 备胎，周四晚前置排雷 |
| LLM API 不可用/超时 | 中 | 离线批产模式（4.3）；provider 抽象随时切换 |
| 策略 4 不敌策略 2（Agent 无增益） | 中 | **这不失败，是报告素材**——题目 5.d 就在问这个；转成"LLM 增益边界"分析章节 |
| ESM 预提取 embedding 与本地变体对不上 | 低 | 用 FLIP 原生变体集，不自造变体做预测输入 |
| 周六事件流+循环延期 | 中 | 周六晚 21:00 检查点未达 M-Sat → 立即触发砍单 1+4 |

---

## 附：题目要求 ↔ 方案模块对照表（自查用）

| 题目任务 | 模块 | 交付物 |
|---|---|---|
| 1 数据选择处理 | M1 | 三池构造 + 分布图 + split 表 |
| 2 适应度模型 | M2 | 指标表 + 散点图 + 不确定性 |
| 3 Agent 设计（五功能五角色） | M3 | loop + 自由区/积木区架构图 |
| 4 知识增强 + 消融 | M4 | 三层 schema + `--no-knowledge` 对比 |
| 5 虚拟实验 2-3 轮 | M5 | 四策略 × 3 轮主图 |
| 6 结果展示 + 失败分析 | M6 | demo + 报告八章节 |
| 加分：主动学习/不确定性/图谱/交互 demo/自动化对接 | M5/M4/M6 | UCB、ensemble 方差、三元组、Streamlit、报告改进节讨论"接 Opentrons/移液工作站即闭环" |
