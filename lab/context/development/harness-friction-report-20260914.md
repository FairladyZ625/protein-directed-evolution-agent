# Harness 使用者摩擦清单(2026-09-14 单会话实录)

本文件由 `ai4s-directed-evolution-agent` 仓的使用者在一次长会话中记录，供 Harness 开发者参考。
**每条都给出可复现的判据或错误原文**，并按「实际造成的代价」排序。

## 写在最前:错误怎么归账

这次会话我(使用者)犯了十几个自己的错误——搜索面遗漏、键名写错、grep 正则与字面混用、
行号位移算错、拿命令 stdout 去比文件 sha256、反复匹配到自己写的更正引述。**下面第 12 节单独列出纯属我自己的那些**，目的是让开发者能判断:哪些是工具问题，哪些是我不会用。

但有一类必须算在工具账上:**引导缺失或设计缺陷使使用者必然踩的坑**。
仓库的 `AGENTS.md` 是 Harness 自己指定的入口文档，而系统不提供任何让它失效的机制;
`ha fact` 没有 `list` 命令，证据却散在四个不同的树里;同一断言要在三类文件里各写一遍而无一致性检查。
这些我原先记在自己账上，**经使用方指出后重新归类**——只怪使用者不解决问题。见第 11 节。

---

## 1. 最贵的一条:门禁校验发生在工作完成之后

**现象**:`reviewReturnBudget` 耗尽后，独立评审 agent 会把整轮活干完——读几十个文件、跑复算脚本、
写出完整 verdict 与缺陷清单——**直到最后一步写入时才被拒**:

```
error code=manual_intervention_required
hint=return budget exhausted: a changes_requested verdict cannot be recorded for this cut.
     Amend the submitted packet with `ha task submit --amend` so the reviewer can approve,
     or raise the budget with `ha settings update --review-return-budget <n>`
```

**代价**:本会话连续两轮(第五、六轮)如此，每轮评审跑 5–8 分钟、数十次工具调用，
产出全部作废——**只在最后一步才知道这轮不可能落库**。

**为什么提示词没解决问题**:hint 建议 `--amend`，但 amend 不增加额度。修完再提交，
下一轮评审仍然无法记录打回。使用者会照着提示进入一个不收敛的循环:
修 → amend → 评审找出真缺陷 → 记不进去 → 再修。本会话转了两圈才看穿。

**建议**:
- 在**派工时**就检查预算，额度为 0 时直接拒绝派发并说明，而不是让 worker 白跑一轮。
- hint 里明确写「amend 不会恢复额度」，避免把使用者导进死循环。
- 让预算可按任务设置，而不只是全仓设置。一个复杂任务耗尽额度会拖住整个仓的配置。

## 2. 回执不能作为成功判据(这一族最影响信任)

### 2a. `ha task submit` 成功时返回的是指导语

成功时返回:

```
Worker must draft closeout.md before completion with Summary, Verification,
Residual Risk, and Same Mechanism Elsewhere; the reviewer verifies and finalizes it
against ground truth.
acceptance: accepted_durable; git: pending; projection: verified
```

这段话读起来像「你还没写 closeout，所以我没受理」。**实际上它已经受理了。**
可靠判据只能去读 `executions/exe_*.md` 的 `State:` 与 `Submitted:` 字段。
本会话我因此误判过一次，向上汇报了「submit 没生效」。

**建议**:成功就说成功(`submitted: exe_xxx at <时间>`)，指导语放到 `note:` 字段里。

### 2b. `projection: verified` 不代表投影已可读

回执写 `projection: verified`，但紧接着读磁盘投影仍是旧值，需要等数秒。
我三次把这种滞后当成操作失败。**没有任何命令能等待投影就绪**，也没有暴露
「回执 revision vs 当前可读 revision」的对比，使用者只能靠 `sleep` 猜。

**建议**:提供 `--wait-projection`，或在回执里给出 revision 号，让使用者能轮询到一致为止。

### 2c. `git: pending` 指哪个 git 没说清(诱发型,代价很大)

