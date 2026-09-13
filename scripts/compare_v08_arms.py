#!/usr/bin/env python3
"""比对 v0.8 各臂:实测批次是否真的分叉,还是只有叙述在变。

第一轮冒烟的教训是:LLM 的工具调用数、redirect 轮次、总结措辞都会变,
而**实际被 oracle 测过的 288 个变体逐位相同**。所以任何「反思起作用了」的判断,
必须落到批次本身,不能落到 agent 说了什么或调了几次工具。

批次身份取 `agent.tool.test.residuals` 事件里 `records[].seq` 的集合哈希——
这是真正花掉预算的那批,不是暂存的、也不是 LLM 声称的。

用法:
    python3 scripts/compare_v08_arms.py [跑批根目录]
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from events.store import iter_stream  # noqa: E402
from events.reflexion import summarise_motif_recurrence  # noqa: E402


def tested_batches(arm_dir: Path) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {}
    for event in iter_stream(arm_dir / "agentic.events.jsonl"):
        if event["event_type"] == "agent.tool.test.residuals":
            out[int(event["round_id"])] = [r["seq"] for r in event["payload"]["records"]]
    return out


def digest(seqs: list[str]) -> str:
    return hashlib.sha256("".join(sorted(seqs)).encode()).hexdigest()[:12]


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tmp/v08-factorial"
    arms = sorted(d for d in root.iterdir() if d.is_dir() and (d / "agentic.metrics.json").exists())
    if not arms:
        print(f"{root} 下没有完成的臂")
        return 1

    print(f"{'臂':38s}{'峰':>8s}{'达峰轮':>7s}{'strong':>7s}{'复现率':>8s}{'后段':>7s}  "
          f"{'采集档':<26s}{'自设ratio':>9s}{'排除motif':>10s}{'redirect':>9s}  "
          f"{'LLM':<5s}{'秒':>5s}  逐轮批次哈希")
    batches = {}
    for arm in arms:
        m = json.loads((arm / "agentic.metrics.json").read_text())
        b = tested_batches(arm)
        batches[arm.name] = b
        wall = (arm.parent / f"{arm.name}.wall-seconds.txt")
        wall_s = wall.read_text().strip() if wall.exists() else "?"
        digests = " ".join(digest(b[r]) for r in sorted(b))
        summary = m.get("summary", {})
        # 采集档位取实际生效值,不取命令行意图 —— 两者曾经不一致(工具层耦合未解),
        # 那一轮四个臂看起来是 2x2、实际是同一个档位。
        composes = [e["payload"] for e in m.get("tool_trace", [])
                    if e.get("event_type") == "agent.tool.compose_batch"]
        sources = {p.get("allocation_source") for p in composes}
        # v0.9 的两个杠杆各自是否被真的行使 —— v0.8 里 agent_requested 是 0/20,
        # 而 exclude_motifs 当时根本不在工具 schema 里,所以「没用」是结构性的。
        n_requested = sum(p.get("allocation_source") == "agent_requested" for p in composes)
        n_excl_calls = sum(bool(p.get("excluded_motifs")) for p in composes)
        motifs = sorted({m0 for p in composes for m0 in (p.get("excluded_motifs") or [])})
        # 峰值与样本效率在 48x6 下都饱和(八臂全部第 2 轮达到候选池真实最优 8.416205),
        # 所以这两列单独看没有区分力;复现率是目前唯一不饱和的指标,必须同屏。
        history = m.get("top10_max_history") or []
        peak_round = (next((i + 1 for i, v in enumerate(history)
                            if abs(v - max(history)) < 1e-9), 0) if history else 0)
        rec = summarise_motif_recurrence(m.get("motif_recurrence") or [])
        pooled = rec["pooled_rate"]
        late = rec["late_pooled_rate"]
        print(f"{arm.name:38s}{summary.get('final_cum_top10_max', 0):8.4f}"
              f"{('r' + str(peak_round)) if peak_round else '?':>7s}"
              f"{summary.get('final_cum_n_strong', 0):7d}"
              f"{(f'{pooled:.1%}' if pooled is not None else '—'):>8s}"
              f"{(f'{late:.1%}' if late is not None else '—'):>7s}  "
              f"{'/'.join(sorted(s or '?' for s in sources)):<28s}"
              f"{f'{n_requested}/{len(composes)}':>9s}"
              f"{f'{n_excl_calls}/{len(composes)}':>10s}"
              f"{str(m.get('redirect_rounds')):>9s}  "
              f"{m.get('llm_round_successes')}/{m.get('llm_round_attempts'):<3}{wall_s:>5s}  {digests}")
        if motifs:
            print(f"{'':38s}└─ 被排除的 motif: {', '.join(motifs)}")

    # 同一 seed、同一采集档位下,反思开/关是否让批次分叉
    print("\n=== 反思开 vs 关(同 seed、同采集档位)===")
    pairs = {}
    for name in batches:
        if "_reflexion-off_" in name:
            pairs[name.replace("_reflexion-off_", "_reflexion-on_")] = name
    any_pair = False
    for on, off in pairs.items():
        if on not in batches:
            continue
        any_pair = True
        rounds = sorted(set(batches[on]) | set(batches[off]))
        diffs = []
        for r in rounds:
            a, b = batches[off].get(r, []), batches[on].get(r, [])
            same = digest(a) == digest(b) if a and b else False
            overlap = len(set(a) & set(b))
            diffs.append(f"r{r}:{'同' if same else f'异({overlap}/{max(len(a), len(b))})'}")
        label = off.replace("_reflexion-off_", "_")
        verdict = "批次未分叉" if all("同" in d for d in diffs) else "**批次已分叉**"
        print(f"  {label:30s} {verdict}   " + " ".join(diffs))
    if not any_pair:
        print("  (还没有成对的开/关两臂)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
