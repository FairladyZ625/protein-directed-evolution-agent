# 包5:预测器阶梯的交付面补齐

你在修一个**已被独立评审打回的任务**。评审全文在任务包 `reviews/` 下最新 .md,**先读它**。

## 缺口

1. **契约要求的三样交付物不存在**:`tests/test_predictor.py`、预测对比图、声明路径的指标表
   (`reports/predictor_metrics.json`)。评审跑 `pytest tests/test_predictor.py` → 文件不存在,零测试执行。
2. **没有从 T2 接口训练的可执行入口**:预测器接受任意 X/y,从不消费 T2 的三池 /
   one-hot / ESM 接口。Makefile 指向 `train_ladder.py` 但该模块无 `__main__`。
3. **没有独立 train/val/test 评测,也没有模型持久化/加载接口**。下游 T7 是重新构造
   `RidgePredictor` 而不是加载已训练模型。
4. **Ridge 的 ensemble 方差退化**:评审合成对照测得 `variance_max=3.08e-33`,XGBoost 亦为
   `1.97e-31`。T7 的 UCB 消费的正是这个方差,退化到 0 意味着探索项失效。
   注:这是历史冻结提交的状态;CEO 已查明根因是提交 `fe5a1a5` 之前每个集成成员拟合的是
   **同一份完整训练集**(fact `F-67F4D429`),`fe5a1a5` 之后改成 bootstrap 重采样才有非平凡方差。
   → 你要保证**当前交付面**上方差非平凡,并补测试断言它非退化(阳性对照:方差恒 0 应让测试红)。

## 必须保留、不得回退(origin/main 05d6e4d,CEO 本轮刚改的)

- `models/train_ladder.py` 的 `evaluate_ladder(..., *, standardize: bool = False)` 参数及其
  docstring 里的对称性约束(任何 one-hot ↔ ESM 比较两边必须传同值)。
- `models/evaluate_all.py` 每组合跑 raw / standardized 两档、产出
  `predictor_ladder_scaling_ablation.json`。
- 新增的 `models/alpha_sweep.py`(answer-agnostic 的 alpha 选择参照实现)。
- **重要口径**(fact `F-5CC3FABA`):表征比较**不许固定 alpha**。alpha 必须在训练集内独立选。
  `train_ladder.py` 注释里的 AAV 数字(raw 0.47→标准化 0.60)是 AAV 专属,不得当通用结论引用。
  你补的指标表与对比图要体现这一口径,不要再产出固定 alpha 的单点比较当结论。

## 验收口径

- `pytest tests/test_predictor.py` 在冻结提交树上全绿,含方差非退化的阳性对照。
- 指标表落在契约声明的路径上,且能由一条可执行命令重新产出。
- 我会自己跑那条命令核对产物,并 grep 持久化/加载接口的调用点。

## 边界

- **只动** `models/`、`tests/test_predictor.py`、指标表与图的产出路径、必要的 Makefile 目标。
- **不要动** `agent/`、`evolution/`、`knowledge/`、`events/`——都有其他 worker 在飞。
- 先 rebase 到最新 `origin/main`(05d6e4d),再动手;上面那几项 CEO 改动必须完整保留。
- 独立 worktree。停止点 = 点名测试绿 + commit,不 push、不发 PR。
- 发现 CEO 判断有误就带证据回报并停手。

---

# 重派(上一轮完全空转)

上一轮这个任务派出去后,worker 的 clone `/private/tmp/ai4s-predictor-delivery` 的 HEAD
仍是 `05d6e4d`,**连一处未提交改动都没有** —— 零产出。回执报 `succeeded` 但那是假回执。

本轮 worktree 已备好:`.worktrees/t-predictor`(分支 `t-predictor`,基于最新 `origin/main`),
`.venv`、`data/pools`、`features/cache` 已符号链接。**在这个 worktree 里干活,别自己开 clone。**

上面 mission 的全部内容仍然有效。另外注意主线已前进,以下是**新增的、不得回退**的东西:

- `models/alpha_sweep.py` 已在主线(answer-agnostic alpha 选择的参照实现)。
- `evolution/results_layout.py` 的 `VERSIONS` 已改为
  `{"workflow": "v1.1", "agentic": "v0.7", "analysis": "v0.1"}`,并注明 agentic v0.6/v0.7
  是兄弟不是递进。你的指标表产物落 `workflow-v1.1`。
- `agent/pipeline.py` 已被硬化(结构化角色 + 候选与实测集合求交);`knowledge/` 的规则
  现在带 `enforcement: gate|advisory` 字段。这些都不要动。
- `lab/reports/analysis-v0.1/` 下已有突变阶数分析的产物,其中的加性外推表用的正是
  answer-agnostic alpha 选法(alpha* 实测为 0.01/1.0/10.0 各不同),可作为你补指标表时的
  口径参照 —— **只读,不要改**。
