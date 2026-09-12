# AI4S 笔试：pi SDK 身份核实 × 前端壳选型 × Agent 形态判定 × 集成架构

> 调研日期：2026-09-10（周四）。服务于 9/13（周日）15:00 冻结的明度数智 AI4S 笔试。
> 触发背景：泽宇拍板技术路线变更「不用自研 loop，用 pi Agent SDK + 开源轻量前端壳二开」。
> **本报告结论先行：这个拍板对「π 是什么」的判断是对的，但对「笔试该不该用它」的判断需要修正——正文给证据。**
> 所有 star 数、维护状态均经 GitHub API 于 2026-09-10 实时核实。

---

## TL;DR（四条硬结论）

1. **身份**：「Py Agent SDK」= 语音「π SDK」（ASR 把"π/pai"转成了"Py"）= **badlogic（Mario Zechner）的 pi-mono**，现已迁移至 **earendil-works/pi**（103.7k★，MIT，TypeScript，本次调研当天仍在推送提交）。⚠️ PyPI 上的 `pi-coding-agent` 是**同名不同项目**（第三方 Ashutosh0428 所写），别装错。泽宇自己面试复盘文件里写的就是「π SDK」，判定置信度极高，**不是** PydanticAI / OpenAI Agents SDK。
2. **前端壳**：pi 官方**没有 web UI**（只有 TUI + 实验性 server/protocol 包）。笔试 demo 主选 **Chainlit**（Python 原生、`@cl.step` 直接渲染五角色时间线、Apache-2.0、12.4k★），备选留在 **Streamlit**（原方案，零新增风险）。assistant-ui / open-webui / LibreChat 均不适合 4 天笔试，理由见 Part 2。
3. **Agent 形态**：题目明说「不要求复杂框架，可使用 prompt + Python 函数调用 + 简单规则实现」。**考的是确定性外围编排 + 局部 LLM 结构化填空，不是自研 Runtime，更不是引一个 coding harness**。五角色推荐「角色 = 流水线阶段（函数）」：3 个纯确定性函数 + 2 个带 Pydantic schema 的 LLM 调用点。**不是**单 agent 多 tool 自由发挥，**不是**五 agent 编排。
4. **集成架构与风险**：pi 从 Python 侧只能走 subprocess（`--mode rpc` / `--mode json`），自定义 Python 工具无法作为 pi 工具注册（必须包成 CLI 让 bash 调，或写 TS 扩展）——为一道明说「不要框架」的题引入 TS 子进程 + CLI 包壳层，**风险不对称**。诚实建议：**保留原方案 §1.4 的纯 Python loop（它本来就是 π 的心智模型复刻），pi 最多做周日可选的 30 分钟彩蛋演示**。事件流埋点用 π 的 RPC 事件流语义对齐 events.jsonl schema——这是叙事资产，不必真跑 π 进程。

---

## Part 1 · 「pi Agent SDK」身份核实与能力清单

### 1.1 身份判定：badlogic pi-mono（现 earendil-works/pi），置信度 ~90%+

**证据链**（按强度排序）：

