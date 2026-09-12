# Closeout

## Summary

更难数据集接入的基础设施:bootstrap 不确定性(5 成员重采样给 UCB 非平凡方差)+ ESM-2 全长序列 embedder + avGFP loader 加固 + 池式单测,已合并 master。

交付提交:`fe5a1a5aa7140a8266a6d99b007a298800856c50`(bootstrap 不确定性 + 更难数据集守卫)。

## Verification

42→43 项单测通过;ESM-2 650M 权重本地缓存(2.6GB)、AAV ESM 嵌入缓存已建(173MB/38,265 条);avGFP loader 对 ProteinGym schema 加固。促成 Fact F-752A64DF。

## Residual Risk

avGFP 原始 CSV 未获取、跨数据集诚实对比与 AAV-ESM 完整跑分【延到优化阶段作为独立任务】——本任务只交付基础设施,不含最终跑分。

## Same Mechanism Elsewhere

bootstrap 方差机制与 ESM 编码接口在 predictor 阶梯、pool_campaign、agentic predict 工具处复用。
