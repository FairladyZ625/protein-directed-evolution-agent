"""T8 看板冒烟测试：五 tab 首屏渲染、模块③(a) 打分与越界提示、分析面板口径标注、只读纪律。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

APP = ROOT / "app" / "demo.py"
HAS_DATA = (ROOT / "data" / "four_mutations_full_data.csv").exists()


@pytest.fixture(scope="module")
def app() -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=300)
    at.run()
    return at


def _text(at: AppTest) -> str:
    return " ".join(
        m.value for m in at.markdown
    ) + " " + " ".join(str(m.label) for m in at.metric) + " " + " ".join(str(m.value) for m in at.metric
    ) + " " + " ".join(c.value for c in at.caption)


def test_first_render_without_exception(app: AppTest):
    assert not app.exception, [e.value for e in app.exception]


def test_three_module_tabs_present(app: AppTest):
    labels = [t.label for t in app.tabs]  # AppTest 打平嵌套 tabs，前三个是主模块
    assert labels[:3] == ["① 四策略对比", "② Agent 思考回放", "③ 实时试玩"]


def test_analysis_tabs_present(app: AppTest):
    labels = [t.label for t in app.tabs]  # AppTest 打平嵌套 tabs（③ 内含 (a)/(b) 两个子 tab）
    assert "④ 位点集中 & 组合理由" in labels
    assert "⑤ 阶数 · 保守性 · alpha" in labels
    assert labels.index("④ 位点集中 & 组合理由") > labels.index("③ 实时试玩")


def test_module1_renders_strategy_metrics(app: AppTest):
    body = _text(app)
    for needle in ("random", "greedy", "agent_no_knowledge", "knowledge_agent"):
        assert needle in body, needle


def test_module2_renders_role_chain_and_chain_status(app: AppTest):
    body = _text(app)
    assert "Scientific Critic" in body
    assert "Data Analyst" in body
    assert "哈希链校验 ✅" in body


def test_module3_scores_wt(app: AppTest):
    labels = " ".join(str(m.label) for m in app.metric)
    assert "预测 mean" in labels and "真实 fitness" in labels


# ---------------------------------------------------------------- 模块④⑤：分析面板


def test_concentration_panel_renders_topk_fields(app: AppTest):
    """④-a：按 JSON 原字段名展示残基集中度（评委可拿字段名回源文件对数）。"""
    body = _text(app)
    for needle in ("topk_concentration", "n_topk_observations",
                   "dominant_residue", "dominant_fraction", "mutation_fraction"):
        assert needle in body, needle


def test_rationales_panel_separates_evidence_from_narrative(app: AppTest):
    """④-b：evidence_source 与 narrative_source 分开；确定性叙事不得冒充 LLM 推理。"""
    body = _text(app) + " " + " ".join(i.value for i in app.info)
    for needle in ("evidence_source", "narrative_source", "measured_rows", "不是 LLM 推理", "V39I"):
        assert needle in body, needle


def test_mutation_order_panel_shows_caveats_and_json_numbers(app: AppTest):
    """⑤-a：口径标注 + 关键数字直接来自源 JSON（留出 0.9094 vs 测试 0.6155；覆盖 1.000→0.312→0.022）。"""
    body = _text(app) + " " + " ".join(w.value for w in app.warning)
    for needle in ("additive_extrapolation", "0.9094", "0.6155", "同阶",
                   "complete_fraction", "1.000", "0.312", "0.022"):
        assert needle in body, needle


def test_conservation_panel_negative_result_framing(app: AppTest):
    """⑤-b：未接入筛选的口径必在；真峰三位点名次（负结果）与相关系数展示。"""
    body = _text(app) + " " + " ".join(i.value for i in app.info) + " " + " ".join(w.value for w in app.warning)
    for needle in ("未接入采集或筛选路径", "conservation_rank", "D0Q", "V18A", "S17E", "负结果"):
        assert needle in body, needle
    # 名称↔位点↔名次 三元对应钉死（记号数字是 0-based：D0Q/V18A/S17E），与源 JSON 逐字段一致
    assert "`D0Q`（pos 1，WT `D`）→ conservation_rank **1 / 28**" in body
    assert "`V18A`（pos 19，WT `V`）→ conservation_rank **4 / 28**" in body
    assert "`S17E`（pos 18，WT `S`）→ conservation_rank **26 / 28**" in body


def test_alpha_sweep_panel_fixed_alpha_trap(app: AppTest):
    """⑤-c：固定 alpha 的预处理反转数字（0.4911/0.2944）与调参后收敛值（0.4893/0.4916）均来自源 JSON。"""
    body = _text(app) + " " + " ".join(w.value for w in app.warning)
    for needle in ("alpha_selected", "0.4911", "0.2944", "0.4893", "0.4916"):
        assert needle in body, needle


def _find_missing_variant() -> str:
    """找一个合法（20 标准氨基酸）但不在 149,361 真值表内的变体，演示「无真值」路径。"""
    from itertools import product

    import pandas as pd

    known = set(pd.read_csv(ROOT / "data" / "four_mutations_full_data.csv", usecols=["Variants"]).Variants)
    aa = "ACDEFGHIKLMNPQRSTVWY"
    for combo in product("VDG", "VDG", "VDG", aa):  # 前三位贴近 WT，找第一个缺失的 4 位组合
        v = "".join(combo)
        if v not in known:
            return v
    raise AssertionError("no missing variant found (unexpected)")


def test_playground_flags_variant_outside_measured_space():
    if not HAS_DATA:
        pytest.skip("landscape csv not present")
    at = AppTest.from_file(str(APP), default_timeout=300)
    at.run()
    at.text_input(key="m3_input").set_value(_find_missing_variant()).run()
    assert not at.exception
    warning = " ".join(w.value for w in at.warning)
    assert "无真值" in warning and "149,361" in warning
    labels = " ".join(str(m.label) for m in at.metric)
    assert "预测 mean" in labels  # 预测照常给出，真值列显示 —


def test_recommender_button_runs_one_round_in_memory():
    if not HAS_DATA:
        pytest.skip("landscape csv not present")
    at = AppTest.from_file(str(APP), default_timeout=600)
    at.run()
    assert not at.exception
    at.button(key="m3b_run").click()
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    success = " ".join(s.value for s in at.success)
    # 8474b6e 起推荐为确定性 one-shot 打分（不再有 llm_source= 文案）；诚实标注保留：
    # 表头写明「模型预测，非实测」，闭环追踪注明事件只进内存 recorder。
    assert "76 个单点候选" in success
    body = _text(at)
    assert "Top-10 推荐突变方案" in body
    assert "（模型预测，非实测）" in body or "模型预测" in body
    assert "五角色闭环追踪" in body  # 内存录制事件与模块②同源渲染


def test_conservation_panel_degrades_when_artifact_missing():
    """阳性对照：临时改名 AAV conservation.json，面板必须给「缺哪个文件 + 跑哪条命令」的提示，
    而不是空白或崩溃；口径标注（不依赖数据存在）仍在。结束后恢复原文件。"""
    path = ROOT / "lab" / "reports" / "analysis-v0.1" / "aav" / "conservation.json"
    if not path.exists():
        pytest.skip("aav conservation.json not present")
    backup = path.with_name("conservation.json.bak")
    path.rename(backup)
    try:
        at = AppTest.from_file(str(APP), default_timeout=600)
        at.run()
        assert not at.exception, [e.value for e in at.exception]
        warnings = " ".join(w.value for w in at.warning)
        assert "conservation.json" in warnings  # 缺哪个文件说清楚
        assert "features/conservation.py" in warnings  # 跑哪条命令能补回
        body = _text(at) + " " + " ".join(i.value for i in at.info) + " " + " ".join(w.value for w in at.warning)
        assert "未接入采集或筛选路径" in body  # 口径标注不随数据消失
        assert "D0Q" not in body  # 数据不在时不得假装有名次表
    finally:
        backup.rename(path)


def test_declared_artifacts_resolve_on_the_real_tree():
    """看板声明的每个产物路径，必须在真实仓库树上解析得到。

    这条测试是为一整族缺陷立的门，而不是为某一个 bug：本仓已经三次因为「产物换了名字 /
    换了周期目录 / 被 gzip 归档」而让面板静默退化，页面照样打开、只是内容没了——
    单元测试用 fixture 跑，看不见真实树，所以一次都没拦住。

    事件流走 resolve_stream_path（`.jsonl` 与归档 `.jsonl.gz` 等价），其余按文件存在判断。
    """
    from app.demo import (ALPHA_SWEEP_JSON, ANALYSIS_DIR, BASELINE_JSON, EVENTS_JSONL,
                          EVENTS_LLM_JSONL, METRICS_JSON, PREDICTOR_JSON, RATIONALES_JSON,
                          REGIMES, SCALING_ABLATION_JSON)
    from events.store import resolve_stream_path

    missing = []
    for name, path in [("METRICS_JSON", METRICS_JSON), ("PREDICTOR_JSON", PREDICTOR_JSON),
                       ("BASELINE_JSON", BASELINE_JSON), ("RATIONALES_JSON", RATIONALES_JSON),
                       ("ALPHA_SWEEP_JSON", ALPHA_SWEEP_JSON),
                       ("SCALING_ABLATION_JSON", SCALING_ABLATION_JSON),
                       *[(f"REGIMES[{k[:6]}]", v) for k, v in REGIMES.items()],
                       *[(f"analysis/{ds}/{f}", ANALYSIS_DIR[ds] / f)
                         for ds in ANALYSIS_DIR for f in ("mutation_order.json", "conservation.json")]]:
        if not path.exists():
            missing.append(f"{name} -> {path}")
    for name, path in [("EVENTS_JSONL", EVENTS_JSONL), ("EVENTS_LLM_JSONL", EVENTS_LLM_JSONL)]:
        if not resolve_stream_path(path).exists():
            missing.append(f"{name} -> {path}（.gz 归档亦无）")
    assert not missing, "看板声明了这些产物但树上没有:\n  " + "\n  ".join(missing)


def test_preset_buttons_actually_change_the_scored_variant():
    """回归门：预设按钮必须真的改到打分结果，而不只是改一个没人读的影子 state。

    带 key 的 widget 在后续 rerun 只认 st.session_state[key]、无视 value=，
    所以「写影子 key + rerun」的写法从第二次渲染起就是死键——页面不报错，按了没反应。
    """
    if not HAS_DATA:
        pytest.skip("landscape csv not present")
    def true_fitness(at: AppTest) -> str:
        return next(str(m.value) for m in at.metric if str(m.label) == "真实 fitness")

    at = AppTest.from_file(str(APP), default_timeout=300)
    at.run()
    at.text_input(key="m3_input").set_value("VDGV").run()
    assert true_fitness(at) == "1.000"  # 阴性对照：按之前是野生型

    at.button(key="m3_preset_peak").click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.session_state["m3_input"] == "FWAA"   # 按钮写的是控件自己的 key
    assert true_fitness(at) == "8.762"              # 打分结果确实跟着变了


def test_critic_rejections_are_aggregated_not_dumped_one_by_one():
    """一轮会门禁 6,539 个候选，knowledge_agent 能一次拒掉 6,500+。

    逐条渲染（每条还带一张 dataframe）会把页面撑死，所以先给「按规则聚合的原因分布」，
    再只展开前几条。这里直接喂 500 条拒稿，断言展开条数有界。
    """
    from app.demo import _CRITIC_EXAMPLES, render_critic

    critiques = [{"accepted": False, "score": 0.5, "note": "rejected by knowledge rules",
                  "rule_check": [{"rule_id": "R-MAX-MUTATIONS", "enforcement": "gate",
                                  "pass": False, "note": "too many"}]}
                 for _ in range(500)]
    rendered: list[str] = []
    import streamlit as st
    real_markdown, real_dataframe, real_caption = st.markdown, st.dataframe, st.caption
    st.markdown = lambda *a, **k: rendered.append(str(a[0]) if a else "")
    st.dataframe = lambda *a, **k: rendered.append("<dataframe>")
    st.caption = lambda *a, **k: rendered.append(str(a[0]) if a else "")
    try:
        render_critic(critiques)
    finally:
        st.markdown, st.dataframe, st.caption = real_markdown, real_dataframe, real_caption

    detail_lines = [r for r in rendered if r.startswith("🚫")]
    assert len(detail_lines) == _CRITIC_EXAMPLES, f"逐条展开了 {len(detail_lines)} 条"
    assert any("拒稿原因分布" in r for r in rendered)
    assert any("其余 492" in r for r in rendered)


def test_demo_module_is_read_only_source():
    source = APP.read_text()
    # 红线：demo 不向磁盘写任何文件（唯一 append 是 _MemoryRecorder 内存录制器）
    for banned in ("write_text", "to_json", "to_csv", ".open(", "EventStore("):
        assert banned not in source, banned
    assert "_MemoryRecorder" in source


# ---- 模块⑥：AAV agentic 线的工具契约面板 ----------------------------------------
# 前五个 tab 全部消费 GB1 workflow 线；agentic 线此前在看板上完全不可见，
# 而试题「Agent 是否真学到科学家思维」的答案恰恰在那条线上。

def test_contract_tab_present(app: AppTest):
    labels = [t.label for t in app.tabs]
    assert "⑥ Agent 工具契约（AAV）" in labels
    assert labels.index("⑥ Agent 工具契约（AAV）") > labels.index("⑤ 阶数 · 保守性 · alpha")


def test_arm_batches_reads_the_tested_batch_not_the_staged_one():
    """批次身份必须取真正花掉预算的那批，不能取 compose_batch 的暂存批次。

    v0.8 的教训:LLM 的工具调用数、redirect 轮次、总结措辞都会变，
    而实际被 oracle 测过的 288 个变体逐位相同。
    """
    from app.demo import V09_CONTRACT_DIR, arm_batches
    arm = V09_CONTRACT_DIR / "contract-v08_reflexion-off_seed-42"
    if not (arm / "agentic.metrics.json").exists():
        pytest.skip("v0.9 四臂归档不在本检出中")
    batches = arm_batches(arm)
    assert sorted(batches) == [1, 2, 3, 4, 5, 6]
    assert all(len(v) == 48 for v in batches.values())


def test_batch_overlap_separates_the_two_contracts():
    """本面板的全部说服力都压在这一条上:同一判据在 v0.9 下看得见差异、v0.8 下看不见。

    若两个契约都报「未分叉」，那是判据不灵敏；若都报「已分叉」，那是对照被污染。
    """
    from app.demo import V09_CONTRACT_DIR, arm_batches, batch_overlap
    if not (V09_CONTRACT_DIR / "contract-v09_reflexion-on_seed-42" / "agentic.metrics.json").exists():
        pytest.skip("v0.9 四臂归档不在本检出中")
    def rows(contract):
        return batch_overlap(arm_batches(V09_CONTRACT_DIR / f"contract-{contract}_reflexion-off_seed-42"),
                             arm_batches(V09_CONTRACT_DIR / f"contract-{contract}_reflexion-on_seed-42"))
    v08, v09 = rows("v08"), rows("v09")
    assert all(r["是否分叉"] == "否" for r in v08), "v0.8 对照臂不该分叉——对照可能被污染"
    assert all(r["是否分叉"] == "是" for r in v09), "v0.9 该分叉——判据可能失灵"
    # 逐轮发散(累积学习的形状),不是一次性跳变
    overlaps = [r["重叠"] for r in v09]
    assert overlaps[0] > overlaps[-1] and overlaps[-1] <= 8


def test_exclusion_audit_flags_motifs_without_evidence():
    """审计必须能抓出「凭空排除」。这里同时给阳性对照:真实数据应当零凭空。"""
    from app.demo import V09_CONTRACT_DIR, exclusion_audit
    arm = V09_CONTRACT_DIR / "contract-v09_reflexion-on_seed-42"
    if not (arm / "agentic.metrics.json").exists():
        pytest.skip("v0.9 四臂归档不在本检出中")
    audit = exclusion_audit(arm)
    assert audit, "反思臂应当有 compose_batch 记录"
    for row in audit:
        assert row["凭空捏造"] == "无", f"第 {row['轮次']} 轮排除了证据里没有的 motif:{row['凭空捏造']}"
        assert row["排除数"] == row["有据可查"]
    # 有选择地排，不是一刀切:最后一轮的证据池明显大于排除数
    assert audit[-1]["累积证据池"] > audit[-1]["排除数"]


# ---- 两个前端融合后的顶层视图切换 -------------------------------------------------
# 融合前 app/demo.py 与 app/timeline.py 是两个独立 streamlit 应用，跑在不同端口、
# 各自 set_page_config，读者要开两个网址才能看全。融合后 timeline 变成 demo 的一个
# 视图，两处风险必须钉住：①两次 set_page_config 会直接抛异常；②timeline 的全局 CSS
# 若在模块导入时注入，会污染实验看板的布局。

def test_default_view_is_the_experiment_dashboard(app: AppTest):
    labels = [t.label for t in app.tabs]
    assert "① 四策略对比" in labels, "默认应停在实验看板"


def test_research_timeline_view_renders_without_exception():
    """切到研究演进视图必须能渲染——这是融合唯一的新失败面。"""
    at = AppTest.from_file(str(APP), default_timeout=300)
    at.run()
    view = next((r for r in at.radio if r.key == "top_view"), None)
    assert view is not None, "顶层视图切换控件不存在"
    assert view.options == ["🔬 实验看板", "🛰️ 研究演进"]
    view.set_value("🛰️ 研究演进").run()
    assert not at.exception, [e.value for e in at.exception]
    body = " ".join(m.value for m in at.markdown)
    assert "AI4SCIENCE" in body or "演进" in body, "研究演进视图没有渲染出内容"


def test_timeline_module_injects_no_style_at_import_time():
    """timeline 的全局 CSS 必须按需注入。模块级注入会污染实验看板。"""
    import app.timeline as timeline
    assert hasattr(timeline, "inject_style"), "CSS 应收进 inject_style()"
    assert timeline._STYLE.lstrip().startswith("<style>")
    # 独立运行时才配置页面；被挂载时由 demo.py 负责，两次调用会抛异常
    import inspect
    assert "standalone" in inspect.signature(timeline.main).parameters
