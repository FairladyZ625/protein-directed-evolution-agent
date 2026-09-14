# AI4S 试题逐条覆盖度审计

> **⚠️ 勘误(2026-09-14)**:本审计写于 2026-09-12 19:36 之前,其中两条判定已被当日晚间的提交推翻,文档未随之更新:
>
> - **E5 / H51 / B05**(「`build_knowledge_graph` 除定义与导出外唯一调用在 `tests/test_knowledge.py`,生产 `agent/`、`evolution/`、`app/` 无调用」) → `ccb8b68`(09-12 21:03)起生产在用:`agent/auto_researcher.py:488` 构建图、`:491-505` 查询 `query_mutation_context` 生成 graph rationale,另有 `:694-705`、`:765-786` 的消费者。该条的「未接线」缺口判定**不再成立**。
> - **E10 / H14 / H15 / H45 / H50 / D4**(「主 GB1 campaign 固定传 `no_knowledge=True` 且未注入 `llm_critic`,Critic 空转」) → `2366506 fix: make four-strategy campaign auditable`(09-12 21:32)起,`evolution/campaign.py` 在 `use_llm` 时显式传入 `llm_critic=_llm_critic(llm_state)`,并以 strategy 区分 `no_knowledge`。
> - **E2** 的 `38 passed in 6.88s` 对应 09-12 的测试树;2026-09-14 CEO 原样复跑同一条七文件命令实测 `79 passed, 1 warning in 24.31s`(独立评审同日测得 `79 passed ... 24.61s`,承重的是 **79** 这个数,秒数差属墙钟抖动)。原写「78 passed in 27.27s」为误,已更正。引用该数字时须标明运行时点。
>
> 受影响的是上述条目及其汇总计数(缺口数被高估——把已接线能力误判为未接线)。其余条目未受影响,例如 **D2**(主 GB1 campaign 使用 `evolution/campaign.py` 的 80 维 one-hot)与 **D5**(入口一致性风险)仍然成立。


> 审计日期：2026-09-12。验收标尺为 `lab/context/research/AI4S-assignment.md`；仓库锁定口径以 worker handbook 的 D1–D5 为准。状态只采用“已交付 / 部分交付 / 存在但未接线 / 未做”。本报告只记录本次从磁盘、Git 索引和真实命令观察到的证据，不把已有报告的自述本身当作实现证据。

## 1. 本次工具证据

| ID | 命令 / 检查 | 本次真实结果 |
|---|---|---|
| E1 | `.venv/bin/python` 读取 `data/four_mutations_full_data.csv` 与三池 CSV | 原表 `(149361, 17)`；WT `VDGV=1.0`；最大 `FWAA=8.76196565571`；train/query/holdout 为 `5000/50000/94361`，两两交集为 0，并集 149361。 |
| E2 | `.venv/bin/pytest -q tests/test_data_pipeline.py tests/test_agent.py tests/test_campaign.py tests/test_knowledge.py tests/test_events.py tests/test_demo_app.py tests/test_pool_campaign.py` | 09-12 实测 `38 passed in 6.88s`；**2026-09-14 同命令复跑为 `79 passed, 1 warning in 24.31s`**（测试树此后增长，两者不是同一基线，不可互相背书）。这是定向单元/集成验证，不等于全 CI 或外部 API 实跑。 |
| E3 | `.venv/bin/pytest -q tests/test_events.py::test_append_hash_chain_and_verification tests/test_events.py::test_tampering_is_detected_at_changed_event` | 阳性链校验与篡改阴性对照均通过：`2 passed in 0.02s`；篡改用例预期在 seq=2 报错，见 `tests/test_events.py:59-66`。 |
| E4 | `pdfinfo` / `shasum -a 256` 复核受控 PDF（**2026-09-14 重测**） | **原记「PDF 存在、A4、4 页、内容仍是旧 GB1 主叙事」已作废**：`harness/final-report/report.pdf` 与 `reports/final-report-v0.7/scientific_report_v0.7_two_column.pdf` 的 sha256 **同为 `30b9173739beaea3ef0efd1746cd186cfacba9ae15203ad450ab4f7b2cb6c321`**，即受控 PDF 已被替换为 v0.7 真源的产物，`pdfinfo` 与独立正则计数双仪器一致实测 **44 页**，真源 `report.md` 与该 PDF 均已被 git 跟踪。那份 4 页 PDF 是另一个文件 `reports/report.pdf`（sha256 `e3180e58…`，仍在仓内、仍被跟踪，但 README 已不再链接它）。 |
| E5 | `rg -n 'build_knowledge_graph' --glob '!**/.worktrees/**' .` | **已接线（2026-09-14 更正）**：`ccb8b68`(09-12 21:03) 起 `agent/auto_researcher.py:488` 在生产路径构建图、`:491-505` 经 `query_mutation_context` 生成 graph rationale，另有 `:694-705`、`:765-786` 的消费者。本审计写作时（09-12 19:36 前）确实只有 `tests/test_knowledge.py` 调用，故原判定「生产无调用」已不成立。 |
| E6 | `rg -n 'no_knowledge|guardrail' agent evolution app tests --glob '*.py'` + 读取 AAV 指标 | GB1 有 `agent_no_knowledge`/`knowledge_agent`；**「AAV 无同协议 `no_knowledge` 对照」一条已于 2026-09-14 作废**：`lab/reports/knowledge-ablation/metrics.json` 是真正的单因子消融——固定 `seeds=[0,1,2]`（配对）、`budget_per_round=48`、`n_rounds=6`、`cold_start=HD<=2`、同一源池、`surrogate=EpistasisRidgePredictor`、`oracle=measured-table lookup after nomination`，**处理变量只有知识门禁+图谱**（无知识组跳过 HD/BLOSUM 门禁与图谱，知识组施加 `HD<=4 && mean BLOSUM62>=0` 并查询仅由已测变体构成的图谱；该门禁属处理变量，不是两组共有条件）。原判定所依据的 v0.1/v0.2/v0.4 确实非单因子匹配，那部分仍成立，但它不再等于「缺对照」。详见 H21。 |
| E7 | 读取 `features/cache/*.npz` shape，并以 `git ls-files features/cache` 核对 | 已提交缓存覆盖 GB1 评测所需的 5000、2168、两个 2000 样本块，均为 1280 维；149361 全表缓存只有 one-hot 80 维。另一个 38265×1280 文件当前未跟踪，不能算 GitHub 交付。 |
| E8 | `git remote -v`、`git ls-files`、README 全内部链接存在性批量核验、`python -m models.train_ladder --help` 实跑（**2026-09-14 重测**） | origin 为公开 GitHub URL。**原记的两条指控均不成立、已作废**：①「README 链接不存在的 `reports/report.pdf`」——该文件**存在**（4 页、已跟踪），且 README **根本不链接它**；README:11-12 链接的是 `reports/final-report-v0.6/scientific_report_v0.6_two_column.pdf`，且 README 的内部链接经批量核验 **7/7 全部可解析**（含 `reports/final-report-v0.6/v07-handoff-02-protocol-and-chapter8.md`，17512 bytes）。②「`make train` 指向无 CLI 入口的 `models/train_ladder.py`」——该模块有 `argparse`(:4)、`main()`(:384)、`--feature {one_hot,esm2}`(:386)、`__main__`(:394)，实跑 `--help` 正常输出 usage（阳性对照），Makefile:19 的 `python -m models.train_ladder --feature one_hot` 是**正确调用**。**真实缺口只剩一条**：README 报告入口指向 v0.6，而当前交付版是 v0.7。 |
| E9 | 读取 `campaign_hard.metrics.json` / `campaign_llm.metrics.json` | 两者均为 149361 提名空间、3 轮、四策略、真实查表 oracle；LLM 记录中部分轮次为 `fallback`，部分为 `llm:claude-sonnet-5`。 |
| E10 | 代码双侧核对 `evolution/campaign.py` 与 `agent/pipeline.py` | **已注入（2026-09-14 更正）**：`2366506 fix: make four-strategy campaign auditable`(09-12 21:32) 起，`evolution/campaign.py` 在 `use_llm` 时显式传入 `llm_critic=_llm_critic(llm_state)`，并以 strategy 区分 `no_knowledge`（不再固定 `True`）；`agent/pipeline.py:103-112` 走结构化 Hypothesis 路径。原判定「固定 `no_knowledge=True` 且未注入 `llm_critic`、Critic 空转」是本审计写作时的状态，现已不成立。 |

