# Closeout

## Summary

知识库/规则库:rules.yaml(突变规则+BLOSUM62)+ validators + networkx 关系图谱 + --no-knowledge 消融开关;供 agent 知识增强与消融对照。

## Verification

validators 单测通过;knowledge_agent 策略在 AAV strong 命中 86 vs greedy 85(BLOSUM 先验小幅增益);--no-knowledge 消融路径验证。促成 Fact F-415E0CB9、F-DB275358。

## Residual Risk

知识规则目前偏通用生化先验;领域专有规则可扩充。BLOSUM 先验在崎岖地形增益有限(见 agentic-v0.1 尸检)。

## Same Mechanism Elsewhere

知识守卫机制(BLOSUM 保守性先验)在 pool_campaign._rank 的 knowledge_agent 与 v0.2 计划的门禁流复用,压制'探索选中死蛋白'。