`harness/` 是一个**嵌套 git 仓**(`harness/.git`)，由 daemon 的 SQLite Outbox 自动提交:

```
$ git -C harness log -1 --format='%h %an %s'
b7c84a6 Harness SQLite Outbox  harness sqlite outbox outbox-2936
$ git -C harness log --format='%an' | sort | uniq -c
   1878 Harness SQLite Outbox <harness-sqlite-outbox@local.invalid>
      1 ZeyuLi
```

而主仓**另外**跟踪着 `harness/` 下 1582 个文件，所以主仓 `git status` 永远显示 `M`。
回执里的 `git: pending` 指的是主仓那一侧。

**我因此得出了完全错误的结论**:查了 `ha daemon --help`(只有 `projection rebuild`、
`repo register|update`)、`ha doc`、`ha ledger`、`ha task`、`ha receipt`、`ha schedule` 六个域全部
不含 git/commit 字样，加上回执恒为 `git: pending`，于是判定「本仓不存在 daemon 自动 git 提交通道」，
并**据此向上汇报了一个不存在的阻塞**，请求授权手动提交。实际上 daemon 一直在提交，当天就提交了 436 次。

**建议**:把字段写成 `git(outer-repo): pending`，或直接给出 `git(harness-inner): committed <sha>`。
一个字段名的歧义在这里造成了一次完整的错误上报。

## 3. 执行记录只从 closeout 派生,但这一点没有任何文档说明

**判据**(同一次 `--amend` 后的字符串计数):

| 字符串 | artifact | closeout | execution |
|---|---:|---:|---:|
| `不对本行下选型结论` | 3 | 0 | 0 |
| `为何此处可下结论` | 1 | 0 | 0 |
| `一律以 wc -l 为准` | 0 | 1 | 2 |
| `modes/full_context` | 1 | 1 | 2 |

执行文件 mtime 与其 `Submitted` 字段同一时刻，排除「amend 未生效」。
结论:**执行回执只吸收 `closeout.md`，完全不吸收任务 artifacts。**

**后果**:凡是只修订 artifact 而没同步修订 closeout 的处置，都不会出现在执行回执里。
独立评审读执行回执判读时，会报「execution 声明与 artifact 不一致」——
本会话第六轮评审的一条阻塞缺陷正是这个机制的产物，是一次**系统性的假冲突**。

**建议**:文档里写明派生源；或在 submit 时对 artifact 与 closeout 做一次一致性提示。

## 4. `ha task progress append` 在 lease 释放后没有恢复路径

```
error code=progress_lease_required
hint=the lease for execution exe_1705de7cba0eef07a48e2c0248 was released;
     task start cannot re-enter the current lifecycle state,
     so progress append has no recovery in this state
```

**错误信息自己承认「no recovery in this state」。** 后果是该任务的进度**永久无法补记**——
我本轮要给一个挂起任务写移交说明，两次都被这条拒掉，只能把内容塞进别处。
这类「系统明确告诉你没有出路」的状态，对使用者是最挫败的。

**建议**:允许以 owner 身份补记(类似 `--as-owner`)，或提供 `progress amend`。

## 5. 命令面不一致 / 不稳定

### 5a. 同一个动词 `show`,两套互斥的参数约定

```
$ ha task show --id task_xxx
error code=unsupported_command ... Run ha task show --help..
$ ha task show task_xxx
status: in_review            # ← 位置参数才对

$ ha fact show F-xxx
error code=unknown_field ... Unknown option F-xxx. Run ha fact show --help..
$ ha fact show --id F-xxx
fact: schema=fact-row/v1 ... # ← --id 才对
```

`task show` 只收位置参数，`fact show` 只收 `--id`，**恰好相反**。
而且 `--id` 传给 `task show` 时报的是 `unsupported_command`(听起来像没这个命令)，
早先我就因此认定「`ha task show` 不存在」，绕了一大圈去读文件。

**建议**:两种形式都接受；至少让参数错误报 `unknown_field` 而不是 `unsupported_command`。

### 5b. `--path` 的解析根在不同命令里不同,且提示自相矛盾

