# AI4S 笔试：Python 原生 Agent Runtime 对比 × 三路线最终裁决

> 调研日期：2026-09-10（周四）。服务于 9/13（周日）15:00 冻结的明度数智 AI4S 笔试。
> 姊妹篇：`AI4S笔试-piSDK与前端壳选型.md`（pi 路线事实与前端壳对比，本篇不重复）。
> 本篇回答一个问题：**既然泽宇开放了「Python 生态有好 Runtime 就不必用 pi」的选项——有没有？最终走哪条路？**
> 所有 star/版本/文档能力均于 2026-09-10 经 GitHub API / PyPI / 官方文档实测核实，逐条附来源。

---

## TL;DR（三条硬结论）

1. **有，而且不止一个能打：Python 生态 2025–2026 已长出完整一代轻量 Agent Runtime**。经实测筛选，**PydanticAI 是本笔试的最优解**——它同时命中四个命门：`Agent.iter()` 节点级循环控制、`ProcessEventStream` 官方文档原话就是 "forward events to … **audit log**"（事件流内核直接对位）、**Z.AI/GLM 一等 provider**（`Agent('zai:glm-5')` 一行起）、工具就是普通 Python 函数（pandas/sklearn 代码原样挂进去）。
2. **三路线裁决：B 胜出。推荐「PydanticAI（loop+事件流+GLM）+ Chainlit demo（Streamlit 保底）」**。pi 全量路线（A）和混合路线（C）在 4 天窗口里都是负期望——A 的跨语言桥接成本上一份报告已算过账（+0.5~1 天），C 是「两个生产者 + schema 归一化」的最差组合。**pi 的正确用法是当叙事资产和周日彩蛋，不是当运行时。**
3. **泽宇否决「自研 loop」的决策被 PydanticAI 满足，且不被打脸**：自研 loop 讨嫌的是「连 retry/结构化校验/工具 schema 都要手写」；PydanticAI 把这三件脏活全包了（type-safe tools + 结构化输出重试 + usage 控制），但 loop 语义、事件流、deps 注入全部可编程——**它不是 LangChain 式的框架绑架，是 FastAPI 团队做的「Pydantic way」最小原语集**。面试话术见 §5。

---

## 1. 候选全景：六个 Python Runtime 实测对比

### 1.1 硬数据总表（2026-09-10 GitHub API / PyPI 实测）

| Runtime | Stars | 创建 | 最近推送 | 当前版本 | License | 一句话定位 |
|---|---|---|---|---|---|---|
| **PydanticAI** (pydantic/pydantic-ai) | 19,845 | 2024-06 | **当天（09-10）** | 2.42.0（V2 稳定版自 2026-06-23） | MIT | FastAPI 团队出品，type-safe agent 原语集 |
| **OpenAI Agents SDK** (openai/openai-agents-python) | 29,321 | 2025-03 | 09-09 | 0.22.2（**仍是 0.x**） | MIT | Swarm 正式继任者，OpenAI 官方轻量 SDK |
| **Google ADK** (google/adk-python) | 21,478 | 2025-04 | 当天 | 2.8.0 | Apache-2.0 | Google 全家桶 Agent 框架（Vertex/Cloud Run/GKE 联动） |
| **Agno** (agno-agi/agno，原 Phidata) | 42,128 | 2022-05 | 当天 | 3.0.9 | Apache-2.0 | 多 agent + AgentOS + 自带 UI 的大而全框架 |
| **Chainlit** (Chainlit/chainlit) | 12,442 | 2023-03 | 09-09 | 2.12.0（Python 3.10–3.13） | Apache-2.0 | Python 聊天 UI 框架，**与任意 agent 集成**（非 runtime） |
| smolagents (huggingface/smolagents) | 29,270 | 2024-12 | 08-25（两周前） | — | Apache-2.0 | HF 极简派，核心 ~1k 行，CodeAgent 写代码当动作 |

