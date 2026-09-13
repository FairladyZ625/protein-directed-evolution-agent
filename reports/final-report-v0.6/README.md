# 研究报告 v0.6

入口为 `scientific_report_v0.6_two_column.pdf`（18 页）或同名离线 HTML；正文源文件为 `report.md`。

本版在本会话 v0.5 底稿上重写，保留收到的另一版 v0.6 与讨论纪要于 `reference_received/`。正文补齐五角色实际数据流、GB1/AAV 跨轮反馈差异、预测器与 α 扫描、三种冷启动、LLM 实际预算、AAV 知识消融与固定采集矩阵、突变阶数和保守性。第八章纳入用户最新提供的 V0.8 首轮单 seed 冒烟，并将第二轮 2×2 保持为进行中的实验。

## 产物

- `report.md`：八章正文、附录与 30 条参考文献。
- `figures/`：12 张主图与 1 张附图，各含 300 dpi PNG 和 SVG。
- `evidence/sources.json`：44 项冻结输入的原路径、快照位置和 SHA-256；基础代码为 `80f4447c5f8ee26267e98199e900230459b785b8`。
- `evidence/v08-*`：另行收到的 V0.8 冒烟报告、两臂指标与原始压缩事件；不是基础代码版本生成的实验。
- `evidence/verification.json`：源文件哈希、V0.8 逐轮集合哈希、残差恒等式、GB1 实际查询、PDF 页数与布局检查。
- `v07-data-receipt.md`：下一版的数据接收与比较条件。
- `verification.md`：本次实际验证记录。

参考资料中有部分过度结论，正文按代码和数据校正。例如：直接低阶覆盖指所有 k 个（k−1）阶组成变体；GB1 LLM 产量比较需使用实际查询分母；AAV 低阶缺测限制机制分解，但不阻止找到池内 ABC；V0.8 第一轮改变工具动作却没有改变送测集合。

## 离线重建

依赖 Python（numpy、matplotlib、beautifulsoup4、PyMuPDF）、Pandoc、Node.js（playwright）和 Chrome。首次捕获证据脚本 `build/snapshot.py` 依赖原仓库和可用的历史资料；常规重建直接使用已冻结的 evidence，不再捕获活动实验。

```bash
python3 build/figures.py
python3 build/build.py
NODE_PATH=/Users/lizeyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules node build/render.cjs
python3 build/verify.py
```

其他机器可配置 Node 模块路径与 `CHROME_EXECUTABLE`。以上流程只重建报告，不训练模型、不运行 campaign、不调用在线 LLM。HTML 内嵌全部图像，可离线打开。PNG/SVG 图表由冻结数值生成；机制图用精确标注的矢量绘图重建，以对应当前执行路径。