```
$ ha doc sync --dry-run --path lab/context/research/x.md
error code=document_not_found
hint=lab/context/research/x.md is daemon-managed; use doc-sync: selected doc-sync path
     does not match an authored candidate
```

**我用的就是 doc-sync**，而提示让我「use doc-sync」。真正的原因是这个 `--path` 从 authored root
(`harness/`)解析，不能带仓库根前缀。而 `ha task complete --path` 恰恰是从**项目仓库根**解析。
同名参数、两套根。

**建议**:提示直接说「path 相对 authored root，去掉 `harness/` 前缀」;或两种写法都接受。

### 5c. `relation list` 与 `relation relate` 参数名不一致

`list` 用 `--source` / `--target`，`relate` 用 `--source-ref` / `--target-ref`。
我按 `relate` 的习惯去 `list`，被 `unknown_field` 拒。

### 5d. 命令形状会腐烂,且旧写法曾是正确的

`ha runtime run <instance> --agent <agent-id>` 曾是派工的正确写法，现被 `invalid_field` 拒，
需改为 `ha agent run <agent-id> --instance <instance>`。仓内配方文档因此长期失效——
**使用者照着自己仓里的文档操作会撞墙**，而那份文档当初是实测写下的。

### 5e. `ha settings show` 不存在(是 `read`),`ha fact` 没有 `list`

小事，但每次都要靠 `--help` 反查。

### 5f. 任务有两个状态维度,而默认视图只显示其中一个

任务同时有 `status`(planned/active/…/cancelled)和 `packageDisposition`(active/archived)。
**不带 `--json` 的 `ha task show` 只打印三行**——`status` / `graph cursor` / `completion gates`
——**完全不显示 `packageDisposition`**。

而 `ha agenda` 的「在飞线」**不按 `packageDisposition` 过滤**(实测 23 条里有 8 条
`archived` 仍在列),**但也不是简单地「`status=active`」**:全仓 11 条 `status=active` 里
只有 3 条进在飞线。

**差出来的那 8 条,执行状态全是 `changes_requested`——而它们在 agenda 的任何分组里都不出现。**
四个分组「在飞线 3 / 待裁 2 / 球在别人手里 2 / 可派队列 21」共 28 条,逐条比对后这 8 条一条都不在。
也就是说:**评审已经打回、正等使用者修的任务,恰好是议程完全看不见的那批**。
而编排纪律把 `ha agenda` 的 pinned 集当作「使用者承诺要做的事」的唯一真源
——最该被看见的一类工作被这个真源漏掉了。

后果:仓里 23 条「在飞」任务中**已有 8 条 `packageDisposition=archived`**,它们全都还显示在在飞线里,
而任何默认视图都看不出这一点。我据此准备了一整轮批量归档,直到探针撞出
`error code=invalid_disposition hint=Reopen task … before archiving it **again**`
——那个 "again" 是唯一暴露真相的线索。整轮准备作废。

同族的两处:
- `ha task list` 的过滤标志是 `--status`,而我按其他命令的习惯写 `--state`,得到
  `unknown_field`;两个词在同一命令面并存(`--state` 在 `relation list` 里是合法的)。
- `ha task capabilities --json <task-id>` 被拒为 `unsupported_command`,而它的 hint 说
  「run `ha task --help` for the commands it does have」——即命令面自描述这条路本身
  在这个子命令上是断的。

**建议**:
- 把 `packageDisposition` 加进默认 `ha task show` 的三行里(它只占一行);
- **给 `changes_requested` 一个自己的议程分组**(例如「等我修」),或至少并入在飞线
  ——这是目前最容易被整批忘掉的一类工作;
- 在分组标题旁标注过滤条件,让「为什么这条不在里面」可以自查,
  而不必像本次一样靠逐条比对 28 行才发现。

## 6. 语义不透明的完成门

### 6a. ci 门的判据与被审任务的 commit 无关

