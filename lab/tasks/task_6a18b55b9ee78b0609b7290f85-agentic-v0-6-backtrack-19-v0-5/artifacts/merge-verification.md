# agentic v0.6 backtrack 合并验证

## 冲突裁决

- import / 基础辅助函数：并存。保留 v0.6 的 `Counter`、`math` 与 backtrack primitives，同时保留主线的 `contextlib`、`signal`、`threading`、wall-clock timeout 和 mutation-code helpers。
- 默认 prompt：沿用 `471536b` 的双段落结构；`SYSTEM_PROMPT` 仍格式化为 `_V05_ACQUISITION_PARAGRAPH`，仅 backtrack 模式运行时替换为 `_V06_ACQUISITION_PARAGRAPH` 并追加 full/semi meta-layer note。
- `run_autoresearch` 参数与状态：并存。主线 `no_knowledge`、knowledge graph、tool lock 保留；v0.6 `backtrack`、trajectory、redirect/stall bookkeeping 追加。
- `compose_batch`：默认无 backtrack 时仍走主线 adaptive acquisition；full/semi 时走纯 predicted-mean。主线 measured-only KG rationale 保留。
- `redirect_batch`：只在 backtrack 模式注册给 LLM；候选仍经过现有 gate，并只使用 surrogate mean 与 measured-best signature。
- test / 事件：保留主线 knowledge-graph cache invalidation 和事件结构；backtrack 模式额外维护 cumulative history 与 payload。
- LLM 执行：默认路径保留主线 atomic `execute_research_round`、wall-clock timeout 和 serialised tool calls；backtrack 路径保留 compose/redirect 二选一协议。无进展兜底统一调用 `compose_batch`，因此默认仍 adaptive、backtrack 仍 pure exploit。
- CLI / 输出：`--no-knowledge` 与 `--backtrack` 并存；仅 backtrack 输出路由到 v0.6 full/semi 子目录，默认 v0.5 路径不变。

## v0.5 默认行为不变

合并前导出：

```bash
.venv/bin/python - <<'PY' > /tmp/task_6a18_v05_system_prompt.before
from agent.auto_researcher import SYSTEM_PROMPT
print(SYSTEM_PROMPT, end='')
PY
```

合并后比较：

```bash
diff -u /tmp/task_6a18_v05_system_prompt.before <(.venv/bin/python - <<'PY'
from agent.auto_researcher import SYSTEM_PROMPT
print(SYSTEM_PROMPT, end='')
PY
)
```

输出为空；合并前后 SHA-256 均为 `191ae4c066f2441a455cbedd127e518f18778bb49c5477e1609add028bed0409`。测试 `test_v05_default_system_prompt_is_byte_identical` 固化此值，`test_v05_mode_keeps_the_adaptive_default_unchanged` 固化 adaptive default。

反向验证中临时把默认格式化段落改为 v0.6，该测试以 exit 1 失败，observed hash 为 `722fd18700bbcb61d5ea740d283a2b26894d2d9b1748884ba8bc70f4cf66b472`；恢复 v0.5 后 packet 复绿。

## 工具证据

- packet：`58 passed, 1 warning in 6.04s`。
- `python3 scripts/check_data_has_code.py`：`agentic-v0.6` 为 `✅`；另有既存且越界的 `pkgA-mainline-truth` commit 缺口。
- `python3 scripts/check_references.py`：`lab/reports/agentic-v0.6/report.md` 为 `✅ 全部可达`；全仓另有 7 个越界既存失效引用。
- `git diff --stat origin/main`：仅 `agent/auto_researcher.py` 与 `tests/test_auto_researcher_backtrack.py`，未改 v0.6 metrics/events/figures。

## 未验证与风险

- 按任务约束未重跑 AAV seed-42 商业 LLM 实验，既有 metrics/events/figures 未覆盖。
- 未调用商业 LLM API；验证覆盖 deterministic primitives、prompt/模式分流与 packet 指定的集成测试。
- 全仓代码-数据和引用审计仍有上述既存缺口，不属于本任务 execution surface。
