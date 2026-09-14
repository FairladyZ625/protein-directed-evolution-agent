已完成返工并留下本地提交：

- Commit：`f9a5bd16f0aa75bf6822d06866a8e1e363bd7162`
- 分支：`codex/task-cea947-knowledge-repair`
- 作者：`ZeyuLi`
- 仅修改 `knowledge/` 和 `tests/test_knowledge.py`

完成内容：

- 补齐标准 BLOSUM62：20×20、400 个有向条目、210 个含对角无序对，并注明 NCBI 来源。
- `_score` 改用显式键存在判断，正确保留 0 分。
- validator 实际输出 `R-PRIORITIZE-HISTORICAL`，覆盖命中与未命中。
- 保持 `--no-knowledge` 返回 `[]`。

验证证据：

```text
pytest -q tests/test_knowledge.py
..... [100%]
5 passed in 0.23s
```

额外探针：

```text
rows=20 directed_entries=400 unordered_with_diagonal=210
all_400_substitutions_classified=True missing=[]
C39W_score=-2
declared_minus_emitted=[]
no_knowledge=[]
```

已同步最新 `origin/main`，分支 ahead 1，工作树洁净。承重事实已记录为 `F-8CA28AD5`。未 push、未创建 PR。