实测判据(已由 fact `F-B0148E72` 锁定):见证只为 **`headBranch=='main'` 且 `status=='completed'`**
的运行发布，且 `workflowName` 须在 `settings.ci.workflows` 内。
**也就是说:一个任务能否完成，取决于 main 分支当前的 CI 状态，而不是它自己的代码。**

这个语义非常反直觉。本会话有两个任务(`task_2e485a1ae`、`task_6a18b55b9`)得以完成，
真实原因是我恰好在同一会话里修绿了 main 的 CI(三个提交)，而不是它们自身有什么变化。
它们的 commit 只存在于本地分支，从未有过对应的 CI run。

**建议**:在 `complete` 的回执里说明见证取自哪个 run(branch + sha + workflow)，
让使用者知道自己在依赖什么。

### 6b. 门是否被要求,取决于交付形态,但无文档

- artifact 锚点任务(`Commit: none`):`completionGates = []`，ci 与 code-doc **都不要求**
- git 锚任务:`completionGates = ["ci", "code-doc-reconciliation"]`

同一个 preset 下，完成门要求因交付形态而异。这个规则我是靠对比四个已完成任务的字段反推出来的。

## 7. 投影与文件不一致(会让只读文件的人用到已废除的证据)

```
$ ha fact show --id F-412E158B   →  state=superseded_fact  invalidated=true
$ grep '^- State:' lab/facts/F-412E158B.md  →  - State: standing
```

`F-6F717548` 同样。**fact 已被 supersede，但磁盘上的 fact 文件仍自称 standing。**
任何读文件而不走 CLI 的人(包括 agent)会把废除的事实当现行证据引用。本会话见到 2 个实例。

**相关**:fact 文件里**不含 taskId**，归属只存在于关系投影。我 `grep lab/facts/` 查不到归属，
据此误判「fact 门未强制」，实际用 `ha relation list --source task/xxx` 一查就有
`produces` 关系。**诱发型**:文件看起来是完整的真源，其实不是。

**建议**:supersede 时同步改写文件头，或在文件里明确标注「权威状态见 CLI」。

## 8. `ha doc status` 的信号被噪音淹没

```
$ ha doc status
doc-status: BLOCKED (277)
...273 条都是 `path is not a supported textual document`(全是 .json)
```

277 个 blocked 里 273 个是 `.json` 这种本来就不该进 doc 面的文件。
真实问题被埋在里面，这个命令因此没法用来判断「文档面是否干净」。

**建议**:把不支持的类型排除在 blocked 之外，或分成两个计数。

## 9. 派工无法选择模型档位

`de-reviewer` 的声明写死 `model=gpt-5.6-luna`，而 `ha agent run` **没有 `--model`**。
本会话 5 次评审派工有 4 次跑在 luna 上(按我们自己的分工，luna 是量活档位、不适合做复核者)。
想为某一次派工提高档位，只能去改 agent 声明——而声明是给所有人共用的。
`--effort` 可调，但那是推理强度，不是模型。

**建议**:允许 `ha agent run --model <id>` 单次覆盖。

## 10. 配置被观察到无声变化

会话中段 `reviewReturnBudget` 从 `4` 变成了 `5`，**而我没有执行任何 `ha settings update`**。
原因未能确定(可能与 daemon build 从 `d8776a0a` 切到磁盘 build `a8283fc1` 有关)。
一个影响流程能否收敛的参数在无人操作时改变，使用者无法信任任何缓存的读数——
本会话之后我每次用它之前都要重读一遍。

---

## 11. 诱发型:引导缺失与设计缺陷使使用者必然踩的坑

本节原先被我记在「自己的错误」里。经使用方指出后重新归类:**这些坑不是粗心，是系统结构决定的**。
一个使用者按系统指定的方式工作却反复出错，问题在系统。

### 11a. `AGENTS.md` 是系统指定的入口,但没有任何失效机制

Harness 的上下文加载规范要求:先读 `harness/harness.yaml`，任务分派后读其 `task_plan.md`，
「route from the task to the smallest relevant context or standard document」。
仓库的 `AGENTS.md` 因此成为操作者最信任的一份文档——**它比官方文档更容易被信任，因为它是本仓实测写下来的**。