| # | 证据 | 来源 |
|---|---|---|
| 1 | 泽宇 9/5 技术面复盘文件已把该 SDK 统一写作「π SDK」，且记录了面试官追问「讲讲 π 的 loop」；泽宇答出「while 循环、system prompt→reasoning→tool call→返回注入→end token、四基础工具（忘了第四个是 bash）」——与 pi 实际行为完全吻合 | 本地 `03-面试/01-技术面/2026-09-05-技术面-复盘.md`（行 26、53-54、70）；pi 默认恰好四工具 `read/write/edit/bash` |
| 2 | 泽宇原话「Claude Agent SDK 封闭、把 Claude Code TUI 外围扒了给你接口；Py(π) 能定制更多、埋点更清晰、同时支持 OpenAI 格式和 Anthropic 格式」——逐条对上 pi 的设计哲学（见 1.3） | 技术面转写 chunk_034-035；pi README「Adapt pi to your workflows, not the other way around」 https://github.com/earendil-works/pi |
| 3 | 「开源的壳子很多，我们主要做二开」= pi 的 Pi Packages 生态（extensions/skills/themes 经 npm/git 分发，专为二开设计） | https://github.com/earendil-works/pi#pi-packages ；https://github.com/badlogic/pi-skills (2.5k★) |
| 4 | 泽宇现役主力 OpenClaw 底层就是 pi（"OpenClaw doesn't implement its own agent loop. It embeds the Pi SDK"）——他日常就在 π 生态里工作，面试讲它天经地义 | https://nader.substack.com/p/how-to-build-a-custom-agent-framework ；https://gist.github.com/dabit3/e97dbfe71298b1df4d36542aceb5f158 |
| 5 | 「今年刚好 Py(π) Agent SDK 那啥一下我们就迁过去了」——2026 年 pi 完成了 `@mariozechner/*` → `@earendil-works/*` 的 npm 命名空间迁移并持续大版本演进，时间线吻合"那啥一下" | https://github.com/earendil-works/pi （README npm badge 现为 @earendil-works/pi-coding-agent；旧名 @mariozechner/pi 见各 fork README，如 https://github.com/timolins/pi-mono） |

**排除项**：
- **不是 PydanticAI / OpenAI Agents SDK**：面试转写校注曾猜这两个（转写文件头部注记），但两者都不满足「壳子生态 + 二开」「coding SDK」语境（面试官原话「就是一个 coding 的 SDK」），且泽宇答 loop 细节答的是 pi 的行为。转写校注本身也标注「未强行还原」——本报告用行为证据还原了：是 π。
- **⚠️ 高危撞名陷阱**：PyPI 包 `pi-coding-agent`（v0.6.0）是印度开发者 Ashutosh Sharma 的独立项目（仓库 Ashutosh0428/pi-agent，带 Streamlit demo），**与 Mario Zechner 无关**。泽宇公司是 Python 栈，若他们 pip 装的这个，那就是另一个平行宇宙——但其 README 描述（planner/sub-agents/skills）与泽宇讲的「pending 队列/steal/follow-up」机制不符，而 **pi 的 RPC 协议里恰好有 `steer`（打断）、`follow_up`（排队追加）、`pendingMessageCount`、`set_steering_mode` 等原语**（见 https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/rpc.md ），泽宇被追问的正是这些 π 机制。判定不变：π。
  - PyPI 链接（供避雷）：https://pypi.org/project/pi-coding-agent/

### 1.2 它是什么（核实过的事实表）

| 项 | 值 | 来源 |
|---|---|---|
| 作者 | Mario Zechner（badlogic，libGDX 作者），现属 earendil-works | https://github.com/earendil-works/pi |
| 仓库 | https://github.com/earendil-works/pi （原 badlogic/pi-mono，GitHub 自动重定向） | GitHub API 2026-09-10 |
| Stars / Forks | **103,707 / 12,963**（今日核实），创建 2025-08-09，最后推送 2026-09-10（当天活跃） | GitHub API |
| 语言 | TypeScript（Node ≥ 适配，无官方 Python 绑定） | 同上 |
| 协议 | **MIT** | 同上 |
| npm 包 | `@earendil-works/pi-coding-agent`（CLI）、`@earendil-works/pi-agent-core`（Agent runtime）、`@earendil-works/pi-ai`(多 provider LLM API)、`@earendil-works/pi-tui`、`@earendil-works/pi-telemetry`、实验性 `pi-server/pi-client/pi-protocol` | https://github.com/earendil-works/pi （packages/ 目录实测：agent, ai, chord, client, coding-agent, evals, protocol, server, session-backends, telemetry, tui） |
| 安装 | `npm install -g --ignore-scripts @earendil-works/pi-coding-agent` 或 `curl -fsSL https://pi.dev/install.sh \| sh` | coding-agent README |
| 官网/文档 | https://pi.dev ，https://pi.dev/docs/latest | README |

### 1.3 核心 API 与能力（笔试相关部分）