## 2. 第二章“项目任务”逐条审计

| 编号 | 试题条目（原文摘要） | 出处 | 状态 | 证据 | 差距与最小补齐动作 |
|---|---|---|---|---|---|
| H01 | 使用公开定向进化/突变效应数据集 | 二·数据 a | 已交付 | `data/README.md:3-8`；`data/download_gb1.py:20,50-51`；E1 | 无。 |
| H02 | 选择具体蛋白质优化任务 | 二·数据 b | 已交付 | `README.md:1-4` 定义 GB1 结合适应度；`reports/final-report-v0.3/report.md:7-11` 定义预算池式优化 | 无。 |
| H03 | 整理 WT、突变序列、位点、fitness | 二·数据 c | 已交付 | `evolution/mutations.py:9-11`；原表含 `Variants/HD/Fitness/sequence`；E1 | 无。 |
| H04 | 划分训练、验证、测试，模拟已完成与未知候选 | 二·数据·独立条目 | 部分交付 | `features/pools.py:19-26,45-60` 和 E1 证明 train/query/holdout 三池隔离；`models/evaluate_all.py:36-39` 只消费 train/query 或 HD train/test | 主评测没有显式 validation 的训练/调参职责；原 CSV 虽有 legacy `*_validation` 列，但当前训练入口未消费。最小动作：在当前协议中明确 train/validation/test(query/holdout) 角色并让训练/选模代码实际读取 validation。 |
| H05 | 建立 baseline 适应度预测模型 | 二·预测模型 | 已交付 | `models/train_ladder.py:38-54,129-151`；`lab/reports/workflow-v1.0/gb1/predictor_ladder.json` | 无。 |
| H06 | 用 Spearman/Pearson/MSE/Top-k 等评估 | 二·预测模型 | 已交付 | `models/train_ladder.py:153-161`；产物含四类指标；E2 | 无。 |
| H07 | 分析能否识别高-fitness 变体 | 二·预测模型 | 已交付 | `reports/final-report-v0.3/report.md:31-42,97`；GB1/AAV 排名与 Top-k 产物 | 无；最终文稿应保留“不宣称统计显著”的边界。 |
| H08 | 设计 LLM Agent 模拟定向进化科研流程 | 二·科学智能体 a | 已交付 | `agent/auto_researcher.py:244-322` 为商业模型工具调用循环；E9 有真实 LLM 轮次记录 | 明确区分 live LLM 与 fallback，不能把整条轨迹笼统写成 LLM。 |
| H09 | 读取当前实验数据和 top variants | 二·科学智能体 b-i | 已交付 | `agent/auto_researcher.py:137-156`；`agent/pipeline.py:48-61` | 无。 |
| H10 | 总结可能有益的突变位点 | 二·科学智能体 b-ii | 已交付 | `agent/auto_researcher.py:143-152`；`evolution/campaign.py:100-124` | 无。 |
| H11 | 提出下一轮候选突变序列 | 二·科学智能体 b-iii | 已交付 | `agent/pipeline.py:63-101`；`evolution/campaign.py:182-213` | 无。 |
| H12 | 调用适应度模型给候选打分 | 二·科学智能体 b-iv | 已交付 | `agent/pipeline.py:103-108`；`evolution/campaign.py:186-190` | 无。 |
| H13 | 按预测结果选择 Top-k | 二·科学智能体 b-v | 已交付 | `evolution/campaign.py:205-213`；每轮产物含 top10，E9 | 无。 |
| H14 | 给出推荐理由 | 二·科学智能体 b-vi | 部分交付 | `agent/pipeline.py:18-21,67-70` 有 `rationale/rule_ids`；事件可回放 | **Critic 那一半已修**（见 E10 更正）：`evolution/campaign.py:243` 在 `use_llm` 时注入 `llm_critic`，`:171-200` 带 `critic_source`/`critic_fallbacks`/`critic_error` 的显式记账（失败一律落确定性回退并留痕），`:407` 把 `llm_critic_source` 写进每行产物。**剩余缺口只有逐候选理由**：`:132-133` 与 `:162-163` 传入的 `rationale`/`rule_ids` 是批次级固定模板串（如 “Top observed substitutions per site under R-GB1-SITES / R-MAX-MUTATIONS.”），不是逐候选推理。最小动作缩为：把候选级 evidence 与规则命中写入真实主跑事件。 |
| H15 | 模块化角色：分析—假设—设计—评估—批判 | 二·科学智能体 c | 已交付（2026-09-14 更正） | 五类实现见 `agent/pipeline.py:48-123`；角色事件测试 `tests/test_agent.py:96-108` 通过 | 结构齐全；原记「主 GB1 campaign 的 Critic 被 `no_knowledge=True` 空转且无 `llm_critic`」已由 `2366506` 修掉（见 E10 更正），该最小动作**已完成**。状态列 2026-09-14 随之由「部分交付」改为「已交付」——此前状态列与本行正文自相矛盾，独立评审指出此点成立。 |
| H16 | 构建小型知识库/突变规则库 | 二·知识 a | 已交付 | `knowledge/rules.yaml:1-41`、`knowledge/validators.py:20-56`；E2 | 无。 |
| H17 | 氨基酸疏水性、电荷、大小、极性 | 二·知识 b-i | 已交付 | `knowledge/rules.yaml:2-22` | 无。 |
| H18 | 保守替换与激进替换 | 二·知识 b-ii | 已交付（2026-09-14 更正） | `knowledge/rules.yaml`；`tests/test_knowledge.py:19-36` | 最小动作两半均已完成：①`5a926f8` 换入完整 BLOSUM62——2026-09-14 CEO 复跑本仓审计 runner 实测 `unordered_pairs=190, missing_pairs=0, zeros_lost=[]`——**完整命令为 `PYTHONPATH=. .venv/bin/python lab/context/research/kb-audit-evidence/audit.py`**(本格原先只给脚本路径、漏了 `PYTHONPATH=.`,独立评审照此执行撞 `ModuleNotFoundError: No module named 'knowledge'`,该报错是本文档命令写漏所致、不是脚本或环境问题,2026-09-14 补齐)；②失败用例已存在 `test_blosum62_is_complete_and_classifies_zero_score_as_neutral`：它断言 400 项齐全与矩阵对称，并用一个非对称 fixture（`{"A": {}, "G": {"A": 0}}`）专打「只有反向存在的零分查表」这条路径，断言 CONSERVATIVE 不过、AGGRESSIVE 过。原「未知配对会跳过分类」的缺口已不存在。 |
| H19 | 限制突变数、拒绝 stop/异常、避免一次过多 | 二·知识 b-iii/iv/v | 已交付 | `knowledge/rules.yaml:35-40`；`knowledge/validators.py:35-50`；拒绝用例 `tests/test_agent.py:130-151` | AAV 与 GB1 的坐标/上限应分配置，避免复用 GB1 硬编码。 |
| H20 | 优先组合历史上较好的单点突变 | 二·知识 b-vi | 已交付 | `evolution/campaign.py:100-124` 按观测均值取每位点 top 替换并组合 | 无。 |
| H21 | 比较有无知识增强时推荐差异 | 二·知识·独立条目 | 已交付（2026-09-14 更正） | `lab/reports/knowledge-ablation/{metrics.json,report.md}`；GB1 侧仍见 `evolution/campaign.py:46,284-287`、`tests/test_campaign.py:67-72`、E9 | AAV 同协议消融已存在且是真正的单因子设计：`metrics.json` 的 `protocol` 块固定 `seeds=[0,1,2]`（配对）、`budget_per_round=48`、`n_rounds=6`、`total_budget=288`、`cold_start=HD<=2`、同一源池、`surrogate=EpistasisRidgePredictor`、`oracle=measured-table lookup after nomination`、`max_hd=4`、`blosum_min=0.0`，唯一处理变量是知识门禁+图谱。配对结果：strong 均值 **54.0 → 162.3**（逐 seed 差 +111/+107/+107）、`cum_top10_max` **6.1862 → 6.5309**（每 seed 均 +0.3447）、平均 HD **8.7095 → 3.4132**、推荐集合平均 Jaccard 仅 0.1077。**边界必须同时申明**：两组达峰率均为 **0/3**（都没碰到池峰 8.4162），故这是「strong 产量」的正结果、不是「找峰」的正结果；且该次 `llm_requested=True` 而 `model=None`、36/36 agent 轮次全超时、完成实验的 LLM 轮次为 0，因此它证明的是 **agent harness + 知识处理**的差异，**不能**声称观察到 LLM 推理的因果增益。自带阴性对照通过（打乱标签 CV 0.0254 对实测 0.9059，判据 `observed>0.8 且 |shuffle|<0.1`）。 |
| H22 | 已有训练数据作为第一轮实验结果 | 二·虚拟实验 a | 已交付 | GB1 `evolution/campaign.py:250-256`；AAV `agent/auto_researcher.py:64-72` | 无。 |
| H23 | Agent 基于当前数据提出下一轮候选 | 二·虚拟实验 b | 已交付 | `evolution/campaign.py:258-272` 每轮用更新后的 train；AAV `agent/auto_researcher.py:289-322` | 无。 |
| H24 | 用测试真值或预测模型作为虚拟实验评估器 | 二·虚拟实验 c | 已交付 | `evolution/campaign.py:16,270-272,294`；E9 为 `measured table lookup` | 无。 |
| H25 | 至少模拟 2–3 轮 | 二·虚拟实验 d | 已交付（超出） | GB1 为 3 轮；AAV 历史含 3/6/12/16 轮，E9 | 无。 |
| H26 | 观察 fitness 是否逐轮提升 | 二·虚拟实验·独立条目 | 已交付 | E9 的 `cum_top10_max_curve`；PDF 第六节曲线 | 无；应同时报告平台期/下降的阴性结果。 |
| H27 | 展示每轮 Agent Top-k 蛋白突变 | 二·结果 a | 已交付 | 每轮 JSON `top10`；`app/demo.py:171-182,430-456` 可切轮次；`reports/final-report-v0.3/evidence/gb1_top10.csv` | 无。 |
| H28 | 分析推荐是否集中在关键位点 | 二·结果 b | 已交付 | **证据锚点已于 2026-09-14 从「4 页 PDF」换为当前真源**:`reports/final-report-v0.7/report.md:155`(第 6 章 虚拟定向进化实验结果)含逐轮 Top-k 与关键位点;事件 Data Analyst 位点画像由 `app/demo.py:374-387` 展示 | 原引「4 页 PDF 第六节」指已被同名替换掉的旧工件,不能继续作证据(同 E4)。 |
| H29 | 比较随机、模型直推、LLM Agent、知识增强 Agent | 二·结果 c | 已交付 | `evolution/campaign.py:3-16,46`；E9；`tests/test_campaign.py:40-47` | 需继续清楚标注 deterministic/fallback/live LLM，避免把第 3/4 组名字当调用事实。 |
| H30 | 分析成功案例和失败案例 | 二·结果 d | 已交付 | `reports/final-report-v0.3/report.md:93-106`；原始 AAV/GB1 指标在 `lab/reports/` | 无。 |
| H31 | 讨论 Agent 是科学思维还是模型调用 | 二·结果·独立条目 | 已交付 | **证据锚点已于 2026-09-14 换为当前真源**:`reports/final-report-v0.7/report.md:342`(第 7 章 失败案例分析)与 `:399`(第 8 章)承载该讨论 | 原引「4 页 PDF 第七节」与 v0.3 行号均指已过期工件,不能继续作证据(同 E4)。 |