来源：GitHub REST API 2026-09-10 实测；PyPI JSON API（chainlit 2.12.0 / pydantic-ai 2.42.0 / openai-agents 0.22.2 / google-adk 2.8.0 / agno 3.0.9）；PydanticAI 版本策略页 https://pydantic.dev/docs/ai/project/version-policy/ （V1 2025-09，V2 稳定 2026-06-23）。

### 1.2 六维评估矩阵（对本笔试的适配度）

评分 1–5。「事件流埋点」指：把每步推理写入自建 events.jsonl 的能力（题目差异化命门）。

| 维度 | PydanticAI | OpenAI Agents SDK | Google ADK | Agno | Chainlit | smolagents |
|---|---|---|---|---|---|---|
| **Agent loop 控制力** | **5**：`Agent.iter()` 暴露节点级图执行（官方：「async-iterate, or manually drive node-by-node」），`RunContext` deps 注入，usage limits 可编程 | 4：内置 loop + `RunHooks/AgentHooks` 生命周期钩子（`on_llm_start/end`、`on_tool_start/end`、`on_handoff`） | 3：`before/after_tool_callback` 可拦截/改写/跳过，但 loop 本体是框架的 | 2：loop 深埋在 Agent/Team/Workflow 抽象后 | —（不是 loop，是 UI） | 3：CodeAgent/ToolCallingAgent 两种范式，loop 简洁但控制面窄 |
| **事件流埋点** | **5**：`ProcessEventStream` capability 官方原话 "forward … model streaming and tool execution events to a handler … websocket, progress bar, **or audit log**"；流式 delta 粒度 | 3：`run_streamed` 出 raw response events + RunItem 事件，粒度可用但非为审计设计 | 3：有 Event Loop/observability 体系，绑定 Google Cloud Trace 生态 | 2：observability 面板导向，自定义落盘要走它的 storage 抽象 | **4**（作为消费者）：`@cl.step` 把任何 Python 函数变成 UI 时间线节点，与 events.jsonl 同源双写极自然 | 3：有日志但自定义事件 schema 要自己包 |
| **多 provider（GLM/OpenAI 兼容/Anthropic）** | **5**：**Z.AI 一等 provider**（`pip install pydantic-ai-slim[zai]`，`Agent('zai:glm-5')`，GLM 系 thinking 模式全支持）；OpenAI 兼容走 `OpenAIProvider(base_url=…)`；Anthropic/Google/xAI/Bedrock/Groq/Mistral/Ollama/OpenRouter 内置 | 4：`set_default_openai_client()` 把任一 OpenAI 兼容端点设为全局默认（对 GLM 干净）；Anthropic/Google 有第三方 adapter（LiteLLM/any-llm） | 2：Google 系一等，其他 provider 要绕 LiteLLM 类适配 | 4：model 层 provider 面宽 | —（跟随宿主 runtime） | 3：默认 HF InferenceClientModel，OpenAI 兼容要过 LiteLLM |
| **Python 数据科学栈融合** | **5**：`@agent.tool` / `@agent.tool_plain` 装饰普通函数，类型注解→schema，docstring→描述；pandas DataFrame/sklearn 模型对象经 `deps_type` 直接注入 | **5**：`@function_tool` 同样是普通函数（inspect + griffe + pydantic 生成 schema，结构化返回注解自动变 strict schema） | 4：Python 函数工具，但推荐经其 tool 生态 | 3：可以，但工具要按它的 Toolkit 风格注册 | **5**：纯 Python 侧，任何函数 | 4：`@tool` 装饰器 |
| **前端/demo 能力** | **4**：`clai web` / `agent.to_web()` 内置浏览器聊天（零代码）；可经 AG-UI / Vercel AI 协议流到自建前端 | 2：无 UI，靠第三方 | 2：dev UI 面向调试 | 3：Agent UI（Next.js/TS，`pnpm install && pnpm dev`）漂亮但**把 TS 栈请回来了** | **5**：`@cl.step(type="tool")` 天然渲染五角色嵌套时间线，自带 React 前端 | 2：Gradio 生态 |
| **二开深度 vs 上手成本（4 天约束）** | **5**：核心概念一个下午吃完（Agent/tool/output/deps），V2 API 已稳定 | 4：原语极少，但 0.x 版本在演进、OpenAI 中心默认值（Responses API）偶有惊喜 | 2：概念面大（Agent/Session/Workflow/Artifact/Deployment），Google 引力强 | 2：Agno v3 演进快、抽象多，4 天内学不完它的正确姿势 | **5**： decorator 即所得 | 4：极简，但 CodeAgent 范式与本题主线不合 |

