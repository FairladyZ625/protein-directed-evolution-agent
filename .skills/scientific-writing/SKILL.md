---
name: scientific-writing
description: "面向 AI for Science 领域的高严谨中文学术报告撰写、De-AI 去油打磨、GB/T 7714-2015 文献引证与图文契约规范。"
---

# Scientific Writing Skill (AI4S & 计算生物学专用)

本 Skill 为面向计算生物学、蛋白质工程与 AI for Science 领域的高严谨学术报告写作指南。用于指导智能体在编写、审校与打磨科学报告时，消除口语化 AI 腔调，严格对齐同行评议期刊标准，实现 100% 真实引证与严密的图文契约。

## 适用场景
- 撰写或审校 AI4S 项目技术报告与白皮书；
- 执行中文学术文本的“去 AI 味”（De-AI Rubric）审查；
- 维护与验证 GB/T 7714-2015 顺序编码制参考文献；
- 维护报告正文与图表（Figure Manifest）的边界契约。

## 核心规则与规范

### 1. 语言与文风准则（De-AI Rubric）
- 必须严格遵守 [references/de-ai-chinese-rubric.md](file:///Users/lizeyu/Projects/ai4s-directed-evolution-agent/.skills/scientific-writing/references/de-ai-chinese-rubric.md)；
- 严禁使用夸张、情绪化、第一人称抒情或小说化比喻；
- 始终以第三人称、客观严谨的实验测量值与统计置信度为叙述依据。

### 2. 真实引证规范（GB/T 7714-2015）
- 必须严格遵循 [references/gbt-7714-2015-rules.md](file:///Users/lizeyu/Projects/ai4s-directed-evolution-agent/.skills/scientific-writing/references/gbt-7714-2015-rules.md) 中已核实的 30 篇核心文献；
- 正文中引用的标号 `[N]` 必须与文末参考文献表 1:1 严格对齐；
- 绝不允许任何形式的作者脑补、虚构或套用 DOI。
- 可运行 `python scripts/verify_citations.py <report_path>` 执行自动化校验。

### 3. 图文契约与独立生图解耦
- 必须遵守 [references/figure-manifest.md](file:///Users/lizeyu/Projects/ai4s-directed-evolution-agent/.skills/scientific-writing/references/figure-manifest.md)；
- 文本报告仅负责撰写详尽的中文学术图注（Figure Caption）与预留插桩锚点（`<!-- FIGURE_X_START -->` ... `<!-- FIGURE_X_END -->`）；
- 实际图形的渲染与美化交由独立生图任务执行。
