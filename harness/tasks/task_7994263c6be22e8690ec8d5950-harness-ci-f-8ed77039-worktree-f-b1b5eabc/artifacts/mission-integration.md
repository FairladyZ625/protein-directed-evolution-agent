# 集成收口:让四个修复包共存(分支 stage-w1234)

四个并行修复包各自正确、合并零冲突,但**两两语义不兼容**,集成后 5 个点名测试失败。
worktree 已备好:`.worktrees/stage`,分支 `stage-w1234`(四包已合)。`.venv`、`data/` 已符号链接。

CEO 已做完诊断(fact `F-43D8C747`),**不要重复调查,直接按下面的方向修**。

## 隔离证据(别怀疑 worker 撒谎,他们没有)

- `w-campaign` 单独跑 `tests/test_campaign.py` → 10 passed
- `w-pipeline` 单独跑 `tests/test_agent.py` → 10 passed
- 配对复现:`w-campaign`+`w-pipeline` → test_campaign 3 failed;
  `w-pipeline`+`w-knowledge` → test_agent 2 failed

## 要修的两条,修复方向已由 CEO 裁定

### 第一条:campaign 的合成夹具缺实测池(改测试,不改代码)

包2 给 `run_pipeline` 加了「候选必须与 149,361 实测集合求交」——**这个约束是对的、是 CEO 要的**
(修的是「提名了 oracle 查不到的变体」这个缺陷)。包1 的合成夹具 `candidate_space_size=16`
且没提供实测集合,于是候选被全过滤,`tests/test_campaign.py:47` 的
`[r["n_nominated"] for r in result["rounds"]]` 从期望 `[2, 2]` 变成 `[]`。

→ **修复方向:补夹具,让合成池提供与候选相交的实测集合。**
→ **禁止**削弱 `[2, 2]` 这个断言,也**禁止**关掉或绕过求交约束。

### 第二条:R-PRIORITIZE-HISTORICAL 被实现成了硬门(改代码)

包3 让 `R-PRIORITIZE-HISTORICAL` 在无历史数据时返回 `pass=False`
(note:`historically high-fitness single mutants: none`)。而 `agent/pipeline.py` 的
`ScientificCritic` 判定是 `ok = all(x["pass"] for x in rules)`,于是**全部候选被拒**,
`PipelineResult.accepted` 为空 → `tests/test_agent.py:197` 失败。

**「优先历史好单点」在语义上是 prioritization(排序建议),不是 viability gate(可行性门禁)。**
它不得参与拒收判定。这是实现方向错误。

→ **修复方向:把规则分成两类** —— 参与拒收的 gate 规则,与只影响排序/提示的 advisory 规则。
  `R-PRIORITIZE-HISTORICAL` 归 advisory;`ScientificCritic` 的 `ok` 只对 gate 类求 all()。
  规则自身要带上这个类别标记(别在 critic 里硬编码规则 ID 白名单——那样下次加规则又会撞)。
→ 该规则的**能力本身要保留**(题面与契约要求「历史好单点优先」),只是改成不拒收。
→ 顺带确认:`--no-knowledge` 消融开关行为不得回退。

## 验收(CEO 亲验)

- `pytest tests/test_campaign.py tests/test_agent.py tests/test_knowledge.py tests/test_events.py`
  在冻结提交树上**全绿**(当前是 5 failed, 28 passed)。
- CEO 会逐条看 diff 判断:**每一处测试改动都要有理由**。把断言改松来求绿 = 整轮作废。
  如果你认为某条断言确实编码了旧的错误行为、应当修改,**在 commit message 里写明为什么**。
- CEO 会 grep 确认求交约束与 `--no-knowledge` 都还在。

## 边界

- 在 `.worktrees/stage` 的 `stage-w1234` 分支上工作。
- 可动:`tests/test_campaign.py`(夹具)、`knowledge/`(规则分类)、`agent/pipeline.py`
  (critic 判定式)。**动 `agent/pipeline.py` 时不要回退包2 的求交与 schema 校验。**
- **不要动** `evolution/campaign.py` 的策略路由(包1 刚修好的 ③④ 参数化
  `no_knowledge=(strategy == "agent_no_knowledge")` 必须保留)、`events/`、`models/`、`app/`。
- 停止点 = 四组点名测试全绿 + commit。**不 push、不发 PR。**
- 不要跑全量测试矩阵(同机还有 3 个 worker 在飞)。
- 发现 CEO 的裁定错了,带证据回报并停手。
