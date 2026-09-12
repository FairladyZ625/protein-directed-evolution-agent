# 包 A 主链真实性修复：第 2 轮检查点报告

日期：2026-09-12  
任务：`task_0bc2d4d678eea24c4930b60a0e`  
状态：第 1、2 项已实现；第 3 项因已提交 ESM-2 缓存覆盖不足按契约停线；第 4 项未越过停线实施。

## 1. Critic 真执行

改前：`evolution/campaign.py` 对两个 Agent 策略都传 `no_knowledge=True`，且不注入 `llm_critic`；Scientific Critic 事件存在但不形成知识门禁。

改后：仅 `knowledge_agent` 使用 `no_knowledge=False`，并在 `use_llm=True` 时注入有调用上限的商业 LLM Critic；`agent_no_knowledge` 继续保持规则与 LLM Critic 均关闭的干净消融。campaign 只从 `PipelineResult.accepted` 提名，不再绕过 Critic。

本轮重新跑出的拒稿事件原文如下。模型对 `FDGV` 给出正向分数 2.332442，但规则门禁依据两个 T5 BLOSUM 规则将它拒绝：

```json
{"accepted": false, "mutations": ["V39F"], "note": "rejected by knowledge rules: R-BLOSUM-CONSERVATIVE, R-BLOSUM-AGGRESSIVE", "rule_check": [{"note": "1 substitutions (limit 4)", "pass": true, "rule_id": "R-MAX-MUTATIONS"}, {"note": "standard amino-acid alphabet", "pass": true, "rule_id": "R-NO-STOP"}, {"note": "V39F: BLOSUM62=-1", "pass": false, "rule_id": "R-BLOSUM-CONSERVATIVE"}, {"note": "V39F: BLOSUM62=-1", "pass": false, "rule_id": "R-BLOSUM-AGGRESSIVE"}, {"note": "position 39", "pass": true, "rule_id": "R-GB1-SITES"}], "score": 2.332442092815148, "sequence": "FDGV"}
```

阴性对照：`tests/test_campaign.py::test_knowledge_critic_rejects_candidate_in_campaign_event` 同时断言无知识事件中全部候选 `accepted=true`，知识组至少有一个带候选序列、突变、失败规则 ID 的拒稿。

## 2. 商业 API 严格结构化输出

改前：Hypothesis Generator 要求模型返回裸 JSON 数组，再用字符串切片和 `json.loads` 手工解析；Critic 接收自由文本。产物模型来源取请求配置值，不能证明响应实际由哪个模型解析。

改后：`agent/llm.py::chat_structured` 通过 PydanticAI `Agent(..., output_type=<Pydantic BaseModel>, retries=0)` 把 `Hypothesis` 或 `CriticReview` 注册为 provider output-tool schema，并由 Pydantic 校验返回参数。该 helper 不解析自由文本、不含 fallback。解析失败直接抛出；campaign 捕获后显式写 `llm_source=fallback`、调用数、失败数、错误和空模型字段。成功时模型字段来自 `AgentRunResult.response.model_name`，不从请求别名推断。

受控 live 证据（共 2 个 provider 请求）：

- Hypothesis：1 次，`UnexpectedModelBehavior: Exceeded maximum output retries (0)`；这是显式 schema 失败，未伪装为 live 成功。
- Scientific Critic：1 次成功，响应侧 `model=claude-sonnet-5`、`requests=1`，解析为 `CriticReview(rationale=..., rule_ids=["R-BLOSUM-CONSERVATIVE"])`。

测试证据：

- `tests/test_agent.py` 断言 `output_type is Hypothesis`、`retries == 0`、响应侧模型为 `claude-sonnet-5`，并验证 schema 异常向上抛出。
- `tests/test_campaign.py::test_structured_llm_failure_is_explicit_fallback` 断言结构化失败被显式计数；无知识组 `critic_llm_calls == 0`，知识组失败时 `critic_llm_failures == 1` 且 `critic_llm_model is None`。

## 3. ESM-2 回到主力

改前：campaign 与 demo 的实际 predictor 都使用 80 维 one-hot。

覆盖审计（仅检查 Git 已提交文件）：

