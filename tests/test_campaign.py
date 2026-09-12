"""Tests for the four-strategy campaign engine (evolution/campaign.py).

Uses a small but *complete* 2^4 = 16-variant landscape (each of the four GB1
sites toggles between its WT residue and one alternative), so every candidate
the agent designs is guaranteed to be measurable by the oracle.
"""
from itertools import product

import pandas as pd
import pytest
from unittest import mock

import evolution.campaign as campaign
from evolution.campaign import RANDOM_SEEDS, plot_campaign, run_campaign

_ALT = {0: "F", 1: "A", 2: "W", 3: "I"}  # one alternative residue per site (WT = "VDGV")
_WT = "VDGV"


def landscape() -> pd.DataFrame:
    rows = []
    for combo in product(*([wt, alt] for wt, alt in zip(_WT, _ALT.values()))):
        seq = "".join(combo)
        # Deterministic additive fitness with a mild pairwise interaction.
        f = 1.0
        f += 1.5 if seq[0] == "F" else 0.0
        f += -0.3 if seq[1] == "A" else 0.0
        f += 0.8 if seq[2] == "W" else 0.0
        f += 0.5 if seq[3] == "I" else 0.0
        f += 0.4 if (seq[0] == "F" and seq[2] == "W") else 0.0
        rows.append({"Variants": seq, "HD": sum(a != b for a, b in zip(seq, _WT)), "Fitness": round(f, 3)})
    return pd.DataFrame(rows)


# 曾经这里有一个 autouse 夹具,用 monkeypatch 给 run_pipeline 注入完整实测空间,
# 以绕过「求交把每个新提名都滤掉」导致的 0 提名。那是在拿测试夹具遮盖一个**生产缺陷**:
# evolution/campaign.py 当时把 train(已测过的)当成可测集合传进 pipeline,真实 campaign 的
# 两条 agent 策略因此跑 0 轮、静默、退出码 0(fact F-C3A81F2E)。生产路径已改为显式传
# measurable_variants=set(df.Variants),夹具随之删除——留着它会继续挡住这条回归。
# 下面 test_four_strategies_share_oracle_and_budget 里的 n_nominated == [2, 2] 就是这条门。


class _EventProbe:
    def __init__(self):
        self.events = []

    def append(self, name, *, round_id=1, strategy="agent", actor=None, payload=None):
        self.events.append({"name": name, "round_id": round_id, "strategy": strategy, "actor": actor})


def test_four_strategies_share_oracle_and_budget():
    report = run_campaign(landscape(), seed=3, n_rounds=2, budget=2, pool_size=8)
    assert set(report["strategies"]) == {"random", "greedy", "agent_no_knowledge", "knowledge_agent"}
    assert report["oracle"] == "measured table lookup"
    assert report["candidate_space_size"] == 16
    for result in report["strategies"].values():
        assert [r["n_nominated"] for r in result["rounds"]] == [2, 2]
        assert all("cum_top10_max" in r for r in result["rounds"])


def test_campaign_is_reproducible():
    a = run_campaign(landscape(), seed=9, n_rounds=2, budget=2, pool_size=8)
    b = run_campaign(landscape(), seed=9, n_rounds=2, budget=2, pool_size=8)
    assert a == b


def test_agent_strategies_actually_invoke_the_five_role_pipeline():
    """Regression guard: ③④ must route through agent.pipeline.run_pipeline, not a
    predictor shortcut. If they did not, no role events would be emitted."""
    probe = _EventProbe()
    run_campaign(landscape(), seed=1, n_rounds=1, budget=2, pool_size=8, event_store=probe)
    role_events = [e for e in probe.events if e["name"] == "agent.role.completed"]
    actors = {e["actor"] for e in role_events}
    assert {"data_analyst", "hypothesis_generator", "mutation_designer",
            "fitness_evaluator", "scientific_critic"} <= actors


def test_agent_knowledge_ablation_reaches_pipeline(monkeypatch):
    original = campaign.run_pipeline
    observed = []

    def probe(*args, **kwargs):
        observed.append({"no_knowledge": kwargs["no_knowledge"],
                         "has_hypothesis_port": "llm_hypothesis" in kwargs,
                         "has_critic_port": "llm_critic" in kwargs})
        return original(*args, **kwargs)

    monkeypatch.setattr(campaign, "run_pipeline", probe)
    run_campaign(landscape(), seed=1, n_rounds=1, budget=2, pool_size=8)
    assert observed == [
        {"no_knowledge": True, "has_hypothesis_port": True, "has_critic_port": True},
        {"no_knowledge": False, "has_hypothesis_port": True, "has_critic_port": True},
    ]


def test_knowledge_agent_differs_from_no_knowledge_acquisition():
    report = run_campaign(landscape(), seed=5, n_rounds=1, budget=2, pool_size=8)
    acq_no = report["strategies"]["agent_no_knowledge"]["acquisition"]
    acq_kn = report["strategies"]["knowledge_agent"]["acquisition"]
    assert acq_no != acq_kn
    assert "BLOSUM62" in acq_kn and "var" in acq_kn


def test_summary_reports_sample_efficiency():
    report = run_campaign(landscape(), seed=7, n_rounds=2, budget=2, pool_size=8)
    for name in ("random", "greedy", "agent_no_knowledge", "knowledge_agent"):
        s = report["summary"][name]
        assert len(s["cum_top10_max_curve"]) == 2
        assert s["final_cum_top10_max"] >= 1.0


