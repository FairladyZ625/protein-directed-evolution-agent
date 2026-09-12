# AI4S 试题逐条覆盖度审计

> 审计日期：2026-09-12。验收标尺为 `harness/context/research/AI4S-assignment.md`；仓库锁定口径以 worker handbook 的 D1–D5 为准。状态只采用“已交付 / 部分交付 / 存在但未接线 / 未做”。本报告只记录本次从磁盘、Git 索引和真实命令观察到的证据，不把已有报告的自述本身当作实现证据。

## 1. 本次工具证据

| ID | 命令 / 检查 | 本次真实结果 |
|---|---|---|
| E1 | `.venv/bin/python` 读取 `data/four_mutations_full_data.csv` 与三池 CSV | 原表 `(149361, 17)`；WT `VDGV=1.0`；最大 `FWAA=8.76196565571`；train/query/holdout 为 `5000/50000/94361`，两两交集为 0，并集 149361。 |
| E2 | `.venv/bin/pytest -q tests/test_data_pipeline.py tests/test_agent.py tests/test_campaign.py tests/test_knowledge.py tests/test_events.py tests/test_demo_app.py tests/test_pool_campaign.py` | `38 passed in 6.88s`。这是定向单元/集成验证，不等于全 CI 或外部 API 实跑。 |
| E3 | `.venv/bin/pytest -q tests/test_events.py::test_append_hash_chain_and_verification tests/test_events.py::test_tampering_is_detected_at_changed_event` | 阳性链校验与篡改阴性对照均通过：`2 passed in 0.02s`；篡改用例预期在 seq=2 报错，见 `tests/test_events.py:59-66`。 |
| E4 | `pdfinfo harness/final-report/report.pdf`；`pdftotext -layout ...` | PDF 存在、A4、4 页；正文有一至八节、GB1 四策略表和失败分析。但内容仍是旧 GB1 主叙事，不是当前 `reports/final-report-v0.3/report.md`。 |
| E5 | `rg -n 'build_knowledge_graph' --glob '!**/.worktrees/**' .` | 除定义/导出外，唯一调用在 `tests/test_knowledge.py:17`；生产 `agent/`、`evolution/`、`app/` 无调用。 |
| E6 | `rg -n 'no_knowledge|guardrail' agent evolution app tests --glob '*.py'` + 读取 AAV 指标 | GB1 有 `agent_no_knowledge`/`knowledge_agent`；AAV `run_autoresearch` 只有 `guardrail` 开关，无同协议 `no_knowledge` 对照。v0.1/v0.2/v0.4 的配置、模型和预算并非严格单因子匹配。 |
| E7 | 读取 `features/cache/*.npz` shape，并以 `git ls-files features/cache` 核对 | 已提交缓存覆盖 GB1 评测所需的 5000、2168、两个 2000 样本块，均为 1280 维；149361 全表缓存只有 one-hot 80 维。另一个 38265×1280 文件当前未跟踪，不能算 GitHub 交付。 |
| E8 | `git remote -v`、`git ls-files harness/final-report ...`、README 路径核对 | origin 为公开 GitHub URL；`harness/final-report/report.pdf` 已跟踪。README 却链接不存在的 `reports/report.pdf`，且 `make train` 指向无 CLI 入口的 `models/train_ladder.py`。 |
| E9 | 读取 `campaign_hard.metrics.json` / `campaign_llm.metrics.json` | 两者均为 149361 提名空间、3 轮、四策略、真实查表 oracle；LLM 记录中部分轮次为 `fallback`，部分为 `llm:claude-sonnet-5`。 |
| E10 | 代码双侧核对 `evolution/campaign.py:182-213` 与 `agent/pipeline.py:110-123` | GB1 两个 Agent 策略调用五角色管线，但调用固定传 `no_knowledge=True`，且未注入 `llm_critic`；知识组只在管线之后叠加 UCB+BLOSUM acquisition。角色事件存在，不代表 Critic 实际执行知识否决或商业 LLM 审查。 |

