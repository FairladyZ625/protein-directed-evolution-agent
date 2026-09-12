# 交付面:一键安装 / 一键运行 / 复现脊柱补全

## Brief

评委拿到这个仓库,应该在 Linux 或 macOS 上跑两条命令就能装好并复现主结果。
现在做不到:没有安装脚本、没有运行脚本,而且**主复现命令刚刚才被发现是坏的**
(`make campaign` 在干净 clone 上 `ModuleNotFoundError`,已由 CEO 修复于 commit `f68f8d7`,
fact `F-6D573C04`)。这类缺陷之所以活了这么久,就是因为**没人在干净环境里跑过一遍**。
这个包要把「干净环境能跑」做成可验证的东西。

## Goal

三件事:

1. **一键安装**:`scripts/install.sh` 在 Linux 与 macOS 上都能从零建好环境。
2. **一键运行**:`scripts/run_all.sh` 跑通「冒烟 → 预测器 → 四策略闭环」并把产物落到版本化目录。
3. **复现脊柱补全**:`harness/reports/experiment_log.jsonl` 覆盖到所有已产出的实验;
   每个版本目录都有 `manifest.json`。

## Context

**这个仓库是一份考卷的交付物**,试题明确要求代码可运行、结果可复现。
用户的原话:「最好也提供一些 Linux、Mac 的脚本,一键安装、一键运行,这些都写清楚。」

仓库形态(读之前先知道):

- **两棵产物树并存,这是合规的不是缺陷**:根 `reports/` 是早期扁平产物 + 用户正在写的
  `reports/final-report-v0.5/`(**这个目录任何人都不许动**);`harness/reports/<方法线>-v<版本>/`
  是版本化树。`harness/reports/migration-audit.md` 记录了迁移审计。
- `requirements.txt` **已存在**,先读它再判断缺什么;不要覆盖重写。
- 依赖分两档:自包含测试只要
  `pytest numpy pandas scipy scikit-learn PyYAML networkx pydantic streamlit matplotlib`
  (见 `.github/workflows/ci.yml`);完整跑还要 44MB 的 GB1 真值表与 ESM-2/torch。
  **安装脚本必须让这两档清晰可选**,别让评委为了看 demo 去下 2GB 的 torch。
- GB1 真值表**故意不进仓库**(见 `data/README.md`);`make smoke` 是无数据、无 API key
  的自包含路径,是评委的推荐首跑。

## Required Reading

| 文件 | 为什么要读 |
|---|---|
| `README.md` | 现有的安装/运行叙事,你要让脚本与它一致(不一致就改 README) |
| `Makefile` | 已有的 6 个入口(data/baseline/train/campaign/smoke/test);脚本应当复用而不是绕过它们 |
| `requirements.txt` | 现有依赖声明,判断缺什么 |
| `.github/workflows/ci.yml` | 轻量依赖清单的权威来源(CI 就是用这一档跑的) |
| `data/README.md` | GB1 真值表的来源与放置说明,安装脚本要引用它而不是复述 |
| `scripts/smoke.py` | 自包含路径的入口,一键运行脚本的第一步 |
| `harness/reports/experiment_log.jsonl` | 脊柱的现有格式;**照它的 schema 追加,不要另立新格式** |
| `harness/reports/workflow-v1.0/manifest.json` | manifest 的现有形状,新建的要同形 |
| `harness/reports/migration-audit.md` | 两棵树的由来,避免你把合规的并存当成要收敛的缺陷 |

## Entry Conditions

- worktree 与分支由 CEO 备好(见 Execution Surface),基于含 `f68f8d7` 的 master。
- `.venv` 已符号链接,GB1 真值表与 `features/cache` 已链接进 worktree。
- **注意**:CEO 正在并行跑 `workflow-v1.1` 的 hard/sparse/llm 三个 regime,产物会陆续落到
  `harness/reports/workflow-v1.1/gb1/`。**你不要动那个目录下的 campaign 产物文件**;
  给 workflow-v1.1 写 `manifest.json` 时,把 campaign 条目按「已产出的文件」写,
  并在 manifest 里留一个说明:该版本的 regime 产物由 CEO 侧补齐。

