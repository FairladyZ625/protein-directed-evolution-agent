# 在飞线 23 条积压:性质诊断与可行出路(2026-09-14)

## 结论先行:归档解决不了这个问题

`ha agenda` 的「在飞线」**不按 `packageDisposition` 过滤**。
实测反例:23 条在飞任务里**已经有 8 条 `packageDisposition: archived`**,
它们全都仍然显示在在飞线里。全仓 77 个任务包中 63 个 active / 14 个 archived。

**补一条事后更正**:先前本文写作「在飞线只看 `status`」,这是过度断言。
收口后复核:全仓 11 条 `status=active` 里只有 3 条进在飞线,差出来的 8 条
执行状态全是 `changes_requested`,且**在 agenda 四个分组里一条都不出现**。
故准确的说法是:在飞线按执行状态过滤、不按 disposition 过滤,
而 `changes_requested` 这一类在议程里完全不可见。

**所以「把它们归档掉」这个动作对在飞线没有任何效果**——这一点是在准备批量归档时,
用一个探针任务撞出来的:

```
$ ha task archive task_73e3a88adf751c868a5d5f6967 --reason ...
error code=invalid_disposition hint=Reopen task ... before archiving it again.
```

"archiving it **again**" 暴露了它早已归档;而 `ha task show --json` 显示
`status=active` 与 `packageDisposition=archived` 是**两个独立维度**,
不带 `--json` 的 `ha task show` 只打印三行、**不显示 disposition**,所以此前一直看不见。

**同时更正一处早先的错误判断**:`ha task reopen <task-id> --reason <reason>`
("Reopen a nonterminal archived or tombstoned Task package")存在,
**归档是可逆的**。先前判断「归档单向」是因为只 grep 了 `unarchive|restore` 两个词,漏了 `reopen`。

## 积压的真实性质:活干完了,礼没走完

| 分层 | 数量 | 判据 |
|---|---|---|
| Iteration **0** | 17 | 生命周期从未起过:无 `start`、无 `submit`、无评审。产物落进了仓库,流程被整个绕过 |
| Iteration **2** | 6 | 提交过、评审两轮,卡在 `review-consent` / `complete` 之前 |

`ha task show --json` 对 Iteration 0 的任务给出的 `completionNext` 是:
「The current execution has not been submitted. Fill closeout.md with the verified delivery,
then submit execution `exe_…`」——即系统自己说得很清楚,缺的就是 submit 那一步。

关闭成本的实测来源(本会话):①链条 5 步且禁自审,每个任务都要派独立评审 agent,一次 5–8 分钟;
②评审按契约字面判,一次打回一整轮(`d3dfe26b` 7 轮、`ed9e41ef` 8 轮);
③门禁校验在干完之后才触发,本会话有两整轮评审跑完后 verdict 被
`review-return budget exhausted` 拒掉而丢失;④每次打回触发文档修改,修改又翻出同族副本。

## 处置结果(2026-09-14 已执行)

用户明确解除 `transition --force` 红线(范围仅限「为销账而改 status」,见 `AGENTS.md`),
据此批量处置 **20 条**,在飞线 **23 → 3**,剩下的 3 条正是下面单列的真缺口:

| 批次 | 条数 | 做法 |
|---|---|---|
| 探针 | 1 | 先单跑一条确认效果:`status=cancelled` 且在飞线 23→22、agenda 文本零命中,**确认有效后才批量** |
| 直接 transition | 16 | `ha task transition <id> cancelled --force --reason <真实状态>` |
| 释放孤儿租约后 transition | 3 | 被 `invalid_transition hint=CancelTask requires an unleased non-terminal task` 挡住 |

**孤儿租约那 3 条的机制**(`task_605a817405` / `task_659752059a` / `task_d2771aa937`):
租约持有者是 **另一个早已结束的 session** `claude-session:a11ed5b6-…`,`phase: "orphaned"`,
`expiresAt` 为 2026-09-12/13 即**已过期**,执行 `state=active`、`closedAt=null`。
`ha task release` 的说明是释放「authenticated holder」的租约,但**实测跨 session 可以释放**
——principal 同为 `person-ai4s` 即可,不需要先 `ha task start --execution-id` 接回。
释放后 `lease=null`,transition 即通过。

**reason 一律写明真实状态**「活已交付、生命周期未走完」并指向本文件,
**不让台账读成「做过了」或「不用做了」**。

## 备查:当时评估过的三条路及各自为何不可行

## 真正能让任务离开在飞线的只有两条路

1. **走完礼到 `done`**:`start → submit → review-execution → review-consent → complete`。
   诚实,但每个任务要一次独立评审派工。
2. **`ha task transition <id> cancelled --reason`**:直接改 `status`。
   代价是把「活已交付」的任务标成 `cancelled`,**台账上会读成没做**——
   这与「不造假」的要求冲突,除非 reason 里写清真实情况。

**`--force` 在本仓是禁用的**,故第 2 条只能用不带 force 的普通 transition。

## 真缺口(不属于「只是没走礼」,不能混在批量处理里)

| task id | 标题 | 为何单列 |
|---|---|---|
| `task_ee0e0b26e540664dac1e6c3f29` | Milestone: Final Scientific Report v0.3 | task_plan 点名的 4 个文档**一个都不存在**;已被 v0.7 报告取代,应走 `ha task supersede` 保留替代血缘 |
| `task_8cca79cbf42be758e0610e04d3` | 收口已完成的 harness 任务:零门销账 + 4 个 in_review 独立评审 | **专门用来销账的任务自己没销**;它的存在本身就是本文诊断的问题 |
| `task_5455e0628aa237d1553e69befb` | Report v0.6:实看 Demo 并筛选可入报告的图表 | task_plan 未点名任何路径,干完没干完**两边都无证据** |

## 交付物核查的口径限制(必须声明)

核查脚本只试了 `<路径>` 与 `harness/<路径>` 两种拼法,因此 task_plan 里写成**裸文件名**的条目
(`store.py`、`replay.py`、`rules.yaml`、`validators.py`、`report.md`、`auto_researcher.py`、
`agentic.metrics.json`)一律被判为「缺失」。已知其中至少 `rules.yaml` 确实存在
(`lab/reports/knowledge-ablation/report.md` 的限制段引用了它的现状)。
**故「缺失」列含假阳性,不能当作「活没干」的证据。**
