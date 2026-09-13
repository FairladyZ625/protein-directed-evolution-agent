"""v0.8 event-stream residual reflexion and motif-level behaviour metrics."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import agent.auto_researcher as auto_researcher
from events.reflexion import (
    DEAD_FITNESS_THRESHOLD,
    extract_round_reflexion,
    format_reflexion_prompt,
    motif_recurrence_rate,
)
from events.store import EventStore
from evolution.pool_campaign import DatasetSpec


WT = "AAAAAAAA"


def _append_residual_event(store: EventStore) -> None:
    store.append(
        "agent.tool.test.residuals",
        round_id=1,
        strategy="agent_no_knowledge",
        actor="experiment",
        payload={
            "residual_definition": "measured_fitness - predicted_mean",
            "records": [
                {"seq": "SAAAAAAA", "predicted_mean": 3.0, "predicted_var": 0.2,
                 "measured_fitness": 0.1, "residual": -2.9},
                {"seq": "ASAAAAAA", "predicted_mean": 2.0, "predicted_var": 0.1,
                 "measured_fitness": 0.15, "residual": -1.85},
                {"seq": "AAGAAAAA", "predicted_mean": 0.2, "predicted_var": 0.3,
                 "measured_fitness": 2.2, "residual": 2.0},
            ],
        },
    )


def test_extract_reflexion_reads_observed_residuals_and_formats_prompt(tmp_path):
    path = tmp_path / "events.jsonl"
    _append_residual_event(EventStore(path))

    reflexion = extract_round_reflexion(path, last_round_id=1, wt=WT, top_k=2)

    assert [row["seq"] for row in reflexion.overestimated_fails] == [
        "SAAAAAAA", "ASAAAAAA",
    ]
    assert [row["seq"] for row in reflexion.underestimated_hits] == ["AAGAAAAA"]
    assert reflexion.motif_summary[0] == {
        "substitution": "A0S",
        "overestimated_fail_count": 1,
        "underestimated_hit_count": 0,
        "total_count": 1,
    }
    prompt = format_reflexion_prompt(reflexion)
    assert "MANDATORY RESIDUAL REFLEXION" in prompt
    assert "SAAAAAAA" in prompt and "predicted=3.000000" in prompt
    assert "measured=0.100000" in prompt and "residual=-2.900000" in prompt


def test_motif_recurrence_positive_control_detects_repeated_lethal_substitution():
    previous = [
        {"seq": "SAAAAAAA", "measured_fitness": 0.1},
        {"seq": "AGAAAAAA", "measured_fitness": 0.4},
    ]
    result = motif_recurrence_rate(
        previous,
        ["SGAAAAAA", "AAAAAGAA", "GAAAAAAA"],
        wt=WT,
    )
    assert DEAD_FITNESS_THRESHOLD == 0.2
    assert result == {
        "n_candidates": 3,
        "n_with_previous_lethal_motif": 1,
        "rate": pytest.approx(1 / 3),
        "previous_lethal_motifs": ["A0S"],
    }


def test_motif_recurrence_negative_control_is_zero_without_repeated_motif():
    result = motif_recurrence_rate(
        [{"seq": "SAAAAAAA", "measured_fitness": 0.1}],
        ["AGAAAAAA", "AAGAAAAA"],
        wt=WT,
    )
    assert result["rate"] == 0.0
    assert result["n_with_previous_lethal_motif"] == 0


def _toy_spec() -> DatasetSpec:
    rows = [
        ("AAAAAAAA", 1.0, 0),
        ("SAAAAAAA", 1.1, 1),
        ("ASAAAAAA", 1.2, 1),
        ("SSAAAAAA", 1.3, 2),
        ("SSSAAAAA", 0.1, 3),
        ("GGGAAAAA", 2.0, 3),
        ("TTTAAAAA", 3.0, 3),
    ]
    df = pd.DataFrame(rows, columns=["seq", "fitness", "hd"])

    def features(sequences: list[str]) -> np.ndarray:
        return np.zeros((len(sequences), 2), dtype=float)

    return DatasetSpec(name="toy", df=df, wt=WT, feature_fn=features)


def test_residual_event_keeps_nomination_time_prediction_across_retraining(
    tmp_path, monkeypatch,
):
    class RetrainChangesPrediction:
        fit_calls = 0

        def __init__(self, seeds=3):
            self.val_spearman = 0.9

        def fit(self, x, y):
            type(self).fit_calls += 1
            self.prediction = float(type(self).fit_calls)
            return self

        def predict(self, x):
            return (
                np.full(len(x), self.prediction, dtype=float),
                np.full(len(x), 0.25, dtype=float),
            )

    monkeypatch.setattr(auto_researcher, "RidgePredictor", RetrainChangesPrediction)
    path = tmp_path / "events.jsonl"
    store = EventStore(path)

    auto_researcher.run_autoresearch(
        _toy_spec(), budget=1, n_rounds=2, seed=0, event_store=store, llm=False,
    )

    residual_events = [
        event for event in store.iter_events()
        if event["event_type"] == "agent.tool.test.residuals"
    ]
    assert len(residual_events) == 2
    assert residual_events[0]["round_id"] == 1
    assert residual_events[0]["payload"]["records"][0]["predicted_mean"] == 1.0
    assert residual_events[1]["payload"]["records"][0]["predicted_mean"] == 2.0
    # Backward compatibility: prediction detail lives only in the new event.
    test_event = next(event for event in store.iter_events()
                      if event["event_type"] == "agent.tool.test")
    assert set(test_event["payload"]) == {"requested", "measured", "spent", "batch_max"}


# ---- 复现率聚合口径 -------------------------------------------------------------
# 为什么需要它:AAV 上峰值与样本效率两个指标都已饱和(八个臂全部在第 2 轮达到候选池
# 真实最优 8.416205,此后四轮不变),复现率是目前唯一不饱和、臂间差异达一个量级的指标。

def test_pooled_rate_is_not_the_mean_of_per_round_rates():
    """必须取合并率。逐轮率取平均会让候选数少的轮次获得同等权重。"""
    from events.reflexion import summarise_motif_recurrence
    rows = [{"round": 1, "n_candidates": 100, "n_with_previous_lethal_motif": 10},
            {"round": 2, "n_candidates": 2, "n_with_previous_lethal_motif": 2}]
    out = summarise_motif_recurrence(rows)
    assert out["pooled_rate"] == pytest.approx(12 / 102)
    assert out["pooled_rate"] != pytest.approx((0.10 + 1.0) / 2)


def test_late_window_excludes_the_rounds_where_arms_have_not_diverged():
    from events.reflexion import summarise_motif_recurrence
    rows = [{"round": r, "n_candidates": 10, "n_with_previous_lethal_motif": k}
            for r, k in [(2, 6), (3, 5), (4, 1), (5, 0), (6, 0)]]
    out = summarise_motif_recurrence(rows, late_from_round=4)
    assert out["pooled_rate"] == pytest.approx(12 / 50)
    assert out["late_pooled_rate"] == pytest.approx(1 / 30)  # 只有 r4-r6
    assert out["late_from_round"] == 4


def test_empty_and_malformed_rows_do_not_fabricate_a_rate():
    """没有数据时必须回 None,不能回 0.0——0.0 会被读成「一次都没复现」。"""
    from events.reflexion import summarise_motif_recurrence
    assert summarise_motif_recurrence([])["pooled_rate"] is None
    assert summarise_motif_recurrence([{"round": 1}])["pooled_rate"] is None
    out = summarise_motif_recurrence([{"round": 2, "n_candidates": 10,
                                       "n_with_previous_lethal_motif": 3}])
    assert out["pooled_rate"] == pytest.approx(0.3)
    assert out["late_pooled_rate"] is None  # r2 不在后段窗口内
