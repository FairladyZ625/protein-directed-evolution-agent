# Closeout

## Summary

五项「数据早已产出、界面一次都没展示」的内容接进了 `app/demo.py`,作为第④⑤两个新 tab
并列呈现,模块①②③ 行为未动。交付提交 `dd02300`,合入主线于 `682a952`。

覆盖试题「结果分析与展示 b. 分析推荐突变是否集中在关键位点」、「结果展示 d-iii 为什么
组合某些突变」,以及加分项③(单点/双点/多点突变效果比较)与④(保守位点分析)。

| Tab | 面板 | 数据源 |
|---|---|---|
| ④ | 位点集中分析 | `workflow-v1.1/gb1/campaign_easy.metrics.json` 的 `topk_concentration` |
| ④ | 组合理由 | `workflow-v1.1/agent_combination_rationales.json` |
| ⑤ | 突变阶数 | `analysis-v0.1/{gb1,aav}/mutation_order.json` |
| ⑤ | 保守位点 | `analysis-v0.1/{gb1,aav}/conservation.json` |
| ⑤ | alpha 扫描 | `workflow-v1.0/gb1/predictor_alpha_sweep.json` + `scaling_ablation.json` |

口径限制按要求原样呈现,没有美化:保守性是未接入采集/筛选路径的自然度先验,真峰三位点
名次(D0Q 第 1、V18A 第 4、S17E 第 26)作为**负结果**展示——按「避开保守位点」筛候选
会先把真峰组成位点挡掉;AAV `0..2→3` 标出留出 0.9094 vs 测试 0.6155;组合理由把
`evidence_source` 与 `narrative_source` 分列,明示确定性叙事不是 LLM 推理。

## Verification

CEO 不采信自述,逐项 ground-truth:

- **文件面**:`git diff --stat master...HEAD` 确为三个文件(`app/demo.py` +467、
  `tests/test_demo_app.py` +82、`README.md` +38),无越界。
- **只读纪律**:`grep -nE "write_text|to_json|to_csv|EventStore\("` 在 `app/demo.py` 上零命中。
- **数字抽查**(面板值 vs 源 JSON 同名字段):`dominant_residue=L` / `dominant_fraction=0.2`、
  AAV `0..2→3` 留出 0.9094 vs 测试 0.6155、`complete_fraction` 1.000→0.312→0.022、
  保守性名次 1 / 4 / 26 —— 四项全部逐字段对回一致。
- **测试**:合并后 `pytest tests/test_demo.py tests/test_demo_app.py` → 19 passed。
- **CEO 亲自点检**:headless 起 streamlit 并用浏览器逐 tab 点开。五个 tab 标签齐全;
  ④ 面板显示 V54 位点 `dominant_fraction 1.0`(top-k 完全集中于 Ala),并明写
  「是代码生成的确定性叙事,不是 LLM 推理,不得当作 LLM 能力展示」;⑤ 面板把保守性负结果
  与固定 alpha 的预处理反转如实展示;③ 面板标注「fitness 为模型预测值,不是实测结果」。
- **阳性对照**:worker 写了 `test_conservation_panel_degrades_when_artifact_missing`,
  临时改名 AAV `conservation.json` 后面板给出「缺哪个文件 + 哪条命令能补」的提示而非空白,
  且存在性检查刻意放在 `@st.cache_data` 之外,缓存不会掩盖缺失。

## Residual Risk

1. **模块②/③共用的 mutation_designer 表格**因 candidates 新增 `combination_rationale`
   (int 键 dict)会触发 streamlit/pyarrow 自动修复警告。非致命、渲染正常,属模块②既有行为,
   本任务未动(修它会改模块②渲染面,超出边界)。
2. **面板④读的是 easy regime 的产物**。hard/sparse/llm 三个 regime 的 `topk_concentration`
   已经产出但界面只展示 easy 一档,读者看不到 regime 之间集中度的差异。
3. **GB1 的 `true_peak_positions` 为空**,保守性面板如实显示「未定义单峰位点」,只有 AAV
   一侧有真峰名次可看。
4. 本任务计划里写的「3 个既存失败」是错的,实测只有 1 个
   (fact `F-281F1B9F`);错误前提由 worker 带证据纠正,CEO 采纳。

## Same Mechanism Elsewhere

「数据早已产出、界面/报告一次都没引用」这个形态在本仓不止一处:同一天还查出
`knowledge-ablation` 的产物在主线而生产代码 `knowledge/ablation.py` 从未合入
(fact `F-94CBEC61`),以及 `agentic-v0.7` 的 47 个结果文件落在任务包而非版本树
(commit `c742ef0`)。三者共因相同:**产出动作与「让它可被找到」的动作是两件事,
只做了前一件**。防复发的钩子是每个版本目录的 `manifest.json` 与
`lab/reports/experiment_log.jsonl` 脊柱——它们把「产物存在」变成可枚举、可核对的事实,
而不是靠人记得去引用。