各格事实来源（抽核）：
- PydanticAI `Agent.iter()`/手动驱动节点：https://ai.pydantic.dev/agents/ ；ProcessEventStream→audit log：https://ai.pydantic.dev/capabilities/process-event-stream/ ；Z.AI provider：https://ai.pydantic.dev/models/zai/ ；OpenAI 兼容 base_url：https://ai.pydantic.dev/models/openai/ ；工具=普通函数：https://ai.pydantic.dev/tools/ ；`clai web`/AG-UI/Vercel AI 接口：https://ai.pydantic.dev/interfaces/
- OpenAI Agents SDK 原语集（Agents/handoffs/guardrails/built-in loop）：https://openai.github.io/openai-agents-python/ ；生命周期钩子全表：https://openai.github.io/openai-agents-python/ref/lifecycle/ ；`@function_tool` schema 生成与 strict 结构化返回：https://openai.github.io/openai-agents-python/tools/ ；非 OpenAI 端点四种接法（`set_default_openai_client` 为全局默认路径）：https://openai.github.io/openai-agents-python/models/
- ADK callbacks（before_tool_callback 可跳过工具执行、after_tool_callback 改写结果）：https://google.github.io/adk-docs/callbacks/ ；全家桶定位（orchestration → workflows → eval → Cloud Run/GKE 部署）：https://google.github.io/adk-docs/
- Agno Agent UI（Next.js/TS，需连本地 AgentOS server，`git clone … && pnpm install && pnpm dev`）：https://docs.agno.com/other/agent-ui
- Chainlit `@cl.step(type="tool")` 机制与 cookbook（OpenAI/LangChain/LlamaIndex/AutoGen/MCP 等 40+ 示例，框架无关）：https://github.com/Chainlit/chainlit/blob/main/backend/README.md ；cookbook 目录实测：https://github.com/Chainlit/cookbook
- smolagents（核心 ~1k 行、CodeAgent/ToolCallingAgent、Docker/E2B 沙箱）：https://huggingface.co/docs/smolagents/en/index

> ⚠️ 诚实标注：docs.chainlit.com 在本调研环境被网络层拦截（DNS/TLS 均不通，curl/urllib/Jina 三路验证），Chainlit 事实取自 GitHub 仓库 README + PyPI + GitHub API，未逐页核对官方文档。上一份报告（piSDK 选型篇 Part 2）已独立核实其 12.4k★/Apache-2.0/活跃维护。

### 1.3 逐个裁决（一段话判词）

