# Agent Guide & Repository Operating Manual

本文件是 Agent 在本仓库工作的统一操作入口与认知基准。任务专属上下文与当前进度请查阅 active task package 与 `task_plan.md`。

**权威源 (SSoT)**: SQLite 状态库与事件流是台账的权威源；Git 提交是代码的权威源。

---

## 1. 核心本体与系统心智模型 (Ontology & Mental Model)

- **代码与 Git 是物理现实 (Code as Physical Reality)**: 代码仓与真实 Git 历史是唯一的生产交付实体。任何文档、计划或台账若脱离可运行、可测试的代码与提交，均无实际效力。
- **Harness 作为认知中枢 (Cognitive Ledger)**: Harness 不是流程路障，而是 Agent 长期演进的外脑与因果追踪器。在长周期任务与多轮协作中，它沉淀「为何决策（Decision）」、「基于何种实测（Fact）」、「交付了什么（Task）」，防止目标偏移与架构失忆。
- **SSoT 与只读投影 (SSoT vs Projections)**:
  - **只读投影 (Projections)**: `harness/` 目录下的 Markdown 文件（`tasks/`、`decisions/`、`facts/` 等）是只读投影视图。不要手工修改其 frontmatter 或机器元数据，统一通过 `ha` CLI 驱动。
- **三元因果闭环 (Triad Causal Loop)**:
  - **Fact（客观观察）**: 真实世界的代码行为、错误复现、基准测试输出、数据分析等客观事实。一切决策始于可复核的 Fact，杜绝主观臆测。
  - **Decision（承重裁定）**: 架构选型、设计裁决、权衡取舍。声明 load-bearing claim 并由 Fact 见证（`evidenced-by`），派生任务。
  - **Task（工作契约）**: 具备边界、验证标准与验收门的原子交付单元。由 Decision 派生（`derives`）。
  - **Fact（交付见证）**: Task 交付后产出新客观 Fact（`task --produces--> fact`），验证假设，完成闭环。

---

## 2. 通用软件工程原则 (Universal Software Engineering Principles)

- **验证优先与测试驱动 (Verification-First & TDD)**: 动手前先确立复现用例与验证脚本；交付前必须运行测试并获得确切证据。永远拿测试结果说话，严禁未经实测断言成功。
- **最小爆炸半径与原子切片 (Minimal Blast Radius)**: 每次修改聚焦于单一垂直可验收切片；使用独立 worktree 隔离工作，严禁在同一提交中混入无关改动。
- **反水面循环 (Anti-Slop & Root-Cause Resolution)**: 修复的默认动作是减法与收窄。针对 Bug 必须直接修复源头，严禁层层叠加无假设依据的重试、防御包装和容错兜底。
- **零猜测性抽象**: 选能完整满足当前需求的最简单实现，不为未来假设预留间接层。

---

## 3. 标准日常开发流 (The Golden Path Workflow)

1. **认领租约 (Start)**: 检视 `harness/harness.yaml` 与目标任务 `task_plan.md`，执行 `ha task start <id>` 获取任务租约（未 start 无法提交）。
2. **隔离开发与测试 (Worktree & TDD)**: 在独立 worktree 中编写代码，运行定向测试或基准验证，确保测试全绿。
3. **记录交付见证 (Fact)**: 运行 `ha fact record --statement "<实测证据>" --source "<代码或测试路径>" --confidence high --task <id>`。
4. **撰写 Closeout 并提交 (Submit)**: 将 `closeout.md` 按规范四节写实（`## Summary`、`## Verification`、`## Residual Risk`、`## Same Mechanism Elsewhere`），执行 `ha task submit <id>`（完成包从 closeout.md 及 commit diff 自动派生）。
5. **独立评审与收口 (Review & Complete)**: 委派独立 reviewer 或执行 `ha task review-execution <id>`，完成 `ha task review-consent <id>`，最后执行 `ha task complete <id>` 销账。

---

## 4. 生命周期纪律与待办管理 (Lifecycle Discipline)

本节总结自本仓实战经验，针对任务积压与执行迷失的根因：

- **开工即 start**: 动手写第一行产物之前先 `ha task start <id>` 拿租约。执行记录必须绑定租约，事后无法补回。
- **产物落盘即 submit**: 交付物落盘当天即执行 `ha task submit <id>`。没 submit 就没有可评审对象，任务会无声停滞。
- **在飞线管理与 Agenda 机制**:
  - `ha agenda` 的在飞线**不按 `packageDisposition` 过滤**：已标记为 `archived` 的任务仍会留在 agenda 中；只有走完流程到 `done` 或通过受限 force 授权 `cancelled` 才能移出。
  - **执行处于 `changes_requested`（评审打回待修）的任务不会在 agenda 任何分组中出现**！排查待修任务必须运行 `ha task list --status active` 并检查最新执行状态，避免打回任务被遗忘。
  - **积压红线**：`ha agenda` 在飞线超过 8 条时停止新开任务，优先收口存量。
