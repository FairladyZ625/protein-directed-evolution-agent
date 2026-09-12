# 包3:知识库补齐承重规则

你在修一个**已被独立评审打回的任务**。评审全文在任务包 `reviews/` 下最新 .md,**先读它**。
注意:评审指出本轮冻结提交 `909ff0a2` 与上一轮被打回的 `4f456890` 在 `knowledge/` 与
`tests/test_knowledge.py` 上**完全同树**——上一轮的缺陷一个都没修。这次要真改。

## 缺口(评审实测)

1. **BLOSUM62 是残缺的**:`rules.yaml` 里只有 10 行 / 88 个有向条目。后果:合法替换 `C39W`
   **不产生任何 BLOSUM 分类**——绝大多数替换落在表外,规则等于不生效。
   → 补全 BLOSUM62(标准 20x20 对称矩阵,210 个无序对 / 400 个有向条目)。
     矩阵数值是公开标准,不要自己编;若仓内已有可靠来源优先用它,否则写明出处。
2. **`_score` 用 `direct or reverse`,合法的 0 分会被吞掉。**
   BLOSUM62 里 0 是有意义的分值(中性替换),而 `or` 把 0 当假值,于是单向存在时 0 分被
   当成"查不到"。→ 改成显式的存在性判断,区分「查不到」与「分值为 0」。
   **这条要配一个针对性测试**:构造一个 BLOSUM 分值恰为 0 的替换,断言它被正确分类为中性
   而不是未知。
3. **`R-PRIORITIZE-HISTORICAL` 声明了但 validator 从不输出。**
   题面与契约都要求「历史好单点优先」的能力。→ 让 validator 真的产出这条规则的判定结果,
   并有测试覆盖它命中与不命中两种情况。

## 验收口径

- `pytest tests/test_knowledge.py` 在冻结提交树上全绿,且新增覆盖上述 2、3 的测试。
- 我会自己验:随机抽若干合法替换(含 `C39W`)确认都能得到 BLOSUM 分类;
  并 grep `R-PRIORITIZE-HISTORICAL` 确认它出现在 validator 的输出路径上而非仅在声明里。
- `--no-knowledge` 消融开关的现有行为不得回退(它现在是对的)。

## 边界

- **只动** `knowledge/`、`tests/test_knowledge.py`。
- **不要动** `agent/`、`evolution/`、`models/`、`events/`——都有其他 worker 在飞。
- 独立 worktree。停止点 = 点名测试绿 + commit,不 push、不发 PR。
- 发现 CEO 判断有误就带证据回报并停手。
