# Closeout

## Summary

交付 `harness/context/research/kb-iteration-research.md`:对本链路"知识库"这一层的现状盘点与迭代方向研究——当前 KB 到底编码了什么、在链路里怎么用、局限在哪,以及有哪些 answer-agnostic 的更丰富先验(进化耦合/结构/保守性/PLM)值得加,按(a)答案无关合法性(b)笼内可行性(c)帮助暴露隐形上位峰的潜力三维打分。

结论是**诚实的小迭代**而不是大工程:当前 KB 只有通用 BLOSUM62 + 20 种氨基酸理化属性,且只当**二元门禁**用(HD≤4 且 mean BLOSUM62≥0),没有任何 AAV 特异的结构/耦合/保守性信息,`build_knowledge_graph` 甚至没有被 `agent/auto_researcher.py` 消费。推荐的首选迭代是"具体残基对缺测覆盖 + 理化多样性引导探索",其次是结构接触软权重;DCA 全量与新 ESM 推理明确后置——ESM zero-shot 在本题已是实测负例,不当银弹。

最承重的实证发现:cold-start 覆盖了全部 378 个**位点对**,但门内 11130 种**具体残基对**中有 7937 种从未被测(占 9533 个门内候选的 71.88%)。这为 v0.7 的峰机制结论("关键二阶组合缺测")提供了独立的、答案无关的量化支撑——不看测试标签也能指出"哪些组合值得测"。

## Verification

- 文档实存并已 canonical 登记:`harness/context/research/kb-iteration-research.md`;fact `F-159073F2`。
- 覆盖率统计经审计复跑一致,且脚本**未读取 fitness 列**,answer-agnostic 边界成立。
- 与独立线互证:`harness/context/research/v07-peak-mechanism.md`(另一路 Astra,不同 worktree、无交叉)独立得出"关键二阶组合缺测"为峰隐形根因,与本文档的覆盖率实证在机制上一致。
- 现有 KB 局限经 CEO 实读 `knowledge/rules.yaml` 与 `knowledge/validators.py` 确认:仅 `R-BLOSUM-CONSERVATIVE`(score≥1)与 `R-BLOSUM-AGGRESSIVE`(score>−1)两条规则,`build_knowledge_graph` 无调用点。
- 附带发现并记录:KB 代码含 GB1 专用遗留硬编码(位点 39/40/41/54、FWAA),在 AAV 主战场是死代码。

## Residual Risk

- **收益未证明**:推荐的"残基对缺测覆盖引导探索"只证明了它能增加低预测值候选的被测机会,**没有证明它能提高达峰率**。在写进最终报告时必须按 future-work 措辞,不得声称已验证有效。
- 三维打分中"帮助暴露隐形峰的潜力"一维是机制推断而非实测,与(a)(b)两维的证据等级不同,文档已分别标注。
- 本任务为 codex 本地无联网执行,候选知识源的可获得性(如 AAV capsid P03135 结构、MSA 深度)基于领域知识推断,未实际拉取数据验证。
- GB1 遗留硬编码尚未清理,留在代码里会误导读者;已另立清理任务承接。

## Same Mechanism Elsewhere

"一个模块声明了能力但没有调用点"(`build_knowledge_graph` 未接线)这个模式在本仓不止一处:研究原型 `research/prototypes/` 下的 VoI/上位算法同样是"存在但未接入主链路"。通用纪律取自编排护栏——**存在 ≠ 被接线**,验收一个模块必须 grep 调用点,躺在仓库里没有调用者与"没做"同形。最终报告在描述系统能力时,须区分"已接入主链路"与"已实现但未接入"两类,不得混为一谈。