**四运行模式**（coding-agent README + docs）：
- Interactive TUI；`pi -p "query"` 单发文本；`pi --mode json` **单发 JSON 事件流**（全部 session 事件按行输出 stdout，官方定位就是"integrating pi into other tools or custom UIs"）；`pi --mode rpc` **stdin/stdout JSONL 双向协议**（官方定位"for non-Node integrations / embedding the agent in other applications, IDEs, or custom UIs"）。来源：https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/rpc.md 、https://pi.dev/docs/latest/json

**Agent runtime（pi-agent-core，二开核心）**——`new Agent({...})`：
- `initialState`: systemPrompt / model / thinkingLevel / tools / messages 全部可编程注入
- 钩子：`beforeToolCall`（可拦截 block）、`afterToolCall`（可改写结果、可 `terminate:true` 提前收束 loop）、`shouldStopAfterTurn`（自定义终止条件）、`transformContext`（上下文裁剪/注入）、`convertToLlm`（自定义消息类型桥接）
- **事件流**（= 泽宇说的「埋点清晰」）：`agent_start → turn_start → message_start/update/end → tool_execution_start/update/end → turn_end → agent_end`，粒度到流式 delta；`agent.subscribe()` 逐事件可订阅
- 中断/排队原语：`steer()`（运行中打断转向）、`followUp()`（跑完追加）、steeringMode/followUpMode、clearAllQueues
- 工具执行可配 parallel/sequential
- 来源：https://github.com/earendil-works/pi/blob/main/packages/agent/README.md

**SDK 层（pi-coding-agent）**：`createAgentSession()` / `createAgentSessionRuntime()`，支持 `customTools`（自定义工具）、`tools` 白名单、`systemPromptOverride`、in-memory session、完全替换 resource loader 的「full control」模式。官方 13 个 SDK 示例从 minimal 到 full-control。来源：https://github.com/earendil-works/pi/tree/main/packages/coding-agent/examples/sdk

**多 provider（= 泽宇说的「同时支持 OpenAI 格式和 Anthropic 格式」）**：内置 40+ provider：Anthropic / OpenAI / Azure / Bedrock / Vertex / Google / DeepSeek / Groq / xAI / OpenRouter / **ZAI Coding Plan（含中国版，即 GLM）** / **MiniMax** / Kimi / Fireworks 等；订阅制（Claude Pro/Max、ChatGPT Plus、Copilot）+ API key 双轨；**自定义 provider 走 `~/.pi/agent/models.json`，只要会讲 OpenAI / Anthropic / Google 任一 API 格式即可接入**；还支持 llama.cpp 本地路由。来源：coding-agent README「Providers & Models」+ https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/providers.md 、docs/models.md

**设计红线（二开前必须知道）**：
- **无 sub-agents**（官方哲学：自己用 extensions 搭或 spawn 多个 pi 实例）；**无 MCP**（用 CLI+README 的 skills 模式替代）；无权限弹窗、无内置 todo——全部刻意留白给二开。来源：README「Philosophy」+ https://mariozechner.at/posts/2025-11-30-pi-coding-agent/
- **埋点/遥测**：有专门包 `@earendil-works/pi-telemetry`（vendor-neutral 遥测契约 + 适配器 + 一致性测试），这就是「埋点更清晰」的实体证据。来源：https://github.com/earendil-works/pi （packages/telemetry）

### 1.4 Python 调用路径（笔试栈的关键约束）

**没有官方 Python SDK/binding。** Python 侧集成只有 subprocess 一条路，两个形态：

1. **RPC 模式**（推荐形态）：`pi --mode rpc` 起常驻子进程，Python 写 stdin / 读 stdout 的 JSONL。协议命令：`prompt`（含图片）、`steer`、`follow_up`、`abort`、`get_state`、`get_messages`、`set_model`、`compact` 等，事件异步流出，`id` 字段做请求关联。来源：https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/rpc.md
2. **JSON 单发模式**：`pi --mode json "prompt"`，一次跑完、事件流按行打 stdout 后退出——适合批处理式调用。