- **PydanticAI ✅ 入选**：唯一一个在「循环控制 / 审计事件流 / GLM 一等支持 / 科学栈零摩擦」四个维度全部拿 5 的候选。且它是 FastAPI 团队做的基础设施级作品（V2 已稳定、MIT、当天仍在推），不背 LangChain 式框架债——「Pydantic way」恰好就是明度面试官要的「schema 圈住 LLM」的官方实现。**没落点可挑：非要说就是 async-first，主线程要用 `run_sync` 或 asyncio.run 适配（一次性成本，几分钟）。**
- **OpenAI Agents SDK ✅ 备选**：真实好用、原语极简，`set_default_openai_client()` 接 GLM 也干净。三处扣分：0.x 版本（4 天窗口里不想当版本迁移的小白鼠）；事件钩子粒度不如 PydanticAI 事件流贴审计需求；handoffs/guardrails 主打多 agent 委派——本题五个角色是流水线不是委派，用不上它的差异化卖点。**若 PydanticAI 的 zai provider 出幺蛾子，退到这里（OpenAI 兼容 base_url 两家都支持），迁移成本半天内。**
- **Google ADK ❌**：能力不弱（callbacks 拦截面完整），但它是「Google 云生态的一等公民 + 其他平台的二等公民」——provider 要绕道、部署叙事是 Cloud Run/GKE、概念面（orchestration/workflows/eval/deployment）全在题目明说不需要的方向上。4 天里学 ADK 的正确姿势本身就是风险。且泽宇反感框架味，ADK 是六个里框架味最正的。
- **Agno ❌**：42k★ 最风光，但两处硬伤：Agent UI 是 Next.js/TS + pnpm + 本地 AgentOS server——**把 pi 路线的 TS 栈原封不动请回来了**，跨语言桥接成本换个马甲；v3.x 抽象面（Agents/Teams/Workflows/Memory/Knowledge/Storage/Evals）远超本题需要。demo 好看不值两天工期。
- **Chainlit ✅ 以「壳」身份入选**：它不是 runtime，是本题前端壳的答案——上一份报告已判它主选，本篇唯一要补的判定是：**它与 PydanticAI 组合零阻抗**（同为 Python 3.10+，cookbook 证明框架无关，`@cl.step` 包住 `agent.iter()` 的每个节点即可）。注意 cookbook 目前无 pydantic-ai 官方示例（目录实测），但机制是通用 async Python，无需官方背书。
- **smolagents ❌（本题主线）**：哲学上最接近「轻」，但 CodeAgent 的动作空间是「写代码」——正是面试官点名不要的「大模型自由发挥」；ToolCallingAgent 范式可用但结构化输出与事件埋点不如 PydanticAI 直接。且默认模型客户端是 HF Inference。留作报告「相关工作」一段的引用素材即可。

---

## 2. 关键机制对位：PydanticAI 怎么嵌进现方案

> 现方案（`AI4S笔试-技术方案.md` §1.4/§M3）的形态判定不变：**角色 = 流水线阶段，LLM 只出现在 Hypothesis Generator 和 Critic 两处**。PydanticAI 替换的不是形态，是原来要手写的 loop 骨架。

| 现方案组件 | PydanticAI 承接方式 | 来源 |
|---|---|---|
| `llm.py` provider 抽象（GLM 默认可切） | 直接删掉——`Agent('zai:glm-5')`，ZAI_API_KEY 环境变量；切 provider 改一个字符串 | https://ai.pydantic.dev/models/zai/ |
| 结构化填空 + 校验失败重试 | `output_type=Hypothesis`（Pydantic model），校验失败自动带 ValidationError 重试（retries 参数可调） | https://ai.pydantic.dev/agents/ |
| 五角色里的 3 个纯函数角色 | 不进 agent——保持纯 Python 函数，由 `campaign.py` 编排（Agent 只包 LLM 两角色；deps 注入 `SiteReport`/模型句柄） | https://ai.pydantic.dev/tools/ |
| events.jsonl 事件流 | ①`ProcessEventStream` capability 把 model/tool 执行事件转给 handler → append 进 events.jsonl（官方文档明示 audit log 用法）；②`Agent.iter()` 手动驱动节点，每个节点边界 emit 业务事件（round.started / proposal.validated …） | https://ai.pydantic.dev/capabilities/process-event-stream/ ; https://ai.pydantic.dev/agents/ |
| LLM 调用埋点细节 | 事件含流式 delta 粒度（`AgentStreamEvent`），token usage 从 `AgentRun` 取——比手写 loop 埋得还全 | 同上 |
| Streamlit demo（§1.6） | 主换 Chainlit：`@cl.step` 渲染五角色时间线 = events.jsonl 的免费 UI 投影；Streamlit 保留为保底（两者读同一份事件流，怎么换都不返工） | https://github.com/Chainlit/chainlit/blob/main/backend/README.md |
| 彩蛋（周日可选） | `clai web` 一行起浏览器聊天，README 附录截个图；pi RPC 单轮录屏照旧按需 | https://ai.pydantic.dev/interfaces/ |

