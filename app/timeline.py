"""Research timeline: streamlit run app/timeline.py."""
from pathlib import Path
import html
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import altair as alt
import pandas as pd
import streamlit as st
from timeline_data import EVIDENCE, VERSIONS, indicators, load_version, mutations, pairwise_effects, read_json, variants

st.set_page_config(page_title='SADE · Research Atlas', page_icon='◈', layout='wide')
st.markdown('''<style>
:root {color-scheme: light;}
.stApp {background:#f6f7f3; color:#192e34}
[data-testid="stHeader"] {background:rgba(246,247,243,.9)}
.block-container {max-width:1400px;padding-top:2.5rem;padding-bottom:3rem}
h1,h2,h3 {letter-spacing:-.035em;color:#173d3e}
h1 {font-size:3.3rem!important;line-height:1.13!important;font-weight:650!important}
.eyebrow {font:600 11px monospace;letter-spacing:.19em;color:#507a73;margin-bottom:18px}
.deck {font-size:17px;color:#657774;max-width:750px;line-height:1.9}
.hero {border-bottom:1px solid #d8e0d8;padding:14px 0 25px;margin-bottom:22px}
.chapter {border-left:3px solid #528f76;padding:8px 0 8px 22px;margin:20px 0}
.chapter h2 {margin:0;font-size:2rem}
.chapter p {margin:6px 0;color:#5d7370}
[data-testid="stMetric"] {background:#fff;border:1px solid #dfe6df;border-radius:14px;padding:17px;min-height:124px}
[data-testid="stMetricValue"] {font-family:monospace;color:#1d6958}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:15px!important}
[data-baseweb="tab-list"] {gap:22px}
[data-testid="stRadio"] > div {gap:8px}
[data-testid="stRadio"] label {background:#fff;border:1px solid #d5dfd7;border-radius:25px;padding:9px 16px!important}
.sequence {display:flex;gap:4px;flex-wrap:wrap;margin:14px 0 20px}
.residue {display:flex;flex-direction:column;align-items:center;background:#e9eee7;border-radius:5px;width:29px;padding:6px 0;font-family:monospace}
.residue small {font-size:9px;color:#6f817a}.residue.changed {background:#d1e8db;color:#176443;border-bottom:2px solid #3b8865}
.note {padding:16px 20px;background:#eaf0e7;border-radius:12px;color:#365b4f;line-height:1.7}
@media(max-width:700px){h1{font-size:2.2rem!important}.block-container{padding:1.1rem}.residue{width:24px}}
</style>''', unsafe_allow_html=True)


def render_narrative(version):
    label, title, story, hypothesis = VERSIONS[version]
    st.markdown(f'<div class="chapter"><div class="eyebrow">{version} / {label}</div><h2>{title}</h2><p>{story}</p></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="note"><b>下一步的科学问题</b>　{hypothesis}</div>', unsafe_allow_html=True)


def render_metrics(metrics):
    baseline = read_json(EVIDENCE / 'baseline.metrics.json')['summary']['final_cum_top10_max']
    data = indicators(metrics, baseline)
    cols = st.columns(4)
    cols[0].metric('新发现 · 最高适应度', f"{data['best']:.4f}", f"第 {data['peak_round']} 个测定批次达峰", delta_color='off')
    cols[1].metric('强变体 / 实测预算', f"{data['strong']} / {data['spent']}", f"命中率 {data['rate']:.1%}", delta_color='off')
    cols[2].metric('探索税 · 描述性峰值差', f"{data['gap']:.4f}", '相对 v0.4 确定性参考', delta_color='off')
    cols[3].metric('相对加性基线增益', f"{data['gain']:+.4f}", '基线 7.5301 · 绝对分值差', delta_color='off')
    st.caption(f"强变体阈值 > {metrics['strong_threshold']}；最高分仅含本次新增测定，排除冷启动 incumbent。探索税为 8.4162 − 本次最高分，跨协议描述差，不代表因果估计或物理能量。")
    rows = pd.DataFrame(metrics['rounds'])[['round', 'spent_after', 'cum_top10_max', 'cum_n_strong']]
    chart = alt.Chart(rows).mark_line(point=alt.OverlayMarkDef(size=70), color='#29755d', strokeWidth=3).encode(
        x=alt.X('spent_after:Q', title='累积实验预算'),
        y=alt.Y('cum_top10_max:Q', title='新发现最高适应度', scale=alt.Scale(zero=False)),
        tooltip=['round', 'spent_after', 'cum_top10_max', 'cum_n_strong'])
    rule = alt.Chart(pd.DataFrame({'fitness': [7.5301, baseline]})).mark_rule(strokeDash=[5, 5], color='#b1b8a7').encode(y='fitness:Q')
    st.altair_chart((chart + rule).properties(height=220), width='stretch')