本会话它有一条早已失效的条目:「本仓 standard-task 的 ci 门结构性不可满足，`submit`/`complete` 必返
`service_rejected`，依据 `gh run list --workflow rewrite-ci.yml` HTTP 404」。
实测 `rewrite-ci` 在整个 CLI dist 里 grep **零命中**，上游早已修复;那个 404 源于拿错 workflow 名
(配置里是 `workflows: [ci]`)。**我照这条推断了两次，两次都错**——一次判定某任务的 `complete` 必被拒
(实际成功)，一次据此推出一个当时无证据的结论(已撤回)。

关键在于:**没有任何机制会告诉我这条过期了。** 系统里有 `ha capabilities`、
`ha task capabilities --json`、各命令的 `--help` 可以自描述当前命令面，
但**没有任何东西把仓内经验文档与实际命令面/门禁语义做交叉校验**。
条目写下时是真的，腐烂后长得跟真的一样。

**建议**:
- 让仓内 recipe 能标注「验证于 revision N」，并在 revision 漂移超过阈值时提示复核;
- 或提供 `ha doctor` 之类的命令，把仓内文档里的命令片段与当前命令面对账;
- 脚手架生成的 `AGENTS.md` 应包含下面 11b–11d 这些语义(证据树布局、派生规则、门禁判据)，
  否则每个使用者都要自己踩一遍再写进去——而写进去的又会腐烂。

### 11b. 证据散在四个树里,而 `ha fact` 没有 `list` 命令

事实与产物分布在至少四处:`lab/reports/`、`lab/context/research/`、`lab/facts/`、
以及每个任务包自己的 `artifacts/`。没有索引，也没有「证据放在哪」的说明。

而 **`ha fact` 没有 `list` 子命令**——无法枚举现有事实。要查「某个数字有没有台账支撑」，
只能靠 grep 文件;而 fact 文件里**不含 taskId**(归属只在关系投影里)，grep 归属也查不到。

**后果**:我判断一个关键数字「无产物支撑」、准备删掉它时，只搜了 `lab/reports/` 一个树。
真源(210 条完整矩阵、25 个文件全部 git 跟踪、自带复现命令)在 `lab/context/research/` 里;
**台账里甚至早有一条现行 fact 明文记着同一组数字**，而我没搜 `lab/facts/`——因为没有命令能列出它们。
这一步差点删掉正确的数据。

**建议**:补 `ha fact list`(带 `--search`);在 fact 文件里写入 taskId;
或提供一个「证据面索引」命令，让「这个断言有没有支撑」成为一次查询而不是一次考古。

### 11c. 同一断言要在三类文件里各写一遍,其中一类不可编辑,且无一致性检查

一次修订要同步到:任务 `artifacts/`(使用者维护)、`closeout.md`(使用者维护)、
以及 `executions/exe_*.md`(**daemon 管理，使用者不可编辑**)。
执行记录只从 closeout 派生(见第 3 节，该规则无文档)，所以:

- 只改 artifact → 执行回执不变 → 评审读回执，报「execution 声明与 artifact 不一致」
- 已经落库的旧执行文件里的过期断言**永久留在那里**，没有任何办法标注或更正

本会话有一条错误断言(「loader 显式过滤 designed」)同时存在于 artifact、closeout
和**四个历史执行文件**里。前两处我能改，后四处改不了。

**这就是「只改被点到的那处」这个形态在本会话重复 8 次的结构性原因**:
系统让同一事实有 N 份副本、其中一部分只读、且不做一致性检查。

**建议**:submit 时对 artifact 与 closeout 做一次一致性提示;
允许给历史执行记录追加一条 `superseded-by` 注记。

### 11d. 「保留勘误横幅而非删除」的既定做法,使 grep 式复核结构性不可靠

本仓(以及 Harness 的一般做法)对翻转的结论是**加勘误横幅而非删除**，以保留结论演变过程。
这个决定本身合理，但直接后果是:同一份文档里同时存在「错误的原文」与「我的更正引述」。