## 2. 第二章“项目任务”逐条审计

| 编号 | 试题条目（原文摘要） | 出处 | 状态 | 证据 | 差距与最小补齐动作 |
|---|---|---|---|---|---|
| H01 | 使用公开定向进化/突变效应数据集 | 二·数据 a | 已交付 | `data/README.md:3-8`；`data/download_gb1.py:20,50-51`；E1 | 无。 |
| H02 | 选择具体蛋白质优化任务 | 二·数据 b | 已交付 | `README.md:1-4` 定义 GB1 结合适应度；`reports/final-report-v0.3/report.md:7-11` 定义预算池式优化 | 无。 |
| H03 | 整理 WT、突变序列、位点、fitness | 二·数据 c | 已交付 | `evolution/mutations.py:9-11`；原表含 `Variants/HD/Fitness/sequence`；E1 | 无。 |
| H04 | 划分训练、验证、测试，模拟已完成与未知候选 | 二·数据·独立条目 | 部分交付 | `features/pools.py:19-26,45-60` 和 E1 证明 train/query/holdout 三池隔离；`models/evaluate_all.py:36-39` 只消费 train/query 或 HD train/test | 主评测没有显式 validation 的训练/调参职责；原 CSV 虽有 legacy `*_validation` 列，但当前训练入口未消费。最小动作：在当前协议中明确 train/validation/test(query/holdout) 角色并让训练/选模代码实际读取 validation。 |
| H05 | 建立 baseline 适应度预测模型 | 二·预测模型 | 已交付 | `models/train_ladder.py:38-54,129-151`；`harness/reports/workflow-v1.0/gb1/predictor_ladder.json` | 无。 |
| H06 | 用 Spearman/Pearson/MSE/Top-k 等评估 | 二·预测模型 | 已交付 | `models/train_ladder.py:153-161`；产物含四类指标；E2 | 无。 |
| H07 | 分析能否识别高-fitness 变体 | 二·预测模型 | 已交付 | `reports/final-report-v0.3/report.md:31-42,97`；GB1/AAV 排名与 Top-k 产物 | 无；最终文稿应保留“不宣称统计显著”的边界。 |
| H08 | 设计 LLM Agent 模拟定向进化科研流程 | 二·科学智能体 a | 已交付 | `agent/auto_researcher.py:244-322` 为商业模型工具调用循环；E9 有真实 LLM 轮次记录 | 明确区分 live LLM 与 fallback，不能把整条轨迹笼统写成 LLM。 |
| H09 | 读取当前实验数据和 top variants | 二·科学智能体 b-i | 已交付 | `agent/auto_researcher.py:137-156`；`agent/pipeline.py:48-61` | 无。 |
| H10 | 总结可能有益的突变位点 | 二·科学智能体 b-ii | 已交付 | `agent/auto_researcher.py:143-152`；`evolution/campaign.py:100-124` | 无。 |
| H11 | 提出下一轮候选突变序列 | 二·科学智能体 b-iii | 已交付 | `agent/pipeline.py:63-101`；`evolution/campaign.py:182-213` | 无。 |
| H12 | 调用适应度模型给候选打分 | 二·科学智能体 b-iv | 已交付 | `agent/pipeline.py:103-108`；`evolution/campaign.py:186-190` | 无。 |
| H13 | 按预测结果选择 Top-k | 二·科学智能体 b-v | 已交付 | `evolution/campaign.py:205-213`；每轮产物含 top10，E9 | 无。 |
| H14 | 给出推荐理由 | 二·科学智能体 b-vi | 部分交付 | `agent/pipeline.py:18-21,67-70` 有 `rationale/rule_ids`；事件可回放 | 主 GB1 rationale 多为固定规则模板，Critic 没有实际 LLM/规则审查（E10）；不足以逐候选解释为何选择某替换/组合。最小动作：把候选级 evidence、规则命中和 critic reason 写入真实主跑事件。 |
| H15 | 模块化角色：分析—假设—设计—评估—批判 | 二·科学智能体 c | 部分交付 | 五类实现见 `agent/pipeline.py:48-123`；角色事件测试 `tests/test_agent.py:96-108` 通过 | 结构齐全，但主 GB1 campaign 的 Critic 被 `no_knowledge=True` 空转且无 `llm_critic`（E10）。最小动作：在知识组接入真实 Critic；无知识组保留明确消融。 |
| H16 | 构建小型知识库/突变规则库 | 二·知识 a | 已交付 | `knowledge/rules.yaml:1-41`、`knowledge/validators.py:20-56`；E2 | 无。 |
| H17 | 氨基酸疏水性、电荷、大小、极性 | 二·知识 b-i | 已交付 | `knowledge/rules.yaml:2-22` | 无。 |
| H18 | 保守替换与激进替换 | 二·知识 b-ii | 部分交付 | `knowledge/rules.yaml:23-39`；`tests/test_knowledge.py:4-8` 证明检测器可出声 | 本地 BLOSUM 表仅为子集，未知配对会跳过分类；当前报告亦在 `reports/final-report-v0.3/report.md:58` 披露 190 对中缺 136 对。最小动作：换完整、有来源校验的 BLOSUM62，并加未知配对失败用例。 |
| H19 | 限制突变数、拒绝 stop/异常、避免一次过多 | 二·知识 b-iii/iv/v | 已交付 | `knowledge/rules.yaml:35-40`；`knowledge/validators.py:35-50`；拒绝用例 `tests/test_agent.py:130-151` | AAV 与 GB1 的坐标/上限应分配置，避免复用 GB1 硬编码。 |
| H20 | 优先组合历史上较好的单点突变 | 二·知识 b-vi | 已交付 | `evolution/campaign.py:100-124` 按观测均值取每位点 top 替换并组合 | 无。 |
| H21 | 比较有无知识增强时推荐差异 | 二·知识·独立条目 | 部分交付 | GB1 有同协议两组及不同 acquisition：`evolution/campaign.py:46,284-287`、`tests/test_campaign.py:67-72`、E9 | 当前最终科学主叙事已转向 AAV，但 AAV v0.1/v0.2/v0.4 改了门禁、surrogate、批次等多个因素，不是同协议有/无知识消融（E6）。最小动作：在锁定 AAV 协议、相同模型/池/预算/seed 下只切知识开关。 |
| H22 | 已有训练数据作为第一轮实验结果 | 二·虚拟实验 a | 已交付 | GB1 `evolution/campaign.py:250-256`；AAV `agent/auto_researcher.py:64-72` | 无。 |
| H23 | Agent 基于当前数据提出下一轮候选 | 二·虚拟实验 b | 已交付 | `evolution/campaign.py:258-272` 每轮用更新后的 train；AAV `agent/auto_researcher.py:289-322` | 无。 |
| H24 | 用测试真值或预测模型作为虚拟实验评估器 | 二·虚拟实验 c | 已交付 | `evolution/campaign.py:16,270-272,294`；E9 为 `measured table lookup` | 无。 |
| H25 | 至少模拟 2–3 轮 | 二·虚拟实验 d | 已交付（超出） | GB1 为 3 轮；AAV 历史含 3/6/12/16 轮，E9 | 无。 |
| H26 | 观察 fitness 是否逐轮提升 | 二·虚拟实验·独立条目 | 已交付 | E9 的 `cum_top10_max_curve`；PDF 第六节曲线 | 无；应同时报告平台期/下降的阴性结果。 |
| H27 | 展示每轮 Agent Top-k 蛋白突变 | 二·结果 a | 已交付 | 每轮 JSON `top10`；`app/demo.py:171-182,430-456` 可切轮次；`reports/final-report-v0.3/evidence/gb1_top10.csv` | 无。 |
| H28 | 分析推荐是否集中在关键位点 | 二·结果 b | 已交付 | 4 页 PDF 第六节“逐轮 Top-k 与关键位点”；事件 Data Analyst 位点画像由 `app/demo.py:374-387` 展示 | 当前 v0.3 正文较弱；最终 PDF 应保留位点分布，而非只列代表序列。 |
| H29 | 比较随机、模型直推、LLM Agent、知识增强 Agent | 二·结果 c | 已交付 | `evolution/campaign.py:3-16,46`；E9；`tests/test_campaign.py:40-47` | 需继续清楚标注 deterministic/fallback/live LLM，避免把第 3/4 组名字当调用事实。 |
| H30 | 分析成功案例和失败案例 | 二·结果 d | 已交付 | `reports/final-report-v0.3/report.md:93-106`；原始 AAV/GB1 指标在 `harness/reports/` | 无。 |
| H31 | 讨论 Agent 是科学思维还是模型调用 | 二·结果·独立条目 | 已交付 | 4 页 PDF 第七节明确回答“结构化、可审计搜索启发式，不是自主科学推理”；v0.3 `report.md:54,103` 更谨慎 | 无。 |