第二章小结（**2026-09-14 重算**）：31 个行级要求中 **29 个已交付、2 个部分交付、0 个完全未做**。两个部分项为 **H04**（validation 职责未接入当前选模协议）与 **H14**（逐候选理由仍为模板）。原写「26 已交付 / 5 部分交付，五个部分项为 H04、H14、H15、H18、H21，其中 H21 是最直接的试题硬缺口」已作废：H15、H18、H21 均已按上表逐条取证翻为已交付，H21 那句「最直接的硬缺口」随之不再成立。H28 已有旧 PDF 与 Demo 证据，当前主文稿仅需保留该能力的展示。

## 3. 第三章“详细要求”逐条审计

| 编号 | 试题条目（原文摘要） | 出处 | 状态 | 证据 | 差距与最小补齐动作 |
|---|---|---|---|---|---|
| H32 | 提交 PDF 实验报告 | 三·报告 a | 已交付（**2026-09-14 更正**） | `reports/final-report-v0.7/report.md` 与 `reports/final-report-v0.7/scientific_report_v0.7_two_column.pdf` 均已 git 跟踪；受控 `harness/final-report/report.pdf` 与该 PDF sha256 同一份，E4 | **原判「部分交付」的两条理由（PDF 是旧 GB1 版本、当前证据边界在 v0.3 真源）已被实测推翻**：受控 PDF 就是当前 v0.7 真源的产物。页数不符是独立缺口，见 H33；README 入口陈旧见 H39。 |
| H33 | PDF 为 3–5 页 | 三·报告 a | **未达标（2026-09-14 更正，方向与原判相反）** | 试题 `AI4S-assignment.md:72` 明文「a. PDF 格式，3—5 页」；实测受控/交付 PDF **44 页**（v0.7，E4），README:11 入口 **25 页**（v0.6）。**没有任何当前入口满足 3–5 页** | **原判「已交付，`pdfinfo` 实测 4 页」作废**：那 4 页指的是已被同名替换掉的旧 `harness/final-report/report.pdf`，拿它替当前 PDF 背书正是本表自己在该格内写过的禁忌（「旧 PDF 的 4 页不能替新 PDF 背书」）。本仓 `assignment-coverage-checklist.md:14,134,226` 早已判该项为硬性格式不符（高），**本表此前与之矛盾，错在本表**。裁剪技术上可行（正文八章约 15.8K 字符；附录 A–L.3 共 30 节约 40K 字符占绝大多数），但**选哪种裁剪方案属 CEO 裁决**，见 checklist:137-139 的 (a)(b)(c)。 |
| H34 | 报告含规定八节 | 三·报告 a-i…viii | 已交付 | **当前真源 `reports/final-report-v0.7/report.md` 的八节标题与试题逐条对应**：`:12` 背景与问题定义、`:21` 数据集介绍、`:63` 适应度预测模型、`:101` LLM Agent 设计、`:125` 知识增强方法、`:155` 虚拟定向进化实验结果、`:342` 失败案例分析、`:399` 改进建议与未来拓展 | 原引「旧 PDF 实测一至八节」与 v0.3 行号已于 2026-09-14 换为当前真源行号。 |
| H35 | 提交 GitHub 链接 | 三·代码 a | 已交付 | `git remote -v` 为 `https://github.com/FairladyZ625/protein-directed-evolution-agent.git`；v0.3 报告第 4 行链接 | 无。 |
| H36 | 含数据处理、训练、Agent 推理、候选生成、评估代码 | 三·代码 b | 已交付 | `data/download_gb1.py`、`models/evaluate_all.py`、`agent/pipeline.py`、`evolution/campaign.py`、`models/train_ladder.py:153-170` | 无。 |
| H37 | README 说明运行环境 | 三·代码 c | 部分交付 | `README.md:105-117` 有 venv/pip 命令；`requirements.txt` 锁版本 | README 未明确支持的 Python 版本/硬件边界，且 ESM 650M 的 MPS/CPU 成本只散落在代码/手册。最小动作：加入 Python 版本、CPU/MPS 模式和预计资源。 |
| H38 | README 说明数据来源 | 三·代码 c | 已交付 | `README.md:14-22` 含 Wu/eLife DOI 和手工放置说明 | 无。 |
| H39 | README 说明运行命令 | 三·代码 c | 部分交付 | `README.md:105-117` 有命令；E8 重测 | **原列的两条理由已作废**（`reports/report.pdf` 存在且 README 不链接它；`models.train_ladder` 有真实 CLI 入口，均见 E8）。**剩余真实缺口两条**：①README:11-12 与 `README.zh-CN.md:11-12` 的报告入口指向 v0.6，当前交付版是 v0.7；②`make data` 名称像下载但实际仅校验本地文件（Makefile:6 的注释已自陈「校验本地 GB1 数据（不下载）」，属命名误导而非功能缺失）。最小动作：README 入口改指 v0.7；`make data` 改名或在 README 明示。 |
| H40 | README 说明主要结果 | 三·代码 c | 已交付 | `README.md:24-38,65-88` | README 是旧 GB1 主叙事，与 D5 当前 revision 的 AAV 结论不一致；应在 D5 修复包同步更新，但“有说明”本项已满足。 |
| H41 | 小规模数据可复现实验流程 | 三·独立条目 | 部分交付 | 16 变体完整景观集成测试 `tests/test_campaign.py:1-53` 本次通过；E2 | 测试可复现小流程，但 README 的主命令依赖 Git 未包含的 44MB CSV，且自动下载关闭；干净 clone 的用户无法按单一命令复现主实验。最小动作：提供许可允许的小样本 fixture/下载校验器和一条真正端到端 smoke 命令。 |
| H42 | 展示 WT 与若干突变序列 | 三·结果 a | 已交付 | PDF 第二节含 `VDGV`、`FWAA`；v0.3 `report.md:17-23` 另含 AAV WT/代表序列 | 无。 |
| H43 | 展示每轮推荐 Top-k | 三·结果 b | 已交付 | 同 H27；v0.3 `report.md:75` 指向完整 `evidence/gb1_top10.csv` | 正文至少保留一张紧凑逐轮表或明确附件链接。 |
| H44 | 表格/曲线展示 fitness 提升 | 三·结果 c | 已交付 | PDF 第六节表和图；`app/demo.py:134-183,202-235`；E9 | 无。 |
| H45 | 展示 Agent 推理：重要位点、替换原因、组合原因、失败原因 | 三·结果 d | 部分交付 | 事件角色链和 Demo 由 `app/demo.py:361-417` 展示；E2/E3 | 重要位点与流程可见；「真实 Critic 空转」一条已由 `2366506` 修掉（见 E10 更正）。剩余项是候选级替换/组合理由多为模板，以及在最终报告截取至少一条真实完整链。 |
| H46 | 外部数据/模型/代码/ChatGPT 辅助需注明来源和方式 | 三·可用资源注意 | 已交付 | **证据锚点已于 2026-09-14 换为当前真源**:`reports/final-report-v0.7/report.md` 的附录 J(工程交付与复现,`:1028`)与附录 K.1–K.7(证据文件与原始来源索引,`:1065` 起)披露数据、模型、代码与语言模型辅助 | 原引「4 页 PDF 附录」与 v0.3 行号均指已过期工件(同 E4)。 |

