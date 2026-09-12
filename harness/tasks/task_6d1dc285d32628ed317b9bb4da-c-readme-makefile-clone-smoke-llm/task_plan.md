# 包C/交付面闭环:README 死链与主叙事、Makefile 入口、干净 clone 可跑的 smoke、LLM 归属实际值

Task Contract: harness-task v1

## Brief

这是**评委第一眼看到的那一面**,现在有硬伤。覆盖度审计判定 D5(revision-report 为真源)打回:交付入口仍指着旧 GB1 叙事。具体:README 首屏推荐的 `reports/report.pdf` **不存在**(点开 404),`make train` 指向一个没有 CLI 入口的文件,`make data` 名字像下载实际只做校验,干净 clone 的人按 README 跑不通主实验。外加一条贯穿全仓的数据卫生问题:自 v0.4 起产物标注的 LLM 是 `gpt-5.6-sol`,而实际解析到的是 `claude-sonnet-5`。

本包只动交付面与台账标签,不碰任何算法实现,因此可以和包A/包B完全并行。

## Goal

1. **修 README**(H39/H37/H40 + D5):修掉三条死链(`reports/report.pdf`、`reports/predictor_metrics.json`、`reports/experiment_log.jsonl`);补 Python 版本、CPU/MPS 模式与预计资源;把主叙事从"GB1 专项"更新为"GB1 + AAV 双数据集,AAV 为当前主战场",**结论以 fact `F-885537A3` 为准**(两目标两策略:纯利用赢大量强变体 strong=166;UCB β=3 赢单峰 30/30 达峰 8.4162;LLM 自主两个都没匹配上)。
2. **修 Makefile 入口**(H39):让 `make train` 调真正可执行的入口;把 `make data` 改名或在帮助里说清它只做本地校验不下载。
3. **干净 clone 的端到端 smoke**(H41):提供许可允许的小样本 fixture(或带校验的获取脚本)+ **一条真正能端到端跑通的命令**,让没有 44MB 原始 CSV 的人也能验证流程。现有 16 变体完整景观集成测试可作为起点。
4. **LLM 归属改成实际值**(数据卫生):把 v0.4 起 metrics/manifest/报告正文里的 `gpt-5.6-sol` 改为实际解析值。**注意甄别**:`harness/agents/de-ml.json` 等 agent 声明里写 `gpt-5.6-sol` 是**正确的**(那是派工身份),不要误改;要改的只有"这一跑实际用了哪个模型"的标签。历史报告用**加勘误段**的方式更正,不覆盖原结论文字(仓内已有勘误横幅先例可照抄格式)。

## Context

- **权威审计**:`harness/context/research/assignment-coverage-audit.md`,条目 H32/H37/H39/H40/H41 与 D5 判定;证据 E4(`pdfinfo` 实测 `harness/final-report/report.pdf` 为 A4 四页、八节齐全但内容是旧 GB1 叙事)、E8(README 链接错误 + Makefile 入口错误)。
- **试题原文**:`harness/context/research/AI4S-assignment.md` 三·代码 c(README 需说明运行环境、数据来源、运行命令、主要结果)、三·独立条目(小规模数据可复现)。
- **数据卫生来源**:v0.7 红队线审计,记在 `harness/reports/agentic-v0.7/report.md`;实际解析逻辑在 `agent/llm.py`。
- **勘误格式范本**:`harness/reports/agentic-v0.4/report.md` 与 `harness/context/research/frontier-landscape-synthesis.md` 顶部各有一条勘误横幅;`harness/context/research/plateau-breaking-methods.md` 顶部是最新一条(2026-09-12)。
- **PDF 不归你**:审计的 P0「用当前真源重制 3–5 页 PDF」由 CEO 与报告 v2.0 任务(`task_db4ace109f72a92847c7349fe1`)负责。**你只需保证 README 指向的路径存在且正确**——如果最终 PDF 还没生成,README 就指向当前存在的真源(Markdown),不要为了让链接不空而伪造一个 PDF。

## Required Reading

1. `harness/context/research/assignment-coverage-audit.md`(**最高权威**:H37/H39/H40/H41 与 D5)。
2. `harness/context/research/AI4S-assignment.md`(**标尺**:三·代码 c 原文)。
3. `README.md`、`Makefile`(**待改主体**)。
4. `agent/llm.py`(**权威**:实际模型解析逻辑——第 4 项必须**实跑一次拿到真实 ID**,不许凭推断改标签)。
5. `harness/context/research/v07-consolidated-summary.md`(**权威**:README 主叙事该写成什么样)。

## Entry Conditions

- 独立 worktree(`t-pkgC-delivery`);`.venv` 与数据 symlink 就位。
- 第 4 项开工前:能实跑一次 `agent/llm.py` 的模型解析并打印实际 ID。**跑不出来就停下报,不得凭推断改标签。**

