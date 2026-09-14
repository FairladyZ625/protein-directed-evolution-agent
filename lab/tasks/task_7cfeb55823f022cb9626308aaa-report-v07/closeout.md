## Summary

交付提交 fbfd5c64ed74660d8e29fd5be200497102316368 ，隔离分支codex/report-v07。v0.7完整PDF/HTML/MD，正文八章12页，总41页；112来源、12实验臂、17图，恢复数学与首页GitHub，整合两份工程交接及第八章设计。v0.6未改。

## Verification

在.worktrees/report-v07运行build/audit_contract.py、build/build.py、build/render.cjs、build/verify.py通过；12事件链、预算、残差、批次、比例分配、复现分母与112源hash通过，41页无溢出，全部页面联系图目视复核。事实F-C6A9A47D。Python使用/Users/lizeyu/miniforge/bin/python3。

## Residual Risk

新实验均seed42；契约为复合处理，单次产量差不作总体因果效应。v09在48×6首轮差异先于卡片，跨契约卡片不相同；12×6后段指标两臂相同。无新增实验。生成机制图已目检，数值图来自冻结数据。

## Same Mechanism Elsewhere

allocation_source与实际整数分配共同审计；不能仅凭requested字段证明主动选择。历史实验与当前协议分别呈现。附录H.7核对第二份交接：不将探索税、无证据或地板强制纯利用的解释直接采信；公式按当前代码含义恢复。