**硬约束**：RPC 是「驱动 pi」的协议，**不是「给 pi 喂宿主工具」的协议**。pi 执行的工具是它自己的（read/write/edit/bash + TS extensions + skills）。要让 π Agent 调你的 Python 突变校验器/适应度模型，只有两条路：
- 把每个 Python 能力包成 CLI（`python -m tools.score --variants x.json` → stdout JSON），靠 pi 的 `bash` 工具调用；
- 写 TS extension 用 `customTools` 注册（工具逻辑仍要桥回 Python）。

两种都要多一层壳。这是 Part 4 风险判断的事实基础。

---

## Part 2 · 前端壳选型

### 2.1 pi 官方有壳吗？

- **TUI**：有，`@earendil-works/pi-tui`（终端 UI 库），pi 的交互模式就是它。不是浏览器壳。
- **Web UI：没有。** 不存在 pi-web / pi-ui 包（GitHub API 查证 404；pi-mono packages 目录实测无 web 包；只有 48★ 的 pi-website 官网仓库）。
- `pi-server / pi-client / pi-protocol`：**实验性**本地服务化协议（durable Session / Agent Harness 接口，CBOR 编码、多 presentation attach）——方向是「把 pi session 服务化」，README 自标 experimental，且零文档化 UI，4 天笔试不可依赖。来源：https://github.com/earendil-works/pi/tree/main/packages/server 、/packages/client 、/packages/protocol
- 聊天自动化侧壳：earendil-works/pi-chat（Slack）。「开源的壳子很多」在 pi 语境= **Pi Packages（npm 二开生态）+ 各家自建 UI**，没有一个开箱即用的官方 web 壳。

### 2.2 候选壳对比（star/维护均 2026-09-10 GitHub API 核实）

| 壳 | Stars | 技术栈 | 协议 | 接自定义 agent loop | 二开难度（对本项目） | 判定 |
|---|---|---|---|---|---|---|
| **Chainlit** | 12,442★ Apache-2.0，昨日在推 | Python | `@cl.step` 装饰器逐层产出步骤树/时间线，自动 UI（React 前端自带） | **原生支持**：Python 函数内任意嵌套 step，流式 token、中间产物、图表全可挂 | **低**：纯 Python，与现有管线同进程，1-2 小时出活 | ✅ **主选** |
| Streamlit（原方案） | — | Python | 脚本式重跑 | 可行但事件时间线要手撸组件 | 已是方案内基线 | ✅ 备选/保底 |
| assistant-ui | 12,089★ MIT，当日在推 | TS React 组件库 | Vercel AI SDK 协议 / 自定义 runtime | 强（本来就是给你包任意 loop 的组件库） | **高**：要写 Next.js + TS runtime adapter，跨语言调 Python 管线 | ✋ 时间富余才考虑 |
| open-webui | 151,523★ | Python 后端 + Svelte | OpenAI 兼容 API / pipelines | 弱-中：按「模型服务」接入，事件时间线/自定义工具面板要按它的插件体系改 | 中-高：体量大、面向模型聊天非 pipeline 演示 | ❌ 杀鸡用牛刀 |
| LibreChat | 42,985★ MIT | TS React 全栈 | OpenAI 兼容 + 插件 | 中：自定义 endpoint 可做，但为多模型聊天设计 | 中-高 | ❌ 同上 |
| lobe-chat | 82,369★ | TS Next.js | OpenAI 兼容 | 弱-中 | 高 | ❌ 同上 |
| vercel/chatbot | 20,933★ | Next.js 模板 | fork 改造 | 中（fork 式） | 中-高；且最后推送 2026-07-08（两个月静默） | ❌ |

（open-webui / lobe-chat 协议为非标准开源协议，笔试项目无所谓，但说明其社区约束。）

### 2.3 推荐