| 缓存 | shape | 完整覆盖 |
|---|---:|---|
| `esm2_t33_650M_UR50D-dbfd1ecc45bd4b72148d.npz` | 5000 × 1280 | 固定 `train_pool` |
| `esm2_t33_650M_UR50D-21445a4f9471dda9a690.npz` | 2168 × 1280 | `HD<=2` 冷启动集合 |
| `esm2_t33_650M_UR50D-beaa40b43aa0f123600f.npz` | 2000 × 1280 | query 局部样本块 |
| `esm2_t33_650M_UR50D-d469efb58db7df4a5429.npz` | 2000 × 1280 | 局部样本块 |
| `gb1-all-one-hot.npz` | 149361 × 80 | 全可测空间，但不是 ESM-2 |

结论：已提交 1280 维缓存既不覆盖 149,361 全提名空间，也不覆盖 hard campaign 需要评分的 `HD>2` 候选。无法在不实时提取或使用未跟踪大缓存的情况下，把 greedy 全空间评分、Agent 候选评分和 demo 任意可测候选都切到 ESM-2。因此本项没有伪造 feature provenance，也没有读取或提交 38,265 × 1280 未跟踪文件；依据 task plan 检查点在此停线。

承重事实：`F-54695D51`。

## 4. demo 输入范围

改前：实现只接受 GB1 四位点 4 字符变体，但顶层叙事申领了“输入野生型序列后自动推荐”的通用 WT 加分。

本轮没有越过第 3 项强制停线改 `app/demo.py`。恢复执行后的明确选择是**收窄文案为 GB1 四位点 demo，不申领通用 WT 加分**。原因是当前 WT、可变位点、mutation notation、训练特征和真值 oracle 都是 GB1 专用；只增加 56 aa 文本框不能形成通用任务配置，反而会重复“声称与实现不一致”。

## GB1 四策略重跑数值

实测协议：当前代码，默认 seed 42，hard 冷启动 `HD<=2`，3 轮 × 每轮 96，仍为 one-hot（ESM 项尚未实施）。与已提交 `campaign_hard.metrics.json` 对比：

| 策略 | 历史 final max / mean / strong / beneficial | 本轮 final max / mean / strong / beneficial | max 曲线（本轮） |
|---|---|---|---|
| random | 5.081244 / 1.635804 / 1 / 7 | 5.081244 / 1.635804 / 1 / 7 | 1.910588 → 1.910588 → 5.081244 |
| greedy | 8.761966 / 6.852635 / 43 / 154 | 8.761966 / 6.970103 / 56 / 178 | 5.772032 → 8.761966 → 8.761966 |
| agent_no_knowledge | 8.761966 / 6.970103 / 56 / 187 | 8.761966 / 7.020288 / 57 / 182 | 5.772032 → 8.761966 → 8.761966 |
| knowledge_agent | 8.761966 / 6.970103 / 57 / 190 | 3.738620 / 3.444298 / 0 / 205 | 3.440218 → 3.738620 → 3.738620 |

答案：**有变化**。尤其知识 Critic 成为真实门禁后，knowledge_agent 的最终最大值从 8.761966 降为 3.738620。实现未为对齐旧数字而回退；该变化的科学叙事交 CEO 裁决。greedy 在本包改动面之外也出现汇总差异，说明历史产物与当前代码/依赖组合不能视为同一可执行快照。

## 验证、风险与下一步

- 点名测试（rebase 尝试安全中止后复验）：`.venv/bin/pytest -q tests/test_agent.py tests/test_campaign.py tests/test_demo_app.py` → `23 passed in 46.82s`。
- 结构检查：`git diff --check` → 无输出。
- 外部 API：实际 2 次；成功 1 次，严格结构化失败 1 次；成功响应模型为 `claude-sonnet-5`。
- 本地提交：`25735cacbcd9d645dc1506f2c9e08f749a99d340`，作者 `ZeyuLi <zeyuli@users.noreply.github.com>`；未 push、未开 PR。
- rebase 风险：`git fetch origin main` 成功，但 `origin/main` 与当前仓库历史无共同 merge-base（`git rev-list --left-right --count origin/main...HEAD` 为 `3 63`）。直接 rebase 会重放 56 个历史提交并在第一个骨架提交对 `.gitignore`、`README.md` 产生任务外 add/add 冲突，已用 `git rebase --abort` 安全中止；没有替仓库历史做跳过或冲突裁决。
- 未验证：ESM-2 主力 campaign、ESM feature provenance、demo 收窄后的 UI 文案，均因第 3 项停线未实施。
- 下一步需 CEO 裁决：是否先另行产出并治理 149,361 全表 ESM 缓存（预计远超当前提交体积），或修改 D2 为可交付的分层协议方案。裁决后才能继续第 3 项；第 4 项按“收窄 GB1 四位点文案”执行。