def render_replay(events, version):
    st.subheader('01 / 实验事件回放')
    st.caption(f'{len(events)} 条原始事件 · SHA-256 链验证通过 · 日志 round_id 与指标测定批次分别呈现')
    rounds = list(dict.fromkeys(e['round_id'] for e in events if e['round_id'] is not None))
    selected = st.selectbox('日志轮次', ['全部', *rounds], key=f'{version}_round')
    filtered = [e for e in events if selected == '全部' or e['round_id'] == selected]
    if not filtered:
        st.info('该轮没有记录。'); return
    key = f'{version}_step_{selected}'
    if key not in st.session_state: st.session_state[key] = 0
    def move(delta):
        st.session_state[key] = max(0, min(len(filtered)-1, st.session_state[key] + delta))
    controls = st.columns(2)
    controls[0].button('← 上一步', on_click=move, args=(-1,), disabled=st.session_state[key] == 0, key=f'{key}_prev')
    controls[1].button('下一步 →', on_click=move, args=(1,), disabled=st.session_state[key] == len(filtered)-1, key=f'{key}_next')
    i = st.select_slider('决策步', options=list(range(len(filtered))), format_func=lambda n: f"{n+1} / {len(filtered)} · {filtered[n]['event_type']}", key=key)
    event = filtered[i]
    st.progress((i+1)/len(filtered))
    if any(word in event['event_type'] for word in ['test', 'acquisition', 'error', 'no_test', 'measurements']):
        st.info(f"关键事件 · {event['event_type']}")
    st.markdown(f"**#{event['seq']} · {event['event_type']}**")
    st.caption(f"{event['actor']} · round {event['round_id']} · {event['ts']}")
    st.json(event, expanded=2)
    with st.expander('该轮事件目录'):
        st.dataframe(pd.DataFrame([{k: e[k] for k in ['seq', 'round_id', 'event_type', 'actor']} for e in filtered]), hide_index=True, width='stretch')
    st.download_button('下载原始 JSONL', (EVIDENCE / version / 'agentic.events.jsonl').read_bytes(), file_name=f'{version}.events.jsonl', mime='application/x-ndjson')


def render_inspector(metrics, events, version):
    st.subheader('02 / 变体与互作检视器')
    catalog = variants(metrics)
    seq = st.selectbox('已测变体 · 各批次 Top 10', list(catalog), format_func=lambda s: f"{catalog[s]['fitness']:.4f} · {s}", key=f'{version}_variant')
    compare = st.selectbox('对比变体', list(catalog), index=min(1,len(catalog)-1), key=f'{version}_compare')
    wt = metrics['wild_type']
    st.caption('残基索引从 0 开始；绿色为相对 WT 的替换。此处为序列示意，不是三维结构。')
    for s in [seq, compare]:
        blocks = ''.join(f'<span class="residue {"changed" if i >= len(wt) or a != wt[i] else ""}"><small>{i}</small>{html.escape(a)}</span>' for i,a in enumerate(s))
        st.markdown(f'<div class="sequence">{blocks}</div>', unsafe_allow_html=True)
    st.metric('实测适应度差 · 所选 − 对比', f"{catalog[seq]['fitness']-catalog[compare]['fitness']:+.4f}")
    try:
        changes = mutations(seq, wt)
    except ValueError as exc:
        st.warning(str(exc)); return
    st.markdown('关键突变：' + (' · '.join(f"`{m['mutation']}`" for m in changes) or 'WT'))
    predictions = []
    for e in events:
        if e['event_type'] == 'agent.acquisition':
            for candidate in e['payload'].get('candidates', []):
                if candidate.get('seq') == seq:
                    predictions.append({'日志轮次': e['round_id'], '预测均值': candidate.get('mean'), '预测方差': candidate.get('var')})
    if predictions: st.dataframe(pd.DataFrame(predictions), hide_index=True)
    else: st.caption('该运行未记录此变体的逐项代理预测；不补造预测分数。')
    st.markdown('**成对上位互作 · WT 背景**')
    st.caption('εᵢⱼ = f(ij) − f(i) − f(j) + f(WT)。由 FLIP 实测分数计算；缺任一背景则为空。多突变背景下的交互可能不同。')
    pairs = pairwise_effects(seq, wt, read_json(EVIDENCE / 'measured_backgrounds.json'))
    if pairs:
        frame = pd.DataFrame(pairs)
        st.dataframe(frame, hide_index=True, width='stretch')
        valid = frame.dropna(subset=['epsilon'])
        if not valid.empty:
            st.altair_chart(alt.Chart(valid).mark_bar(color='#50836c').encode(x=alt.X('epsilon:Q', title='实测上位效应 ε'), y=alt.Y('pair:N', title=None), tooltip=['pair','epsilon']).properties(height=max(100, len(valid)*25)), width='stretch')
    else: st.info('至少需要两个替换才能计算成对互作。')
    st.caption('未提供拟合 Potts 系数或物理 ΔG；适应度与 ε 不作为 kcal/mol 能量呈现。')


