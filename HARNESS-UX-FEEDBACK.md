# Harness Anything — Agent 上手摩擦反馈与改进建议

**来源**：一个 Claude(Opus)CEO 会话在 ai4s 项目里连续操作 Harness 治理面(建实体、挂关系、建决策、closeout 10+ 任务)后的第一手复盘。
**读者**：Harness Anything 维护者。**目的**：把"学习曲线陡"从主观抱怨落成可执行的改动清单。

---

## TL;DR

Harness 的**概念模型是清晰且优雅的**:Fact → Decision → Task → 下一个 Fact 是一个闭环(观察催生裁定,裁定派生工作,工作产出新观察)。问题不在概念,在**操作路径只能靠"逐个报错"反向发现**——每个治理动作平均要撞 3–6 次墙,每次错误只暴露一个隐藏前置条件。对 agent 这是大量 round-trip 和 token;对转交的人这是反复的"它又卡住了"。

**一句话建议**:把校验从**反应式(一次一个错)**改成**目标导向的前置清单(一次列全)**,并让"声明了什么"可发现,而不是只报"你违反了某个没告诉你的声明"。

---

## 这次会话真实撞墙记录(每一行都是一次失败的 round-trip)

**目标 A:把一份报告挂到任务上(`report --relates--> task`)**
1. `ha relation relate` → `missing_field`:要 `--rationale`。
2. 加了 rationale → `relation_triple_undeclared`:report→task 未声明。错误没说**哪些三元组是声明了的**。
3. 去 `ha vertical entity-kind upsert` 补声明 relations → schema 报错:relations 每条**必须带 `decisionClaimRef` + `decisionContentPin`**(要先有决策)。这才发现关系种类的声明本身需要一个决策授权——鸡生蛋。

**目标 B:建决策并接受它**
4. `fact --evidences--> decision` → `relation_triple_undeclared`(方向/类型错,靠猜)。
5. `fact --supports--> decision` → 又 undeclared。
6. `decision/C1 --evidenced-by--> fact` → 成功(第 3 次猜中)。
7. GUI 接受 → `body_placeholder`:决策 body 只有标题,要填 `## 背景/裁定/影响`。propose 时没提示、没脚手架。
8. GUI 接受 → `coverageRows 0/1 未覆盖 C1`:光有 evidence 关系不够,还要 `ha decision claim fulfill --mode evidenced` 单独标记。两个动作是分开的,且没有任何地方说"接受需要同时满足这两个"。
9. `applies_to has no repository path-bearing module` 警告——但样板决策 applies_to 也是空的且能接受。**硬门和软警告混在一起显示,分不清哪个真拦。**

**目标 C:closeout 任务**
10. `ha task submit` → `invalid_field`:要 `--from-file/--json-input`,不能裸提交。
11. 提交 → `lease_required`:要先 `ha task start` 拿租约。
12. 提交 → `invalid_submission: verificationNotes must be an array`:字段是数组不是字符串,靠报错才知道。
13. 完成还需 closeout.md 的**四个精确小节**(Summary/Verification/Residual Risk/Same Mechanism Elsewhere),否则 `closeout_placeholder`——只在 AGENTS.md 里写着,提交时不提示。

**合计:三个目标,约 13 次失败 round-trip**,全部是"隐藏前置条件被逐个揭示"。

---

## 根因

1. **校验是反应式的**:每个动作只在执行时校验,且**只报第一个**违反项。一个动作有 N 个前置,就要撞 N 次。
2. **"声明了什么"不可发现**:`relation_triple_undeclared` 只说你错了,不说**对这个 source kind,哪些 (type,target) 是合法的**。`--help` 列的是所有 relation *类型*,不是已声明的*三元组*。
3. **占位符/必填只在文档里,不在工具里**:body 的四小节、closeout 的四小节、决策接受的双条件(evidence 关系 + claim fulfill),都写在 AGENTS.md,但 propose/create 时不生成脚手架、submit 时不预检。
4. **daemon 管理面 vs git 工作树 不透明**:decisions/tasks/entities 的 .md 是 daemon 管的(gitignore),要走 `ha ... amend --body-file`,不能直接编辑——但没有明显信号,新手会去 `vim decision.md`。
5. **硬门与软警告同色呈现**:accept 面板把 `body_placeholder`(硬拦)和 `applies_to 空`(软警告,样板也空)并列红/黄,判断不了哪个真的拦住。

---

## 改进建议(按性价比排序)

