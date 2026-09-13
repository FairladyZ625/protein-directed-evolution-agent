"""Deterministic, read-only reflexion over observed prediction residual events."""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .replay import select_events
from .store import iter_stream


# Pre-registered before the v0.8 comparison.  AAV variants below this measured
# fitness are treated as lethal for the motif-recurrence behaviour metric.
DEAD_FITNESS_THRESHOLD = 0.2


@dataclass(frozen=True)
class RoundReflexion:
    """Observed-only residual lessons extracted for one completed round."""

    round_id: int
    overestimated_fails: list[dict[str, Any]]
    underestimated_hits: list[dict[str, Any]]
    motif_summary: list[dict[str, Any]]


def _mutation_set(sequence: str, wild_type: str) -> frozenset[str]:
    if len(sequence) != len(wild_type):
        return frozenset()
    return frozenset(
        f"{wild}{position}{mutant}"
        for position, (wild, mutant) in enumerate(zip(wild_type, sequence))
        if wild != mutant
    )


def _residual_records(events: Sequence[Mapping[str, object]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for event in events:
        if event.get("event_type") != "agent.tool.test.residuals":
            continue
        payload = event.get("payload")
        if not isinstance(payload, Mapping):
            continue
        raw_records = payload.get("records")
        if not isinstance(raw_records, list):
            continue
        for raw in raw_records:
            if not isinstance(raw, Mapping):
                continue
            try:
                row = {
                    "seq": str(raw["seq"]),
                    "predicted_mean": float(raw["predicted_mean"]),
                    "predicted_var": float(raw["predicted_var"]),
                    "measured_fitness": float(raw["measured_fitness"]),
                    "residual": float(raw["residual"]),
                }
            except (KeyError, TypeError, ValueError):
                continue
            records.append(row)
    return records


def extract_round_reflexion(
    stream_path: str | Path,
    *,
    last_round_id: int,
    wt: str,
    top_k: int = 3,
) -> RoundReflexion:
    """Read one round from the event stream and rank its observed residual lessons."""
    events = select_events(iter_stream(stream_path), round_id=last_round_id)
    records = _residual_records(events)
    limit = max(0, int(top_k))
    overestimated = sorted(
        (
            row for row in records
            if row["residual"] < 0.0
            and row["measured_fitness"] < DEAD_FITNESS_THRESHOLD
        ),
        key=lambda row: (-abs(row["residual"]), row["seq"]),
    )[:limit]
    underestimated = sorted(
        (row for row in records if row["residual"] > 0.0),
        key=lambda row: (-abs(row["residual"]), row["seq"]),
    )[:limit]

    over_counts: Counter[str] = Counter()
    under_counts: Counter[str] = Counter()
    for row in overestimated:
        over_counts.update(_mutation_set(row["seq"], wt))
    for row in underestimated:
        under_counts.update(_mutation_set(row["seq"], wt))
    motifs = sorted(set(over_counts) | set(under_counts))
    motif_summary = [
        {
            "substitution": motif,
            "overestimated_fail_count": over_counts[motif],
            "underestimated_hit_count": under_counts[motif],
            "total_count": over_counts[motif] + under_counts[motif],
        }
        for motif in motifs
    ]
    motif_summary.sort(key=lambda row: (-row["total_count"], row["substitution"]))
    return RoundReflexion(
        round_id=int(last_round_id),
        overestimated_fails=overestimated,
        underestimated_hits=underestimated,
        motif_summary=motif_summary,
    )


def format_reflexion_prompt(reflexion: RoundReflexion, *,
                            exclusion_entrypoint: bool = False) -> str:
    """Render an observed-only reflexion card for deterministic prompt injection.

    ``exclusion_entrypoint`` names the v0.9 ``compose_batch(exclude_motifs=...)`` parameter in
    the closing constraint. Under the v0.8 contract there was no parameter that could express
    "do not pick candidates carrying N21D", so the constraint was unactionable by construction
    and the agent could only honour it in prose; keep it False to reproduce v0.8 byte-for-byte.
    """
    lines = [
        f"MANDATORY RESIDUAL REFLEXION (observed round {reflexion.round_id}):",
        "Residual definition: measured_fitness - nomination-time predicted_mean.",
        f"Lethal threshold fixed before the run: measured_fitness < {DEAD_FITNESS_THRESHOLD:g}.",
    ]
    if reflexion.overestimated_fails:
        lines.append("Overestimated lethal variants (largest absolute residual first):")
        for row in reflexion.overestimated_fails:
            lines.append(
                f"- {row['seq']}: predicted={row['predicted_mean']:.6f}, "
                f"variance={row['predicted_var']:.6f}, measured={row['measured_fitness']:.6f}, "
                f"residual={row['residual']:+.6f}"
            )
    else:
        lines.append("Overestimated lethal variants: none observed in the recorded batch.")
    if reflexion.underestimated_hits:
        lines.append("Underestimated variants (largest positive residual first):")
        for row in reflexion.underestimated_hits:
            lines.append(
                f"- {row['seq']}: predicted={row['predicted_mean']:.6f}, "
                f"variance={row['predicted_var']:.6f}, measured={row['measured_fitness']:.6f}, "
                f"residual={row['residual']:+.6f}"
            )
    else:
        lines.append("Underestimated variants: none observed in the recorded batch.")
    if reflexion.motif_summary:
        motif_text = ", ".join(
            f"{row['substitution']} (over={row['overestimated_fail_count']}, "
            f"under={row['underestimated_hit_count']})"
            for row in reflexion.motif_summary
        )
        lines.append(f"Observed substitution motifs: {motif_text}.")
    if exclusion_entrypoint:
        lines.append(
            "ACTION CONSTRAINT: before selecting this round, explicitly account for the lethal "
            "motifs above. The actionable entry point is "
            "`compose_batch(exclude_motifs=[...])`, which drops every candidate carrying the "
            "listed substitutions before scoring; pass the motifs you judge lethal there rather "
            "than only naming them in prose, and say which ones you deliberately kept and why."
        )
    else:
        lines.append(
            "ACTION CONSTRAINT: before selecting this round, explicitly account for the lethal "
            "motifs above and avoid carrying them forward unless current measured evidence justifies it."
        )
    return "\n".join(lines)


def motif_recurrence_rate(
    previous_residuals: Sequence[Mapping[str, object]],
    current_candidates: Sequence[str],
    *,
    wt: str,
    fatal_threshold: float = DEAD_FITNESS_THRESHOLD,
) -> dict[str, Any]:
    """Fraction of current nominees carrying any prior-round lethal substitution."""
    lethal_motifs: set[str] = set()
    for row in previous_residuals:
        try:
            measured = float(row["measured_fitness"])
            sequence = str(row["seq"])
        except (KeyError, TypeError, ValueError):
            continue
        if measured < float(fatal_threshold):
            lethal_motifs.update(_mutation_set(sequence, wt))

    candidates = [str(sequence) for sequence in current_candidates]
    repeated = sum(bool(_mutation_set(sequence, wt) & lethal_motifs) for sequence in candidates)
    return {
        "n_candidates": len(candidates),
        "n_with_previous_lethal_motif": repeated,
        "rate": repeated / len(candidates) if candidates else 0.0,
        "previous_lethal_motifs": sorted(lethal_motifs),
    }
