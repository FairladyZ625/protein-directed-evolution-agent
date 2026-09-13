# 研究报告 v0.7

[GitHub · FairladyZ625/protein-directed-evolution-agent](https://github.com/FairladyZ625/protein-directed-evolution-agent)

入口为 `scientific_report_v0.7_two_column.pdf` 或同名离线 HTML。八章正文12页、参考文献1页、附录28页，合计41页；正文源文件为 `report.md`。v0.6原样保留。

## 本版更新

- 纳入V0.8采集因子、V0.9契约因子，以及新完成的12×6预算对照，共12臂；均为seed42，未自行运行多seed。
- 以allocation_source判断主动设参，分别记录默认回显和实际比例。
- 重算复现率的分子、分母和r4–6后段窗口；区分前轮低值相关替换与累计卡片证据，不把复现率当成生物学失败概率。
- 48×6下v09反思对照交集46→8，但首轮分叉先于注入；12×6下前两轮相同、从第3轮分叉，交集12/12/9/6/7/7。两种预算分别解释，不据小差值宣称稳定收益。
- 从清洗后完整AAV表验证候选池最高值8.416205、初始最优9.536457，初始集仅3条高于候选峰；这是设计范围而非Agent失败。
- 恢复v0.5的数学定义。核心公式回到正文，完整协议、Ridge/交互、方差、采集、覆盖/结构权重、上位差分和行为指标位于附录L，EVI位于I。14个原显示公式块逐项记录在formula-inventory.json；旧FULL差值保留为历史说明，不用于当前对照。
- 保留试题八章、首页方法图与未来双循环架构。GitHub链接位于首页顶部并通过PDF链接检查；更新残差机制生图的文字以匹配已完成契约实验。

## 导航

- `chapter-mapping.md`：八章内容及当前PDF页码。
- `evidence/contract-audit.json`：12臂预算、批次、事件链、排除/卡片、复现率、达峰轮与来源字段的独立重算。
- `evidence/new-experiment-arms.json`：三组研究的12臂路径。
- `evidence/aav-domain/`：完整清洗子集压缩CSV、原始表指纹与最高值检查。
- `evidence/sources.json`：112项冻结输入，保留历史来源并新增当前交接、固定代码、原始事件、指标与stdout日志。
- `evidence/imagegen-prompts.json`、`v07-image-edit.json`：实际内置生图/修图记录和选定输出SHA-256。
- `evidence/formula-inventory.json`：v0.5数学公式恢复对照。
- `evidence/verification.json`、`layout-check.json`、`visual-qa/`：数值、图像、公式、链接与页面检查。

正式引用17张图：11张正文图与6张补充图，包含4张生成插画。图S6的更新由内置ImageGen完成，数值图由冻结数据绘制。旧未引用图像和前稿保留作版本来源。

## 重建与验证

Python需numpy、pandas、matplotlib、beautifulsoup4、PyMuPDF；另需Pandoc、Node.js/Playwright及Chrome。推荐使用本机已验证的`/Users/lizeyu/miniforge/bin/python3`。

```bash
python3 build/audit_contract.py
python3 build/figures.py
python3 build/contract_figures.py
python3 build/source_index.py
python3 build/build.py
NODE_PATH=/Users/lizeyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules node build/render.cjs
python3 build/verify.py
```

此流程只重建报告，不运行实验、不调用在线LLM、不重新生图。Pandoc遇到公式转换失败会终止，避免把TeX源码直接带进PDF。渲染后验证页数、全部图像、MathML、首页GitHub链接、112源哈希与新实验断言。

附录I给出后续独立seed配对设计。本版已接收48×6与12×6完成数据，不等待其他实验，也不把其后结果混入冻结版本。
