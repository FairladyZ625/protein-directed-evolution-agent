"""策略① 随机突变基线：GB1 三轮虚拟定向进化（M1/T1）。

闭环：轮 0 冷启动池（全表按 HD 分层抽 5,000 条）→ 每轮随机提名 96 个未测变体 →
查全量真值表（oracle，模拟湿实验）→ 回流池。产出每轮 top-10 真实 fitness 指标 JSON 与曲线图。

口径：
- 候选空间 = 4 位点 × 20 aa 合法组合中 oracle 可测的 149,361 个（160,000 中缺 10,639 个无真值，
  不进候选，与「只用 FLIP 原生变体集」一致），扣除已测变体后无放回均匀抽样。
- 每轮 top10_max / top10_mean / n_hit_nonzero 统计当轮 96 个提名；cum_* 统计第 1..r 轮全部提名
  （不含冷启动池，池子单列在 round0_pool 作参照）。非零命中 = fitness > 0.01。

运行：python evolution/random_baseline.py（即 make baseline）
M3 复用：from evolution.random_baseline import propose_random
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from evolution.results_layout import run_dir

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "four_mutations_full_data.csv"
_GB1 = run_dir("workflow", "gb1")
OUT_JSON = _GB1 / "random_baseline.metrics.json"
OUT_FIG = _GB1 / "figures" / "random_baseline.png"

EXPECTED_ROWS = 149_361
AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
WT = "VDGV"  # V39 / D40 / G41 / V54
SEED = 42
N_ROUNDS = 3
BUDGET = 96  # 96 孔板
POOL_SIZE = 5_000
TOP_K = 10
NONZERO = 0.01


def load_landscape(path: Path = DATA_PATH) -> pd.DataFrame:
    """读全量真值表（Variants/HD/Fitness）并校验数据契约；不符即抛错，不做清洗。"""
    df = pd.read_csv(path, usecols=["Variants", "HD", "Fitness"])
    fitness = pd.to_numeric(df["Fitness"], errors="coerce")
    variants = df["Variants"].astype(str)
    hd = sum((variants.str[i] != WT[i]).astype(int) for i in range(len(WT)))
    problems = []
    if len(df) != EXPECTED_ROWS:
        problems.append(f"行数 {len(df)} != {EXPECTED_ROWS}")
    if fitness.isna().any():
        problems.append(f"Fitness 解析失败 {int(fitness.isna().sum())} 行")
    if not variants.str.fullmatch(f"[{AMINO_ACIDS}]{{4}}").all():
        problems.append("Variants 存在非 4 位 20aa 组合")
    if not variants.is_unique:
        problems.append("Variants 有重复")
    if not (hd == df["HD"]).all():
        problems.append("HD 与 Variants 相对 WT 的汉明距离不一致")
    if problems:
        raise ValueError(f"数据契约不符，停止上报（不自行清洗）：{'；'.join(problems)}")
    df = df.assign(Variants=variants, Fitness=fitness).sort_values("Variants", ignore_index=True)
    wt_fitness = df.loc[df["Variants"] == WT, "Fitness"].tolist()
    if wt_fitness != [1.0]:
        raise ValueError(f"数据契约不符，停止上报：WT {WT} fitness={wt_fitness}，应为 [1.0]")
    return df


def build_cold_start_pool(df: pd.DataFrame, rng: np.random.Generator, size: int = POOL_SIZE) -> pd.DataFrame:
    """轮 0 历史账本：按 HD 分层比例抽样（最大余数法），每层至少 1 条（WT 必入池），总数恰为 size。"""
    counts = df["HD"].value_counts().sort_index()
    share = counts / counts.sum() * (size - len(counts))
    quota = np.floor(share).astype(int)
    leftover = size - len(counts) - int(quota.sum())
    quota.iloc[np.argsort(-(share - quota).to_numpy(), kind="stable")[:leftover]] += 1
    quota += 1
    hd = df["HD"].to_numpy()
    idx = np.concatenate([rng.choice(np.flatnonzero(hd == h), size=q, replace=False) for h, q in quota.items()])
    return df.iloc[np.sort(idx)].reset_index(drop=True)


def propose_random(candidates: np.ndarray, budget: int, rng: np.random.Generator) -> np.ndarray:
    """策略①：从未测候选（去重的变体字符串数组）中无放回均匀抽 budget 个。"""
    return rng.choice(candidates, size=budget, replace=False)


def simulate(df: pd.DataFrame, seed: int = SEED, n_rounds: int = N_ROUNDS, budget: int = BUDGET,
             pool_size: int = POOL_SIZE) -> tuple[pd.DataFrame, list[pd.DataFrame]]:
    """冷启动池 + n_rounds 轮（随机提名 → 查表 → 回流），返回 (轮 0 池, 每轮实测批次)。"""
    rng = np.random.default_rng(seed)
    oracle = df.set_index("Variants")  # 全表即完美 oracle
    tested = build_cold_start_pool(df, rng, pool_size)
    pool, batches = tested, []
    for _ in range(n_rounds):
        candidates = df.loc[~df["Variants"].isin(tested["Variants"]), "Variants"].to_numpy()
        picks = propose_random(candidates, budget, rng)
        batch = oracle.loc[picks].reset_index()  # 虚拟湿实验：查真值
        batches.append(batch)
        tested = pd.concat([tested, batch], ignore_index=True)  # 回流进历史账本
    return pool, batches


def _r(x: float) -> float:
    return round(float(x), 6)


def _topk_stats(tested: pd.DataFrame) -> dict:
    top = tested.nlargest(TOP_K, "Fitness", keep="first")
    n_hit = int((tested["Fitness"] > NONZERO).sum())
    return {
        "top10_max": _r(top["Fitness"].max()),
        "top10_mean": _r(top["Fitness"].mean()),
        "n_hit_nonzero": n_hit,
        "hit_rate_nonzero": _r(n_hit / len(tested)),
        "top10": [[v, _r(f)] for v, f in zip(top["Variants"], top["Fitness"])],
    }


def landscape_stats(df: pd.DataFrame) -> dict:
    f = df["Fitness"].sort_values(ascending=False).to_numpy()
    k = int(np.ceil(0.01 * len(f)))
    return {
        "n_variants": len(f),
        "n_missing_combos": len(AMINO_ACIDS) ** 4 - len(f),
        "max_fitness": _r(f[0]),
        "best_variant": df.loc[df["Fitness"].idxmax(), "Variants"],
        "top1pct_n": k,
        "top1pct_threshold": _r(f[k - 1]),
        "top1pct_mean": _r(f[:k].mean()),
        "frac_nonzero": _r((f > NONZERO).mean()),
        "wt_fitness": 1.0,
    }


def build_report(df: pd.DataFrame, pool: pd.DataFrame, batches: list[pd.DataFrame], seed: int) -> dict:
    landscape = landscape_stats(df)
    rounds = []
    for r, batch in enumerate(batches, start=1):
        cum = _topk_stats(pd.concat(batches[:r], ignore_index=True))
        rounds.append({
            "round": r,
            "n_nominated": len(batch),
            **_topk_stats(batch),
            "cum_top10_max": cum["top10_max"],
            "cum_top10_mean": cum["top10_mean"],
            "cum_n_hit_nonzero": cum["n_hit_nonzero"],
            "pool_size_after": len(pool) + sum(len(b) for b in batches[:r]),
        })
    worst = max(r["top10_mean"] for r in rounds)
    return {
        "strategy": "random",
        "seed": seed,
        "n_rounds": len(batches),
        "budget_per_round": len(batches[0]) if batches else 0,
        "cold_start_pool_size": len(pool),
        "nonzero_threshold": NONZERO,
        "candidate_space": "4 位点 × 20 aa 合法组合 ∩ oracle 可测（全表），扣除已测，无放回均匀抽样",
        "data": str(DATA_PATH.relative_to(ROOT)),
        "reproduce": "make baseline  # = python evolution/random_baseline.py",
        "landscape": landscape,
        "round0_pool": {"hd_counts": {int(h): int(n) for h, n in pool["HD"].value_counts().sort_index().items()},
                        **_topk_stats(pool)},
        "rounds": rounds,
        "negative_control": {
            "rule": "每轮 top10_mean 须显著低于全表 top-1% 均值，否则疑查询逻辑有 bug",
            "max_round_top10_mean": worst,
            "landscape_top1pct_mean": landscape["top1pct_mean"],
            "passed": worst < landscape["top1pct_mean"],
        },
    }


def run_baseline(df: pd.DataFrame, seed: int = SEED) -> dict:
    return build_report(df, *simulate(df, seed=seed), seed=seed)


def plot_curve(report: dict, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, muted, grid, surface = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
    blue, orange, aqua = "#2a78d6", "#eb6834", "#1baf7a"
    rounds, land, pool = report["rounds"], report["landscape"], report["round0_pool"]
    x = [r["round"] for r in rounds]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.6), gridspec_kw={"width_ratios": [1.6, 1]})
    fig.patch.set_facecolor(surface)
    for ax in (ax1, ax2):
        ax.set_facecolor(surface)
        ax.grid(axis="y", color=grid, lw=0.8)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color(muted)
        ax.tick_params(colors=muted, labelsize=9)
        ax.set_xticks(x, [f"R{i}" for i in x])
        ax.set_xlabel("round (96 random nominations each)", color=muted, fontsize=9)

    refs = [
        (pool["top10_mean"], f"round-0 pool top-10 mean ({pool['top10_mean']:.2f})"),
        (land["top1pct_mean"], f"landscape top-1% mean ({land['top1pct_mean']:.2f})"),
        (land["wt_fitness"], "wild type VDGV (1.00)"),
    ]
    for y, label in refs:
        ax1.axhline(y, color=muted, lw=1, ls=(0, (4, 3)), zorder=1)
        ax1.text(x[-1] + 0.3, y, label, color=muted, fontsize=8, va="bottom", ha="right")
    series = [  # (key, label, color, marker, 数值标注偏移；None = 不直标，靠图例)
        ("top10_max", "round batch top-10 max", orange, "s", 7),
        ("top10_mean", "round batch top-10 mean", blue, "o", -14),
        ("cum_top10_mean", "cumulative top-10 mean (R1..Rr)", aqua, "D", None),
    ]
    for key, label, color, marker, dy in series:
        ys = [r[key] for r in rounds]
        ax1.plot(x, ys, color=color, lw=2, marker=marker, ms=7, mec=surface, mew=1.5, label=label, zorder=3)
        if dy is None:
            continue
        for xi, yi in zip(x, ys):
            ax1.annotate(f"{yi:.2f}", (xi, yi), textcoords="offset points", xytext=(0, dy), ha="center",
                         fontsize=8, color=ink)
    ax1.set_xlim(x[0] - 0.3, x[-1] + 0.3)
    ax1.set_ylim(0, max(pool["top10_mean"], land["top1pct_mean"], max(r["top10_max"] for r in rounds)) * 1.15)
    ax1.set_ylabel("true fitness (oracle lookup)", color=muted, fontsize=9)
    ax1.set_title("Top-10 true fitness per round", color=ink, fontsize=11, loc="left")
    ax1.legend(loc="upper left", fontsize=8, frameon=False, labelcolor=ink, bbox_to_anchor=(0, 0.78))

    rates = [r["hit_rate_nonzero"] for r in rounds]
    ax2.bar(x, rates, width=0.55, color=blue, zorder=3, label="round batch hit rate")
    for xi, r in zip(x, rounds):
        ax2.annotate(f"{r['n_hit_nonzero']}/{r['n_nominated']}", (xi, r["hit_rate_nonzero"]),
                     textcoords="offset points", xytext=(0, 4), ha="center", fontsize=8, color=ink)
    ax2.axhline(land["frac_nonzero"], color=muted, lw=1, ls=(0, (4, 3)), zorder=4,
                label=f"landscape share ({land['frac_nonzero']:.1%})")
    ax2.legend(loc="upper right", fontsize=8, frameon=False, labelcolor=ink)
    ax2.set_xlim(x[0] - 0.6, x[-1] + 0.6)
    ax2.set_ylim(0, 1)
    ax2.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax2.set_ylabel(f"hit rate (fitness > {report['nonzero_threshold']})", color=muted, fontsize=9)
    ax2.set_title("Non-zero hit rate per round", color=ink, fontsize=11, loc="left")

    fig.suptitle(f"Strategy 1 - random baseline on GB1 (seed={report['seed']}, "
                 f"{report['budget_per_round']}/round, cold-start pool {report['cold_start_pool_size']:,})",
                 color=ink, fontsize=12, x=0.01, ha="left")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, facecolor=surface, metadata={"Software": None})
    plt.close(fig)


def _print_summary(report: dict) -> None:
    land, pool = report["landscape"], report["round0_pool"]
    print(f"[data] {land['n_variants']:,} variants | max {land['max_fitness']:.3f} ({land['best_variant']}) | "
          f"top-1% mean {land['top1pct_mean']:.3f} | fitness>{NONZERO} {land['frac_nonzero']:.1%}")
    print(f"[round 0] cold-start pool {report['cold_start_pool_size']:,} HD={pool['hd_counts']} | "
          f"top10_max {pool['top10_max']:.3f} top10_mean {pool['top10_mean']:.3f} | "
          f"nonzero {pool['n_hit_nonzero']}/{report['cold_start_pool_size']} ({pool['hit_rate_nonzero']:.1%})")
    for r in report["rounds"]:
        print(f"[round {r['round']}] nominated {r['n_nominated']} | top10_max {r['top10_max']:.3f} "
              f"top10_mean {r['top10_mean']:.3f} | nonzero {r['n_hit_nonzero']}/{r['n_nominated']} "
              f"({r['hit_rate_nonzero']:.1%}) | cum top10_max {r['cum_top10_max']:.3f} "
              f"top10_mean {r['cum_top10_mean']:.3f} | pool {r['pool_size_after']:,}")
    nc = report["negative_control"]
    print(f"[negative control] {'PASS' if nc['passed'] else 'FAIL'}: max round top10_mean "
          f"{nc['max_round_top10_mean']:.3f} < landscape top-1% mean {nc['landscape_top1pct_mean']:.3f}")


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description="策略① 随机突变基线：GB1 三轮虚拟定向进化")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    parser.add_argument("--out-fig", type=Path, default=OUT_FIG)
    args = parser.parse_args(argv)

    report = run_baseline(load_landscape(), seed=args.seed)
    _print_summary(report)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    plot_curve(report, args.out_fig)
    print(f"[out] {args.out_json}\n[out] {args.out_fig}")
    return report


if __name__ == "__main__":
    main()