于是任何 grep 式复核都会命中自己写的「原写『……』已删」，报出不存在的残留。
**本会话至少 4 次因此误判**，每次都要再花一轮去区分「活的断言」与「我的引述」。

**建议**:给勘误内容一个机器可识别的标记(例如 `<!-- errata:quoted -->` 包裹)，
让工具与后续读者能把「引述的旧文」与「现行断言」分开。

### 11e. `ha doc show` 把 CLI 装饰与文档正文混在一起,没有 `--raw`

要验证「投影与工作树是否一致」，自然的做法是比对两者的哈希。
但 `ha doc show` 的输出里混着 CLI 的头尾行(`schema=`、`status=`、`acceptance:`)，
构造上就不可能与原文件等价——**我因此报了一次假的「投影不一致」**，
之后只能自己写脚本剥掉头尾再逐行 diff。

**建议**:加 `--raw` 只输出文档正文;或在回执里给出正文的内容哈希，让一致性检查变成一次比较。

---

## 12. 纯属我自己的错误,与 Harness 无关

1. **键名写错**:用 `hit_peak` 去读实际键名为 `peak_hit` 的记录，得到「达峰 0/210」的假读数。
2. **谎报仪器**:文档里写「`wc -l` 实测」，填的却是 Python `split('\n')` 的读数
   (123 vs 124，差 1 来自末尾换行计法)。不是数错，是把一个仪器的读数冒充另一个。
3. **grep 正则与字面混用**:`grep '**GB1 …**'` 被当正则解析报错，
   后续统计因此落到整个文件而非目标行，三个读数全错。
4. **行号位移算错**:`lines.insert(13, s)` 插入的是**一个**列表元素(字符串内含换行)，
   位移是 +1 而我按 +2 算，断言中止、文件一字未改，而我那一轮的「复核」还按位移后的假设
   读了未修改的文件，输出了一份无意义的表格。
5. **写后立刻读投影**:三次把投影滞后当成操作失败。这一条工具侧也有责任(见第 2b 节缺等待机制)，
   但我明知有滞后还是没等，算我的。
6. **我自己改了配置,把自己的搜索工具弄瞎了,还没立刻发现。** 我把 `harness/` 整目录写进
   `.gitignore`(目的是让台账目录只由它自己的嵌套仓跟踪)。本会话的 `grep` 实际是一个包装
   **ugrep** 的 shell 函数,而 ugrep 默认尊重 `.gitignore`——于是从那一刻起,
   `grep -rn <串> .` 对整个 `harness/` 树**一律返回假阴性**,而显式写成
   `grep -rn <串> harness/` 仍然命中。我因此拿到过一次「同族假断言零残留」的假干净读数,
   差一点据此收口。**救回来的是阳性对照**:我拿一个自己刚写进文档、必然存在的串去试,
   `-r .` 报 0 而显式路径报 2,仪器坏掉才暴露。这条纯属我的操作后果,与 Harness 无关;
   写在这里是因为**「改完配置先用阳性对照重新标定检测器」**这个动作,我是吃了亏才做的。

---

## 小结:对开发者最有价值的四条

1. **把门禁校验提到派工之前**(第 1 节)。让 worker 干完一整轮再拒，是最贵的浪费。
2. **让回执可信**(第 2 节)。成功就说成功;`projection` 与 `git` 这两个字段目前会把使用者引向错误结论，
   其中 `git: pending` 直接造成了一次完整的错误上报。
3. **消除「文件看起来是真源、其实不是」的地方**(第 3、7 节)。
   执行记录只从 closeout 派生、fact 文件自称 standing 而实际已废除——
   这两处都让读文件的人拿到错的东西，而读文件是 agent 的默认行为。
4. **把操作者必须知道的语义放进脚手架,并给经验文档一个失效机制**(第 11 节)。
   证据树布局、派生规则、门禁判据、参数约定这四样，目前每个使用者都要自己踩一遍再写进 `AGENTS.md`;
   而写进去的条目会腐烂，且腐烂后没有任何东西会提醒你——**本会话两次误判都源于此**。