第二章小结：31 个行级要求中 26 个已交付、5 个部分交付、0 个完全未做。五个部分项为 H04、H14、H15、H18、H21；其中 H21 是最直接的试题硬缺口。H28 已有旧 PDF 与 Demo 证据，当前主文稿仅需保留该能力的展示。

## 3. 第三章“详细要求”逐条审计

| 编号 | 试题条目（原文摘要） | 出处 | 状态 | 证据 | 差距与最小补齐动作 |
|---|---|---|---|---|---|
| H32 | 提交 PDF 实验报告 | 三·报告 a | 部分交付 | `harness/final-report/report.pdf` 已跟踪且可读，E4/E8 | PDF 是旧 GB1 版本；当前证据边界在 `reports/final-report-v0.3/report.md`，且其 handoff 明示尚未验收 PDF。最小动作：从当前 v0.3/后续 revision 真源重新制版，替换受控交付 PDF。 |
| H33 | PDF 为 3–5 页 | 三·报告 a | 已交付 | `pdfinfo` 实测 4 页，E4 | 重制当前版后必须再次检查页数；旧 PDF 的 4 页不能替新 PDF 背书。 |
| H34 | 报告含规定八节 | 三·报告 a-i…viii | 已交付 | 旧 PDF 实测一至八节；当前 `reports/final-report-v0.3/report.md:7,13,27,44,56,64,93,109` 也精确对应八节 | 无。 |
| H35 | 提交 GitHub 链接 | 三·代码 a | 已交付 | `git remote -v` 为 `https://github.com/FairladyZ625/protein-directed-evolution-agent.git`；v0.3 报告第 4 行链接 | 无。 |
| H36 | 含数据处理、训练、Agent 推理、候选生成、评估代码 | 三·代码 b | 已交付 | `data/download_gb1.py`、`models/evaluate_all.py`、`agent/pipeline.py`、`evolution/campaign.py`、`models/train_ladder.py:153-170` | 无。 |
| H37 | README 说明运行环境 | 三·代码 c | 部分交付 | `README.md:105-117` 有 venv/pip 命令；`requirements.txt` 锁版本 | README 未明确支持的 Python 版本/硬件边界，且 ESM 650M 的 MPS/CPU 成本只散落在代码/手册。最小动作：加入 Python 版本、CPU/MPS 模式和预计资源。 |
| H38 | README 说明数据来源 | 三·代码 c | 已交付 | `README.md:14-22` 含 Wu/eLife DOI 和手工放置说明 | 无。 |
| H39 | README 说明运行命令 | 三·代码 c | 部分交付 | `README.md:105-117` 有命令；E8 | README 报告链接 `reports/report.pdf` 不存在；Makefile 的 `train` 调用无 CLI 入口的 `models/train_ladder.py`，`make data` 名称像下载但实际仅验证本地文件。最小动作：修链接、让 `make train` 调 `models.evaluate_all` 或真正入口，并把 `make data` 改名/说明。 |
| H40 | README 说明主要结果 | 三·代码 c | 已交付 | `README.md:24-38,65-88` | README 是旧 GB1 主叙事，与 D5 当前 revision 的 AAV 结论不一致；应在 D5 修复包同步更新，但“有说明”本项已满足。 |
| H41 | 小规模数据可复现实验流程 | 三·独立条目 | 部分交付 | 16 变体完整景观集成测试 `tests/test_campaign.py:1-53` 本次通过；E2 | 测试可复现小流程，但 README 的主命令依赖 Git 未包含的 44MB CSV，且自动下载关闭；干净 clone 的用户无法按单一命令复现主实验。最小动作：提供许可允许的小样本 fixture/下载校验器和一条真正端到端 smoke 命令。 |
| H42 | 展示 WT 与若干突变序列 | 三·结果 a | 已交付 | PDF 第二节含 `VDGV`、`FWAA`；v0.3 `report.md:17-23` 另含 AAV WT/代表序列 | 无。 |
| H43 | 展示每轮推荐 Top-k | 三·结果 b | 已交付 | 同 H27；v0.3 `report.md:75` 指向完整 `evidence/gb1_top10.csv` | 正文至少保留一张紧凑逐轮表或明确附件链接。 |
| H44 | 表格/曲线展示 fitness 提升 | 三·结果 c | 已交付 | PDF 第六节表和图；`app/demo.py:134-183,202-235`；E9 | 无。 |
| H45 | 展示 Agent 推理：重要位点、替换原因、组合原因、失败原因 | 三·结果 d | 部分交付 | 事件角色链和 Demo 由 `app/demo.py:361-417` 展示；E2/E3 | 重要位点与流程可见，但主跑的候选级替换/组合理由多为模板，真实 Critic 空转（E10）。最小动作同 H14/H15，并在最终报告截取至少一条真实完整链。 |
| H46 | 外部数据/模型/代码/ChatGPT 辅助需注明来源和方式 | 三·可用资源注意 | 已交付 | 4 页 PDF 附录披露 GB1、ESM、scikit-learn、LLM；v0.3 `report.md:119` 披露语言模型辅助 | 无。 |

