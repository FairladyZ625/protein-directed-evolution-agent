# 包2:五角色流水线补齐三项硬约束

你在修一个**已被独立评审打回的任务**。评审全文在任务包 `reviews/` 下最新 .md,**先读它**。

## CEO 已复核的事实(别重复调查)

`agent/pipeline.py` 的五个角色**是真的在跑**,LLM 端口经 `evolution/campaign.py:193` 的
`_llm_hypothesis` 真调网关(`chat_json`),失败时把 `state["source"]` 如实记成 `fallback`。
这部分不是假的,**不要推翻重写**。真正的缺口是下面三条。

## 缺口

1. **没有构造 PydanticAI `Agent`,也没有 `output_type=Pydantic schema`。**
   契约写的是「PydanticAI 五角色」。现状是 Pydantic 的 `BaseModel` 做结构化输出 + 直连
   OpenAI 兼容客户端——Pydantic 用了,PydanticAI 的 `Agent` 没用。
   参照实现在同仓 `agent/auto_researcher.py:256-282`(它真用了 `Agent` + `UsageLimits`)。
   → 两条路选一条,**选哪条你判断,但必须自洽**:
     (a) 在 pipeline 的两个 LLM 角色里真用 `Agent(model, output_type=<schema>)`;
     (b) 若你判断 (a) 对本流水线是过度工程,则把契约声称改成实测支持的样子,
         并在 closeout 里写明为什么 PydanticAI 的 Agent 在这里不划算。
     **我要的是不造假,不是要你硬凑框架。** 但 (b) 必须给出站得住的对价理由。
2. **两个 LLM 端口是任意 `Callable`,异常与非 schema 返回会直接向上传播。**
   → 端口要有 schema 校验和异常边界。fallback 语义沿用现有的 `state["source"]` 记账法。
3. **`MutationDesigner` 不把候选与 149,361 实测集合求交**(阳性对照仍提名集合外的 `IEGV`)。
   这条最严重:提名了 oracle 查不到的变体,等于凭空产出候选。
   → 候选必须与实测集合求交;补一个阳性对照测试,断言集合外变体被拒。

## 验收口径

- `pytest tests/test_agent.py` 在冻结提交树上全绿,且**新增**一个断言"集合外变体被拒"的测试。
- 我会自己 grep 求交逻辑与 PydanticAI 的使用,不看汇报。

## 边界

- **只动** `agent/pipeline.py`、`tests/test_agent.py`。
- **`run_pipeline` 的签名必须保持不变**(另一个 worker 正在 `evolution/campaign.py` 里调它):
  `run_pipeline(pool, predictor, *, event_store, llm_hypothesis, llm_critic, budget, round_id, no_knowledge)`。
- **不要动** `evolution/`、`models/`、`knowledge/`、`events/`、`agent/auto_researcher.py`。
- 独立 worktree。停止点 = 点名测试绿 + commit,不 push、不发 PR。
- 发现 CEO 判断有误就带证据回报并停手。