**架构一句话**：`campaign.py`（确定性 DBTL 外环）→ 每轮调 `RoundAgent = Agent('zai:glm-5', output_type=HypothesisList, tools=[查表oracle, 适应度打分], deps_type=CampaignContext)` → ProcessEventStream + 节点 emit 双路写 events.jsonl → Chainlit/Streamlit 读投影。**事件命名继续借 pi 的 RPC 语义**（`tool_execution_start/end`、`agent_settled`→`round.completed`），架构图照画「事件模型对齐 pi Agent Runtime」——pi 的叙事资产一点没丢。

---

## 3. 三路线最终裁决表

| 维度（权重） | **A：pi + 子进程桥/JSON 驱动 + 找前端壳** | **B：PydanticAI + Chainlit（Streamlit 保底）** | **C：混合（Python 主体 + pi headless 只当 LLM loop）** |
|---|---|---|---|
| **4 天工期风险**（权重最高） | **3/10**：Node 子进程生命周期 + RPC JSONL 解析（官方明示 LF-only 陷阱）+ Python 能力全包 CLI 壳 + 前端壳另找 + README 复现要求考官装 Node+pi。周六关键日风险被放大（上篇测算 +0.5~1 天） | **9/10**：pip install 即全量；单进程；工具=普通函数；GLM 一等 provider；Chainlit 与管线同语言同进程。新增风险仅「Chainlit 会话模型 vs 固定布局」——保底 Streamlit 已在方案内 | **4/10**：A 的全部桥接成本照付，另加「两个事件生产者 + schema 归一化」（上篇估算 30–60 行 + 联调）；pi 在 C 里提供的只是 LLM loop，而 LLM loop 恰是 B 里最成熟的部分——为最不缺的东西付最贵的成本 |
| **效果上限** | 6/10：TUI 帅但笔试演示要 web；demo 体验取决于能不能及时找到并驯服壳 | **9/10**：Chainlit step 树时间线 = 推理过程展示（题目 3.d.iv）的最短路径；`clai web` 白送一个聊天界面；事件流三投影（UI/jsonl/sqlite）叙事完整；四策略对比、消融、回放全部不受影响 | 7/10：上限=B，外加「runtime 可切换」的展示点；但两个系统都要调试到能演示，实际到达率低于 B |
| **面试叙事价值** | 9/10：与泽宇生产环境/已讲过的 pi 迁移故事完全一致；「我用生产 SDK 交付」 | **8.5/10**：三段式都成立——①「题目栈纯 Python，评分环境 pip 即复现，我选了与约束一致的路线」是工程判断力；②「我评估过 pi（TS harness）与 PydanticAI，最终事件模型借了 pi 的 RPC 语义」= 迁移故事的延伸而非否定；③PydanticAI=FastAPI 团队的 type-safe 工具 schema，直接对位面试官「schema 圈住 LLM」原话。扣 0.5：没有「我生产在用」的第一人称加持 | 7/10：「runtime 无关架构」听起来高级，但面试官追问「为什么不给纯 Python」时，答案（为了用 pi 的 loop）在本题语境下站不住——loop 是最不该外包给跨语言进程的部分 |
| **开发顺滑度** | 4/10：调试面四层（模型/prompt/CLI 壳/RPC 桥） | **9/10**：调试面两层（模型/代码）；V2 API 稳定；文档质量高（FastAPI 团队传统艺能） | 5/10：三层调试面 + 双系统心智负担 |
| **加权合计** | 5.0 | **8.9** | 5.4 |

---

## 4. 最终推荐（不骑墙）

**走路线 B：PydanticAI 承担 agent loop + 结构化输出 + 事件流埋点，Z.AI GLM 做 provider，Chainlit 做 demo（Streamlit 保底），pi 降级为叙事资产 + 周日可选彩蛋。**

三个理由，按权重排：