第三章小结：15 项中 10 项已交付、5 项部分交付（H32、H37、H39、H41、H45）。最危险的是“当前真源尚未生成受控 3–5 页 PDF”和“README 一键复现路径不闭合”。

## 4. 第四章“考核重点”逐条审计

| 编号 | 考核重点 | 状态 | 证据 | 差距与最小补齐动作 |
|---|---|---|---|---|
| H47 | 理解定向进化基本科学流程 | 已交付 | `reports/final-report-v0.3/report.md:7-11`；代码每轮冻结候选后查标签并回填 | 无。 |
| H48 | 处理真实突变与 fitness 数据 | 已交付 | E1；`tests/test_data_pipeline.py:15-48` 本次通过 | 无。 |
| H49 | 训练合理适应度模型 | 已交付 | `models/evaluate_all.py:32-68`；predictor artifact；E2 | 无。 |
| H50 | Agent 形成假设—设计—评估—反馈迭代 | 部分交付 | `agent/pipeline.py:48-123` 与 `evolution/campaign.py:258-280` | 数据回填存在，但主跑 Critic 没执行知识/LLM 审查，假设理由也多为模板。按 H14/H15 补。 |
| H51 | 合理引入氨基酸性质、规则或知识图谱 | 部分交付 | 规则与 BLOSUM 进入 acquisition；E5/E10 | 理化属性和图谱没有进入主链，BLOSUM 不完整，且 AAV/GB1 语义混用。按 H18/H21 和 bonus B05 补。 |
| H52 | 通过实验比较证明 Agent 作用 | 部分交付 | GB1 四策略同预算对比存在，E9；AAV 有多代结果 | 单 seed GB1、LLM/fallback 混合；AAV 缺严格知识消融且固定采集函数胜过 FULL LLM。当前只能证明流程差异，不能证明通用 Agent/LLM 增益。补同协议多 seed 因子消融。 |
| H53 | 分析失败原因，不只展示成功 | 已交付 | `reports/final-report-v0.3/report.md:93-106` | 无。 |

