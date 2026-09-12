"""GB1 定向进化看板（T8 可交互 demo）——单文件、只读消费上游产物。

五个模块（对应题目「可交互 demo」「结果分析与展示」加分项 + 「输入野生型序列后自动推荐突变方案」）：
  ① 四策略对比    读 reports/campaign_metrics.json（T7 产出，schema t7.v2）。
  ② 五角色回放    读 reports/campaign_events*.jsonl（T4 事件流，带 SHA-256 哈希链）。
  ③ 实时试玩      one-hot + Ridge（T3 模型）秒级打分；一键跑一轮 agent 推荐复用
                  evolution.campaign.run_campaign（事件只进内存录制器，供模块②同源展示）。
  ④ 位点集中 & 组合理由  读 workflow-v1.1 的 campaign_easy.metrics.json（topk_concentration）
                  与 agent_combination_rationales.json（证据/叙事来源分开标注）。
  ⑤ 阶数·保守性·alpha    读 analysis-v0.1 的 mutation_order/conservation 与 workflow-v1.0 的
                  predictor_alpha_sweep / scaling ablation；口径限制（同阶留出高估、
                  保守性是未接入筛选的自然度先验、固定 alpha 的预处理反转）原样展示。

纪律：本看板全程只读——@st.cache_data / @st.cache_resource 缓存加载，
绝不 append 事件流、绝不覆盖 reports/ 下任何产物；模块③(b) 的推荐事件
收集在内存 recorder 中，不落盘。任一数据文件缺失时对应面板给出
「缺哪个文件 + 跑哪条命令」的明确提示，不静默空白。运行：streamlit run app/demo.py（或 make demo）。
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

from agent.llm import llm_config  # noqa: E402
from evolution.mutations import validate_variant  # noqa: E402

from evolution.results_layout import report_dir, run_dir  # noqa: E402
_GB1 = run_dir("workflow", "gb1", create=False)
METRICS_JSON = _GB1 / "campaign_easy.metrics.json"
METRICS_LLM_JSON = _GB1 / "campaign_llm.metrics.json"
# Three honest cold-start regimes (see report ch.6/7). Default view = the hard
# extrapolation regime, so the demo does not lead with the "easy" (data-rich) result.
REGIMES = {
    "hard · 低阶外推 (HD≤2 冷启动，推荐)": _GB1 / "campaign_hard.metrics.json",
    "easy · 随机池 (≈98% HD≥3，数据充裕)": _GB1 / "campaign_easy.metrics.json",
    "sparse · 极稀疏 (仅 77 个单突变)": _GB1 / "campaign_sparse.metrics.json",
}
EVENTS_JSONL = _GB1 / "campaign_easy.events.jsonl"
EVENTS_LLM_JSONL = _GB1 / "campaign_llm.events.jsonl"
BASELINE_JSON = _GB1 / "random_baseline.metrics.json"
PREDICTOR_JSON = _GB1 / "predictor_ladder.json"
TRAIN_POOL = ROOT / "data" / "pools" / "train_pool.csv"
LANDSCAPE_CSV = ROOT / "data" / "four_mutations_full_data.csv"

# ---- 模块④⑤（分析面板）的数据源：全部只读，见 harness/reports/ 的版本化产物树 ----
RATIONALES_JSON = report_dir("workflow") / "agent_combination_rationales.json"
ANALYSIS_DIR = {ds: run_dir("analysis", ds, create=False) for ds in ("gb1", "aav")}
_V10_GB1 = run_dir("workflow", "gb1", version="v1.0", create=False)
ALPHA_SWEEP_JSON = _V10_GB1 / "predictor_alpha_sweep.json"
SCALING_ABLATION_JSON = _V10_GB1 / "predictor_ladder_scaling_ablation.json"
# 数据缺失时的诚实降级提示：缺哪个文件、跑哪条命令能补回（阳极性对照由 tests 验证）
HINTS = {
    "metrics": "先跑 `make campaign`（即 `python evolution/campaign.py`）重新生成。",
    "rationales": "该快照捕获自 `make campaign` 五角色事件流里 mutation_designer 的 "
                  "`agent.role.completed` 事件（产出代码见 `agent/pipeline.py`；本快照由 commit "
                  "`ed3b4f2` 固定入库）。",
    "mutation_order": "先跑 `PYTHONPATH=. python analysis/mutation_order.py` 重新生成。",
    "conservation": "先跑 `PYTHONPATH=. python features/conservation.py --dataset {ds} "
                    "--data <对应 DMS 真值表 csv> --output-dir harness/reports/analysis-v0.1` 重新生成。",
    "alpha_sweep": "先跑 `python -m models.alpha_sweep` 重新生成（该文件存档于 workflow-v1.0 周期目录）。",
    "scaling": "先跑 `python -m models.evaluate_all` 重新生成（该文件存档于 workflow-v1.0 周期目录）。",
}

REFERENCE_WT = "VDGV"  # GB1 dataset reference at V39 / D40 / G41 / V54
MUTABLE_POSITIONS = (39, 40, 41, 54)
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
    # 随机基线在产物里有两处数字:summary.* 是 seed 42 单次,strategies.random.multi_seed
    # 是 5 个 seed 的均值±标准差。三个 regime 的单 seed 值看起来有明显大小关系,而多 seed
    # 统计显示它们在 ±1σ 内完全重叠——引单 seed 会读出一个统计上不存在的趋势(fact
    # F-6394AB50)。指标卡默认展示的就是读者会引用的数字,所以这里对随机基线直接把均值±σ
    # 标出来,不把它藏在「选做」开关后面。
    random_multi = strategies.get("random", {}).get("multi_seed") or {}
    random_last = (random_multi.get("rounds") or [{}])[-1]
    cols = st.columns(4)
    for col, name in zip(cols, STRATEGY_LABELS):
        with col:
            s = finals.get(name)
            if not s:
                st.metric(STRATEGY_LABELS[name], "—")
                continue
            caption = (f"top10_mean {s['final_cum_top10_mean']:.3f} · "
                       f"强结合体 {s['final_cum_n_strong']}")
            if name == "random" and random_last.get("cum_top10_max_std") is not None:
                caption = (f"{random_multi.get('n_runs', '?')} seed 均值 "
                           f"{random_last['cum_top10_max_mean']:.3f} ± "
                           f"{random_last['cum_top10_max_std']:.3f} · "
                           f"上方数字是 seed 42 单次")
            st.metric(STRATEGY_LABELS[name], f"{s['final_cum_top10_max']:.3f}",
                      delta=caption, delta_color="off")
    if random_last.get("cum_top10_max_std") is not None:
        st.caption(
            "口径:随机基线请引用 "
            f"**{random_multi.get('n_runs', '?')} seed 均值 "
            f"{random_last['cum_top10_max_mean']:.3f} ± {random_last['cum_top10_max_std']:.3f}**,"
            "不要引卡片上那个 seed 42 单次值——三个 regime 的单 seed 值看似有大小关系,"
            "而多 seed 统计显示它们在 ±1σ 内重叠,并无差异。"
            "其余三个策略目前只有单 seed(42),策略之间的差值没有误差棒。"
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
            "本轮 Critic 无拒稿。注意两条策略在这里的行为并不相同：策略③ agent_no_knowledge 以 "
            "`no_knowledge=True` 运行，知识规则被消融掉、确实不在此处拦截；策略④ knowledge_agent 以 "
            "`no_knowledge=False` 运行，知识规则在此处**是生效的**，只是本轮恰好没有候选被拒。"
            "两者的差异还额外体现在 acquisition 层（④ 有 UCB + BLOSUM62 先验）。"
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
                        labeled = {f"{REFERENCE_WT[i]}{p}": v for i, (p, v) in enumerate(sorted(gains.items(), key=lambda kv: int(kv[0])))}
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


def relative_mutations(variant: str, wild_type: str) -> tuple[str, ...]:
    """Describe a four-site variant relative to the WT entered in this demo."""
    normalized_variant = validate_variant(variant)
    normalized_wt = validate_variant(wild_type)
    return tuple(
        f"{source}{position}{target}"
        for source, position, target in zip(normalized_wt, MUTABLE_POSITIONS, normalized_variant)
        if source != target
    )


def single_mutant_candidates(wild_type: str) -> tuple[str, ...]:
    """The input-dependent menu: every one-step substitution from this WT."""
    from evolution.mutations import AMINO_ACIDS

    normalized_wt = validate_variant(wild_type)
    return tuple(
        normalized_wt[:site] + residue + normalized_wt[site + 1:]
        for site, source in enumerate(normalized_wt)
        for residue in AMINO_ACIDS
        if residue != source
    )


def recommend_from_wild_type(wild_type: str, predictor, *, top_k: int = 10) -> list[dict]:
    """Score the input WT's one-step menu with the existing one-hot Ridge model.

    This deliberately does not use the campaign oracle: the displayed values are
    predictions, so a WT absent from the measured landscape is never presented as
    experimentally grounded.
    """
    from features.one_hot import encode_one_hot

    normalized_wt = validate_variant(wild_type)
    candidates = single_mutant_candidates(normalized_wt)
    means, variances = predictor.predict(encode_one_hot(candidates))
    wt_mean = float(predictor.predict(encode_one_hot([normalized_wt]))[0][0])
    ranked = sorted(zip(candidates, means, variances), key=lambda row: (-float(row[1]), row[0]))[:top_k]
    return [
        {"variant": variant, "mutations": relative_mutations(variant, normalized_wt),
         "predicted_fitness": float(mean), "predicted_variance": float(variance),
         "predicted_gain_vs_wt": float(mean) - wt_mean}
        for variant, mean, variance in ranked
    ]


def recommendation_disclaimer(wild_type: str, observed_variants: set[str]) -> str:
    """Honest label for recommendations; never imply an unmeasured WT was assayed."""
    normalized_wt = validate_variant(wild_type)
    if normalized_wt not in observed_variants:
        return f"`{normalized_wt}` 无实测基准；以下推荐的 fitness 为**模型预测值而非实测值**。"
    return "以下推荐的 fitness 为**模型预测值，不是实测结果**。"


def render_playground_module() -> None:
    st.subheader("③ 实时试玩——输入野生型后自动推荐突变方案")
    has_landscape = load_landscape() is not None
    has_pool = TRAIN_POOL.exists()
    if not has_pool:
        st.warning("缺少 `data/pools/train_pool.csv`，试玩器停等（打分与推荐都需要模型）。")
        return
    if not has_landscape:
        st.info(
            "未找到 `data/four_mutations_full_data.csv`（46 MB 真值表，不入库）。"
            "打分与模型推荐仍可用（one-hot + Ridge），但没有真值校验和分位。"
        )

    raw_wild_type = st.text_input("野生型（4 个标准氨基酸，V39/D40/G41/V54）",
                                  value=st.session_state.get("m3_wt", REFERENCE_WT), key="m3_wt_input")
    try:
        wild_type = validate_variant(raw_wild_type)
    except ValueError as exc:
        st.error(f"野生型输入无效：{exc}")
        return
    st.session_state["m3_wt"] = wild_type
    _, truth = landscape_arrays()
    disclaimer = recommendation_disclaimer(wild_type, set(truth))
    if wild_type not in truth:
        st.warning(disclaimer)
    else:
        st.caption(disclaimer)

    tab_a, tab_b = st.tabs(["(a) 变体打分", "(b) 自动推荐一轮"])

    with tab_a:
        _render_scorer(has_landscape, wild_type)
    with tab_b:
        _render_recommender(wild_type, has_landscape)


def _render_scorer(has_landscape: bool, wild_type: str) -> None:
    st.markdown(
        f"输入 4 位点变体（位点 V39/D40/G41/V54，当前野生型 `{wild_type}`）→ one-hot 80 维 → "
        "Ridge 集成（`models.train_ladder.RidgePredictor`，在 `data/pools/train_pool.csv` 上拟合）"
        "输出预测 mean/var；有真值表时同时给出真实 fitness 与全表分位。"
    )
    default = st.session_state.get("m3_variant", wild_type)
    variant = st.text_input("变体（4 个标准氨基酸）", value=default, key="m3_input").strip().upper()
    c1, c2, c3 = st.columns(3)
    c1.caption("试试已知名次：")
    if c2.button("FWAA（全表最高 8.762）"):
        st.session_state["m3_variant"] = "FWAA"
        st.rerun()
    if c3.button("VDGV（野生型）"):
        st.session_state["m3_variant"] = wild_type
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
    muts = list(relative_mutations(normalized, wild_type)) or ["（无突变 = 野生型）"]
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
        wt_fitness = truth.get(wild_type)
        cols[2].metric("真实 fitness", f"{float(true_fitness):.3f}",
                       delta=(f"{float(true_fitness) - float(wt_fitness):+.3f} vs 输入 WT"
                              if wt_fitness is not None else "输入 WT 无实测基准"), delta_color="normal")
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


def _strict_knowledge_check(variants: list[str], wild_type: str) -> pd.DataFrame | None:
    """只读预演：用知识库规则（no_knowledge=False）复核推荐，展示「打架」案例。不写任何事件。"""
    if wild_type != REFERENCE_WT:
        return pd.DataFrame([{
            "variant": "—", "mutations": "—", "verdict": "未运行",
            "failed_rules": "现有知识规则锚定标准 GB1 WT VDGV；自定义 WT 仅展示 Ridge 模型预测。",
        }])
    from knowledge.validators import validate_candidate

    rows = []
    for v in variants:
        muts = list(relative_mutations(v, wild_type))
        checks = validate_candidate(muts, no_knowledge=False)
        failed = [c for c in checks if not c["pass"]]
        rows.append({"variant": v, "mutations": " ".join(muts) or "输入 WT",
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


def _render_recommender(wild_type: str, has_landscape: bool) -> None:
    st.markdown(
        "以当前输入 WT 为中心枚举 76 个**单点**替换，用现有 one-hot Ridge 逐个打分并取 Top-k。"
        "因此候选菜单、突变记号与“相对 WT 增益”都会随输入重算。表中的 fitness **均为模型预测值，不是实测结果**。"
        "标准 `VDGV` 时额外复用 T7 `evolution.campaign.run_campaign` 跑一轮内存闭环以展示五角色回放；"
        "该内核尚不接受自定义 WT 参数，故不会把其标准 WT oracle 结果冒充为自定义 WT 的实验结果。"
        "**所有事件只进内存 recorder，本看板不向事件流写任何字节。**"
    )
    c1, c2 = st.columns(2)
    with c1:
        top_k = st.slider("推荐数量（Top-k）", 3, 20, 10, key="m3b_top_k")
    with c2:
        strict = st.checkbox("严格知识校验预演", value=True,
                             help="标准 VDGV 时对 Top-k 跑 knowledge/validators；自定义 WT 不套用固定 WT 规则。",
                             key="m3b_strict")

    if st.button("🚀 自动推荐", type="primary", key="m3b_run"):
        with st.spinner("用已缓存的 Ridge 对当前 WT 的单点菜单打分 …"):
            recommendations = recommend_from_wild_type(wild_type, fit_predictor()[0], top_k=top_k)
            trace = None
            if wild_type == REFERENCE_WT and has_landscape:
                # The campaign's standard-GB1 trace is useful provenance, but its
                # oracle fitness is deliberately kept out of the prediction table.
                trace = _run_recommendation("knowledge_agent", max(12, top_k), False)
        st.session_state["m3b_recommendations"] = recommendations
        st.session_state["m3b_trace"] = trace
        st.session_state["m3b_key"] = (wild_type, top_k)

    recommendations = st.session_state.get("m3b_recommendations")
    trace = st.session_state.get("m3b_trace")
    key = st.session_state.get("m3b_key")
    if recommendations is None:
        st.caption("点击上方按钮开始（尚未运行）。")
        return
    if key != (wild_type, top_k):
        st.info("野生型或 Top-k 已变更，重新点击「自动推荐」更新结果。")
        return
    st.success(f"完成：已对 `{wild_type}` 的 76 个单点候选打分，以下为预测 Top-{top_k}。")
    rows = [{"推荐变体": row["variant"], "相对输入 WT 的突变": " ".join(row["mutations"]),
             "预测 fitness（非实测）": round(row["predicted_fitness"], 3),
             "预测增益 vs 输入 WT": round(row["predicted_gain_vs_wt"], 3),
             "预测 var": f"{row['predicted_variance']:.1e}"}
            for row in recommendations]
    st.markdown(f"**Top-{top_k} 推荐突变方案（模型预测，非实测）**")
    st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)

    if strict:
        st.markdown("**严格知识校验预演**（只读复核，不写事件流）")
        st.dataframe(_strict_knowledge_check([r["variant"] for r in recommendations], wild_type),
                     width='stretch', hide_index=True)

    if trace is not None:
        result, events = trace
        st.markdown("**标准 VDGV 的单轮五角色闭环追踪**（事件来自内存 recorder）")
        chain = role_chains(attribute_strategies(events)).get(("knowledge_agent", 1))
        if chain:
            render_role_chain(chain, "knowledge_agent", 1)


# ---------------------------------------------------------------- 模块④⑤：分析面板（只读展示上游产物）


def _missing_artifact(path: Path, how_to_regenerate: str) -> bool:
    """诚实降级：缺文件给明确提示（哪个文件 + 哪条命令），不静默空白。

    存在性检查刻意放在 @st.cache_data 之外——改名做阳性对照时，
    即使同一进程里该路径曾命中缓存，也能立刻看到降级提示。
    """
    if path.exists():
        return False
    st.warning(f"缺数据文件 `{path.relative_to(ROOT)}`——{how_to_regenerate} 本面板停等，其余面板不受影响。")
    return True


def _analysis_axes(nrows: int = 1, ncols: int = 1, figsize: tuple[float, float] = (10.5, 4.2)):
    """分析面板共用的 matplotlib 底版（图表内文字用英文，避免评测机缺中文字体）。"""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, muted, grid, surface = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    fig.patch.set_facecolor(surface)
    flat = np.atleast_1d(axes).ravel() if nrows * ncols > 1 else axes
    for ax in np.atleast_1d(axes).ravel():
        ax.set_facecolor(surface)
        ax.grid(axis="y", color=grid, lw=0.8)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color(muted)
        ax.tick_params(colors=muted, labelsize=8)
    return fig, flat, ink, muted


def render_concentration_panel() -> None:
    """④-a 推荐突变是否集中在关键位点：按策略 × 位点展示 top-k 残基分布。"""
    st.markdown("#### ④-a 推荐突变是否集中在关键位点——top-k 残基集中度")
    st.caption(
        "数据源：`harness/reports/workflow-v1.1/gb1/campaign_easy.metrics.json` 的 "
        "`strategies.<策略>.topk_concentration`（easy 档 · 随机池冷启动）。只读展示，数字均为 JSON 原字段。"
    )
    if _missing_artifact(METRICS_JSON, HINTS["metrics"]):
        return
    metrics = load_metrics(str(METRICS_JSON)) or {}
    available = [name for name in STRATEGY_LABELS
                 if (metrics.get("strategies", {}).get(name, {}) or {}).get("topk_concentration")]
    if not available:
        st.warning("`campaign_easy.metrics.json` 中没有任何 `topk_concentration` 字段——该统计是后加的，请用带它的 campaign 版本重跑。")
        return

    default = available.index("knowledge_agent") if "knowledge_agent" in available else 0
    strategy = st.selectbox("策略", available, index=default, format_func=STRATEGY_LABELS.get, key="m4a_strategy")
    tc = metrics["strategies"][strategy]["topk_concentration"]
    st.caption(f"`n_topk_observations` = {tc.get('n_topk_observations')}（该策略累计 top-k 观测数，JSON 原字段）")

    cols = st.columns(4)
    for col, (pos, wt) in zip(cols, zip(("39", "40", "41", "54"), "VDGV")):
        info = tc["positions"].get(pos, {})
        with col:
            st.markdown(f"**{wt}{pos}**（WT 残基 `{wt}`）")
            counts = info.get("residue_counts", {})
            if counts:
                st.bar_chart(pd.Series(counts, name="residue count in top-k"))
            st.caption(
                f"dominant_residue `{info.get('dominant_residue')}` · "
                f"dominant_fraction `{info.get('dominant_fraction')}` · "
                f"mutation_fraction `{info.get('mutation_fraction')}`"
            )

    rows = []
    for name in available:
        t = metrics["strategies"][name]["topk_concentration"]
        for pos, wt in zip(("39", "40", "41", "54"), "VDGV"):
            info = t["positions"].get(pos, {})
            rows.append({
                "strategy": name,
                "position": f"{wt}{pos}",
                "dominant_residue": info.get("dominant_residue"),
                "dominant_fraction": info.get("dominant_fraction"),
                "mutation_fraction": info.get("mutation_fraction"),
                "residue_counts": " ".join(f"{k}:{v}" for k, v in (info.get("residue_counts") or {}).items()),
            })
    st.markdown("**四策略 × 四位点对照（字段名与 JSON 一致）**")
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.caption(
        "读法：dominant_fraction 高 = 该策略 top-k 在此位点集中于单一残基；"
        "mutation_fraction = top-k 中该位点偏离 WT 的比例。这直接回答试题「推荐突变是否集中在关键位点」。"
    )


def render_rationales_panel() -> None:
    """④-b 为什么组合某些突变：实测增益（evidence）与叙事（narrative）分开标注。"""
    st.markdown("#### ④-b 为什么组合这些突变——组合理由与实测增益")
    st.caption("数据源：`harness/reports/workflow-v1.1/agent_combination_rationales.json`（workflow-v1.1 周期捕获）。")
    if _missing_artifact(RATIONALES_JSON, HINTS["rationales"]):
        return
    data = load_metrics(str(RATIONALES_JSON)) or {}
    prov = data.get("provenance", {})
    st.caption(f"事件：`{data.get('event_type')}` · actor `{data.get('actor')}` · round {data.get('round_id')}")

    rationales = data.get("combination_rationales", [])
    narrative_sources = sorted({str(r.get("narrative_source")) for r in rationales})
    llm_text = prov.get("llm_generated_text")
    if narrative_sources == ["deterministic"]:
        st.info(
            "**证据与叙事分开看**：`evidence_source`（实测统计量从哪来）与 `narrative_source`（那句解释由谁生成）"
            f"是两个独立字段。本快照 narrative_source=`deterministic`、provenance.llm_generated_text=`{llm_text}`——"
            "**下面的组合理由是代码生成的确定性叙事，不是 LLM 推理**，不得当作 LLM 能力展示。"
        )
    else:
        st.info(
            f"evidence_source 与 narrative_source 分列展示（本文件 narrative_source 集合 = {narrative_sources}）。"
            "叙事为 LLM 生成时会如实标注，fallback 的理由不会冒充 LLM 推理。"
        )

    measured = data.get("measured_rows", [])
    if measured:
        st.markdown("**实测行（`measured_rows`，组合依据的原始观测）**")
        st.dataframe(
            pd.DataFrame([{"mutations": " ".join(r.get("mutations", [])), "fitness": r.get("fitness")}
                          for r in measured]),
            width="stretch", hide_index=True,
        )

    if not rationales:
        st.warning("`combination_rationales` 为空——没有任何组合理由可展示。")
        return
    st.markdown("**组合候选（`combination_rationales`）**")
    st.dataframe(
        pd.DataFrame([{
            "组合": " + ".join(r.get("selected_single_mutations", [])),
            "empirical_position_gains": "; ".join(f"pos{k}={v:.3f}" for k, v in (r.get("empirical_position_gains") or {}).items()),
            "positions_non_conflicting": "✅" if r.get("positions_non_conflicting") else "❌",
            "rule_ids": " ".join(r.get("rule_ids", [])),
            "evidence_source": r.get("evidence_source"),
            "narrative_source": r.get("narrative_source"),
        } for r in rationales]),
        width="stretch", hide_index=True,
    )
    for r in rationales:
        st.markdown(
            f"> **`{' + '.join(r.get('selected_single_mutations', []))}`**：{r.get('deterministic_summary', '')}\n\n"
            f"`evidence_source=`{r.get('evidence_source')}` · `narrative_source=`{r.get('narrative_source')}`"
        )


def render_mutation_order_panel() -> None:
    """⑤-a 单点/双点/多点突变对比：四层分析（分布/加性外推/上位/低阶覆盖）。"""
    st.markdown("#### ⑤-a 单点 / 双点 / 多点突变的优化效果——突变阶数分析")
    ds_labels = {"aav": "AAV（28 aa，阶数 0–28，加分项③主证据）", "gb1": "GB1（四位点，阶数 0–4）"}
    ds = st.selectbox("数据集", ("aav", "gb1"), index=0, format_func=ds_labels.get, key="m5a_ds")
    path = ANALYSIS_DIR[ds] / "mutation_order.json"
    st.caption(f"数据源：`harness/reports/analysis-v0.1/{ds}/mutation_order.json`（只读分析线，不跑新实验）。")
    if _missing_artifact(path, HINTS["mutation_order"]):
        return
    d = load_metrics(str(path)) or {}
    st.caption(
        f"`{d.get('dataset')}` · 可测变体 {d.get('n_measured_variants'):,} · "
        f"WT `{d.get('wt_sequence')}` · wt_fitness `{d.get('wt_fitness')}`"
    )

    st.markdown("**① 各阶分布（`distribution_by_order`，全部实测）**")
    dist = pd.DataFrame([
        {"order": int(k), **{kk: vv for kk, vv in v.items() if kk != "source"}}
        for k, v in (d.get("distribution_by_order") or {}).items()
    ]).set_index("order").sort_index()
    st.dataframe(dist, width="stretch")

    st.markdown("**② 加性外推（`additive_extrapolation`）：只用 ≤k 阶训练，外推 k+1 阶**")
    rows = []
    for r in d.get("additive_extrapolation", []):
        by_alpha = r.get("validation_spearman_by_alpha", {})
        alpha = r.get("alpha_selected")
        val = by_alpha.get(str(alpha), by_alpha.get(float(alpha), float("nan")))
        rows.append({
            "train_orders": r.get("train_orders"), "test_order": r.get("test_order"),
            "n_train": r.get("n_train"), "n_test": r.get("n_test"),
            "alpha_selected": alpha,
            "validation_spearman@selected": round(float(val), 4),
            "test_spearman": round(float(r.get("test_spearman", float("nan"))), 4),
        })
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    for r in d.get("additive_extrapolation", []):
        if str(r.get("train_orders")) != "0..2" or r.get("test_order") != 3:
            continue
        by_alpha = r.get("validation_spearman_by_alpha", {})
        alpha = r.get("alpha_selected")
        val = by_alpha.get(str(alpha), by_alpha.get(float(alpha), float("nan")))
        st.warning(
            f"⚠️ 跨阶外推被系统性高估（`{ds}` 的 0..2→3 行）：**留出验证 {float(val):.4f} vs 测试 "
            f"{float(r.get('test_spearman', float('nan'))):.4f}**。留出集是从**同阶**训练数据里切出来的，"
            "只反映阶内拟合，不反映跨阶外推；alpha 也是在这个同阶留出上选的，救不了这个落差。"
        )

    st.markdown("**③ 上位效应（`epistasis_by_order`：observed − (WT + Σ 实测单点效应)）**")
    epi = pd.DataFrame([
        {"order": int(k),
         **{kk: vv for kk, vv in v.items() if kk not in ("source", "strongest_positive", "strongest_negative")}}
        for k, v in (d.get("epistasis_by_order") or {}).items()
    ]).set_index("order").sort_index()
    st.dataframe(epi, width="stretch")

    st.markdown("**④ 低阶完整覆盖率（`lower_order_coverage_by_order`）——高阶峰为什么学不到**")
    cov_rows = pd.DataFrame([
        {"order": int(k), "n_variants": v.get("n_variants"), "n_complete": v.get("n_complete"),
         "complete_fraction": v.get("complete_fraction"), "mean_subset_coverage": v.get("mean_subset_coverage")}
        for k, v in (d.get("lower_order_coverage_by_order") or {}).items()
    ]).set_index("order").sort_index()
    st.dataframe(cov_rows, width="stretch")
    fig, ax, ink, muted = _analysis_axes(figsize=(10.5, 3.6))
    ax.bar(cov_rows.index, cov_rows["complete_fraction"], color="#2a78d6", alpha=0.85)
    ax.set_xlabel("mutation order", color=muted, fontsize=9)
    ax.set_ylabel("complete_fraction", color=muted, fontsize=9)
    ax.set_title("Lower-order completeness collapses with order (why high-order peaks are unlearnable)",
                 color=ink, fontsize=11, loc="left")
    fig.tight_layout()
    st.pyplot(fig, width="stretch")
    cov = d.get("lower_order_coverage_by_order") or {}
    if all(str(k) in cov for k in (2, 3, 4)):
        st.warning(
            f"低阶支撑塌方（`{ds}`）：complete_fraction 2 阶 **{cov[str(2)]['complete_fraction']:.3f}** → "
            f"3 阶 **{cov[str(3)]['complete_fraction']:.3f}** → 4 阶 **{cov[str(4)]['complete_fraction']:.3f}**。"
            "高阶变体几乎找不到完整的低阶组合支撑，其组合效应只能靠外推——这是高阶真峰难学的结构性原因。"
        )

    peak = d.get("aav_peak_posthoc")
    if peak:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("真峰 order", peak.get("order"))
        c2.metric("observed_fitness", f"{float(peak.get('observed_fitness', float('nan'))):.3f}")
        c3.metric("additive_prediction", f"{float(peak.get('additive_prediction', float('nan'))):.3f}")
        c4.metric("epistasis_residual", f"{float(peak.get('epistasis_residual', float('nan'))):.3f}")
        loc = peak.get("lower_order_coverage", {})
        st.caption(
            f"真峰 `{peak.get('sequence')}` 的 lower_order_coverage：{loc.get('n_measured')} / {loc.get('n_required')} "
            f"(fraction `{loc.get('fraction')}`，缺 `{', '.join(loc.get('missing_sequences', []))}`)"
        )


def render_conservation_panel() -> None:
    """⑤-b 保守位点：ESM-2 熵 × 实测效应，负结果口径原样展示。"""
    st.markdown("#### ⑤-b 保守位点分析——ESM-2 逐位置熵 vs 实测效应（负结果）")
    st.warning(
        "**口径（必读）**：ESM-2 熵是**自然度先验**，仅用于事后分析，**未接入采集或筛选路径**。"
        "本仓真峰已被证明是反自然的；若把「避开保守位点」当门禁，会先把真峰组成位点挡掉（见下方名次）。"
    )
    ds_labels = {"aav": "AAV（28 aa，有真峰位点记录）", "gb1": "GB1（56 aa，四位点组合空间）"}
    ds = st.selectbox("数据集", ("aav", "gb1"), index=0, format_func=ds_labels.get, key="m5b_ds")
    path = ANALYSIS_DIR[ds] / "conservation.json"
    st.caption(f"数据源：`harness/reports/analysis-v0.1/{ds}/conservation.json`（只读分析线）。")
    if _missing_artifact(path, HINTS["conservation"].format(ds=ds)):
        return
    c = load_metrics(str(path)) or {}
    st.caption(f"模型 `{c.get('model')}` · {c.get('entropy_definition')}")

    positions = c.get("positions", [])
    peaks = c.get("true_peak_positions") or []
    # 真峰突变记号（D0Q/V18A/S17E）的数字是 0-based 位点，与 conservation-report.md 一致；
    # 按 JSON 自带的 position_zero_based 键映射，名次/熵等数字全部取自 JSON 原字段。
    peak_names = {0: "D0Q", 18: "V18A", 17: "S17E"}

    def _peak_label(p: dict) -> str:
        return peak_names.get(p.get("position_zero_based"), f"pos {p.get('position')}")

    fig, ax, ink, muted = _analysis_axes(figsize=(10.5, 3.8))
    ax.plot([p["position"] for p in positions], [p["entropy_nats"] for p in positions],
            color="#52514e", lw=1.6)
    if peaks:
        ax.scatter([p["position"] for p in peaks], [p["entropy_nats"] for p in peaks],
                   color="#eb6834", s=64, zorder=3, label="true peak positions")
        for p in peaks:
            ax.annotate(f"{_peak_label(p)} (rank {p['conservation_rank']})",
                        (p["position"], p["entropy_nats"]), textcoords="offset points",
                        xytext=(6, 8), fontsize=8.5, color="#eb6834")
        ax.legend(fontsize=8.5, frameon=False, labelcolor=ink)
    ax.set_xlabel("sequence position (1-based)", color=muted, fontsize=9)
    ax.set_ylabel("ESM-2 entropy (nats)", color=muted, fontsize=9)
    ax.set_title(f"Per-position masked-token entropy ({ds}); low = more conserved",
                 color=ink, fontsize=11, loc="left")
    fig.tight_layout()
    st.pyplot(fig, width="stretch")

    table = pd.DataFrame([{
        "position": p.get("position"), "wild_type": p.get("wild_type"),
        "entropy_nats": p.get("entropy_nats"), "conservation_rank": p.get("conservation_rank"),
        "n_mutated_observations": p.get("n_mutated_observations"),
        "beneficial_fraction": p.get("beneficial_fraction"),
        "max_fitness_gain": p.get("max_fitness_gain"),
        "effect_measured": p.get("effect_measured"),
        "true_peak": any(q.get("position") == p.get("position") for q in peaks),
    } for p in positions]).sort_values("conservation_rank")
    st.dataframe(table, width="stretch", hide_index=True)
    st.caption("名次按熵从低到高排：conservation_rank=1 是最保守位置；effect_measured=false 的位点无实测单突变。")

    if peaks:
        st.markdown("**真峰三位点的保守性名次（负结果，不美化）**")
        for p in sorted(peaks, key=lambda q: q["conservation_rank"]):
            st.markdown(
                f"- `{_peak_label(p)}`（pos {p['position']}，WT `{p['wild_type']}`）→ conservation_rank "
                f"**{p['conservation_rank']} / {len(positions)}** · entropy_nats `{p['entropy_nats']:.4f}`"
            )
        st.info(
            "三个真峰组成位点中**两个落在高保守区**（最保守的第 1、第 4 位）。"
            "若按「避开保守位点」的先验筛候选，会先丢掉 D0Q/V18A，把已知反自然真峰挡在门外——"
            "保守性先验在这里是**负结果**，所以保持事后分析定位、绝不接入采集或筛选路径。"
        )
    else:
        st.caption("`true_peak_positions` 为空——该数据集（GB1）的真峰是四位点组合结果，本分析未定义单峰位点，如实不展示。")

    corr = c.get("correlations", {})
    c1, c2 = st.columns(2)
    c1.metric("ρ(名次, 单突变有益比例)",
              f"{float(corr.get('spearman_rank_vs_beneficial_fraction', float('nan'))):.3f}",
              f"p = {float(corr.get('spearman_rank_vs_beneficial_fraction_pvalue', float('nan'))):.3f}",
              delta_color="off")
    c2.metric("ρ(名次, 单突变最大增益)",
              f"{float(corr.get('spearman_rank_vs_max_fitness_gain', float('nan'))):.3f}",
              f"p = {float(corr.get('spearman_rank_vs_max_fitness_gain_pvalue', float('nan'))):.3f}",
              delta_color="off")
    if ds == "gb1":
        st.caption("GB1 仅 4 个可变位点有实测对照，检验功效极低，不足以支持关联结论（原分析报告结论）。")


def render_alpha_sweep_panel() -> None:
    """⑤-c 为什么不能固定 Ridge alpha：固定 alpha 的预处理反转 + 逐特征选 alpha。"""
    st.markdown("#### ⑤-c 为什么不能固定 Ridge alpha——逐特征 alpha 扫描")
    st.caption(
        "数据源：`harness/reports/workflow-v1.0/gb1/predictor_alpha_sweep.json`（曲线）与 "
        "`predictor_ladder_scaling_ablation.json`（固定 alpha 消融）。"
    )
    sweep_missing = not ALPHA_SWEEP_JSON.exists()
    scaling_missing = not SCALING_ABLATION_JSON.exists()
    if sweep_missing:
        st.warning(f"缺 `harness/reports/workflow-v1.0/gb1/predictor_alpha_sweep.json`——{HINTS['alpha_sweep']} 扫描曲线停等。")
    if scaling_missing:
        st.warning(f"缺 `harness/reports/workflow-v1.0/gb1/predictor_ladder_scaling_ablation.json`——{HINTS['scaling']} 固定 alpha 对照停等。")
    if sweep_missing and scaling_missing:
        return
    sweep = load_metrics(str(ALPHA_SWEEP_JSON)) if not sweep_missing else None
    ablation = load_metrics(str(SCALING_ABLATION_JSON)) if not scaling_missing else None

    if sweep and ablation:
        raw_fix = ablation.get("esm2__random", {}).get("raw", {}).get("ridge", {}).get("spearman", float("nan"))
        std_fix = ablation.get("esm2__random", {}).get("standardized", {}).get("ridge", {}).get("spearman", float("nan"))
        raw_sel = (sweep.get("esm2__random__raw") or {}).get("test_spearman_at_selected", float("nan"))
        std_sel = (sweep.get("esm2__random__standardized") or {}).get("test_spearman_at_selected", float("nan"))
        st.warning(
            f"**固定 alpha 的陷阱**：同一份数据、同一个 Ridge，固定默认 alpha 时 ESM-2（random 划分）"
            f"raw **{float(raw_fix):.4f}** → standardized **{float(std_fix):.4f}**，结论随预处理**反向**；"
            f"按验证集逐特征调过 alpha 后两侧收敛到 **{float(raw_sel):.4f} / {float(std_sel):.4f}**。"
            "落差来自 alpha 与特征尺度耦合（one-hot 逐维方差 ≈0.25，GB1 的 ESM-2 ≈1e-4），"
            "不是表征优劣——所以任何「固定 alpha 比表征」的结论都不成立。"
        )

    if ablation:
        st.markdown("**固定默认 alpha 的标准化消融（`predictor_ladder_scaling_ablation.json` · ridge）**")
        fix_rows = []
        for combo, by_prep in ablation.items():
            if not isinstance(by_prep, dict) or "raw" not in by_prep:
                continue
            raw_v = (by_prep.get("raw", {}).get("ridge", {}) or {}).get("spearman")
            std_v = (by_prep.get("standardized", {}).get("ridge", {}) or {}).get("spearman")
            fix_rows.append({"combo": combo, "raw_spearman": raw_v, "standardized_spearman": std_v,
                             "flip": "🔁 |Δ|>0.1" if raw_v is not None and std_v is not None
                             and abs(raw_v - std_v) > 0.1 else ""})
        st.dataframe(pd.DataFrame(fix_rows), width="stretch", hide_index=True)

    if not sweep:
        return
    st.markdown("**逐特征 alpha 扫描（`predictor_alpha_sweep.json`，8 个组合，标记选中 alpha）**")
    st.caption("字段与 JSON 同名：`alpha_selected` / `val_spearman_at_selected` / `test_spearman_at_selected`。")
    combos = sorted(sweep.keys())
    st.dataframe(
        pd.DataFrame([{
            "combo": k,
            "alpha_selected": sweep[k].get("alpha_selected"),
            "val_spearman_at_selected": sweep[k].get("val_spearman_at_selected"),
            "test_spearman_at_selected": sweep[k].get("test_spearman_at_selected"),
        } for k in combos]),
        width="stretch", hide_index=True,
    )

    fig, axes, ink, muted = _analysis_axes(2, 4, figsize=(13.5, 6.4))
    for ax, combo in zip(axes, combos):
        entry = sweep[combo]
        by_alpha = entry.get("test_spearman_by_alpha", {})
        xs = sorted(by_alpha, key=float)
        ax.plot([float(x) for x in xs], [by_alpha[x] for x in xs], color="#2a78d6", lw=1.8, label="test")
        val_alpha = entry.get("val_spearman_by_alpha", {})
        if val_alpha:
            ax.plot([float(x) for x in xs], [val_alpha.get(x, float("nan")) for x in xs],
                    color="#8a8a86", lw=1.2, ls=(0, (4, 3)), label="val (selection)")
        sel = entry.get("alpha_selected")
        if str(sel) in by_alpha:
            ax.scatter([float(sel)], [by_alpha[str(sel)]], color="#eb6834", s=48, zorder=3)
        feature, split, prep = combo.split("__")
        ax.set_xscale("log")
        ax.set_title(f"{feature} · {split} · {prep}", fontsize=9, loc="left")
    axes[0].legend(fontsize=7.5, frameon=False, labelcolor=ink)
    for ax in axes:
        ax.set_xlabel("ridge alpha (log)", fontsize=8)
    axes[0].set_ylabel("spearman", fontsize=8)
    axes[4].set_ylabel("spearman", fontsize=8)
    fig.suptitle("Test Spearman vs alpha per (feature x split x preprocessing); orange dot = selected alpha",
                 fontsize=11, color=ink, x=0.02, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    st.pyplot(fig, width="stretch")
    st.caption("选法：训练集内 80/20 留出选 alpha（answer-agnostic，不看测试集），再在测试集上报分。")


# ---------------------------------------------------------------- 入口


def main() -> None:
    st.title("🧬 GB1 蛋白定向进化 · 科学智能体看板")
    st.markdown(
        "四策略闭环对比 + 五角色 Agent 思考回放 + 实时试玩 + 分析面板（位点集中 / 组合理由 / "
        "突变阶数 / 保守位点 / alpha 扫描）。数据：GB1 四位点组合空间"
        "（V39/D40/G41/V54，野生型 `VDGV`），真值表 149,361 / 160,000。"
    )
    st.caption(
        "本看板**只读**消费 T7/T4/T3 产物与 `harness/reports/` 分析产物（`@st.cache_data` / `@st.cache_resource`），"
        "不写事件流、不覆盖 `reports/` 或 `harness/reports/`。运行：`streamlit run app/demo.py`（或 `make demo`）。"
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["① 四策略对比", "② Agent 思考回放", "③ 实时试玩", "④ 位点集中 & 组合理由", "⑤ 阶数 · 保守性 · alpha"]
    )
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
    with tab4:
        render_concentration_panel()
        st.divider()
        render_rationales_panel()
    with tab5:
        render_mutation_order_panel()
        st.divider()
        render_conservation_panel()
        st.divider()
        render_alpha_sweep_panel()

    st.divider()
    st.caption(
        "ai4s-directed-evolution-agent · T8 demo · 上游：T7 campaign / T4 事件流 / T3 Ridge 预测器 / "
        "analysis-v0.1 只读分析线"
    )


if __name__ == "__main__":
    main()
