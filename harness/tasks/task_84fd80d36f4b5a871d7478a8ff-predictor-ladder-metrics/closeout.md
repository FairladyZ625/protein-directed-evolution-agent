# Closeout

## Summary

预测器阶梯:one-hot·ESM-2 × Ridge·XGBoost·MLP 三级,5-seed bootstrap 给出均值+方差(供 UCB),Spearman/Pearson/MSE/Top-k 指标;随机划分 vs HD 外推双口径诚实评测。

## Verification

predictor_ladder.json 落库:随机划分 esm2·ridge 0.493,HD 外推 esm2·mlp 0.493(ESM 泛化更好);5-seed 方差非平凡(供后续 UCB)。促成 Fact F-5182F98C。

## Residual Risk

HD 外推口径下所有模型 Spearman 仅 0.28-0.49,反映真实困难;这是诚实结果非缺陷。

## Same Mechanism Elsewhere

能力交付:bootstrap 方差机制被 evolution/pool_campaign._rank 的 UCB 项(LAMBDA_UCB·√var)与 agentic 的 predict 工具复用。
