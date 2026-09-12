# Closeout

## Summary

GB1 数据管线+特征:加载校验 149,361 个有真值变体、突变解析(WT=VDGV/4 位点)、train/holdout/query 三池切分(5,000 / 50,000 / 94,361,互不相交、并集 149,361、WT 在 train)、one-hot 与 ESM-2 特征(嵌入按批缓存)。为全链路提供统一数据与特征底座。

## Verification

- **本任务定向单测**:`tests/test_data_pipeline.py` = **6 passed**(clean-env 可复现)。
- 三池实测 5,000 / 50,000 / 94,361,互不相交、并集 149,361、WT 在 train。
- 仓库内已提交、clean-env 可命中的特征证据:one-hot 缓存 `(149361, 80)`;train ESM 缓存命中输出 `(5000, 1280)`。
- 促成 Fact `F-997BBF50`,与上述事实及 completionClaim 一致。
- 说明:全套回归 `pytest tests/` = 43 passed 仅作整体健康度参考,本任务完成以定向 6 passed 为准。

## Residual Risk

- ESM-2 650M **权重为机器本地**(`~/.cache/torch/hub/checkpoints/esm2_t33_650M_UR50D.pt`,不在仓库、gitignore),clean-env 全量 runtime 提取依赖可下载权重(网络/证书条件);**仓库内自包含的可验证证据仅为已提交的 one-hot 缓存与 train 批次 ESM 缓存**,不含全量 650M 实时提取的独立验证。
- 大数据原始文件 gitignore,评委按 `data/README` 下载。

## Same Mechanism Elsewhere

能力交付(非缺陷修复):定长序列→特征的编码机制在 `evolution/datasets.py` 的 `one_hot_encoder`/`esm_encoder` 复用,后续 AAV/avGFP loader 均调用同一编码接口;仓库搜索确认下游 pool_campaign 与 agentic predict 工具都经此接口取特征。
