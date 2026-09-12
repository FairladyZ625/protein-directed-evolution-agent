# 交付前仓库整理:迁移审计

**日期**:2026-09-12 | **执行**:CEO 亲做(红线是「数据只增不删」,不下放)

## 为什么亲做

历史上出过一次静默脱管:提交 `55a4b0b` 把 18 个产物移进当时被 gitignore 的目录,
导致它们无声地脱离版本控制(fact `F-39FA1D33`)。本轮整理因此先建完整 SHA-256 基线,
动完再逐份对照,并对**对照脚本本身**做阳性对照。

## 诊断修正:两棵树不是乱,README 才是

初判是「根 `reports/` 与 `harness/reports/` 两棵树重复,该收敛成一棵」。按内容比对后
这个判断**不成立**:

- 根 `reports/` 与 `harness/reports/` 按 SHA-256 比,66 份内容重叠、59 份只在根、91 份只在 harness。
- 而那 59 份里**最要紧的是 `reports/final-report-v0.5/` 整个目录**——正在撰写中的活报告,
  含 `build/` 构建脚本与渲染产物。动它会直接破坏报告线。

所以两棵树是**合理分工**:`reports/` = 报告撰写树,`harness/reports/` = 实验产物树。
`evolution/results_layout.py` 的模块 docstring 也是这么说的(它写「最终多章报告单独撰写,
不在此处」)。

**真正的问题是 README 系统性地把读者指向旧产物**:

| README 位置 | 原先指向 | 实际情况 |
|---|---|---|
| 第 10 行「完整实验报告」 | `reports/report.pdf` | 早已被 v0.5 取代,评委会打开旧报告 |
| 第 91 行「主台账」 | `reports/experiment_log.jsonl`(7 条) | canonical 那份在 `harness/reports/`(15 条) |
| 第 116 行预测器产物 | `reports/predictor_metrics.json` | 已迁到 `harness/reports/workflow-v1.*/gb1/` |
| 第 142 行目录说明 | `reports/` 装一切 | 早已分成两棵树 |

四处已改,并写明两棵树的分工;README 内全部相对链接经校验**零死链**。

## 处置明细

| 对象 | 处置 | 依据 |
|---|---|---|
| 仓库根 `figures/`(11 文件,20:07,未跟踪) | **归档**到 `harness/reports/figures-orphan-20260912/`,从根移走 | 内容与另两处同名图集**三方互不相同**,不是重复项;无法确认归属,按只增不删归档。详见该目录 README |
| `reports/experiment_log.jsonl`(7 条) | 移除 | 逐条 hash 比对确认是 `harness/reports/experiment_log.jsonl`(15 条)的**真子集,0 条独有** |
| `reports/.DS_Store` | 移除 + 加入 `.gitignore` | 系统垃圾 |
| `reports/report_standalone.html` | 移除 | 全仓零引用 |
| `/tmp/` | 加入 `.gitignore` | 临时工作区 |
| `reports/final-report-v0.5/` | **不动** | 撰写中的活报告 |
| `reports/report.pdf` / `.html` | **保留** | README 已改指 v0.5;文件留作历史版本 |
| `reports/final-report-v0.3/`、`reports/figures/` | **保留** | 历史报告版本;`reports/figures/` 与 v0.3 图集同内容且被历史任务包引用 |

## 数据完整性对照

| | 唯一内容份数(按 SHA-256) |
|---|---|
| 整理前(两棵树合集) | 216 |
| 整理后 | **224** |
| 计为丢失 | **2** |

那 2 份是 `reports/.DS_Store`(系统垃圾,有意移除)与 `reports/experiment_log.jsonl`
(文件整体 SHA 不同故计为一份,但其**每一条记录**都保留在 canonical 脊柱中,已逐条 hash 验证)。

**实验数据丢失:0 份。** 整理后总数反而增加 8 份,来自同轮抢救入库的未跟踪证据。

### 对照脚本的阳性对照

空结果不能当通过。故意从「整理后」清单里剔除 1 份内容,对照脚本报 **3 份丢失**
= 真实 2 份 + 注入 1 份,**说明该探针确实会对丢失出声**,不是沉默通过。

## 同轮抢救入库的数据(此前 git 未跟踪,worktree 一删即永久丢失)

| 来源 worktree | 入库位置 | 内容 |
|---|---|---|
| `t-astra-seeds` | `harness/context/research/v07-multiseed-evidence/` | v0.7 证据包 336KB(整目录 134MB 全未跟踪);128MB `cache/` 是派生缓存不入库 |
| `t-knowledge-ablation` | `harness/reports/knowledge-ablation/` | 试题要求的有无知识增强对照,13 文件 1.5MB |
| `t-agentic` | `harness/reports/pool-campaign-aav-agentic/` | AAV 池式 campaign 的 metrics/events/曲线 |
| `t-astra-kb` | `harness/context/research/kb-audit-evidence/` | 知识库审计脚本与两轮审计结果 |
| `t-v05` / `t-v06` | `harness/reports/agentic-v0.{5,6}/` | 两版数据(只取数据,代码留在 tag) |

## 仍未完成

- **复现脊柱覆盖不全**:15 条,缺 `agentic-v0.1/v0.3/v0.5/v0.6/v0.7`、`analysis-v0.1`、
  `workflow-v1.1` 的 predictor/alpha 扫描/标准化消融、三份 final-report。
  README 已如实写明「部分脊柱」而非声称完整索引。
- `analysis-v0.1`、`workflow-v1.1`、`final-report-v0.3`、`pkgA`/`pkgB` 缺 `manifest.json`。
- `pkgA-mainline-truth`(仅 1 个 report.md,无数据)与 `pkgB-eval-protocol` 不符合
  `<line>-v<version>` 命名契约,属包交付记录而非研究周期,建议在 README 里标注其性质。