1. **工期数学**：B 比 A 省下的 0.5~1 天正好是周六「四策略 × 3 轮 + 事件流回放」最重关卡需要的缓冲。4 天项目里，工期风险就是一切其他价值的前提——A 的叙事优势再大，demo 跑不完都是零分卷。
2. **能力对位**：本题对 runtime 的三个真实需求——LLM 圈在 schema 里、每步推理可落盘、GLM 直连——PydanticAI 三项全部是官方一等特性（不是 workaround），pi 三项全部要过桥（schema 校验跨进程回喂、事件流过桥接层、provider 倒是 pi 强项但 PydanticAI 也不弱）。**为一道题需要的三个能力选一个三项全一等、一个三项全要桥的，这不是偏好问题。**
3. **叙事不被削弱**：泽宇担心的「不用 pi 叙事断裂」不成立。新叙事更完整：「我的生产环境用 pi（TS），笔试题栈是 Python——我按约束选了 PydanticAI，但事件模型和 loop 语义沿用 pi 的设计（tool_execution_start/end、agent_settled），两个 runtime 的心智模型是一致的。」这句话同时展示了：技术选型服从约束、抽象能力（跨 runtime 的共同语义）、生产经验（真用过 pi 才说得出它的语义）。**比「硬上 pi」更像资深架构师的答案。**

**行动项（并入技术方案 §1.4/§M3/4.2 计划）**：
- 周五晚（原找 Streamlit 模板的时段）：`pip install "pydantic-ai-slim[zai]"`，用 GB1 假数据跑通最小 `Agent('zai:glm-5', output_type=Hypothesis)`——**这一步是 B 路线的排雷点，30 分钟内出结果，失败立即降级 OpenAI 兼容 base_url，再不行退路线 A 的话周四晚就知道而不是周六**。
- 周六上午（事件流内核时段）：ProcessEventStream handler → events.jsonl 适配器（预计 <40 行，替代原方案手写 loop 里的埋点）+ 纯函数三角色保持不动。
- 周日：Chainlit demo（若会话模型打架，Streamlit 保底照旧）；`clai web` 截图进 README 附录；时间富余加 pi RPC 单轮录屏彩蛋。

---

## 5. 面试话术（背下来）

**「你为什么没用 pi / 没自研 loop？」**
> 「我评估了三条路：pi Agent SDK、PydanticAI、自研。pi 我生产环境在用，但它是 TS runtime，Python 工具要包 CLI 经 bash 调，为一道题引入跨语言桥接，风险与收益不成比例；自研 loop 则要手写重试、结构化校验、工具 schema 这些每个 runtime 都要解决的轮子。PydanticAI 是 FastAPI 团队的最小原语集——LLM 被圈在 Pydantic schema 里做结构化填空，工具就是带类型注解的普通 Python 函数，我们的 pandas/sklearn 管线原样挂进去；事件流用它的 ProcessEventStream 直接落 audit log，事件命名我沿用了 pi 的 RPC 语义，所以两套 runtime 的心智模型是一致的。题目说『不要求复杂框架』——我理解这是奖励最小依赖下的最大控制力，PydanticAI 的定位正好在这个甜点上。」

**若被追问 PydanticAI 细节（备料）**：`Agent.iter()` 节点级手动驱动 / `output_type` 校验重试 / `deps_type` 依赖注入（模型句柄、数据池直接传）/ Z.AI 一等 provider 与 GLM thinking 模式 / ProcessEventStream 转发 `AgentStreamEvent`。每一条都有官方文档 URL 可引（见 §1.2 来源清单）。

---

## 6. 风险登记（B 路线新增项）

| 风险 | 概率 | 缓解 |
|---|---|---|
| `pydantic-ai-slim[zai]` 的 zai provider 与当前 GLM 端点/模型名不匹配 | 低-中 | 周五晚 30 分钟排雷（§4 行动项）；降级链：zai provider → OpenAI 兼容 `OpenAIProvider(base_url=…)` → openai-agents SDK（半天迁移）→ 原自研 loop 兜底（技术方案 §1.4 从未删除） |
| PydanticAI async-first 与现有同步管线（sklearn/Streamlit）风格冲突 | 低 | `run_sync()` 全覆盖同步场景；Chainlit 本身 async 原生，反而更顺 |
| Chainlit 会话模型（多用户多会话）与「一键跑 3 轮固定布局」的演示诉求打架 | 中 | 上篇已定 Streamlit 保底；两者消费同一 events.jsonl，切换零返工 |
| PydanticAI V2 API 与网上旧教程（V1 语法）混杂，抄示例踩坑 | 中 | 只看官方文档 ai.pydantic.dev（本篇全部来源即官方站）；跳过一切 2026-06 之前的博客示例 |
| 事件流三投影（jsonl/sqlite/UI）schema 漂移 | 低 | schema 定义单点化（一个 `events.py` 常量表），Chainlit/Streamlit/replay 全部从常量表生成 |
| 面试官反而期待 pi 现身（「你们不是在用 pi 吗」） | 低 | §4 理由 3 的话术正面回答；README 附录留 pi RPC 彩蛋录屏位（周日时间富余才做） |

