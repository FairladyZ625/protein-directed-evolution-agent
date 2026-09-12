# 独立评审：report-v05

## Verdict

打回（changes_requested）。核心报告内容与版式可交付，但在已锁定的系统边界上仍有两项需要补强的证据/措辞；不建议在补强前把本次执行记为无条件通过。

## 工具证据

- `python build/verify.py` 通过：12 页、8 章、30 条引用、5 张图、0 个空表格单元格、0 个版式溢出，`experiments_rerun=false`。
- GB1 报告与 `evidence/gb1_summary.json` 一致：FWAA/8.761966；96 条/轮、3 轮；四策略累计 beneficial hits 为 7/154/176/125。
- AAV 报告与 `evidence/aav_plot_data.json` 一致；正文区分门内未测池最大值 8.416205 与初始已知值 9.536457，未把池内峰写成全局峰。
- 正文写出 149,361 实测组合、160,000 理论组合、10,639 缺测、ESM-2 650M/1,280 维与 one-hot，并保留 AB=NA 的上位性边界。
- 第 7.6 节已加入“研究者应调用和验证工具，而非无工具猜 fitness”的论述；未把微积分能力或通用 LLM 能力写成实验结论。
- `bibliography-audit.json` 有 30 条条目，验证脚本检查正文引用和 DOI 链接均存在。

## Findings

### P1 — 商业 API 边界无法由交付证据复核

`report.md:146` 只写“提供 LLM 接口”，并称 GB1 记录使用 `claude-sonnet-5` 通过 hypothesis port 接入；`evidence/gb1_summary.json` 也只有同名字符串。交付目录没有提供商、API 调用元数据、脱敏请求/响应记录或可核验运行日志，无法确认主结果满足已锁定的“商业 API”口径，也无法区分真实调用与配置标签。AAV 矩阵没有调用 LLM，这一点正文已说明。

修复方向：补最小脱敏 provenance（provider、model、调用阶段、schema 版本、时间/运行 ID；不提交密钥和完整 prompt），或将正文降格为“记录标注为 claude-sonnet-5，实际 API 调用未随本交付复核”，并明确 GB1 中哪些候选由 LLM 产生、哪些由代码完成。

### P2 — 事件流“交付层”边界没有在正文中明确落地

图 1 的 prompt/图示包含 `Event log`，第 4.3 节只讨论 SHA-256 链；正文没有明确声明事件流是前端过程回放与审计链的交付层，也没有说明哪些角色输出必须写入事件流。仅阅读 PDF 正文容易把它理解成可选 provenance 装饰，而不是已锁定的交付边界。

修复方向：在第 4.3 节明确：事件流属于交付层，承载候选生成、规则校验、冻结、Oracle/预测器调用、结果回写和审计回放；SHA 链只提供篡改检测，不替代事件流，也不证明因果性。若本版只展示概念图而未交付事件流实现，应明确标为设计边界，避免暗示已实现。

## Residual risk / unverified

- 未重新运行实验、训练模型或逐篇联网复核文献；本轮只检查随交付复制的源快照、报告源码、HTML/PDF 和定向 verify 输出。
- 主控已完成逐页视觉检查；本轮验证了 PDF 文本边界和 layout-check，但未重新逐页放大检查图片中文字可读性。
- 未调用 review-consent、complete、push 或合并。

## Review basis

审阅依据为任务计划、AI4S worker handbook、AI4S-assignment.md、交付提交 `1b9fb16b775d6adba75eed9771eb79b8753e81cd` 及本轮实际工具输出。