第三章小结（**2026-09-14 二次重算**）：15 项中 **10 已交付、4 部分交付、1 未达标**。原写「10 项已交付、5 项部分交付（H32、H37、H39、H41、H45）」已作废——两项方向相反地翻转：**H32 翻已交付**（受控 PDF 已是 v0.7 真源产物，sha256 同一份），**H33 由已交付翻未达标**（44 页 / 25 页 对试题明文 3—5 页）。4 个部分项为 H37、H39、H41、H45；唯一未达标项为 **H33**。最危险的已不再是「当前真源尚未生成受控 PDF」——真源已制版且已跟踪——而是**报告页数硬性不符试题**，以及「README 入口仍指 v0.6」这一行级修复。

## 4. 第四章“考核重点”逐条审计

| 编号 | 考核重点 | 状态 | 证据 | 差距与最小补齐动作 |
|---|---|---|---|---|
| H47 | 理解定向进化基本科学流程 | 已交付 | `reports/final-report-v0.3/report.md:7-11`；代码每轮冻结候选后查标签并回填 | 无。 |
| H48 | 处理真实突变与 fitness 数据 | 已交付 | E1；`tests/test_data_pipeline.py:15-48` 本次通过 | 无。 |
| H49 | 训练合理适应度模型 | 已交付 | `models/evaluate_all.py:32-68`；predictor artifact；E2 | 无。 |
| H50 | Agent 形成假设—设计—评估—反馈迭代 | 部分交付 | `agent/pipeline.py:48-123` 与 `evolution/campaign.py:258-280` | 数据回填存在；「主跑 Critic 没执行知识/LLM 审查」一条 **2026-09-14 更正为已修**（`2366506` 起注入 `llm_critic`，见 E10/H14）。**剩余缺口只有**假设理由多为模板，按 H14 补。 |
| H51 | 合理引入氨基酸性质、规则或知识图谱 | 部分交付（差距已大幅收窄，2026-09-14 更正） | 规则与 BLOSUM 进入 acquisition；E5/E10；`agent/auto_researcher.py:492,694-705,776`；`lab/reports/knowledge-ablation/` | 原三条差距中两条已修：**BLOSUM 已完整**（190/190，见 H18）、**图谱已进主链**（生成 rationale 并以 `agent.tool.knowledge_graph` 事件落盘，真实产物记 `knowledge_graph_enabled=True`，见 B05）；理化属性也已作为 `R-PHYSICOCHEMICAL` 具名规则出声。**剩余缺口只有 AAV/GB1 语义混用与跨蛋白规则硬编码**（`R-GB1-SITES` 仍写死 39/40/41/54，见 H19），清理工作另挂 `task_ff24b0e33edb3412f4dd070e4b`。 |
| H52 | 通过实验比较证明 Agent 作用 | 部分交付（差距收窄，2026-09-14 更正） | GB1 四策略同预算对比存在，E9；AAV 见 `lab/reports/knowledge-ablation/`（3 配对 seed 同协议消融） | 「AAV 缺严格知识消融」一条**已修**（见 H21：单因子、3 配对 seed、带阴性对照与锚点复现）。**剩余缺口**：GB1 侧仍为单 seed、LLM/fallback 混合；且消融那次 36/36 agent 轮次超时、LLM 轮次 0，固定采集函数（UCB β=3）仍胜过 FULL LLM。故当前可证明「agent harness + 知识处理」的差异，**仍不能**证明通用 LLM 推理增益。补 GB1 侧多 seed 与一次 LLM 真正完成的对照。 |
| H53 | 分析失败原因，不只展示成功 | 已交付 | `reports/final-report-v0.3/report.md:93-106` | 无。 |

