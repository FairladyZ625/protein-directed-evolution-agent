## Summary

完成探索税形式化理论报告及可复跑数学检查。交付提交 cbb4a71b9d5e72c0af00aa0146943ecc6376f7fc，位于 task/exploration-tax-voi 分支。任务工件 artifacts/exploration-tax-formalization.md 已通过 Harness 发布；提交快照在 research/exploration-tax-voi/。报告包含有符号探索税、有限视界分解、条件命中凸性、有限预算后悔界、后验收敛与 VoI 采集方程；不修改运行算法。

## Verification

报告有 5828 个汉字，超过 3500 字要求。
python research/exploration-tax-voi/verify.py 通过：实测差值算术、四槽混合策略穷举、Bellman 恒等式、高斯信息恒等式及凸性数值示例。
git diff --check 通过；三个指定文献已查阅原文并在报告附链接。
事实 F-F69AE97E 已关联本任务，记录报告级数值核对与证据局限。
尚未取得独立执行审查与所有者同意。

## Residual Risk

未重放原始 AAV 事件流；v0.5 材料未提供独立终态数值，不能声称 v0.1–v0.5 原始数据完全吻合，此项验收仍有缺口。
VoI 松弛未实现或实测，证明依赖明确列出的模型、校准、反馈和效用条件。
完整报告在规范任务包中由 daemon 管理；公开 Git 快照已从隔离分支快进到派工绑定工作区；未推送远端。

## Same Mechanism Elsewhere

机制：信息缩减只有在剩余决策中兑现为终端效用才值得挤占测定机会。
本任务只增加理论文档，不改变运行行为，故代码同机制修复搜索不适用。对指定科学报告和 v0.5 调研定向检索探索比例、累计最佳值和预算：两处均包含追加预算后最佳值下降的解释。报告第 8 节说明它不能作为同一累计轨迹退化的证据，并要求后续核对原始运行口径。
