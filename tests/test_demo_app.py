"""T8 看板冒烟测试：三模块首屏渲染、模块③(a) 打分与越界提示、只读纪律。"""
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
    assert "llm_source=" in success  # 如实标注本轮 LLM 来源（deterministic / fallback / llm:*）
    body = _text(at)
    assert "Top-10 推荐突变方案" in body
    assert "本轮五角色推理链" in body  # 内存录制事件与模块②同源渲染


def test_demo_module_is_read_only_source():
    source = APP.read_text()
    # 红线：demo 不向磁盘写任何文件（唯一 append 是 _MemoryRecorder 内存录制器）
    for banned in ("write_text", "to_json", "to_csv", ".open(", "EventStore("):
        assert banned not in source, banned
    assert "_MemoryRecorder" in source
