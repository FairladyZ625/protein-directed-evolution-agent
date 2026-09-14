## Summary
交付 Report v0.5：12页双栏PDF、Markdown、离线HTML、两张ImageGen架构图、三张程序化数据图与证据快照。交付提交 193c1947eac558b156bbc2c775282112d5a7ed02，分支codex/report-v05，工作树.worktrees/report-v05。文件均位于reports/final-report-v0.5。
用户补充的研究者角色与预测器分工论证已纳入第7.6节（PDF第9页）。独立复核指出的两项问题已修订：API模型标注降格并明确逐次provenance未复核；第4.3节补明事件流的交付层职责与覆盖范围。

## Verification
python3 reports/final-report-v0.5/build/verify.py：12页、8章、30引用、5图、零空数据格、零页内溢出；GB1源数值、输入快照、数学渲染、PDF文本边界验证通过。
已逐页目视12页，修正公式和第8页底部间距；两张生图已核对英文标签及流向，图5两次定向修改。
源证据v07-peak-mechanism.md保持逐字节复制，包含源文件既有EOF空行；其他新增文件的git diff --check通过。没有重跑实验或全量代码CI。

## Residual Risk
文献沿用存档的出版元数据，未重新在线逐篇核对30篇全文。GB1预测表仍为旧汇总点估计，缺少误差分布并已明确标注；生成式概念图不作为实验或结构证据。其余边界详见第8.2节。

## Same Mechanism Elsewhere
已在摘要、Agent定位、统计表、图注和结论统一处理同类过强断言、确定性重复误读、候选池最优混淆以及已实现与提案混写；保留AB缺测。未修改其他版本报告和业务代码。