## 5. 第五章“加分项”单独审计

| 编号 | 加分项 | 状态 | 证据 | 差距与最小补齐动作 |
|---|---|---|---|---|
| B01 | 主动学习或强化学习选下一轮 | 已交付 | `evolution/pool_campaign.py:142-188` 每轮重训并从未测池选样；AAV `agent/auto_researcher.py` 同类 | 已由主动学习满足，不需要为凑项另做 RL。 |
| B02 | 不确定性估计（GP/集成） | 已交付 | `models/train_ladder.py:18-36` bootstrap 方差；UCB 在 `evolution/campaign.py:206-207` | 报告应继续声明方差未校准。 |
| B03 | 比较单点、双点、多点优化效果 | 部分交付 | HD 分层/低阶外推在 `features/pools.py:29-42`，PDF 有 HD 计数 | 没有相同预算下按突变阶数的优化效果对照。最小动作：按 HD=1/2/≥3 分组报告命中率、增益和预算效率。 |
| B04 | 引入结构信息或保守位点分析 | 部分交付 | BLOSUM 保守替换先验已用；`knowledge/rules.yaml:23-39` | 这是替换保守性，不是位点保守性或结构接触；若申领此加分，至少增加有来源的位点 conservation 或结构接触特征并做消融。 |
| B05 | 知识图谱表示位点—突变—性质—fitness | 存在但未接线 | `knowledge/validators.py:67-83` 可建图，`tests/test_knowledge.py:16-22` 阳性用例通过；E5 证明无生产调用 | 最小动作：在 Analyst/Hypothesis/Critic 至少一处查询图谱并记录 query→recommendation 证据；否则只称原型，不申领效果加分。 |
| B06 | 交互 demo：输入 WT 后自动推荐 | 部分交付 | `app/demo.py:530-651` 可对硬编码 GB1 四位点变体打分并一键推荐；Demo tests 本次通过 | 输入仅 4 字符变体且 WT/位点硬编码，不接受任意 56 aa WT 自动识别/推荐。最小动作：要么把文案收窄为“GB1 四位点 demo”，要么实现完整 WT 输入与任务配置。 |
| B07 | 讨论连接真实自动化实验平台 | 已交付 | `reports/final-report-v0.3/report.md:111-116` 提及真实测量/设备闭环及 SiLA 2，明确尚未接入 | 无；保持“未来工作”措辞。 |

