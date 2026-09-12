# Milestone: Final Scientific Report v0.3 完备答卷与自演进体系深度论证

Task Contract: harness-task v1

## Brief
编制并交付高水准双轨制学术科研成果体系：
1. **主技术报告（Main Scientific Report v0.3）**：严格锚定明度数智 AI4S 笔试题 8 大指定章节规范，以最高学术严谨度阐明蛋白质定向进化智能体系统的完整研发答卷。
2. **前沿思考与认知升维报告（Supplementary Research & Thinking Report）**：系统沉淀从 v0.1 到 v0.7 的实验认知演进、人机协同外环因果归因、微观大模型探索税与 UCB 收敛机制、真实科研目标契约与多目标帕累托哲学、以及五大流水线未来蓝图。

## Goal
输出符合国际计算生物学/AI4S 会议与同行评审标准的正式中文学术成果体系：
- 主答卷报告：`reports/final-report-v0.3/report.md`（严格 8 章节，PDF 排版就绪）；
- 思考探索报告：`reports/final-report-v0.3/supplementary_thinking_report.md`；
- 双向同步至用户工作区 `protein-directed-evolution-agent/reports/` 对应位置；
- 建立端到端可追溯的证据链与文献引证网络（GB/T 7714-2015 格式，30+ 篇真实顶级同行评审论文）。

## Context
在前期研发中，团队已在 GB1（14.9万变体，首轮直击 8.762 全局真峰 FWAA）与 AAV（3.8万变体，历经 v0.1 放养失活、v0.2 物理门禁、v0.3 代理体检、v0.4 上位感知击穿加性天花板、v0.5 批次退火、v0.7 确定性 UCB β=3 在 30/30 种子下 100% 达峰 8.4162）上积累了大量翔实实验数据。
同时，团队深刻洞察并厘清了多重关键科学悖论：
1. **9.536 冷启动已知 vs 8.4162 未测候选池全局真峰** 的严格物理与实验边界；
2. **微观连续数值收敛打不过固定数学公式**（LLM 卡在 7.829 鞍点，UCB 100% 达峰 8.4162）的诚实负结果；
3. **大模型在外环作为司令官与因果归因引擎** 的核心系统定位；
4. **Target-Driven Stopping（目标驱动停止）与 6~7 突变位点多目标帕累托优化** 的真实科研哲学；
5. **冷启动 71.88% 缺失残基对雷达与 3D 接触软约束** 的知识库新范式。
本任务负责将上述所有实验结果、理论推导、反思证伪与前沿蓝图沉淀为极高学术水准的双轨制报告体系。

## Required Reading
1. `harness/context/research/AI4S-assignment.md`: 明度数智官方 8 大章节考核规范与加分项标准；
2. `harness/reports/final-report-v0.2/report.md`: 既有 8 章基础文本（事实与基线数据来源）；
3. `reports/explainer_for_humans.html`: 详尽的理论推导、数学证明、因果归因与 12 大问答；
4. `harness/context/research/frontier-landscape-synthesis.md`: 国际 2024~2026 前沿学术文献综述；
5. `.skills/scientific-writing/references/gbt-7714-2015-rules.md`: GB/T 7714-2015 真实文献引证库；
6. `.skills/scientific-writing/references/de-ai-chinese-rubric.md`: 中文学术去 AI 味规范与替换清单。

## Entry Conditions
1. AAV 各代完整实验证据流与哈希链（v0.1 ~ v0.7）已完备固化；
2. 30 篇核心参考文献经核验全要素真实，无虚构作者或套用 DOI；
3. 5 大科学图表（系统架构图、GB1收敛图、AAV上位景观、探索税对比、五机双循环 RSI 架构）插桩接口已定义完毕；
4. 本任务的 `artifacts/` 目录已装配好核心理论与实验事实底本。

## Dependencies
- 前序依赖：v0.1~v0.7 算法评测数据、Streamlit 前端数据层、学术文献规范；
- 后续承接：报告审阅委员会、独立生图/制版工作流、答辩交付。

