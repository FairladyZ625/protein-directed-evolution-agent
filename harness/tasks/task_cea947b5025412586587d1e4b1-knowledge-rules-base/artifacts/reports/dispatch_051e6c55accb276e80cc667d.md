# Independent execution review

- Task: `task_cea947b5025412586587d1e4b1`
- Execution: `exe_7cc5a1dbb2c53daa1fc67fd7b4`
- Iteration: 0
- Frozen submission digest: `sha256:15cb06cab0e42b8e2052036f5b7c24c3fdf0b5b82ca8db09d0d5d573e0e162b4`
- Frozen delivery commit: `4f456890ca43dfe007e4b17c63c06c3fa26f147f`
- Verdict: `changes_requested`

## Verdict

打回。冻结提交中的基础实现可运行，原定向测试为 `3 passed in 0.15s`，`--no-knowledge` 返回空列表，图谱样例为 49 节点、83 边且包含 `has_property`、`occurs_at`、`contains`、`improves` 四类关系。但实现没有兑现任务契约中“BLOSUM62 保守分级”和“优先组合历史好单点”两项承重能力。

## Tool evidence

1. `git ls-tree 4f456890...` 确认冻结树包含 `knowledge/rules.yaml`、`knowledge/validators.py`、`tests/test_knowledge.py`；评审从该提交经 `git archive` 导出到临时目录执行，没有以当前工作区文件替代冻结内容。
2. 冻结树运行 `.venv/bin/python -m pytest -q tests/test_knowledge.py`，真实输出：`3 passed in 0.15s`。
3. 阳性对照 `validate_candidate("V39W")` 能产生 BLOSUM=-3 且激进规则失败，证明检测路径会出声。
4. 覆盖性对照 `validate_candidate("C39W")` 只返回数量、字母表和位点三项，完全没有 `R-BLOSUM-CONSERVATIVE` 或 `R-BLOSUM-AGGRESSIVE`。磁盘 `rules.yaml` 的 `blosum62` 只有 10 个行键且各行是部分列，不是 20×20 BLOSUM62；`_score` 还以 `dict.get(...) or ...` 取值，使合法的 0 分条目被当作缺失值。
5. 声明/实现双侧核验：`rules.yaml` 声明 6 个 ID，包括 `R-PRIORITIZE-HISTORICAL`；对 `validate_candidate(["V39I", "D40E"])` 汇总实际输出只有另外 5 个 ID，`validators.py` 没有历史单点数据参数或该规则的任何输出分支。
6. 图谱对照 `build_knowledge_graph([{id: "v1", mutations: ["V39I"], fitness: 2.0}])` 实测为 49 节点、83 边，关系集合与题面四种示例一致。该结果也表明 closeout 引用的两个 standing facts 对同一类样例分别声称 49/50 节点，至少一条计数已失真，不能同时作为可靠验收证据。

## Defects

1. **BLOSUM62 覆盖不完整（阻断）**：合法 20aa 替换中大量组合无法分类，且 0 分替换被 `_score` 的 truthiness 写法吞掉。Agent 会在这些候选上静默缺少保守/激进规则，违反“BLOSUM62 保守分级”和“validators 可返回规则命中/违规”的契约。
2. **历史好单点规则未实现（阻断）**：`R-PRIORITIZE-HISTORICAL` 仅存在于 YAML，校验器既不接收历史 fitness，也不产生此稳定 ID，无法支撑 rationale 引用或知识增强决策。
3. **测试覆盖不足**：现有测试只覆盖 `V→I` 和 `V→W` 两个恰好存在于稀疏矩阵的替换，因此没有暴露全字母覆盖、0 分矩阵项和第六条规则缺失。
4. **事实计数冲突**：`F-415E0CB9` 记 49 节点，`F-DB275358` 记 50 节点；本轮冻结树复测为 49。后续 closeout 应只引用复现一致的事实。

## Actionable repair

1. 放入可查证的完整 20×20 BLOSUM62（或可靠库加载），用显式 `is not None` 处理 0 分；对全部 400 个有序氨基酸对做覆盖测试，并至少加入一个 0 分和一个原稀疏表缺失对的阳性对照。
2. 为历史规则定义明确输入契约（例如历史单点 `{mutation: fitness}` 与阈值/排序），让 validator 对候选稳定输出 `R-PRIORITIZE-HISTORICAL` 的 pass/violate 与可引用 note；同时验证 `--no-knowledge` 仍短路所有规则。
3. 增加测试断言：YAML 中每个可执行规则 ID 均能在对应场景被触发；保留当前图谱四关系与消融测试。
4. 修复后重新记录唯一、可复现的图谱计数事实，并在新的 submission iteration 中提交复核。

## Unverified

- `knowledge_agent AAV strong 86 vs greedy 85` 属跨任务实验结果，本任务契约的定向验收不依赖该数字，本轮未重跑。
- 未执行全量测试矩阵，遵循任务只跑 `tests/test_knowledge.py` 的限制。