## Dependencies

- 上游:覆盖度审计(`task_d5e9455a1235d1554b1967c708`)。
- 下游:最终报告 v2.0(`task_db4ace109f72a92847c7349fe1`)必须用修正后的 LLM 归属;评委读 README。
- **并发(硬约束)**:包A(`task_0bc2d4d678eea24c4930b60a0e`,动 `evolution/campaign.py`/`agent/pipeline.py`/`agent/llm.py`/`app/demo.py`)、包B(`task_51297081bf4eeb7e466da8a3e1`,动 `features/pools.py`/`models/**`/`analysis/**`)、知识增强实验(`task_25092f640504bf3b040f6adfb5`,动 `knowledge/**`/`agent/auto_researcher.py`)。**全部是禁区。**
- 注意:`agent/llm.py` 是**包A的文件面**。你只**读**它拿实际模型 ID,**不要改它**。

## Execution Surface

- 分支 `t-pkgC-delivery`;dispatcher 注入 cwd。
- **允许写**:`README.md`、`Makefile`、`data/README.md`、smoke fixture 与其测试、`harness/reports/**` 与 `reports/**` 里的**模型标签与勘误段**、`harness/reports/pkgC-delivery/report.md`。
- **禁区**:所有算法实现(`agent/`、`evolution/`、`models/`、`features/`、`knowledge/`、`analysis/`、`app/`)、CI/oracle、并发 worker 的文件面。
- 禁区之外自行判断,事后汇报动了哪些我没预见的面。

## Constraints

- **只改标签,不改数据**:第 4 项任何触碰实验数值(fitness/指标数)的改动都是越界,立即停手报告。
- **历史报告加勘误,不覆盖原结论文字**——错误发生过的痕迹要保留,这本身是诚实性证据。
- **不许伪造链接目标**:宁可 README 指向 Markdown 真源,也不为了填链接造一个空 PDF。
- smoke fixture 必须是**许可允许**的小样本;不得把大数据文件塞进 Git。
- README 的结论必须与 `F-885537A3` 一致,不得复述已被取代的旧结论(如"greedy 直达真峰"、"没有方法能可靠达峰")。
- 若某几轮实际用了不同模型,**分版本如实标注**,不做统一化简。

## Checkpoint

- 第 4 项:实跑拿到实际模型 ID 后**先停并报**(贴解析输出),确认后再批量改标签。
- 第 3 项:smoke 命令跑通后停并报(贴完整命令与输出尾部),CEO 确认它确实是"干净 clone 可跑"再继续。
- **异议型停**:若发现 README 里某条主叙事改动会与在飞的包A/包B结果冲突(例如包A 把 ESM-2 改回主力后 README 的表征描述又要变),停下来报,不要抢先写一个会马上过期的版本。

## CI/Gate Authority Stop Condition

非 CI/gate 任务。已知本仓 standard-task 的 ci 完成门结构性不可满足(fact `F-8ED77039`,上游修复在飞);submit/complete 必被拒。不绕门、不改 CI、不 `transition --force`;失败即 `ha task progress append` 记录后停手。

## Implementation Plan

- 实跑 `agent/llm.py` 解析,记录实际模型 ID 与解析代码路径 → 停报。
- grep 全仓 `gpt-5.6-sol`,逐处判定"标签错"还是"派工身份对",只改前者;历史报告加勘误段。
- 修 README 三条死链 + 运行环境 + 主叙事;修 Makefile 入口与命名。
- 做 smoke fixture + 一条端到端命令,实跑验证 → 停报。
- 写 `harness/reports/pkgC-delivery/report.md`。
- `ha fact record --task task_6d1dc285d32628ed317b9bb4da` 记实际模型 ID 与影响面。

## Deliverable Contract

- 修好的 `README.md` / `Makefile` / smoke fixture + 一条实跑通过的端到端命令。
- 模型标签更正 + 历史报告勘误段。
- `harness/reports/pkgC-delivery/report.md`:改了哪些、哪些 `gpt-5.6-sol` 是正确的没改、smoke 命令与实跑输出。
- ≥1 条 fact;本地 commit,不 push、不开 PR。
- 回报:实际模型 ID、改了几处、smoke 命令是什么。

## Evidence Protocol

- 实际模型 ID 必须来自一次真实解析输出,不得来自文档或推断。
- 死链修复要给"修复后路径确实存在"的 `ls` 证据。
- smoke 命令要贴完整命令与输出尾部,不接受"应该能跑"。
- 区分"标签错"与"派工身份对"两类,分别列清单。

## Verification

- 停手点 = 改动落盘 + smoke 实跑通过 + report + ≥1 fact + 本地 commit。
- CEO 语义验收(是否只动标签没动数据、README 结论是否等于 F-885537A3)不可下放。
