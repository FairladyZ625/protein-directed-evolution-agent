结论：T5 知识库已完成并提交本地 commit `909ff0a`。

完成内容：

- `knowledge/rules.yaml`
  - 6 条稳定 ID 规则：突变数上限、标准氨基酸、BLOSUM62 保守/激进分级、GB1 位点限制、历史突变优先。
  - 20 种氨基酸理化性质。
- `knowledge/validators.py`
  - 候选突变校验 API。
  - `--no-knowledge` CLI 消融开关。
  - NetworkX 三元组图谱构建。
- `tests/test_knowledge.py`
  - 保守替换放行、激进替换命中、超限及消融、图谱结构测试。

工具证据：

- 定向测试：`3 passed`
- 规则数：6
- 图谱示例：49 节点、83 边
- `--no-knowledge` 返回空约束列表
- `V39W` 命中 `R-BLOSUM-AGGRESSIVE`

已记录 Harness fact：`F-415E0CB9`。

风险：当前 worktree 存在未跟踪 `.venv`，未纳入提交；`origin/main` 引用不可用，因此未执行 rebase。