## Dependencies

无阻塞。与前端包(`task_498b2ca7094a2c824a59e90b7c`,在飞,只动 `app/demo.py` /
`tests/test_demo_app.py` / README 的 demo 一节)文件面不重叠——**README 是唯一可能撞车的文件,
你改 README 时只动安装/运行那几节,不要动 demo 一节。**

## Execution Surface

**可写**:`scripts/`(新建 `install.sh` / `run_all.sh`)、`requirements.txt`、
`requirements-full.txt`(如果你决定分档)、`Makefile`、`README.md` 的安装与运行小节、
`harness/reports/experiment_log.jsonl`(只追加)、各版本目录的 `manifest.json`(只新建缺的)。

**禁区**:
- `reports/final-report-v0.5/`(用户正在写的报告,**绝对不动**)
- `app/demo.py`、`tests/test_demo_app.py`(前端包在飞)
- `harness/reports/workflow-v1.1/gb1/campaign_*.{json,jsonl,png}`(CEO 在跑)
- 任何已有 `manifest.json`(只新建缺的,不改已有的)
- `evolution/`、`models/`、`agent/`、`knowledge/`、`events/` 的算法代码
  ——这个包是交付面,不是算法面

## Constraints

- **脚本要在 Linux 和 macOS 上都成立**:别用 GNU 专有 flag(`readlink -f`、`sed -i` 无参、
  `grep -P`)。POSIX sh 或显式 `#!/usr/bin/env bash` + 只用 bash 3.2 有的特性(macOS 自带的
  就是 3.2)。**不要假设有 `python`,只假设有 `python3`。**
- **脚本失败要响亮**:`set -euo pipefail`;每个前置缺失给出「缺什么 + 怎么装」的具体一句话,
  不要静默继续跑出半个结果。
- **不要把 44MB 数据或 2GB torch 做成必需**:安装脚本默认装轻量档,完整档要显式开关
  (例如 `./scripts/install.sh --full`),并在输出里说明差别。
- **脊柱只追加**:`experiment_log.jsonl` 是 append-only、带 `prev_hash`/`hash` 链的。
  **补历史条目时不要重写整个文件破坏哈希链**——先读明白链是怎么算的
  (`events/store.py` 是同一套机制的实现),按链尾追加;如果历史条目在链上无法补
  (因为它们发生在更早的时间点),**就在脊柱旁边写一个 `experiment_log.README.md` 说明
  哪些运行没能进链、为什么**,不要伪造时间戳或哈希把它们塞进去。
  **诚实的缺口说明优于伪造的完整性。**
- **manifest 里的每个 sha256 必须是真算的**,不许抄、不许填占位。
- 补脊柱条目时,`command` 字段必须是**真能跑出该产物的命令**。如果你不确定某个历史产物
  是什么命令跑出来的,**写 `"command": null` 加一个 `provenance_note` 说明来源不明**,
  不要猜一条命令写上去——那会让读者以为跑得出来。

## Checkpoint

三个停手点,任一命中就带证据回报、不要自己硬解:

1. `experiment_log.jsonl` 的哈希链机制读不明白,或补条目会破链。
2. 某个历史产物的来源命令查不到(去 `harness/tasks/*/artifacts/` 和 git log 找过之后仍无)。
3. 在 macOS 上跑通但你无法判断 Linux 行为(例如需要 `nproc`、`/proc`),
   **不要写一个你没法验证的分支**,回报让 CEO 决定。

## CI/Gate Authority Stop Condition

停止点 = 下列证据齐全 + commit。**不 push、不发 PR。**
不要跑全量测试矩阵(同机还有其他 worker,16 核跑两套会把机器拖死)。