## 5. 第五章“加分项”单独审计

| 编号 | 加分项 | 状态 | 证据 | 差距与最小补齐动作 |
|---|---|---|---|---|
| B01 | 主动学习或强化学习选下一轮 | 已交付 | `evolution/pool_campaign.py:142-188` 每轮重训并从未测池选样；AAV `agent/auto_researcher.py` 同类 | 已由主动学习满足，不需要为凑项另做 RL。 |
| B02 | 不确定性估计（GP/集成） | 已交付 | `models/train_ladder.py:18-36` bootstrap 方差；UCB 在 `evolution/campaign.py:206-207` | 报告应继续声明方差未校准。 |
| B03 | 比较单点、双点、多点优化效果 | 部分交付 | HD 分层/低阶外推在 `features/pools.py:29-42`，PDF 有 HD 计数 | 没有相同预算下按突变阶数的优化效果对照。最小动作：按 HD=1/2/≥3 分组报告命中率、增益和预算效率。 |
| B04 | 引入结构信息或保守位点分析 | 部分交付 | BLOSUM 保守替换先验已用；`knowledge/rules.yaml:23-39` | 这是替换保守性，不是位点保守性或结构接触；若申领此加分，至少增加有来源的位点 conservation 或结构接触特征并做消融。 |
| B05 | 知识图谱表示位点—突变—性质—fitness | 已交付：接线完成（**不申领效果加分**，2026-09-14 更正） | `knowledge/validators.py:67-83` 建图；生产消费在 `agent/auto_researcher.py:488`（构图）、`:492`（`query_mutation_context` 生成 rationale）、`:694-705`（发 `agent.tool.knowledge_graph` 事件）、`:776`（注入 `check_knowledge` 的 `scientific_critic`）；**跑批证据**：`lab/reports/v09-contract/contract-v09_reflexion-on_seed-42/agentic.metrics.json` 记 `knowledge_graph_enabled=True`，该事件名出现在全仓 11 个真实产物中 | 最小动作（在 Critic 处查询图谱并记录 query→recommendation 证据）**已完成**，E5 的「无生产调用」判定已作废。**但效果加分仍不申领**：`lab/reports/knowledge-ablation/report.md` 自述未做「门禁开、图谱关」的第二层消融，知识组增益主要来自既定 HD/BLOSUM 门禁，图谱的独立贡献未被隔离。 |
| B06 | 交互 demo：输入 WT 后自动推荐 | 部分交付 | `app/demo.py:530-651` 可对硬编码 GB1 四位点变体打分并一键推荐；Demo tests 本次通过 | 输入仅 4 字符变体且 WT/位点硬编码，不接受任意 56 aa WT 自动识别/推荐。最小动作：要么把文案收窄为“GB1 四位点 demo”，要么实现完整 WT 输入与任务配置。 |
| B07 | 讨论连接真实自动化实验平台 | 已交付 | `reports/final-report-v0.3/report.md:111-116` 提及真实测量/设备闭环及 SiLA 2，明确尚未接入 | 无；保持“未来工作”措辞。 |