- **主选 Chainlit**：它解决的是泽宇换壳的真实动机——「比 Streamlit 漂亮 + 有会话管理 + 能展示 Agent 步骤」。`@cl.step` 天然渲染五角色嵌套步骤（Data Analyst → Hypothesis → Designer → Evaluator → Critic → Decision），等于把 events.jsonl 的回放**免费**变成 UI 组件；Python 原生意味着零跨语言成本。https://docs.chainlit.com/
- **备选 Streamlit**（原方案不动）：如果 Chainlit 的会话模型和「一键跑 3 轮 + 图表」的固定布局打架，退回原方案没有任何沉没成本。
- **明确不推荐**在 4 天窗口里上 assistant-ui / open-webui / LibreChat：全部引入 TS 栈或重插件体系，与「Python 栈笔试」的评分环境（README 复现命令要简单）冲突。
- **叙事加成**：Chainlit 的 step 树 + 泽宇的事件流回放可做成同一套事件 schema 的两个投影（UI 时间线 + events.jsonl + sqlite），报告里写「一次埋点，三处消费」。

---

## Part 3 · 笔试题对 Agent 形态的真实要求判定

### 3.1 题面判读（原文引用）

- 「Agent 不要求复杂框架，可使用 **prompt + Python 函数调用 + 简单规则**实现」（任务 3.c 末段）
- 「Agent 工具：LangChain、LlamaIndex、OpenAI API，**或自行实现**的 prompt + Python 函数调用」（3.e.d 可用资源）
- 考核重点：「**把 LLM Agent 设计成『假设生成—突变设计—模型评估—反馈迭代』的科研流程**」「合理引入氨基酸性质、突变规则或知识图谱」「**通过实验比较证明 Agent 的作用**」「分析模型失败原因」
- 展示要求 3.d.**iv**：「展示 Agent 的推理过程」（位点重要性判断依据 / 替换理由 / 组合理由 / 失败原因）

**判定 ①**：题目要的是**外围确定性编排 + 局部 LLM 结构化调用**。既不要自研 Runtime，更不要现成 coding-agent Runtime（π 是为「读写代码文件 + 跑 bash」设计的 harness，笔试的 Agent 根本不碰文件系统——五个功能全部是「数据进→结构化出」）。考官把「简单规则」写进题面，是在**奖励可控性、惩罚框架堆料**——与明度面试官「可控的小积木块，不要大模型自由发挥」完全同构。

**判定 ②（五角色形态）**：**角色 = 流水线阶段（Python 函数），不是五个 agent，也不是一个自由 agent 的五个 tool。**

- Data Analyst / Mutation Designer / Fitness Evaluator：LLM 参与度 = 0（原方案 §M3 表已定），它们就是函数，挂成 agent tool 纯属浪费且引入不可控性；
- Hypothesis Generator / Scientific Critic：LLM 调用点，Pydantic schema 约束输出（`Hypothesis{site, from_aa, to_aa, rationale, rule_refs[]}`），校验失败带指引重试；
- 外层 `campaign.py` 顺序编排（题目 3.b.i–vi 本来就是线性 i→vi），轮次由确定性代码驱动。

**为什么不是「单 agent 多 tool 自由循环」**：题目 5.c 要对比四种策略（随机/模型直推/LLM Agent/知识增强 Agent），其中三种**没有 LLM 循环**——把流程做成自由 agent 会让你无法对三种基线做同构对比，5.d 的失败分析也无从控制变量。**为什么不是「五 agent 编排」**：五个角色间无并行、无协商、无消息传递需求，多 agent 只增加失败面和 token 成本；连 π 官方都明确「No sub-agents」（哲学层面反对）。

**代码骨架（纯 Python，推荐形态）**：

```python
# agent/pipeline.py —— 角色=阶段，LLM 只在两处出现
class RoundPipeline:
    def run(self, ctx: CampaignContext) -> RoundResult:
        site_report = self.analyze_data(ctx)          # Data Analyst：纯函数，SiteReport schema
        hypotheses = self.gen_hypotheses(site_report) # LLM#1：Pydantic 约束 + rule_refs 校验，失败重试≤2
        candidates = self.design_mutations(hypotheses) # Mutation Designer：纯组合器 + 规则过滤
        scored      = self.eval_fitness(candidates)    # Fitness Evaluator：M2 模型 (mean, var)
        topk        = self.critic_select(scored)       # LLM#2 低温度复核 + 规则校验器三件套
        ctx.events.emit("decision.made", chose=topk)   # 事件流埋点贯穿每一步
        return topk
```