---

## 7. 来源清单（全部 2026-09-10 实测可达）

**GitHub API / PyPI（star、推送、版本）**
1. https://api.github.com/repos/pydantic/pydantic-ai · https://pypi.org/project/pydantic-ai/ （19,845★ / 2.42.0）
2. https://api.github.com/repos/openai/openai-agents-python · https://pypi.org/project/openai-agents/ （29,321★ / 0.22.2）
3. https://api.github.com/repos/google/adk-python · https://pypi.org/project/google-adk/ （21,478★ / 2.8.0）
4. https://api.github.com/repos/agno-agi/agno · https://pypi.org/project/agno/ （42,128★ / 3.0.9）
5. https://api.github.com/repos/Chainlit/chainlit · https://pypi.org/project/chainlit/ （12,442★ / 2.12.0）
6. https://api.github.com/repos/huggingface/smolagents （29,270★）

**PydanticAI 官方文档**
7. Agents / `Agent.iter()` 节点驱动：https://ai.pydantic.dev/agents/
8. ProcessEventStream（audit log 原话）：https://ai.pydantic.dev/capabilities/process-event-stream/
9. Z.AI provider（zai:glm-5 / thinking 模式）：https://ai.pydantic.dev/models/zai/
10. OpenAI 兼容端点（base_url/api_key）：https://ai.pydantic.dev/models/openai/
11. 函数工具（@agent.tool / RunContext / deps）：https://ai.pydantic.dev/tools/
12. Interfaces（clai web / AG-UI / Vercel AI）：https://ai.pydantic.dev/interfaces/
13. 版本策略（V2 稳定 2026-06-23）：https://pydantic.dev/docs/ai/project/version-policy/

**OpenAI Agents SDK**
14. 概览（原语集/built-in loop）：https://openai.github.io/openai-agents-python/
15. 生命周期钩子：https://openai.github.io/openai-agents-python/ref/lifecycle/
16. 工具与 strict schema：https://openai.github.io/openai-agents-python/tools/
17. 非 OpenAI 模型四种接法：https://openai.github.io/openai-agents-python/models/
18. 流式事件：https://openai.github.io/openai-agents-python/streaming/

**ADK / Agno / smolagents**
19. ADK callbacks：https://google.github.io/adk-docs/callbacks/ ；定位：https://google.github.io/adk-docs/
20. Agno Agent UI（Next.js/pnpm/AgentOS）：https://docs.agno.com/other/agent-ui
21. smolagents（~1k 行 / CodeAgent）：https://huggingface.co/docs/smolagents/en/index

**Chainlit**
22. backend README（@cl.step 机制 / cookbook 指引）：https://github.com/Chainlit/chainlit/blob/main/backend/README.md ；cookbook 目录实测（40+ 框架示例，无 pydantic-ai 官方示例）：https://github.com/Chainlit/cookbook ；官方文档站 docs.chainlit.com 在本调研环境网络层不可达，已用仓库一手材料替代

**本地上下文**
23. `AI4S笔试-piSDK与前端壳选型.md`（pi 事实基准、Chainlit 主选判定、路线 A 风险测算）
24. `AI4S笔试-技术方案.md`（§1.4 provider 抽象 / §1.5 事件流内核 / §M3 五角色）
25. `AI4S笔试-research.md`（题目要求与数据集/模型选型）