def render_whitepapers():
    st.header('理论白皮书 / 从观察到形式化')
    st.caption('原始研究文稿供审阅；数学结论的适用条件与离线实验观察须分别判断。')
    files = sorted((EVIDENCE / 'whitepapers').glob('*.md'))
    chosen = st.selectbox('选择白皮书', files, format_func=lambda p: p.stem.replace('_', ' '))
    st.download_button('下载原文', chosen.read_bytes(), file_name=chosen.name, mime='text/markdown')
    st.markdown(chosen.read_text())


def main():
    st.markdown('<div class="hero"><div class="eyebrow">SADE / RESEARCH ATLAS　 ·　 AAV LANDSCAPE</div><h1>从自由探索，<br>到可验证的发现。</h1><p class="deck">六代研究，一条证据链。沿时间线回看假说如何改变、实验如何回应，以及那些让下一次突破成为可能的失败。</p></div>', unsafe_allow_html=True)
    version = st.radio('研究时间线', [*VERSIONS, '理论白皮书'], horizontal=True, key='version', label_visibility='collapsed', format_func=lambda v: f'{v} · {VERSIONS[v][0]}' if v in VERSIONS else v)
    if version == '理论白皮书':
        render_whitepapers(); return
    render_narrative(version)
    try: data = load_version(version)
    except (OSError, ValueError) as exc:
        st.error(f'证据无法读取，已停止该版本展示：{exc}'); return
    if data['metrics'] is None:
        st.info('诊断研究 · 未运行 campaign，因此没有新增发现指标、事件回放或本代变体。')
        st.subheader('01 / 表征 × 代理扫描')
        st.dataframe(pd.DataFrame(data['scan']['rows']), hide_index=True, width='stretch')
        st.subheader('02 / 排名与表达力')
        st.bar_chart(pd.DataFrame(data['scan']['rows']).assign(model=lambda d:d.feature+' × '+d.surrogate).set_index('model')['peak_rank_gate'], color='#50836c')
        st.caption('排名越低越好；最优组合 #1283，仍超出单次排序前 288 的范围。后续自适应实验不能由此直接判定不可达。')
    else:
        metrics = data['metrics']
        st.caption(f"运行类型：{'LLM 工具调用' if metrics['llm_used'] else '确定性参考（非 LLM 自主回溯）'} · {metrics.get('reference') or metrics.get('surrogate','one_hot')} · 冷启动 {metrics['cold_start_size']:,} · 候选池 {metrics['candidate_pool_size']:,}")
        if version == 'v0.5': st.warning('证据校正：本运行 metrics 的强变体数为 163；总报告表格写为 82。本页采用原始实测指标。')
        if version == 'v0.7': st.info('证据边界：本页展示 alternating-seed42 确定性交替参考；llm_used=false、backtrack=null。8.4162 是未测候选池峰，非包含冷启动样本的全数据集最高分。')
        render_metrics(metrics)
        left, right = st.columns([1, 1.15], gap='large')
        with left, st.container(border=True): render_replay(data['events'], version)
        with right, st.container(border=True): render_inspector(metrics, data['events'], version)
    with st.expander('证据来源与可复现性'):
        manifest = read_json(EVIDENCE / 'provenance.json')
        st.json({k:v for k,v in manifest.items() if k.startswith(version) or k == 'measured_backgrounds.json'}, expanded=2)
        st.caption('JSONL 与 metrics 为逐字节快照；来源路径相对规范仓库根。背景分数是原始测定表的只读子集。')
    st.divider()
    st.caption('SADE · Research Atlas　/　READ-ONLY EVIDENCE　/　2026　 ·　原 GB1 演示：streamlit run app/demo.py')

if __name__ == '__main__': main()
