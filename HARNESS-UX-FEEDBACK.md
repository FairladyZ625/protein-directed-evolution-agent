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

## 一句总结给维护者

概念闭环(Fact→Decision→Task)已经很好了。**唯一缺的是把每个跃迁的"隐藏前置条件集合"从文档/报错里,前置成一个可查询的清单**。做了 P0 的 `preflight`,agent 的上手成本会断崖式下降——因为 agent 最怕的不是规则多,是规则**不可见、只能靠撞**。
