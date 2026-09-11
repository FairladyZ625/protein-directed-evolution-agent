"""GB1 定向进化看板（T8 可交互 demo）——单文件、只读消费上游产物。

三个模块（对应题目「可交互 demo」加分项 + 「输入野生型序列后自动推荐突变方案」）：
  ① 四策略对比    读 reports/campaign_metrics.json（T7 产出，schema t7.v2）。
  ② 五角色回放    读 reports/campaign_events*.jsonl（T4 事件流，带 SHA-256 哈希链）。
  ③ 实时试玩      one-hot + Ridge（T3 模型）秒级打分；一键跑一轮 agent 推荐复用
                  evolution.campaign.run_campaign（事件只进内存录制器，供模块②同源展示）。

纪律：本看板全程只读——@st.cache_data / @st.cache_resource 缓存加载，
绝不 append 事件流、绝不覆盖 reports/ 下任何产物；模块③(b) 的推荐事件
收集在内存 recorder 中，不落盘。运行：streamlit run app/demo.py（或 make demo）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:  # streamlit run 不保证把仓库根加进 sys.path
    sys.path.insert(0, str(ROOT))

from agent.llm import llm_available, llm_config  # noqa: E402
from evolution.mutations import validate_variant, variant_to_mutations  # noqa: E402

METRICS_JSON = ROOT / "reports" / "campaign_metrics.json"
METRICS_LLM_JSON = ROOT / "reports" / "campaign_metrics_llm.json"
# Three honest cold-start regimes (see report ch.6/7). Default view = the hard
# extrapolation regime, so the demo does not lead with the "easy" (data-rich) result.
REGIMES = {
    "hard · 低阶外推 (HD≤2 冷启动，推荐)": ROOT / "reports" / "campaign_metrics_hard.json",
    "easy · 随机池 (≈98% HD≥3，数据充裕)": ROOT / "reports" / "campaign_metrics.json",
    "sparse · 极稀疏 (仅 77 个单突变)": ROOT / "reports" / "campaign_metrics_sparse.json",
}
EVENTS_JSONL = ROOT / "reports" / "campaign_events.jsonl"
EVENTS_LLM_JSONL = ROOT / "reports" / "campaign_events_llm.jsonl"
BASELINE_JSON = ROOT / "reports" / "random_baseline_metrics.json"
PREDICTOR_JSON = ROOT / "reports" / "predictor_metrics.json"
TRAIN_POOL = ROOT / "data" / "pools" / "train_pool.csv"
LANDSCAPE_CSV = ROOT / "data" / "four_mutations_full_data.csv"

WT = "VDGV"  # V39 / D40 / G41 / V54
STRATEGY_LABELS = {
    "random": "① random 随机基线",
    "greedy": "② greedy 贪心（Ridge 全空间打分）",
    "agent_no_knowledge": "③ agent_no_knowledge 五角色 Agent",
    "knowledge_agent": "④ knowledge_agent 知识增强 Agent",
}
FIGURE_LABELS = {  # 图表内文字用英文，避免评测机缺中文字体出豆腐块
    "random": "random",
    "greedy": "greedy (Ridge full-space)",
    "agent_no_knowledge": "agent (no knowledge)",
    "knowledge_agent": "knowledge agent",
}
ROLE_ORDER = ("data_analyst", "hypothesis_generator", "mutation_designer",
              "fitness_evaluator", "scientific_critic")
ROLE_LABELS = {
    "data_analyst": ("1️⃣", "Data Analyst 数据分析"),
    "hypothesis_generator": ("2️⃣", "Hypothesis Generator 假设生成"),
    "mutation_designer": ("3️⃣", "Mutation Designer 突变设计"),
    "fitness_evaluator": ("4️⃣", "Fitness Evaluator 适应度评估"),
    "scientific_critic": ("5️⃣", "Scientific Critic 科学审稿"),
}

st.set_page_config(page_title="GB1 定向进化看板", page_icon="🧬", layout="wide")


# ---------------------------------------------------------------- 基础加载（全部只读、缓存）


@st.cache_data(show_spinner="读取 T7 四策略指标 …")
def load_metrics(path_str: str) -> dict | None:
    path = Path(path_str)
    if not path.exists():
        return None
    return json.loads(path.read_text())


@st.cache_data(show_spinner="读取 T4 事件流 …")
def load_events(path_str: str) -> list[dict] | None:
    path = Path(path_str)
    if not path.exists():
        return None
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


@st.cache_data(show_spinner="加载 149,361 真值表 …")
def load_landscape() -> pd.DataFrame | None:
    if not LANDSCAPE_CSV.exists():
        return None
    from evolution.random_baseline import load_landscape as _load

    return _load(LANDSCAPE_CSV)


@st.cache_resource(show_spinner="拟合 Ridge 预测器（one-hot，train_pool 5,000 条） …")
def fit_predictor():
    from features.one_hot import encode_one_hot
    from models.train_ladder import RidgePredictor

    pool = pd.read_csv(TRAIN_POOL)
    model = RidgePredictor()
    model.fit(encode_one_hot(pool.Variants.tolist()), pool.Fitness.to_numpy())
    return model, pool.Fitness.to_numpy()


def landscape_arrays():
    """(fitness 有序数组, {variant: fitness}) 供分位/真值查询；缺数据时返回 (None, {})。"""
    df = load_landscape()
    if df is None:
        return None, {}
    return df.Fitness.to_numpy(), df.set_index("Variants")["Fitness"].to_dict()


# ---------------------------------------------------------------- 模块①：四策略对比曲线


def _strategy_palette() -> dict[str, str]:
    return {"random": "#8a8a86", "greedy": "#2a78d6",
            "agent_no_knowledge": "#eb6834", "knowledge_agent": "#1baf7a"}


def _multi_seed_random_curves(seeds: tuple[int, ...], n_rounds: int) -> np.ndarray:
    """只读重模拟随机提名（复用 T1 simulate，不触碰任何 reports 产物）。"""
    from evolution.random_baseline import simulate

    df = load_landscape()
    curves = []
    for seed in seeds:
        _, batches = simulate(df, seed=seed, n_rounds=n_rounds)
        cum = pd.concat(batches, ignore_index=True)
        curve = [float(pd.concat(batches[:r], ignore_index=True).Fitness.max()) for r in range(1, len(batches) + 1)]
        curves.append(curve)
        del cum
    return np.asarray(curves, dtype=float)


@st.cache_data(show_spinner="重模拟多 seed 随机基线（选做误差带） …")
def _cached_random_curves(seeds: tuple[int, ...], n_rounds: int) -> np.ndarray:
    return _multi_seed_random_curves(seeds, n_rounds)


def render_campaign_module(metrics: dict) -> None:
    st.subheader("① 四策略对比——同一预算下的累计 top-10 真实 fitness")
    strategies = metrics.get("strategies", {})
    oracle = metrics.get("oracle", "?")
    space = metrics.get("candidate_space_size", 0)
    budget = metrics.get("budget_per_round", 0)
    st.caption(
        f"schema `{metrics.get('schema_version')}` · 冷启动：{metrics.get('cold_start', '?')} · "
        f"oracle：{oracle} · 可测空间 {space:,} / 160,000 · 每轮预算 {budget} · LLM：{metrics.get('llm')}"
    )

    refs = {}
    baseline = load_metrics(str(BASELINE_JSON))
    if baseline and "landscape" in baseline:
        land = baseline["landscape"]
        refs = {"top1pct": land["top1pct_mean"], "max": land["max_fitness"],
                "best": land["best_variant"]}

    with st.expander("选项：随机策略多 seed 误差带（选做）"):
        st.markdown(
            "用 T1 `simulate()` 对随机提名额外重模拟若干 seed（均值 ± 标准差阴影）。"
            "这是**新的只读模拟**，不读取也不覆盖任何 `reports/` 产物；首次开启约多花数秒，之后走缓存。"
        )
        band_on = st.toggle("开启随机误差带", value=False, key="band_on")
    band = None
    if band_on:
        n_rounds = max(len(s.get("rounds", [])) for s in strategies.values())
        seeds = (42, 1, 2, 3, 7, 11)
        curves = _cached_random_curves(seeds, n_rounds)
        if curves.size:
            band = {"mean": curves.mean(axis=0), "std": curves.std(axis=0), "n": len(seeds)}

    fig = _campaign_figure(strategies, refs, band)
    st.pyplot(fig, width='stretch')

    finals = metrics.get("summary", {})
    cols = st.columns(4)
    for col, name in zip(cols, STRATEGY_LABELS):
        with col:
            s = finals.get(name)
            if not s:
                st.metric(STRATEGY_LABELS[name], "—")
                continue
            st.metric(
                STRATEGY_LABELS[name],
                f"{s['final_cum_top10_max']:.3f}",
                delta=f"top10_mean {s['final_cum_top10_mean']:.3f} · 强结合体 {s['final_cum_n_strong']}",
                delta_color="off",
            )

    with st.expander("每轮明细（top10 当轮实测）"):
        name = st.selectbox("策略", list(STRATEGY_LABELS), format_func=STRATEGY_LABELS.get, key="m1_detail")
        rounds = strategies.get(name, {}).get("rounds", [])
        if rounds:
            st.dataframe(
                pd.DataFrame([
                    {k: r.get(k) for k in ("round", "n_nominated", "top10_max", "top10_mean",
                                           "n_hit_beneficial", "cum_top10_max", "cum_top10_mean",
                                           "cum_n_strong", "pool_size_after", "llm_source")}
                    for r in rounds
                ]).set_index("round"),
                width='stretch',
            )
            st.markdown(f"获取函数：`{strategies.get(name, {}).get('acquisition', '')}`")


def _campaign_figure(strategies: dict, refs: dict, band: dict | None):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, muted, grid, surface = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    fig.patch.set_facecolor(surface)
    ax.set_facecolor(surface)
    ax.grid(axis="y", color=grid, lw=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(muted)
    ax.tick_params(colors=muted, labelsize=9)

    if band is not None:
        x = np.arange(1, len(band["mean"]) + 1)
        ax.fill_between(x, band["mean"] - band["std"], band["mean"] + band["std"],
                        color=_strategy_palette()["random"], alpha=0.18, lw=0,
                        label=f"random ±1σ ({band['n']} seeds resimulated)")
    seen_ends: set[float] = set()
    for name, label in FIGURE_LABELS.items():
        rounds = strategies.get(name, {}).get("rounds", [])
        if not rounds:
            continue
        x = [r["round"] for r in rounds]
        y = [r["cum_top10_max"] for r in rounds]
        ax.plot(x, y, color=_strategy_palette()[name], lw=2.2, marker="o", ms=6,
                mec=surface, mew=1.4, label=label, zorder=3)
        end = round(float(y[-1]), 2)
        if end not in seen_ends:  # 并列（如两条 agent 曲线同止于 oracle 上限）只标一次
            seen_ends.add(end)
            ax.annotate(f"{end:.2f}", (x[-1], y[-1]), textcoords="offset points",
                        xytext=(8, -3), fontsize=9, color=ink)

    ax.axhline(1.0, color=muted, lw=1, ls=(0, (4, 3)), zorder=1)
    ax.text(0.99, 1.0, "wild type VDGV = 1.00", color=muted, fontsize=8,
            va="bottom", ha="right", transform=ax.get_yaxis_transform())
    if refs.get("top1pct"):
        ax.axhline(refs["top1pct"], color=muted, lw=1, ls=(0, (1, 3)), zorder=1)
        ax.text(0.99, refs["top1pct"], f"landscape top-1% mean {refs['top1pct']:.2f}",
                color=muted, fontsize=8, va="bottom", ha="right", transform=ax.get_yaxis_transform())
    if refs.get("max"):
        ax.axhline(refs["max"], color=muted, lw=1, ls=(0, (1, 3)), zorder=1)
        ax.text(0.99, refs["max"], f"oracle max {refs['max']:.2f} ({refs.get('best', '')})",
                color=muted, fontsize=8, va="bottom", ha="right", transform=ax.get_yaxis_transform())

    ax.set_xlabel("round (96 nominations each, scored by oracle lookup)", color=muted, fontsize=9)
    ax.set_ylabel("cumulative top-10 max true fitness", color=muted, fontsize=9)
    ax.set_title("Four-strategy sample efficiency on GB1 (same pool & budget)",
                 color=ink, fontsize=12, loc="left")
    ax.legend(loc="upper left", fontsize=8.5, frameon=False, labelcolor=ink)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------- 模块②：五角色推理回放


class _MemoryRecorder:
    """模块③(b) 的同源事件收集器：接口对齐 EventStore.append，但只进内存、不落盘。"""

    def __init__(self) -> None:
        self.events: list[dict] = []

    def append(self, event_type: str, *, round_id: int | None, strategy: str | None,
               actor: str, payload: dict | None = None, ts: str | None = None) -> dict:
        event = {"seq": len(self.events) + 1, "ts": ts or "", "event_type": event_type,
                 "round_id": round_id, "strategy": strategy, "actor": actor,
                 "payload": dict(payload or {}), "prev_hash": "", "hash": ""}
        self.events.append(event)
        return event

    def iter_events(self):
        return iter(self.events)


def attribute_strategies(events: list[dict]) -> list[dict]:
    """给 strategy='agent' 的角色事件标注归属策略（按 campaign 段落的顺序切分）。"""
    attributed, current = [], None
    for event in events:
        item = dict(event)
        if event["event_type"] == "campaign.started":
            current = event["strategy"]
        elif event["event_type"] == "campaign.completed":
            current = None
        if event["strategy"] == "agent" and current:
            item["attributed_strategy"] = current
        attributed.append(item)
    return attributed


def role_chains(events: list[dict]) -> dict[tuple[str, int], dict[str, dict]]:
    """{(strategy, round): {actor: event}}——仅聚合五角色事件。"""
    chains: dict[tuple[str, int], dict[str, dict]] = {}
    for event in events:
        strategy = event.get("attributed_strategy") or event.get("strategy")
        if event["event_type"] == "agent.role.completed":
            chains.setdefault((strategy, int(event["round_id"])), {})[event["actor"]] = event
    return chains


def _chain_status(events: list[dict]) -> str:
    """纯读的哈希链校验（复算 events/store.py 的链式 SHA-256），不写任何文件。"""
    import hashlib

    prev_hash, expected_seq = "", 1
    try:
        for event in events:
            if event.get("seq") != expected_seq:
                raise ValueError(f"chain broken at seq={event.get('seq')}")
            body = {key: event.get(key) for key in ("seq", "ts", "event_type", "round_id",
                                                    "strategy", "actor", "payload")}
            canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            digest = hashlib.sha256((prev_hash + canonical).encode("utf-8")).hexdigest()
            if event.get("prev_hash") != prev_hash or event.get("hash") != digest:
                raise ValueError(f"chain broken at seq={event.get('seq')}")
            prev_hash, expected_seq = event["hash"], expected_seq + 1
    except Exception as exc:  # noqa: BLE001
        return f"哈希链校验 ❌ {exc}"
    return f"哈希链校验 ✅ 通过（{len(events)} 事件）· head `{prev_hash[:16]}…`"


def render_critic(critiques: list[dict]) -> None:
    rejected = [c for c in critiques if not c.get("accepted", True)]
    accepted_n = len(critiques) - len(rejected)
    c1, c2 = st.columns(2)
    c1.metric("Critic 放行", f"{accepted_n} / {len(critiques)}")
    c2.metric("Critic 拒稿", len(rejected))
    if not rejected:
        st.info(
            "本轮 Critic 无拒稿：campaign 中五角色以 `no_knowledge=True` 运行（策略间知识差异由 "
            "acquisition 层的 UCB + BLOSUM62 先验承载），知识规则不在此处拦截。"
            "想在页面上看知识规则「打架」，到模块③勾选「严格知识校验预演」。"
        )
        return
    for c in rejected:
        st.markdown(
            f"🚫 **拒稿** score={c.get('score', float('nan')):.3f} — {c.get('note', '')}"
        )
        checks = c.get("rule_check") or []
        if checks:
            st.dataframe(pd.DataFrame(checks).set_index("rule_id"), width='stretch')


def render_role_chain(chain: dict[str, dict], strategy: str, round_id: int) -> None:
    """渲染一轮五角色推理链（模块②与模块③(b) 共用同一渲染器，保证同源）。"""
    for actor in ROLE_ORDER:
        event = chain.get(actor)
        if event is None:
            continue
        payload = event.get("payload", {})
        icon, label = ROLE_LABELS[actor]
        with st.container(border=True):
            head = f"{icon} **{label}**　`{strategy}` · round {round_id}"
            if actor == "data_analyst":
                st.markdown(head)
                c1, c2 = st.columns([1, 2.2])
                gains = payload.get("position_gains", {})
                with c1:
                    st.caption(f"观测池 {payload.get('n_observations', 0):,} 条")
                    if gains:
                        labeled = {f"{WT[i]}{p}": v for i, (p, v) in enumerate(sorted(gains.items(), key=lambda kv: int(kv[0])))}
                        st.bar_chart(pd.Series(labeled, name="位点平均增益"))
                with c2:
                    subs = payload.get("substitutions", [])
                    st.caption(f"观测到的替换 {len(subs)} 个（展示前 16）")
                    st.markdown("· ".join(f"`{s}`" for s in subs[:16]) or "—")
            elif actor == "hypothesis_generator":
                st.markdown(head)
                st.markdown(f"> {payload.get('rationale', '')}")
                st.markdown("规则依据：" + " · ".join(f"`{r}`" for r in payload.get("rule_ids", [])))
                muts = payload.get("mutations", [])
                st.caption(f"提名替换 {len(muts)} 个（展示前 16）")
                st.markdown("· ".join(f"`{m}`" for m in muts[:16]) or "—")
            elif actor == "mutation_designer":
                cands = payload.get("candidates", [])
                st.markdown(head + f"　— 组合库 {len(cands):,} 个候选")
                if cands:
                    st.dataframe(pd.DataFrame(cands[:12]), width='stretch', hide_index=True)
                    if len(cands) > 12:
                        st.caption(f"… 其余 {len(cands) - 12:,} 个略")
            elif actor == "fitness_evaluator":
                scored = payload.get("candidates", [])
                st.markdown(head + f"　— 模型打分 {len(scored):,} 个")
                if scored:
                    top = sorted(scored, key=lambda c: -c["mean"])[:10]
                    st.dataframe(
                        pd.DataFrame([{"sequence": c["sequence"], "mutations": " ".join(c["mutations"]),
                                       "pred_mean": round(c["mean"], 4), "pred_var": round(c["variance"], 6)}
                                      for c in top]),
                        width='stretch', hide_index=True,
                    )
            elif actor == "scientific_critic":
                st.markdown(head)
                render_critic(payload.get("critiques", []))


def render_replay_module() -> None:
    st.subheader("② 五角色 Agent 思考过程回放——读 T4 事件流（只读）")
    files = {"campaign_events.jsonl（确定性主跑）": str(EVENTS_JSONL),
             "campaign_events_llm.jsonl（LLM 池跑）": str(EVENTS_LLM_JSONL)}
    events = None
    chosen = None
    if EVENTS_JSONL.exists() or EVENTS_LLM_JSONL.exists():
        available = {k: v for k, v in files.items() if Path(v).exists()}
        chosen = st.selectbox("事件流文件", list(available), key="m2_file")
        events = load_events(available[chosen])
    if not events:
        st.warning(
            "未找到 `reports/campaign_events*.jsonl`——先跑 `make campaign` 生成事件流。"
            "本模块占位停等，其余模块不受影响。"
        )
        return

    st.caption(
        f"每行一个 JSON 事件（`seq/ts/event_type/round_id/strategy/actor/payload/prev_hash/hash`）。"
        f"{_chain_status(events)}"
    )
    attributed = attribute_strategies(events)
    chains = role_chains(attributed)
    if not chains:
        st.info("该事件流中没有五角色事件（可能只有 random/greedy 策略）。")
        return

    pairs = sorted(chains.keys())
    strategy_names = sorted({s for s, _ in pairs})
    left, right = st.columns([1, 1])
    with left:
        strategy = st.selectbox("策略", strategy_names, format_func=STRATEGY_LABELS.get, key="m2_strategy")
        rounds = [r for s, r in pairs if s == strategy]
    with right:
        round_id = st.slider("轮次", min(rounds), max(rounds), min(rounds), key="m2_round")
    chain = chains.get((strategy, round_id))
    if not chain:
        st.info("该策略此轮没有五角色事件。")
        return
    render_role_chain(chain, strategy, round_id)

    rejections = []
    for (s, r), ch in chains.items():
        for c in (ch.get("scientific_critic", {}).get("payload", {}) or {}).get("critiques", []):
            if not c.get("accepted", True):
                rejections.append((s, r, c))
    if rejections:
        st.markdown("**全流 Critic 拒稿案例**")
        for s, r, c in rejections[:8]:
            st.markdown(f"- `{s}` round {r}：score={c.get('score')} — {c.get('note', '')}")
    else:
        st.caption("全流扫描：本事件流 Critic 无拒稿记录（原因见上方说明）。")


# ---------------------------------------------------------------- 模块③：实时试玩 + 自动推荐


def render_playground_module() -> None:
    st.subheader("③ 实时试玩——输入变体秒级打分；一键跑一轮 agent 推荐")
    has_landscape = load_landscape() is not None
    has_pool = TRAIN_POOL.exists()
    if not has_pool:
        st.warning("缺少 `data/pools/train_pool.csv`，试玩器停等（打分与推荐都需要模型）。")
        return
    if not has_landscape:
        st.info(
            "未找到 `data/four_mutations_full_data.csv`（46 MB 真值表，不入库）。"
            "打分仍可用（one-hot + Ridge），但**真值校验、分位与自动推荐不可用**。"
        )

    tab_a, tab_b = st.tabs(["(a) 变体打分", "(b) 自动推荐一轮"])

    with tab_a:
        _render_scorer(has_landscape)
    with tab_b:
        if has_landscape:
            _render_recommender()
        else:
            st.info("自动推荐需要真值表（oracle 查表），当前停等。")


def _render_scorer(has_landscape: bool) -> None:
    st.markdown(
        f"输入 4 位点变体（位点 V39/D40/G41/V54，野生型 `{WT}`）→ one-hot 80 维 → "
        "Ridge 集成（`models.train_ladder.RidgePredictor`，在 `data/pools/train_pool.csv` 上拟合）"
        "输出预测 mean/var；有真值表时同时给出真实 fitness 与全表分位。"
    )
    default = st.session_state.get("m3_variant", WT)
    variant = st.text_input("变体（4 个标准氨基酸）", value=default, key="m3_input").strip().upper()
    c1, c2, c3 = st.columns(3)
    c1.caption("试试已知名次：")
    if c2.button("FWAA（全表最高 8.762）"):
        st.session_state["m3_variant"] = "FWAA"
        st.rerun()
    if c3.button("VDGV（野生型）"):
        st.session_state["m3_variant"] = WT
        st.rerun()

    try:
        normalized = validate_variant(variant)
    except ValueError as exc:
        st.error(str(exc))
        return
    if normalized != variant:
        st.session_state["m3_variant"] = normalized

    model, _ = fit_predictor()
    from features.one_hot import encode_one_hot

    mean_arr, var_arr = model.predict(encode_one_hot([normalized]))
    mean, variance = float(mean_arr[0]), float(var_arr[0])

    fitness_sorted, truth = landscape_arrays()
    true_fitness = truth.get(normalized)
    muts = [str(m) for m in variant_to_mutations(normalized)] or ["（无突变 = 野生型）"]
    st.markdown("突变记号：" + " · ".join(f"`{m}`" for m in muts))

    cols = st.columns(4)
    cols[0].metric("预测 mean", f"{mean:.3f}")
    cols[1].metric("预测 var", f"{variance:.2e}")
    if true_fitness is None:
        cols[2].metric("真实 fitness", "—")
        cols[3].metric("全表分位", "—")
        st.warning(
            f"`{normalized}` **不在 149,361 可测空间内**（真值表缺失该组合，属于已知的 10,639 个缺数据）。"
            "以上仅是模型预测，无真值可校验。"
        )
    elif fitness_sorted is not None:
        pct = float((fitness_sorted < true_fitness).mean() * 100)
        rank = int((fitness_sorted > true_fitness).sum()) + 1
        cols[2].metric("真实 fitness", f"{float(true_fitness):.3f}",
                       delta=f"{float(true_fitness) - 1.0:+.3f} vs WT", delta_color="normal")
        cols[3].metric("全表分位", f"{pct:.2f}%", delta=f"排名 #{rank:,} / 149,361", delta_color="off")
        if float(true_fitness) > 1.0:
            st.success(f"真实 fitness {float(true_fitness):.3f} > 1.0，为有益突变。")
        else:
            st.caption(f"真实 fitness {float(true_fitness):.3f} ≤ 1.0，未超野生型。")

    predictor_metrics = load_metrics(str(PREDICTOR_JSON))
    card = ((predictor_metrics or {}).get("one_hot__random", {}) or {}).get("ridge", {})
    if card:
        st.caption(
            "模型卡片（`reports/predictor_metrics.json` · one_hot__random · ridge）："
            f"Spearman {card.get('spearman', float('nan')):.3f} · "
            f"top-1% 命中 {card.get('top_k', float('nan')):.2f} · "
            f"MSE {card.get('mse', float('nan')):.3f}（Ridge 种子间同构，var≈0 属预期）"
        )


def _strict_knowledge_check(variants: list[str]) -> pd.DataFrame | None:
    """只读预演：用知识库规则（no_knowledge=False）复核推荐，展示「打架」案例。不写任何事件。"""
    from knowledge.validators import validate_candidate

    rows = []
    for v in variants:
        muts = [str(m) for m in variant_to_mutations(v)]
        checks = validate_candidate(muts, no_knowledge=False)
        failed = [c for c in checks if not c["pass"]]
        rows.append({"variant": v, "mutations": " ".join(muts) or "WT",
                     "verdict": "🚫 拒稿" if failed else "✅ 放行",
                     "failed_rules": "; ".join(f"{c['rule_id']}（{c['note']}）" for c in failed) or "—"})
    return pd.DataFrame(rows)


def _run_recommendation(strategy: str, budget: int, use_llm: bool):
    """跑一轮四策略 campaign（n_rounds=1）；事件进内存 recorder，绝不落盘。"""
    from evolution.campaign import run_campaign

    df = load_landscape()
    recorder = _MemoryRecorder()
    result = run_campaign(df, n_rounds=1, budget=budget, event_store=recorder, use_llm=use_llm)
    return result, recorder.events


def _render_recommender() -> None:
    st.markdown(
        "复用 T7 `evolution.campaign.run_campaign`（`n_rounds=1`）跑一轮闭环推荐：冷启动池 → "
        "五角色流水线提名 → 模型打分 → acquisition 选 top-k → oracle 查表。"
        "确定性模式秒级出结果；LLM 模式调用自有 API 池（异常自动降级并如实标注 `llm_source`）。"
        "**所有事件只进内存录制器，本看板不向事件流写任何字节。**"
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        strategy = st.radio("策略", ["agent_no_knowledge", "knowledge_agent"],
                            format_func=STRATEGY_LABELS.get, key="m3b_strategy")
    with c2:
        budget = st.slider("本轮预算（提名数）", 12, 96, 48, step=12, key="m3b_budget")
    with c3:
        can_llm = llm_available()
        hint = "" if can_llm else "未检测到 .env（API_KEY），LLM 选项自动禁用"
        use_llm = st.checkbox("用 LLM（较慢，可能降级）", value=False, disabled=not can_llm,
                              help=hint or "Hypothesis Generator 走自有 API 池；失败自动回退确定性路径", key="m3b_llm")
        strict = st.checkbox("严格知识校验预演", value=True,
                             help="对 top-k 逐个跑 knowledge/validators 规则（no_knowledge=False），"
                                  "展示知识库会拦下哪些 agent 提名", key="m3b_strict")

    if st.button("🚀 跑一轮推荐", type="primary", key="m3b_run"):
        with st.spinner("运行中：确定性模式约 3 秒；LLM 模式取决于 API 池时延 …"):
            result, events = _run_recommendation(strategy, budget, use_llm)
        st.session_state["m3b_result"] = result
        st.session_state["m3b_events"] = events
        st.session_state["m3b_key"] = (strategy, budget, use_llm)

    result = st.session_state.get("m3b_result")
    events = st.session_state.get("m3b_events")
    key = st.session_state.get("m3b_key")
    if result is None:
        st.caption("点击上方按钮开始（尚未运行）。")
        return
    if key and key[0] != strategy:
        st.info("左侧策略已切换，重新点击「跑一轮推荐」查看该策略结果。")

    chosen = result["strategies"][key[0]]
    rounds = chosen.get("rounds", [])
    if not rounds:
        st.warning("该策略本轮没有产出（候选耗尽）。")
        return
    payload = rounds[0]
    llm_source = payload.get("llm_source", "deterministic")
    st.success(
        f"完成：提名 {payload['n_nominated']} 个 · 当轮 top10_max {payload['top10_max']:.3f} · "
        f"累计 top10_max {payload['cum_top10_max']:.3f} · `llm_source={llm_source}`"
    )
    if use_llm and llm_source == "fallback":
        st.warning("本轮 LLM 调用失败，已降级到确定性路径（llm_source=fallback）。")

    # 预测（角色事件里的模型分）与 oracle 真值对照
    pred = {}
    for event in events:
        if event["event_type"] == "agent.role.completed" and event["actor"] == "fitness_evaluator":
            pred = {c["sequence"]: (c["mean"], c["variance"]) for c in event["payload"]["candidates"]}
            break
    rows = []
    for variant, true_fitness in payload.get("top10", []):
        p_mean, p_var = pred.get(variant, (None, None))
        rows.append({"variant": variant, "真实 fitness": round(float(true_fitness), 3),
                     "预测 mean": round(p_mean, 3) if p_mean is not None else "—",
                     "预测 var": f"{p_var:.1e}" if p_var is not None else "—"})
    st.markdown(f"**Top-10 推荐突变方案**（获取函数：{chosen.get('acquisition', '')}）")
    st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)

    if strict:
        st.markdown("**严格知识校验预演**（只读复核，不写事件流）")
        st.dataframe(_strict_knowledge_check([v for v, _ in payload.get("top10", [])]),
                     width='stretch', hide_index=True)

    st.markdown("**本轮五角色推理链**（与模块②同一渲染器；事件来自内存录制器）")
    chains = role_chains(attribute_strategies(events))
    chain = chains.get((key[0], payload["round"]))
    if chain:
        render_role_chain(chain, key[0], payload["round"])


# ---------------------------------------------------------------- 入口


def main() -> None:
    st.title("🧬 GB1 蛋白定向进化 · 科学智能体看板")
    st.markdown(
        "四策略闭环对比 + 五角色 Agent 思考回放 + 实时试玩。数据：GB1 四位点组合空间"
        "（V39/D40/G41/V54，野生型 `VDGV`），真值表 149,361 / 160,000。"
    )
    st.caption(
        "本看板**只读**消费 T7/T4/T3 产物（`@st.cache_data` / `@st.cache_resource`），"
        "不写事件流、不覆盖 `reports/`。运行：`streamlit run app/demo.py`（或 `make demo`）。"
    )

    tab1, tab2, tab3 = st.tabs(["① 四策略对比", "② Agent 思考回放", "③ 实时试玩"])
    with tab1:
        available = {label: p for label, p in REGIMES.items() if p.exists()}
        if not available:
            st.warning("未找到 campaign 指标——先跑 `make campaign`（或 `python -m evolution.campaign --cold-start low_hd`）。本模块占位停等。")
        else:
            label = st.radio("冷启动设定（GB1 本身可解，故对比重点是样本效率与批次产出，而非能否达峰）",
                             list(available), horizontal=True, key="regime")
            metrics = load_metrics(str(available[label]))
            render_campaign_module(metrics)
    with tab2:
        render_replay_module()
    with tab3:
        render_playground_module()

    st.divider()
    st.caption(
        "ai4s-directed-evolution-agent · T8 demo · 上游：T7 campaign / T4 事件流 / T3 Ridge 预测器"
    )


if __name__ == "__main__":
    main()