**如果坚持用 π 实现**（面试叙事版，不推荐为默认）：一个 π Agent 实例对应一轮 DBTL，五个角色写进 system prompt 分节，我方确定性能力包成 CLI 由 π 的 bash/customTools 调用，外层 Python campaign loop 经 RPC 驱动 `prompt("执行第 N 轮…")` 并订阅事件流。骨架：

```python
# pi_rpc.py（伪码）：常驻子进程 + 事件流桥接
proc = spawn("pi --mode rpc --provider zai --model glm-4.7")
# 每轮：
send({"type":"prompt","message":round_prompt(n, site_report_digest)})
for ev in jsonl_lines(proc.stdout):
    bridge_to_events(ev)   # message_update→agent.thought, tool_execution_*→tool.called/result
    if ev.type=="agent_settled": break
```

这条路的真实收益只有一个：**RPC 事件流（`message_update`/`tool_execution_start/end`/`agent_settled`）与 events.jsonl 的 schema 几乎一一对应**，「埋点清晰」可以直接引用 π 事件名做设计——但这个收益**抄 schema 就能拿到**，不必真跑进程。

---

## Part 4 · 集成架构建议（含 4 天风险对比）

### 4.1 分工切分（若走 π 路线，边界在哪）

| 职责 | 归属 | 说明 |
|---|---|---|
| DBTL 轮次推进、三池数据、四策略对比、结果评估 | **Python 外层编排**（campaign.py） | 纯确定性，π 无角色 |
| 突变解析/校验、组合生成、适应度模型、不确定性 | **Python 函数，包 CLI**（`python -m tools.X --json`） | π 侧经 bash 调用；报错设计保持「报错即指引」 |
| 假设生成、Critic 复核 | π Agent（system prompt 分节 + schema 说明在 prompt 里） | ⚠️ π 无原生结构化输出强制——schema 校验要放回 Python 侧，失败重试经 `follow_up` 回喂 |
| 事件流/审计 | **Python 桥接层**：RPC 事件 → events.jsonl 映射（`message_update`→`agent.thought`；`tool_execution_start/end`→`tool.called/tool.result`；`agent_settled`→`round.completed`）；确定性代码直接 emit | append-only + sqlite 投影照原方案，π 不碰存储 |
| LLM provider | π 的 provider 层（内置 ZAI/GLM、MiniMax；或 models.json 挂任何 OpenAI 格式端点） | 与原方案「GLM 默认」兼容 |
| UI | Chainlit 读 events.jsonl / sqlite 投影渲染时间线 | 与 π 解耦——π 换掉 UI 不受影响 |

### 4.2 事件流埋点能否直接吐到 events.jsonl

**能，但要过一层桥**：π 的 RPC/JSON 模式把全部 session 事件以 JSONL 流出（这是官方定位的集成方式），桥接线程按映射改写事件名/补齐轮次 ID 后 append 进 events.jsonl。注意两点：① π 事件里没有「业务语义」（它不知道这是第几轮 DBTL、哪个角色在说话），业务 ID 由外层在 prompt 边界注入并靠 `id` 关联；② 确定性阶段（纯 Python 函数）的事件不经过 π，直接 emit——**事件流会有两个生产者，schema 归一化是额外工作量**（约 30-60 行，可控但不免费）。参考：https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/rpc.md

### 4.3 4 天工期风险对比（诚实版）

| 维度 | A：π RPC 路线 | B：纯 Python 函数调用（原方案 §1.4） |
|---|---|---|
| 运行时 | +Node 子进程生命周期管理（起/挂/超时/僵尸进程）、RPC 协议解析（LF-only JSONL，官方明示 Node readline 都不合规，Python 端要小心） | 单进程，无 |
| 工具接线 | 每个 Python 能力包 CLI + stdout JSON 契约 + 调试两层 | 直接函数调用 |
| 结构化输出 | π 为 coding 优化，无强制 JSON schema；校验-重试环要跨进程经 follow_up 回喂 | OpenAI 兼容 API 原生 JSON mode/function calling + Pydantic，一行校验 |
| 事件流 | 现成流 + 桥接层 + 双生产者归一 | 单生产者直接 emit（原方案 ~150 行含 replay） |
| 调试面 | 出错要分辨：模型问题/prompt 问题/CLI 壳问题/RPC 桥问题 | 模型或代码，二选一 |
| 复现（README 要求） | 考官要装 Node + pi + API key 才能跑 Agent 部分 | pip install 即全量复现 |
| 评分收益 | 「用了和面试同一个 SDK」的叙事一致性 | 「题目明说不要求框架，我选择最小自研」同样是叙事，且原方案已写明「心智模型 = π 同款 loop」 |
| 工期占比（估） | 集成壳+桥接+调试：**+0.5～1 天**，周六关键日风险放大 | 0（已在计划内） |

