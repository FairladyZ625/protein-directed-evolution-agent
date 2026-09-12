# 仓库交付前整理:双报告树收敛、根目录散落物归位、数据脊柱补全

## Brief

本周要把仓库交给评委,现状偏乱。三个具体问题,都已由 CEO 实测确认:

1. **两棵并行的报告树**:根 `reports/`(149 个文件)与 `harness/reports/`(141 个文件)。
   而 `evolution/results_layout.py` 的模块 docstring 明确声明 canonical 位置是
   `harness/reports/<line>-v<version>/`,根 `reports/` 是历史遗留。评委会看到两份看似
   都权威的产物树,无从判断该信哪个。
2. **根目录散落物**:`figures/`、`tmp/` 直接躺在仓库根。
3. **数据脊柱残缺**:`harness/reports/experiment_log.jsonl` 只有 15 条,
   缺 agentic-v0.1 / v0.3 / v0.5 / v0.6 / v0.7、analysis-v0.1(mutation_order 与
   conservation)、workflow-v1.1 的 predictor_metrics / predictor_alpha_sweep /
   predictor_ladder_scaling_ablation、以及三份 final-report。该文件是模块 docstring
   里声明的「版本脊柱,记录每个产物的 git commit 与 SHA-256」,残缺等于复现链断掉。

## Goal

评委 clone 下来后:**只看到一棵权威产物树**,每个版本的数据都在,且每份产物都能从脊柱
反查到「哪个 commit、哪条命令、SHA-256 是多少」。

## Context

版本口径(已裁定,写在 `evolution/results_layout.py` 的 `VERSIONS`):
- `workflow` v1.1 —— 交付主线(数据→预测器→五角色→四策略→demo),跑 GB1
- `agentic` v0.7 —— 自主 researcher 线,跑 AAV;**v0.6 与 v0.7 是兄弟不是递进**(F-84AE8976)
- `analysis` v0.1 —— 只读分析线(突变阶数、保守位点)

另有两个**不符合 `<line>-v<version>` 命名契约**的文件夹:`pkgA-mainline-truth`(只有
一个 report.md,无任何数据)、`pkgB-eval-protocol`(3 个文件)。它们是包A/包B 的交付记录。

## Required Reading

- `evolution/results_layout.py`(模块 docstring 是产物布局的单一真源)
- `harness/reports/experiment_log.jsonl`(看现有 15 条的字段形状,照它补)
- `data/README.md`(说明哪些大文件有意不提交)

## Entry Conditions

独立 worktree,基于最新 `origin/main`。

## Dependencies

无阻塞。注意 `harness/reports/workflow-v1.1/` 下 CEO 正在重跑四策略,**那个目录别动**。

## Execution Surface

可动:根 `reports/` 的收敛、`figures/`、`tmp/`、`.gitignore`、
`harness/reports/experiment_log.jsonl` 的补全、各版本缺失的 `manifest.json`、
`README.md` 里指向产物位置的说明。

**不要动** `harness/reports/workflow-v1.1/`(CEO 在跑)、`harness/reports/agentic-v0.*/`
与 `final-report-v0.*/` 里**已有的数据文件内容**(可以加 manifest,不可改数据)、
`evolution/`、`agent/`、`models/`、`knowledge/`、`events/`、`app/`。

## Constraints

- **数据只增不删(红线)**。根 `reports/` 里若有 `harness/reports/` 没有的产物,
  **必须先迁移过去再谈清理**;任何一个产物文件在本任务里丢失即整轮作废。
  历史上已经出过一次这种事:提交 `55a4b0b` 把 18 个产物移进当时被 gitignore 的目录,
  导致它们静默脱离版本控制(fact `F-39FA1D33`)。**不要重演。**
- 迁移前后各做一次**文件清单 + SHA-256 对照**,把对照表作为交付物之一。
- 脊柱补全的每条记录里,`git_commit` 必须是**真的产出该产物的那个 commit**;
  查不到就把该条标为 `git_commit: "unknown"` 并在 note 里说明为什么查不到——
  **不许填一个看起来合理的 commit**。
- 不许为了让目录变整齐而删除任何 `harness/facts/`、`harness/decisions/`、
  `harness/tasks/` 下的内容。

## Checkpoint

若发现根 `reports/` 与 `harness/reports/` 存在**内容冲突**(同名产物但 SHA-256 不同),
**停手回报**,把冲突清单给 CEO 裁定哪份是权威——这是语义判断,不下放。

## CI/Gate Authority Stop Condition

停止点 = 迁移对照表干净 + `make test` 绿 + commit。**不 push、不发 PR。**

## Implementation Plan

1. 全量列出根 `reports/` 与 `harness/reports/` 的文件与 SHA-256,做差集。
2. 差集里只在根 `reports/` 有的 → 迁入 `harness/reports/` 对应版本目录(按内容判断归属;
   判断不了的回报)。
3. 根 `reports/` 收敛后,在 `README.md` 与 `data/README.md` 里写明唯一权威产物树位置。
4. `figures/`、`tmp/` 归位或加进 `.gitignore`(判断:是产物就归位,是临时就忽略)。
5. 按现有 15 条的字段形状补全脊柱。
6. 给缺 manifest 的版本补 `manifest.json`(analysis-v0.1、final-report-v0.3、
   pkgA-mainline-truth、pkgB-eval-protocol)。

## Deliverable Contract

- 收敛后的单一产物树。
- `harness/reports/migration-audit.md` —— 迁移前后的文件清单 + SHA-256 对照表,
  明确写出「迁移了几个、丢失 0 个」。
- 补全后的 `experiment_log.jsonl`。
- 各版本的 `manifest.json`。
- `README.md` 的产物位置说明。

## Evidence Protocol

- **阳性对照**:对照表必须能证明它会发现丢失——故意在对照脚本里漏掉一个文件时,
  脚本必须报出差异(把这个自检写进 `migration-audit.md`)。
- 每条脊柱记录的 `git_commit` 标明是查证得到还是 `unknown`。
- 迁移后 `find harness/reports -type f | wc -l` 的数字要与对照表一致。

## Verification

- CEO 会自己跑 `find` 数文件、抽查若干 SHA-256、并在干净 clone 里确认只有一棵产物树。
- CEO 会检查 `migration-audit.md` 里「丢失 0 个」这个断言有对照证据支撑。