## 6. 锁定五条 decision 口径复核

| Decision | Verdict | 工具证据与判断 |
|---|---|---|
| D1 提名空间 149,361 | 通过 | `evolution/campaign.py:199-204,241-245,291-295` 与 E9；缺失 10,639 明示，没有把缺真值候选当 0。 |
| D2 ESM-2 主力 + one-hot L1，缓存入库 | 打回 | ESM-2 提取/评测和部分已提交缓存存在（E7），但 GB1 闭环与 Demo 的实际 predictor 都是 80 维 one-hot：`evolution/campaign.py:56-62,186-190`、`app/demo.py:104-112,532-536`。这不符合“ESM-2 主力、one-hot L1”的锁定口径。 |
| D3 事件流属交付层 | 通过 | 事件流进入 campaign、报告和 Demo；E3 用正常链与篡改链两侧验证，不是只信 `verify()` 沉默。 |
| D4 商业 API + 严格 Pydantic schema | 打回 | 商业 OpenAI-compatible API 已接且有 live 记录（`agent/llm.py:61-76`、E9），但 GB1 实际只让 Hypothesis 返回原始 JSON 数组后手工解析，未请求 provider schema；主跑未注入 `llm_critic`（E10）。 |
| D5 revision-report 为真源 | 打回 | 当前 v0.3 Markdown已修正多项结论，但受控 PDF/README 仍是旧 GB1 叙事，且 README PDF 链接错误（E4/E8）。交付入口没有统一指向 revision 真源。 |

## 7. 汇总表

### 7.1 硬要求缺口（必须补）