## 6. 锁定五条 decision 口径复核

| Decision | Verdict | 工具证据与判断 |
|---|---|---|
| D1 提名空间 149,361 | 通过 | `evolution/campaign.py:199-204,241-245,291-295` 与 E9；缺失 10,639 明示，没有把缺真值候选当 0。 |
| D2 ESM-2 主力 + one-hot L1，缓存入库 | 打回 | ESM-2 提取/评测和部分已提交缓存存在（E7），但 GB1 闭环与 Demo 的实际 predictor 都是 80 维 one-hot：`evolution/campaign.py:56-62,186-190`、`app/demo.py:104-112,532-536`。这不符合“ESM-2 主力、one-hot L1”的锁定口径。 |
| D3 事件流属交付层 | 通过 | 事件流进入 campaign、报告和 Demo；E3 用正常链与篡改链两侧验证，不是只信 `verify()` 沉默。 |
| D4 商业 API + 严格 Pydantic schema | 打回 | 商业 OpenAI-compatible API 已接且有 live 记录（`agent/llm.py:61-76`、E9），但 GB1 实际只让 Hypothesis 返回原始 JSON 数组后手工解析，未请求 provider schema。（「主跑未注入 `llm_critic`」一条已由 `2366506` 修掉，见 E10 更正；本条剩余缺口仅为 provider schema。） |
| D5 revision-report 为真源 | **部分通过（2026-09-14 更正）** | **核心诉求已满足**：受控 `harness/final-report/report.pdf` 与 `reports/final-report-v0.7/scientific_report_v0.7_two_column.pdf` sha256 同一份（`30b91737…`），即交付 PDF 已由当前 v0.7 真源制版，且真源 `report.md` 与 PDF 均已被 git 跟踪（E4）。原写「受控 PDF/README 仍是旧 GB1 叙事，且 README PDF 链接错误（E4/E8）」已被实测推翻、作废。**剩余未通过部分**：README:11-12 入口仍指 v0.6 而非 v0.7，交付入口未统一到最新真源。 |

