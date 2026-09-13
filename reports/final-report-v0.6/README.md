# 研究报告 v0.6 · 附录与插画修订

入口：`scientific_report_v0.6_two_column.pdf` 或同名离线 HTML。全文 23 页：正文 8 页、参考文献 1 页、附录 14 页。Markdown 正文为 `report.md`。

## 本轮调整

首页压紧标题与摘要，并加入五角色生图总览和完整研究问题。图 1、3、8 使用内置 ImageGen，延续用户认可的 v0.5 插画风格：纯白背景、柔和蓝绿桃色、深色轮廓、简洁图标与英文标签。已逐项核对标签和箭头，修正 Hypothesis→Designer 连线、Critic→Event log 路径以及 GB1 四残基示意。

正文集中在模型、角色、搜索结果、组合效应和研究者定位。完整模型表、参数扫描、消费者接线、调用审计、采集矩阵、逐阶分析、保守性统计、首轮 V0.8 条件、复现与数据交接，以及全部44项证据来源索引，均已编入附录 A–K。

实验数字与44项冻结输入不变。本次是呈现修订；V0.8后续轮次由报告v0.7单独整合。重排前稿保存在 `evidence/report-before-appendix-polish.md`，用户提供的参考稿和讨论纪要仍完整保留。

## 文件导航

- `report.md`：8节正文、30条参考文献和完整附录。
- `figures/*_imagegen.png`：3张正式生成插画。旧矢量机制图保留作版本记录，不再用于PDF。
- `evidence/imagegen-prompts.json`：完整生成/修图提示词、内置工具说明、选定输出路径与SHA-256。工具接口未暴露具体模型版本选择。
- `figures/`：正式采用13张图，其中8张正文图、5张补充图；数值图保留PNG/SVG。
- `evidence/sources.json`：44项原始输入快照及哈希。
- `evidence/verification.json`、`layout-check.json`、`visual-qa/`：数值、图像完整性及逐页验证。
- `verification.md`：实际检查记录。

## 离线重建

依赖 Python（numpy、matplotlib、beautifulsoup4、PyMuPDF）、Pandoc、Node.js（playwright）及 Chrome。

```bash
python3 build/figures.py
python3 build/build.py
NODE_PATH=/Users/lizeyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules node build/render.cjs
/Users/lizeyu/miniforge/bin/python3 build/verify.py
```

其他机器配置自己的Python、Node模块路径与 `CHROME_EXECUTABLE`。重建使用已冻结数据和已保存生图，不运行实验、不在线生成图像；PDF页数与实际引用图片动态核验。HTML内嵌全部图像，可离线阅读。
