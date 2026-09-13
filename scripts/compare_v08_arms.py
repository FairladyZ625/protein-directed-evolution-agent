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

    print(f"{'臂':36s}{'redirect':12s}{'LLM':>7s}{'墙钟s':>7s}  逐轮批次哈希")
    batches = {}
    for arm in arms:
        m = json.loads((arm / "agentic.metrics.json").read_text())
        b = tested_batches(arm)
        batches[arm.name] = b
        wall = (arm.parent / f"{arm.name}.wall-seconds.txt")
        wall_s = wall.read_text().strip() if wall.exists() else "?"
        digests = " ".join(digest(b[r]) for r in sorted(b))
        print(f"{arm.name:36s}{str(m.get('redirect_rounds')):12s}"
              f"{m.get('llm_round_successes')}/{m.get('llm_round_attempts'):<5}{wall_s:>7s}  {digests}")

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