## 7. 汇总表

### 7.1 硬要求缺口（必须补）

53 个硬要求行中（**2026-09-14 二次重算**）：**43 已交付、9 部分交付、1 未达标**。原写「43 已交付、10 部分交付、0 完全未做」已作废——**H32 由部分交付翻已交付**、**H33 由已交付翻未达标**，两项方向相反，总计数 53 不变。9 个部分项为 H04、H14（第二章）、H37、H39、H41、H45（第三章）、H50、H51、H52（第四章）；**唯一未达标项为 H33（报告 PDF 页数）**。合并为 **6** 个可执行修复包（原 7 包中「AAV 主线缺同协议知识消融」已完成）：

| 优先级 | 缺口包 | 关联条目 | 最小补齐动作 | 估计 |
|---|---|---|---|---|
| ~~P0-a~~ **CEO 裁定接受该缺口,不执行** | **报告 PDF 页数硬性不符试题**（交付 44 页 / README 入口 25 页，对 3—5 页） | H33 | **2026-09-14 CEO 裁定:材料已提交,不再裁剪、不追求严格合规。**此行保留在表内是为了**不掩盖缺口**:`H33` 的判定仍为**未达标**(试题 `AI4S-assignment.md:72` 明文 3—5 页,实测 44/25 页),事实不因裁定而改变;改变的只是「是否投入工时修它」。若日后要修,原方案仍成立:正文八章约 15.8K 字符可压入 5 页,附录 A–L.3 共 30 节约 40K 字符另立单独 PDF | 不执行 |
| ~~P0-b~~ **CEO 裁定不执行** | README 报告入口仍指 v0.6，当前交付版为 v0.7 | H39 + D5 | **2026-09-14 CEO 裁定:材料已提交,不改。**原动作为改 `README.md:11-12` 与 `README.zh-CN.md:11-12` 指向 v0.7(受控 PDF 已是 v0.7 真源产物,无需重制)。本项与 P0-a 同一处入口,P0-a 既不执行,本项随之不执行。**缺口仍如实存在**:README 入口指向的是 v0.6 的 25 页 PDF,而当前交付版是 v0.7;`H39` 判定仍为**部分交付** | 不执行 |
| ~~P0~~ **已完成** | ~~AAV 主线缺同协议知识消融~~ | H21/H51/H52 | 已由 `lab/reports/knowledge-ablation/` 完成：单因子、3 配对 seed、带阴性对照与 v0.7 锚点复现；paired 结果 strong 54.0→162.3、`cum_top10_max` 6.1862→6.5309、达峰率两组均 0/3 | — |
| P0 | ~~主跑 Scientific Critic 空转~~（已由 `2366506` 修掉）、商业 API 未严格 schema | H14/H15/H45/H50 + D4 | 剩余动作：用 provider/Pydantic 结构化输出；事件记录逐候选理由。`llm_critic` 接入已完成 | 0.5 天 + API 时延 |
| P1 | D2 主链未使用 ESM-2 | D2 | 让主力 campaign/demo predictor 读取已缓存 ESM-2；one-hot 仅保留 L1/离线 fallback，并记录 feature provenance | 0.5–1 天 |
| P1 | validation 职责未接入当前选模协议 | H04 | 明确 train/validation/query-test/holdout，选超参只看 validation，最终一次看 holdout | 0.5 天 |
| P1 | ~~知识替换表不完整~~（已修，190/190）、**跨蛋白规则硬编码** | H51 | 剩余动作：把位点/WT/HD 规则参数化为 dataset spec，加 AAV 坐标测试。完整 BLOSUM62 与零分/非对称查表用例均已落地（H18） | 0.5 天 |
| P1 | README/干净 clone 复现闭环不完整 | H37/H39/H41 | 修 Make targets、数据获取/校验措辞，提供可提交小样本 smoke fixture 与一条端到端命令 | 0.5 天 |