- **独立评审纪律**: 一个被审任务派一次 reviewer（`ha agent run de-reviewer --task <被审任务> --instance <inst> --role reviewer --cwd <仓库根> --detach`）。一人统管多个任务会导致 worker 写入时遭遇 `executor_binding_invalid`，整轮作废。
- **走完 consent 才算完**: 必须走完 `review-execution` → `review-consent` → `complete`，停在 review-execution 会导致前期评审成本全部沉没。

---

## 5. 本仓特有规范与实操配方 (Repository Specifics & Recipes)

### 5.1 CI 完成门与 force 授权边界

- **CI 完成门判据**: 本仓 `harness.yaml` 配置为 `workflows: [ci]`。CI 完成门见证的是 `main` 分支上处于 `completed` 状态的 `ci` 工作流运行，与被审分支自身的临时 commit 无关。只要 `main` 分支的 `ci` 是绿的，`ha task complete` 会自动铸造见证；严禁擅改 CI 配置或新建无用 workflow。
- **`transition --force` 受限授权**: 仅当任务实际产物已合并入主线、仅为**清理历史孤立积压任务销账**时，允许使用：
  ```bash
  ha task transition <id> cancelled --force --reason "<真实情况说明及对照记录>"
  ```

  授权严禁扩展至「硬闯红门」、「绕过未通过测试」或「将未完成工作标为完成」。

### 5.2 实测命令配方 (Copy-Paste Ready)

#### 配方 1: 记录 Fact

```bash
ha fact record --statement "<客观实测观察>" --source "<代码/测试/日志文件路径>" --confidence high [--task <task-id>]
```

*注：带 `--task` 会自动建立 `task --produces--> fact` 边，满足任务完成门的 Fact 要求。*

#### 配方 2: 制定决策 (Decision) 并履约 Claim

```bash
# ① 提议决策（chosen / rejected / claims 必填，rejected 必带 whyNot）
ha decision propose --json-input @- <<'J'
{"title":"...","question":"...","riskTier":"low","urgency":"medium","decisionClass":"ordinary",
 "chosen":[{"id":"CH1","text":"...","rationale":"..."}],
 "rejected":[{"id":"RJ1","text":"...","whyNot":"..."}],
 "claims":[{"id":"C1","loadBearing":true,"text":"..."}]}
J

# ② 撰写正文四节并提交（文件须在仓库内）
printf '## 背景\n...\n## 裁定\n...\n## 影响\n...\n## 验证\n...\n' > .body.md
ha decision amend <id> --body-file .body.md && rm .body.md

# ③ 建立 Fact 并履约 load-bearing claim（否则 accept 报 coverageRows 0/N）
ha fact record --statement "<支撑该 claim 的实测事实>" --source "<证据路径>" --confidence high
ha relation relate --source-ref decision/<id>/C1 --target-ref fact/F-xxxx --type evidenced-by --rationale "..." --expected-version 0
ha decision claim fulfill <id> --id C1 --mode evidenced

# ④ 校验决策完整性
ha decision validate <id>
```

#### 配方 3: 任务收口与交付 (Task Closeout)

```bash
# ① 认领或接回租约（若已有 active 执行，带 --execution-id 接回）
ha task start <id> [--execution-id <exe_...>]

# ② 写实 closeout.md（必须包含以下四个标准二级标题）：
#   ## Summary
#   ## Verification
#   ## Residual Risk
#   ## Same Mechanism Elsewhere

# ③ 提交交付包（完成包从 closeout.md 及提交 diff 自动派生，不加 --json-input）
ha task submit <id>

# ④ 独立评审与授权（由独立 reviewer 角色或通过 CLI 录入）
ha task review-execution <id> --review-id <rev-id> --json-input @- <<'J'
{"verdict":"approved","reason":"...","evidenceChecked":["..."]}
J
ha task review-consent <id> --review-id <rev-id>

# ⑤ 最终销账完成
ha task complete <id>
```

#### 配方 4: 登记工件与自定义实体 (Entity Import)

```bash
ha vertical entity-kind upsert --from-file kind.json
ha entity import --kind <kind> --locator <文件或目录路径> --expected-version 0 --title "..."
```

### 5.3 已知合法关系三元组 (Declared Triples)

- `task --produces--> fact` (记 fact 带 `--task` 自动建立)
- `decision/<claim> --evidenced-by--> fact` (支撑决策 claim)
- `decision/<claim> --derives--> task` (决策派生任务)
- `<artifact-kind>/<ENTITY> --relates--> task` (需在 kind 中预先声明)
- 遇到 `relation_triple_undeclared` 时，说明该三元组未经声明，应检查方向或更新 kind 定义，切勿盲目尝试不存在的 relation type。