### P0 — 目标导向的前置清单(最高杠杆,能一举消掉大半 round-trip)
给每个生命周期跃迁一个 **`next`/`preflight` 子命令**,一次列全所有未满足项及修法:
```
ha decision preflight <id>            # 要接受它,还差什么
  body:            ✅ 已填四小节
  claim C1:        ❌ 未覆盖 → 需 evidence 关系 + `ha decision claim fulfill --id C1 --mode evidenced`,或 --judgment-only
  applies_to:      ⚠ 空(软警告,不阻塞)
  → 硬门 1 项未过
ha task preflight <id>                # 要 complete,还差什么(lease/submit packet/closeout 四小节/fact)
```
这一条就能把"撞 6 次"变成"看 1 次清单一次改对"。

### P1 — 让"已声明的三元组"可发现
`relation_triple_undeclared` 的错误里直接列出该 source kind 的合法三元组;并加 `ha relation triples [--source-kind fact]` 查询命令。现在靠猜 evidenced-by/supports/relates,纯浪费。

### P1 — 治理型关系的 "compilation authority" 完全不透明(实测彻底卡死)
想给自建实体种类声明一条受治理的关系(`report --relates--> task`),流程是:建决策→填 body→接受→拿 contentPin→在 kind 的 relations 里填 `decisionClaimRef`+`decisionContentPin`。全部照做、`vertical validate` 也 valid=true,但真去 `ha relation relate` 时报 `invalid_vertical_contract: Decision claim ref decision/<id>/CH1 does not exist in the compilation authority`。
- 换 C1(claim)/CH1(chosen)都报同样错;既有的 research 种类能用,是因为它的决策是**导入快照(imported_snapshot)**、天生在 authority 集里。
- **没有任何命令或文档说明:一个新建+已接受的决策如何进入 "compilation authority"**;`validate` 还骗人(声明能过、使用即挂)。结果:用正常 propose→accept 流程创建的决策**无法**授权一条自建关系种类——这条路事实上走不通。
- 建议:①`validate` 就该在编译期发现 authority 缺失并报错,而不是等到 relate;②给一条 `ha vertical decision-authority add <decision>` 或在 accept 决策时可选"纳入 vertical 编译授权";③错误里直接说明如何让该决策进入 authority。

### P1 — 创建即脚手架
`ha decision propose` 自动把 body 填成带四小节的模板(而非留空触发 body_placeholder);`ha task create` 的 closeout.md 已有占位,但可在 submit 时**预检四小节存在**并直接指出缺哪节。

### P2 — 提交/接受的 packet 用 schema 自描述 + 样例
`ha task submit --example` 打印一份可改的 JSON 样例(字段名 + 数组/字符串类型标注);`ha decision accept` 在缺 evidence 时,一次性提示"两条路:①claim fulfill+evidence 关系 ②--judgment-only",而不是分两次报错。

### P2 — 硬门/软警告分区呈现
校验与 GUI accept 面板把 errors(阻塞)和 warnings(不阻塞)分开成两组,标题写明"以下 0 项阻塞 / 2 项建议",消除"哪个真拦我"的困惑。

### P3 — daemon 管理面给出明确信号
对 daemon 管理的 .md,在文件顶部注释或 `ha` 提示"此文件由 daemon 管理,请用 `ha decision amend --body-file`,勿直接编辑";`--body-file` 要求在 workspace 内(踩过:scratchpad 在外被拒),错误可直接建议一个合法路径。

### P3 — 一页"闭环操作手册"随 CLI 分发
不是概念文档,是**配方**:record fact → propose decision(带 body 模板)→ accept(双条件)→ create task → start → submit(packet 样例)→ closeout(四小节)→ complete,每步一行命令 + 一句坑。见本仓 AGENTS.md 新增的"治理配方"节即是一个可抄的样板。

---

## GUI 侧缺陷(用户第一手反馈,与 CLI 同等重要)

1. **Task 详情页没有"人做 review-consent"的入口**。CLI 生命周期是 start→submit→**review-execution→review-consent**→complete,但 GUI 的 Task 详情里根本没有让人执行 review/consent 的地方——只有**决策(Decision)有审批按钮**。后果:任务 submit 进入 in_review 后,**人在 GUI 里无路可走**,只能靠 CLI 或派另一个 agent 来 review。这等于生命周期在 GUI 上断了一节。
   - 建议:Task 详情页补一个"独立评审 / 同意完成"区(镜像 Decision 的接受面板),支持人读 closeout 四小节 + 提交包后一键 review-consent→complete。

