# Scientific Report v0.5

交付：`scientific_report_v0.5_two_column.pdf`（12页），对应独立离线HTML、`report.md`、图像与证据摘录。

## 主要修订

- 保留八章主题，收紧大模型能力、结构机制和统计显著性的外推。
- 第7.6节新增用户提出的“研究者角色与预测器角色的区分”：训练目标与任务目标不等同，Agent应选择、调用与验证预测工具，不能以通用知识替代任务校准。
- 区分GB1达峰和产量；区分AAV确定性单轨迹与30个采集随机种子；Seed42未混入统计。
- AAV strong阈值改为≥，AB缺测保留为NA；修正旧稿若干全长序列转录错误的呈现方式，正文以零基突变标注与核实的WT序列为准。
- 图1、图5由内置ImageGen按用户学术插画风格生成；完整最终prompt见evidence/imagegen-prompts.json。图5经两次定向编辑修正背景与箭头。
- 三张数据图程序化重绘；图3为AAV结果、图4为实测局部子图，按首次出现顺序编号。
- 双栏正文、跨栏图表、短表头、单一图注；公式采用本地MathML，无网络字体或脚本依赖。

## 重建

需要Python（matplotlib、numpy、beautifulsoup4、PyMuPDF）、pandoc、Node.js、playwright和本机Chrome。构建脚本从自身路径解析资源。在仓库根运行：

```sh
python3 reports/final-report-v0.5/build/figures.py
python3 reports/final-report-v0.5/build/build.py
node reports/final-report-v0.5/build/render.cjs
python3 reports/final-report-v0.5/build/verify.py
```

若playwright不在默认Node搜索路径，通过`NODE_PATH`指定已安装模块目录。浏览器默认macOS Google Chrome安装位置；可用`CHROME_EXECUTABLE`覆盖。生成式图像已固定保存，重建PDF不重新请求生图。

## 证据与范围

GB1主结果来自gb1_summary.json；AAV来自v07-multiseed-robustness.md；局部分析来自v07-peak-mechanism.md与epistasis.json。输入快照校验和见sources.json。文献沿用已保存的bibliography-audit.json；修订时另检查Meta官方ESM说明（https://github.com/facebookresearch/esm），用于核对表征/结构预测/变体效应工具的区别，未声称重新联网逐篇审计30篇文献。

本次没有重跑闭环实验或训练模型。verification.json记录数字、引用、数学渲染、页内边界及文件检查；layout-check.json记录逐页几何检查。源材料中的历史结论与本版的审慎解释应区分阅读。