**结论（不骑墙）**：**主线走 B（纯 Python loop），这不是放弃 π 路线，而是 π 路线的正确打开方式**——原方案 §1.4 的自研 loop 本来就是 π 的 `agentLoop` 心智模型复刻（system prompt 注入 → reasoning → tool call 抽取 → 执行 → 回填 → 终止检测），π 的事件命名（`tool_execution_start/end`、`agent_settled`）直接借来做 events.jsonl 的事件 schema 命名，报告架构图照画「事件模型对齐 π Agent Runtime」。**周日若 M-Sat 提前达成**，加一个 ≤30 分钟的可选彩蛋：`pi --mode rpc` 起一个真 π 进程跑单轮 demo 的录屏，证明「同一管线可切换到现成 Runtime」——放 README 附录，不进主链路。面试被问「你为什么不用 π」的标准答案：「π 是 coding harness，它的四工具（read/write/edit/bash）和本题的管线无交集；我复用了它的事件模型与 loop 语义，把确定性部分留在 Python——这正是 π 哲学（Adapt pi to your workflows, not the other way around）的应用。」

**前端壳**：Chainlit 主选 + Streamlit 保底（见 Part 2.3），两者都不与 π 耦合，路线怎么定都不返工。

---

## 附：本报告引用源清单

- pi 主仓库 / README / 哲学：https://github.com/earendil-works/pi （含 badlogic/pi-mono 旧名重定向）
- RPC 协议（steer/follow_up/pending/JSONL 规范）：https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/rpc.md
- JSON 事件流模式：https://pi.dev/docs/latest/json ；https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/json.md
- Agent runtime（事件流/钩子/并行工具）：https://github.com/earendil-works/pi/blob/main/packages/agent/README.md
- SDK 示例（createAgentSession/customTools/full-control）：https://github.com/earendil-works/pi/tree/main/packages/coding-agent/examples/sdk
- providers/models.json 自定义 provider：https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/providers.md
- π 作者哲学长文：https://mariozechner.at/posts/2025-11-30-pi-coding-agent/ ；反 MCP：https://mariozechner.at/posts/2025-11-02-what-if-you-dont-need-mcp/
- OpenClaw 基于 π：https://nader.substack.com/p/how-to-build-a-custom-agent-framework ；https://gist.github.com/dabit3/e97dbfe71298b1df4d36542aceb5f158
- ⚠️ 撞名 PyPI 包（非 π）：https://pypi.org/project/pi-coding-agent/ （GitHub: Ashutosh0428/pi-agent）
- pi-skills 二开生态：https://github.com/badlogic/pi-skills
- 前端壳：Chainlit https://github.com/Chainlit/chainlit ；assistant-ui https://github.com/assistant-ui/assistant-ui ；open-webui https://github.com/open-webui/open-webui ；LibreChat https://github.com/danny-avila/LibreChat ；lobe-chat https://github.com/lobehub/lobe-chat ；vercel/chatbot https://github.com/vercel/chatbot
- 本地证据：`03-面试/01-技术面/2026-09-05-技术面-原文转写.md`（chunk_024/033-037）、`2026-09-05-技术面-复盘.md`（π SDK、pending 队列追问）、`01-调研/AI4S笔试-技术方案.md`（§1.4/§M3 原始决策）、`03-面试/AI4S笔试.docx`（题目原文 3.c/3.e.d/考核重点）
- star/维护数据：GitHub REST API，2026-09-10 实测