要跑的定向测试只有:`pytest -q tests/test_predictor.py tests/test_campaign.py`(确认你没碰坏入口)。

注:本仓 `standard-task` 的 CI 见证门结构性不可满足(fact `F-8ED77039`)。
**不要新建 workflow、不要改 `.github/workflows/`、不要 `transition --force`。**
记录进度后交 CEO。

## Implementation Plan

1. **读现状**:`requirements.txt` 缺什么、`Makefile` 的 6 个入口分别需要什么前置。
2. **`scripts/install.sh`**:检测 `python3` 版本(≥3.11)、建 `.venv`、装轻量档依赖、
   校验 import 能过;`--full` 追加 torch/fair-esm 与数据放置提示。
   **结尾打印「下一步跑什么」。**
3. **`scripts/run_all.sh`**:分阶段跑,每阶段前打印它需要什么、产物落哪;
   缺 GB1 数据时**自动降级到 smoke 路径并明说**,而不是报错退出。
4. **`requirements.txt` 分档**并与 CI 清单对齐(CI 装的那一档必须是 requirements 的子集,
   否则 CI 绿而本地红)。
5. **Makefile** 加 `install` / `run-all` 两个目标转调脚本,保持单一真源。
6. **README** 的安装与运行小节改成「两条命令」开头,旧的手动步骤保留在下面作为备选。
7. **脊柱补全**:把 `analysis-v0.1`、`knowledge-ablation`、agentic v0.1/v0.3/v0.5/v0.6、
   以及 `workflow-v1.0` 的 alpha-sweep 与 scaling-ablation 这几次运行登记进去
   (来源命令查 `README.md:136-139` 与各 `manifest.json`)。
8. **补 manifest**:`analysis-v0.1`、`workflow-v1.1`、`final-report-v0.3`、
   `knowledge-ablation`、`pkgA-mainline-truth`、`pkgB-eval-protocol`、
   `pool-campaign-aav-agentic` 七个目录缺 `manifest.json`。

## Deliverable Contract

- `scripts/install.sh`、`scripts/run_all.sh`,两者都 `chmod +x`。
- 收口后的 `requirements.txt`(+ 可选 `requirements-full.txt`)。
- `Makefile` 的 `install` / `run-all` 目标。
- README 安装与运行小节。
- 追加后的 `experiment_log.jsonl` + 必要时的 `experiment_log.README.md` 缺口说明。
- 七个新 `manifest.json`。
- 一份 `harness/tasks/<本任务>/artifacts/delivery-verification.md`:
  记录你**实际跑过**的验证命令与输出摘要,以及你**没能验证**的部分(诚实列出)。

## Evidence Protocol

- **一键安装必须在真的干净环境里验过**,不是在已经装好的 `.venv` 里跑一遍就算。
  做法:`python3 -m venv /tmp/probe-venv` 装一遍,然后用那个 venv 跑 `make smoke`。
  **把输出摘要贴进 delivery-verification.md。**
- **阴性对照必做**:故意制造一个前置缺失(例如把 `data/four_mutations_full_data.csv`
  临时改名),证明 `run_all.sh` 给出的是**明确的降级提示**而不是崩栈或静默空跑。
  做完记得改回来。
- **每个 manifest 的 sha256 要能被独立重算**:在 delivery-verification.md 里给出重算命令。
- 脊柱新条目要能被读者据 `command` 跑出同样的产物;跑不出的必须标 `command: null` + 说明。

## Verification

- CEO 会在一个全新的 `/tmp` venv 里跑 `scripts/install.sh` 与 `scripts/run_all.sh`。
- CEO 会抽查两三个 manifest 的 sha256 是否对得上。
- CEO 会检查脊柱里是否有「猜出来的 command」——发现一条即打回。
- CEO 会确认 `reports/final-report-v0.5/` 一个字节都没变。