2. **状态命名对不上**。CLI 状态是 `in_review`,但 GUI 看板把它显示成"**封存中(Finalizing)**",且没有单独的"**待审阅 / In Review**"分桶。用户在看板上看不到"这些任务在等我审"这一语义。
   - 建议:GUI 增加 `In Review` 状态列/标签,与 CLI 的 `in_review` 对齐;"封存中/Finalizing"若是另一含义应区分,否则统一命名。

3. **连带影响**:因为人无法在 GUI 完成 Task review,实际闭环只能靠"再派一个 review agent(不同 actor,规避 self-review 的 `actor_unauthorized`)代为 review+consent+complete"。这可行但重——**它把本应是人 30 秒点一下的动作,变成一次 agent 派工**。这条恰好反证了 GUI 评审入口缺失的代价。

## 运行时缺陷:zcode(GLM)worker 在 detached dispatch 里完全跑不了 `ha`

派 GLM worker(`zcode-glm-5-3`)做独立评审时,它的 Bash 工具层对**所有** `ha`/`npx harness-anything` 命令一律返回 `No permission client configured for Bash`——连 `ha --version`、绝对路径、`env`、复合命令都被拦;只有 `echo`/`ls`/`which` 这类只读命令能过。即:**在无人值守(detached/headless)的 zcode runtime 里,需要权限确认的命令无客户端可问,直接硬拒**,导致任何写库动作(review/consent/complete/fact)全部无法执行。
- 对比:codex runtime(`codex-api`)在同样 detached 下能正常跑 `ha` 写命令。
- 后果:GLM worker 目前**只能做只读活**(它确实只读核实了任务 ground-truth 并如实汇报),不能承担任何 Harness 写生命周期的委托。
- 另一并发缺陷:`de-reviewer` 这类 agent 声明把 `runtime_type` 钉死为 codex,`ha runtime run zcode-glm-5-3 --agent de-reviewer` 直接 `agent_runtime_type_mismatch`;想用 GLM 当评审只能裸派 `--role reviewer`(绕过声明)。建议:①修 zcode runtime 的 headless 权限客户端;②允许 agent 声明跨 runtime_type 复用,或提供每类 runtime 的对等角色声明。

## 运行时缺陷(最卡)：dispatched worker 写不进 daemon,导致"独立评审"整条无法落库

派 codex worker(codex-api,订阅启用后**能正常运行并产出真实评审报告**——甚至真发现了一个任务的记录矛盾)做 review→consent→complete 时,它的 `ha` 一律报 `daemon_unavailable … workspace is not registered`:
- worker 明明在本机(它自己找到 `/Users/lizeyu/.local/bin/ha`、`/opt/homebrew/opt/node@24`),但连不上 CEO session 用的同一个 daemon(pid 98889,socket 在 `/var/folders/.../T/harness-anything/daemon-501-*.sock`,repos=10 含本仓)。
- worker 尝试自救:`ha daemon repo register` → `EINVAL/invalid_field`;`ha daemon start --service` → `daemon_start_runtime_forbidden`(worker 不许起 daemon)。
- 最可能原因:**codex worker 的沙箱 HOME/userRoot 与主 session 不同 → 看的是另一个 `~/.harness` → 既无注册也无 daemon**。
- 连锁:`noIndependentReview` 逃生路(错误提示说 review JSON 可用 `{noIndependentReview, noIndependentReviewReason}`)实际传入仍报 `invalid_command`,schema 不明,executor 走不通。
- **净后果:一个需要"不同 actor 写库"的动作(独立评审 consent),在"远程/沙箱 worker 连不上本地 daemon + 本机 executor 被 actor_unauthorized + GUI 无入口 + 逃生路 schema 不明"的四重夹击下,事实上无法完成。** baseline milestone 的 10 个任务因此只能停在 in_review,尽管工作、closeout、fact、报告实体、以及一份真实的 codex 只读评审全部就绪。
- 建议(按重要性):①**让 dispatched worker 与 CEO session 共享同一 daemon/userRoot**(或在派发时把 daemon endpoint+workspace 注册透传进 worker 环境)——这是打通"agent 独立评审"的命门;②补 GUI 的 Task review 入口(见上文 GUI 缺陷);③把 `noIndependentReview` 逃生路的 JSON schema 在 `--help` 里写清,并允许 executor 在无独立评审可得时凭理由完成。

## 一句总结给维护者

概念闭环(Fact→Decision→Task)已经很好了。**唯一缺的是把每个跃迁的"隐藏前置条件集合"从文档/报错里,前置成一个可查询的清单**。做了 P0 的 `preflight`,agent 的上手成本会断崖式下降——因为 agent 最怕的不是规则多,是规则**不可见、只能靠撞**。