最先补 **P0-a 报告页数**：它是试题明文的硬性格式要求，也是本次二次重算中**唯一方向变差**的一项；它需要你先定裁剪方案，我不替你选。**原写「最先补 P0 当前报告真源（H32/H39 + D5）」已作废**：真源已制版、受控 PDF 与之 sha256 同一份，该包只剩 P0-b 的两行 README 入口改动。**原文并列的「P0 AAV 知识消融」已于 2026-09-14 移除**——该项已由 `lab/reports/knowledge-ablation/` 完成（单因子、3 配对 seed、带阴性对照与 v0.7 锚点复现），不再是待补缺口；其实测边界（`model=null`、36/36 agent 轮次超时、完成实验的 LLM 轮次为 0，故只能证明 agent harness + 知识处理的差异、不能推断 LLM 因果增益）随 H21 一并保留。

### 7.2 加分项缺口（可选）

| 状态 | 条目 |
|---|---|
| 已交付 | B01 主动学习、B02 集成不确定性、B07 自动化实验平台讨论、B05 知识图谱（接线完成，不申领效果加分） |
| 部分交付 | B03 按突变阶数比较、B04 结构/位点保守性、B06 通用 WT 输入 demo |
| 存在但未接线 | 无（B05 已于 2026-09-14 核实接线完成，移入「已交付」行） |
| 未做 | 无（但部分项不能按完整加分申领） |

### 7.3 已交付能力（带证据）

| 能力簇 | 已交付证据 |
|---|---|
| 真实数据与可测空间 | E1；H01–H03；D1 |
| 预测模型与指标 | H05–H07；predictor JSON；E2 |
| 候选生成、评分、回填闭环 | H09–H13、H22–H26；E9 |
| GB1 四策略比较 | H27–H31；`campaign_hard/llm.metrics.json` |
| 审计事件流 | D3；E3 正常/篡改双侧验证 |
| 报告结构和基础交付 | H33–H36、H42–H44、H46；GitHub remote。**2026-09-14 更正:原写「4 页 PDF」已作废**——那 4 页指已被同名替换掉的旧 `harness/final-report/report.pdf`,当前受控 PDF 为 v0.7 的 **44 页**,`H33` 已判**未达标**(见 E4/H33/§8)。此行保留在「已覆盖」是因 H34–H36、H42–H44、H46 的结构性要求成立;**页数一项不在其中** |
| 加分能力 | B01、B02、B07；**B05 知识图谱**（接线完成，不申领效果加分——见 §7.2 与第 5 章 B05 行；2026-09-14 补入，此前 §7.2 已改而本行漏改，属同一文档内两处不一致） |

## 8. Verdict 与 residual risk

**Verdict：打回（changes requested）——2026-09-14 二次重述；同日 CEO 就剩余缺口作出接受裁定,见下方「CEO 收口裁定」。** 仓库对试题主体的覆盖度已经高，且没有发现整类硬要求「完全未做」；当前剩 **9 个部分项 + 1 个未达标项**。**上一版写「仍然阻塞语义验收的 P0 只剩一个：当前受控 PDF 不是 revision 真源、README 入口指错（H32/H39 + D5）」已作废，且方向被实测推翻**：受控 PDF 与 v0.7 真源 sha256 同一份，真源问题已消除（H32 翻已交付、D5 转部分通过），入口问题收窄为改两行 README（P0-b）。**但同一次重测暴露了一个更硬的缺口**：`AI4S-assignment.md:72` 明文要求 3—5 页，实测交付 PDF 44 页、README 入口 25 页，**H33 由已交付翻未达标**（P0-a）；且本仓 checklist 早已如此判定，本表此前与之矛盾、错在本表。另有 D2（主链未用 ESM-2）与 D4（商业 API 未请求 provider schema）两条锁定口径未通过——D4 的「未注入 `llm_critic`」那半已修，剩余仅 schema。因此仍不放行；阻塞项为 **P0-a（需 CEO 裁决裁剪方案）+ P0-b + D2 + D4**。

未验证项：本次没有调用外部 LLM、没有重跑 ESM-2 650M、没有重跑完整 GB1/AAV campaign、没有检查远端 GitHub 页面内容或全 CI；这些均不得从定向测试推断为通过（09-12 基线为 38 passed；2026-09-14 同命令复跑为 79 passed，测试树已增长，两者不是同一基线）。

### CEO 收口裁定(2026-09-14)

本审计的 Verdict 仍是「打回」,该判定**不撤回**——它描述的是交付物相对试题的客观差距。但 CEO 就是否继续投入工时修补作出裁定,逐条如下:

| 缺口 | 条目 | CEO 裁定 | 缺口是否仍存在 |
|---|---|---|---|
| 报告 PDF 页数(44/25 页 对 3—5 页) | H33 | **接受,不裁剪** | **是**,判定仍为未达标 |
| README 入口仍指 v0.6 | H39 + D5 | **接受,不改** | **是**,判定仍为部分交付 |
| 主链未使用 ESM-2 | D2 | 未变更(留待后续) | 是 |
| 商业 API 未请求 provider schema | D4 | 未变更(留待后续) | 是 |

**裁定的性质必须说清**:CEO 裁定的是**资源投入**(材料已提交,不再为形式合规返工),**不是**把未达标项改判为已交付。本文档因此保持「43 已交付 / 9 部分交付 / 1 未达标」的原判定不变,并把上述四项缺口继续显式列出。**任何下游文档不得据本裁定声称试题页数要求已满足。**