## Execution Surface
- 主工作区：`/Users/lizeyu/Projects/ai4s-directed-evolution-agent`
- 镜像工作区：`/Users/lizeyu/Projects/protein-directed-evolution-agent`
- 核心写入：`harness/tasks/task_ee0e0b26e540664dac1e6c3f29-scientific-report-v0-3/artifacts/`, `harness/reports/final-report-v0.3/`, `reports/`

## Constraints
1. **严格 8 章节答卷**：主报告必须 100% 严格对齐官方题目要求的 8 大章节编号与标题，绝不跳步或漏项；
2. **严谨学术去 AI 味**：严禁使用口语化、浮夸煽情或轻佻措辞，严禁第一人称情绪化表达，遵循《自然》/《中国科学》中文学术论文体例；
3. **真实文献引证**：所有引用的论文必须真实存在且元数据准确无误；
4. **诚实科学边界**：客观陈述大模型在微观数值收敛上的负结果，绝不粉饰或隐瞒探索税（0.5872），突出科学诚实性；
5. **分卷承载**：前沿思考、五大流水线与人机协同演进内容独立沉淀至 Supplementary Report，既确保答卷简洁聚焦，又展现深厚研发视野。

## Checkpoint
1. `artifacts/` 资料库装配完成并通过校验；
2. 主报告（8 章节）初稿生成并通过去 AI 味与引证校验；
3. Supplementary 思考报告生成并通过理论严谨性校验；
4. 双仓同步与排版校验通过。

## CI/Gate Authority Stop Condition
非 CI 权限改动，纯文档与学术规范交付。无需修改 CI 权威面。

## Implementation Plan
1. **阶段一：工件素材装配（Artifacts Assembly）**
   - 编写 `01-exam-contract-and-mapping.md`（8 章节逐项考点映射表）；
   - 编写 `02-empirical-findings-and-paradoxes.md`（9.536 vs 8.4162、0.5872 探索税、UCB β=3 验证、人机协同外环因果归因等实证论述）；
   - 编写 `03-real-world-philosophy-and-frontiers.md`（Target-Driven Stopping、6~7位点帕累托优化、71.88%缺失残基雷达、五大流水线蓝图）；
   - 编写 `04-academic-writing-and-citation-spec.md`（30+ 真实文献引证库与去 AI 味规范）。
2. **阶段二：编写主答卷报告（Main Scientific Report v0.3）**
   - 严格按 8 章节布局撰写高严谨学术 Markdown 论文；
   - 整合 GB1 与 AAV 实验数据、三级预测模型梯队、五角色 Agent 设计与消融对比；
   - 融入图表插桩与完整 GB/T 7714 文献列表。
3. **阶段三：编写补充前沿思考报告（Supplementary Research & Thinking Report）**
   - 系统阐述系统演化哲学、人机协同自证伪、内环数学与外环智能体分工、五大流水线与自演进自主实验室（SDL）蓝图。
4. **阶段四：学术校验与双仓同步**
   - 运行引证闭环检查脚本；
   - 同步至双仓库 `reports/` 目录。

## Deliverable Contract
- 主答卷：`harness/reports/final-report-v0.3/report.md`
- 补充思考：`harness/reports/final-report-v0.3/supplementary_thinking_report.md`
- 双仓同步：镜像至 `protein-directed-evolution-agent/reports/`
- 任务材料工件：`harness/tasks/task_ee0e0b26e540664dac1e6c3f29-scientific-report-v0-3/artifacts/` 下 4 份完整学术底本。

## Evidence Protocol
提供生成文件的 SHA-256 指纹、字数统计、8 章节结构核对单与 30+ 篇文献对齐清单。

## Verification
- 检查主报告 8 章节与题目要求 100% 对应；
- 检查学术用语严谨性与图表引用完整性；
- 检查双仓镜像文件完全一致。