def test_random_baseline_is_repeated_over_fixed_independent_seeds():
    report = run_campaign(landscape(), seed=999, n_rounds=2, budget=2, pool_size=8)
    aggregate = report["strategies"]["random"]["multi_seed"]
    assert aggregate["seeds"] == list(RANDOM_SEEDS)
    assert aggregate["n_runs"] == len(RANDOM_SEEDS)
    assert all("cum_top10_max_mean" in row and "cum_top10_max_std" in row
               for row in aggregate["rounds"])


def test_audit_events_cover_each_dbtl_step():
    probe = _EventProbe()
    run_campaign(landscape(), seed=2, n_rounds=1, budget=2, pool_size=8, event_store=probe)
    names = {event["name"] for event in probe.events}
    assert {"campaign.propose.completed", "campaign.oracle.completed",
            "campaign.refill.completed", "campaign.retrain.completed"} <= names


def test_topk_residue_concentration_is_reported():
    report = run_campaign(landscape(), seed=4, n_rounds=1, budget=2, pool_size=8)
    for result in report["strategies"].values():
        concentration = result["topk_concentration"]
        assert concentration["n_topk_observations"] == 2
        assert set(concentration["positions"]) == {"39", "40", "41", "54"}
        for position in concentration["positions"].values():
            assert 0.0 <= position["dominant_fraction"] <= 1.0
            assert 0.0 <= position["mutation_fraction"] <= 1.0


def test_object_fitness_is_coerced_and_random_band_is_drawn(tmp_path, monkeypatch):
    frame = landscape()
    frame["Fitness"] = frame["Fitness"].astype(str)
    report = run_campaign(frame, seed=6, n_rounds=1, budget=2, pool_size=8)

    import matplotlib.axes
    calls = []
    original = matplotlib.axes.Axes.fill_between

    def fill_between(self, *args, **kwargs):
        calls.append(args)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(matplotlib.axes.Axes, "fill_between", fill_between)
    plot_campaign(report, tmp_path / "curve.png")
    assert calls
    assert (tmp_path / "curve.png").is_file()


def _probe_candidate():
    """一个最小的合法 ScoredCandidate,给端口形状测试用。"""
    from agent.pipeline import CombinationRationale, ScoredCandidate
    return ScoredCandidate(
        mutations=["V39I"], sequence="IDGV", mean=4.2, variance=0.1,
        combination_rationale=CombinationRationale(
            selected_single_mutations=["V39I"], empirical_position_gains={39: 3.1},
            positions_non_conflicting=True, rule_ids=["R-GB1-SITES"],
            deterministic_summary="probe"))

def test_llm_critic_port_returns_a_shape_criticreview_accepts():
    """`_llm_critic` 的返回值要能过 `CriticReview` 的校验。

    它曾经返回裸字符串,而 `agent.pipeline._structured_call` 会拿返回值去
    `CriticReview.model_validate()`——那需要一个带 `note` 字段的映射。于是每一次
    LLM critic 调用都抛 ValidationError 并静默降级成确定性注释:一次真 LLM 跑出来的
    critique 列表 15/15 全是「accepted (deterministic critic fallback)」,而端点本身
    19 秒就能正常应答。这条测试不打网络,只钉住跨这个边界的形状契约。
    """
    from agent.pipeline import CriticReview
    from evolution.campaign import _llm_critic

    calls = []

    def fake_chat(prompt):
        calls.append(prompt)
        return "  The candidate is chemically conservative and passes every gate.  "

    state = {}
    port = _llm_critic(state)
    with mock.patch("evolution.campaign.chat_json", fake_chat):
        review = CriticReview.model_validate(port(_probe_candidate(), []))
    assert calls, "端口没有真的调用 chat_json"
    assert review.note.startswith("The candidate is chemically conservative")
    assert state["critic_source"].startswith("llm:")
    assert state["critic_llm_calls"] == 1

    # 空回复必须算调用失败,而不是变成一条署名给模型的空白 critique
    state_empty = {}
    with mock.patch("evolution.campaign.chat_json", lambda prompt: "   "):
        empty = CriticReview.model_validate(_llm_critic(state_empty)(_probe_candidate(), []))
    assert "fallback" in empty.note
    assert state_empty["critic_source"] == "fallback"
    assert state_empty["critic_fallbacks"] == 1


def test_scientific_critic_caps_live_llm_critiques_but_gates_every_candidate():
    """LLM 只写注释,门禁始终是确定性的且覆盖每一个候选。

    修好 measurable_variants 之后一轮会设计上千个候选,而一次真 critique 约 19 秒;
    不设上限,单轮要跑几小时。这条测试钉住:预算只限制 LLM 调用次数,
    不减少被门禁检查的候选数。
    """
    from agent.pipeline import ScientificCritic, ScoredCandidate, CombinationRationale

    def make(mutations, sequence, mean):
        return ScoredCandidate(
            mutations=mutations, sequence=sequence, mean=mean, variance=0.1,
            combination_rationale=CombinationRationale(
                selected_single_mutations=mutations, empirical_position_gains={},
                positions_non_conflicting=True, rule_ids=["R-GB1-SITES"],
                deterministic_summary="probe"))

    scored = [make(["V39I"], "IDGV", 5.0), make(["D40E"], "VEGV", 4.0), make(["V54I"], "VDGI", 3.0)]
    seen = []

    def port(candidate, rules):
        seen.append(candidate.sequence)
        return {"note": "live"}

    accepted, checks = ScientificCritic(port, llm_budget=1).run(scored)
    assert len(checks) == 3, "门禁必须检查每一个候选"
    assert len(seen) == 1, f"LLM 调用应被预算限制为 1 次,实际 {len(seen)} 次"
    assert checks[0].note == "live" and checks[1].note == "accepted"
    assert len(accepted) == 3