53 个硬要求行中：**40 已交付、13 部分交付、0 完全未做**。13 个部分项合并为 7 个可执行修复包：

| 优先级 | 缺口包 | 关联条目 | 最小补齐动作 | 估计 |
|---|---|---|---|---|
| P0 | 当前真源未形成最终受控 PDF，README 入口还指错 | H32/H39 + D5 | 用 revision/current report 重制 3–5 页 PDF，`pdfinfo` 复验；修 README 链接与主结论 | 0.5–1 天 |
| P0 | AAV 主线缺同协议知识消融 | H21/H51/H52 | 固定 AAV 数据、surrogate、预算、seed，只切知识开关，输出 paired 指标与候选差异 | 0.5–1 天（不含 ESM 重算） |
| P0 | 主跑 Scientific Critic 空转，商业 API 未严格 schema | H14/H15/H45/H50 + D4 | 知识组启用规则 Critic；接 `llm_critic`；用 provider/Pydantic 结构化输出；事件记录逐候选理由 | 0.5–1 天 + API 时延 |
| P1 | D2 主链未使用 ESM-2 | D2 | 让主力 campaign/demo predictor 读取已缓存 ESM-2；one-hot 仅保留 L1/离线 fallback，并记录 feature provenance | 0.5–1 天 |
| P1 | validation 职责未接入当前选模协议 | H04 | 明确 train/validation/query-test/holdout，选超参只看 validation，最终一次看 holdout | 0.5 天 |
| P1 | 知识替换表不完整、跨蛋白规则硬编码 | H18/H51 | 使用完整 BLOSUM62；把位点/WT/HD 规则参数化为 dataset spec；加未知配对与 AAV 坐标测试 | 0.5 天 |
| P1 | README/干净 clone 复现闭环不完整 | H37/H39/H41 | 修 Make targets、数据获取/校验措辞，提供可提交小样本 smoke fixture 与一条端到端命令 | 0.5 天 |

最先补 **P0 当前报告真源 + P0 AAV 知识消融**：前者决定交出去的材料是否承载最新、诚实结论；后者直接对应试题明写的比较要求，也是 CEO 已发现且现有 AAV 主线仍无法回答的问题。

### 7.2 加分项缺口（可选）

| 状态 | 条目 |
|---|---|
| 已交付 | B01 主动学习、B02 集成不确定性、B07 自动化实验平台讨论 |
| 部分交付 | B03 按突变阶数比较、B04 结构/位点保守性、B06 通用 WT 输入 demo |
| 存在但未接线 | B05 知识图谱 |
| 未做 | 无（但部分项不能按完整加分申领） |

### 7.3 已交付能力（带证据）

| 能力簇 | 已交付证据 |
|---|---|
| 真实数据与可测空间 | E1；H01–H03；D1 |
| 预测模型与指标 | H05–H07；predictor JSON；E2 |
| 候选生成、评分、回填闭环 | H09–H13、H22–H26；E9 |
| GB1 四策略比较 | H27–H31；`campaign_hard/llm.metrics.json` |
| 审计事件流 | D3；E3 正常/篡改双侧验证 |
| 报告结构和基础交付 | H33–H36、H42–H44、H46；4 页 PDF + GitHub remote |
| 加分能力 | B01、B02、B07 |

## 8. Verdict 与 residual risk

**Verdict：打回（changes requested）。** 仓库对试题主体的覆盖度已经高，且没有发现整类硬要求“完全未做”；但当前交付仍有 13 个行级部分项，其中 3 个 P0 会直接影响语义验收：当前 PDF 不是 revision 真源、AAV 没有严格有/无知识增强对照、主跑 Critic/严格结构化商业 API 没有真正接线。D2/D4/D5 三条锁定口径也未通过，因此不能以“基本都做了”为理由放行。

未验证项：本次没有调用外部 LLM、没有重跑 ESM-2 650M、没有重跑完整 GB1/AAV campaign、没有检查远端 GitHub 页面内容或全 CI；这些均不得从本次 38 个定向测试推断为通过。
