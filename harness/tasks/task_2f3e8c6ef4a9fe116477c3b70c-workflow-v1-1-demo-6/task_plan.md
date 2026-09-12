# demo 接受野生型序列输入,并按输入重算位点菜单

产物版本:`workflow-v1.1` —— 交付主线下一版。本任务只动 demo 这一层。

## Brief

笔试题加分项第六条是「实现一个简单可交互 demo,**输入野生型序列后自动推荐突变方案**」。
`app/demo.py` 三个模块都在且做得不错(四策略对比 / 五角色回放 / 实时试玩,有 `st.text_input`
收变体并秒级打分、一键跑一轮 agent 推荐),**但它偏题**。

## Goal

让「输入野生型序列 → 自动推荐突变方案」这条路径真的存在且可用。
成功判据:换一个野生型,推荐集合随之变化(而不是永远围着写死的 `VDGV` 转)。

## Context

CEO 已核实的偏题点:
- `app/demo.py:48` 把 `WT = "VDGV"` **写死**;
- 模块③的 `st.text_input("变体(4 个标准氨基酸)")` 收的是**变体**,不是野生型;
- 于是题目要的那条路径实际不存在。

GB1 口径:四个可变位点 V39/D40/G41/V54,WT `VDGV` fitness = 1.0,真值表 149,361 / 160,000。

## Required Reading

- `app/demo.py` 全文(尤其它的只读纪律 docstring)
- `evolution/campaign.py` 的 `run_campaign` 签名(单轮路径,只读复用)
- `README.md` 的 Interactive demo 一节

## Entry Conditions

worktree `.worktrees/t-demo-wt` 已建好,`.venv` 已符号链接。基线 `origin/main`。

## Dependencies

无阻塞依赖。注意 `task_df963f97f7ae5411853967621d`(Agent 推理显式化)之后会改 demo 的
五角色回放模块,但那个任务排在你之后,不冲突。

## Execution Surface

**只动**:`app/demo.py`、`tests/test_demo.py`、`README.md` 的 demo 一节。

**不要动**:`evolution/`、`agent/`、`models/`、`knowledge/`、`events/`——都有其他 worker 在飞。
只读复用它们的接口没问题;**若发现必须改它们才能做成,带证据回报并停手**,别硬改。

## Constraints

**必须保留、不得回退**:demo 全程**只读**的纪律(现有 docstring 写明:
`@st.cache_data`/`@st.cache_resource` 缓存加载,绝不 append 事件流、绝不覆盖 `reports/` 下
任何产物;模块③的推荐事件只进内存 recorder,不落盘)。这条纪律是对的,
**不要为了新功能破坏它**。模块①②现有行为不变。

**诚实性**:用户输入的 WT 不在 149,361 实测集合里时(完全可能),必须**显式告知**
「该野生型无实测基准,以下推荐的 fitness 为模型预测值而非实测」。
**不许把预测值当实测值展示。**

## Checkpoint

若判断"支持任意全长序列输入"成本过高,**可以只支持四位点口径并说明**,这是允许的降级;
但「换 WT 推荐随之变化」这条不可降级,做不到就回报停手。

## CI/Gate Authority Stop Condition

停止点 = `pytest tests/test_demo.py` 绿 + commit。**不 push、不发 PR、不打 tag。**
不要跑全量测试矩阵(同机多 worker)。

## Implementation Plan

1. **野生型输入框**:接受用户输入的野生型序列。至少支持 GB1 四位点口径(4 个标准氨基酸,
   默认 `VDGV`);实现成支持全长 + 指定可变位点更好,不强求。
2. **按输入重算位点菜单**:候选替换集合、one-hot 编码基准、「相对野生型的增益」
   这些量全部相对用户输入的 WT 重算,不再用写死值。
3. **自动推荐**:给定输入 WT,输出 Top-k 推荐突变及预测 fitness 与理由。
   复用现有 `evolution.campaign.run_campaign` 单轮路径与 Ridge 打分,**别另造模型**。
4. **输入校验与诚实降级**:非标准氨基酸、长度不符 → 明确报错,
   **不要静默回退到 `VDGV`**;WT 无实测基准 → 按 Constraints 显式标注。

## Deliverable Contract

- 改造后的 `app/demo.py`。
- `tests/test_demo.py` —— 纯逻辑抽成可测函数或用 streamlit 无头调用,二者皆可。
- `README.md` 的 Interactive demo 一节同步更新运行命令与新增能力。

## Evidence Protocol

- **阳性对照必做**:换一个 WT,推荐必须随之变化;**若两个不同 WT 给出同一套推荐,测试要红**。
- 非法输入 → 断言明确报错(不是静默回退)。
- WT 不在实测集合 → 断言返回/展示里带"预测值非实测"的标记。

## Verification

- `pytest tests/test_demo.py` 在冻结提交树上全绿,阳性对照真的能红。
- CEO 会自己 `streamlit run app/demo.py` 起来,换两个不同 WT 看推荐是否真的变。
- CEO 会 grep 确认 `WT = "VDGV"` 这种写死值不再控制下游计算。
