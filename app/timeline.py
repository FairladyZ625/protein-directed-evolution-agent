"""Research timeline dashboard: streamlit run app/timeline.py."""
from pathlib import Path
import html
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import altair as alt
import pandas as pd
import streamlit as st
from timeline_data import (
    COGNITION_ARC,
    DUAL_LOOP,
    EVIDENCE,
    EXECUTIVE_SUMMARY,
    HONEST_BOUNDARIES,
    OUTER_KINDS,
    OUTER_LOOP,
    RESEARCH_INSIGHTS,
    VERSIONS,
    indicators,
    interpret_event,
    load_version,
    mutations,
    pairwise_effects,
    read_json,
    variants,
)

# 本文件既可独立运行（streamlit run app/timeline.py），也可被 app/demo.py 作为
# 「研究演进」视图挂载。两种入口只能有一个 set_page_config，因此它只在独立运行时执行；
# 样式同理改为按需注入，避免被挂载时污染主看板的布局。
def _standalone_page_config() -> None:
    st.set_page_config(
        page_title='SADE · 蛋白质自演进科学智能体学术看板',
        page_icon='🧬',
        layout='wide',
    )


# ---------------------------------------------------------------------------
# 全局视觉样式：现代 Slate + Emerald 配色方案 (严格保持 96% 宽幅与卡片质感)
# ---------------------------------------------------------------------------
_STYLE = '''<style>
:root {
  color-scheme: light;
  --bg-main: #f8fafc;
  --bg-card: #ffffff;
  --border-card: #e2e8f0;
  --text-main: #0f172a;
  --text-muted: #475569;
  --text-light: #94a3b8;
  --emerald-600: #059669;
  --emerald-700: #047857;
  --emerald-50: #ecfdf5;
  --emerald-100: #d1fae5;
  --emerald-border: #a7f3d0;
  --blue-600: #2563eb;
  --blue-50: #eff6ff;
  --blue-border: #bfdbfe;
  --amber-600: #d97706;
  --amber-50: #fffbeb;
  --amber-border: #fde68a;
  --rose-600: #e11d48;
  --rose-50: #fff1f2;
  --rose-border: #fecdd3;
  --purple-600: #7c3aed;
  --purple-50: #f5f3ff;
  --purple-border: #ddd6fe;
}

body, .stApp {
  background-color: var(--bg-main) !important;
  color: var(--text-main) !important;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif !important;
}

[data-testid="stHeader"] {
  background: rgba(248, 250, 252, 0.92) !important;
  backdrop-filter: blur(10px) !important;
}

.block-container {
  max-width: 96% !important;
  padding: 1.8rem 2.5rem 4rem 2.5rem !important;
}

h1, h2, h3, h4 {
  color: var(--text-main) !important;
  letter-spacing: -0.025em !important;
  font-weight: 750 !important;
}

/* Hero Section */
.hero-container {
  background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
  border: 1px solid var(--border-card);
  border-radius: 20px;
  box-shadow: 0 8px 30px rgba(15, 23, 42, 0.04);
  padding: clamp(24px, 3.2vw, 40px);
  margin-bottom: 24px;
}

.hero-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--emerald-50);
  border: 1px solid var(--emerald-border);
  color: var(--emerald-700);
  padding: 4px 14px;
  border-radius: 9999px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.1em;
  margin-bottom: 12px;
}

.hero-title {
  font-size: clamp(26px, 2.5vw, 36px);
  font-weight: 850;
  line-height: 1.25;
  color: var(--text-main);
  margin-bottom: 12px;
}

.hero-deck {
  font-size: 15.5px;
  color: var(--text-muted);
  line-height: 1.8;
  max-width: 1080px;
  margin-bottom: 20px;
}

.hero-stats-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border-card);
}

.hero-stat-pill {
  background: #ffffff;
  border: 1px solid var(--border-card);
  border-radius: 10px;
  padding: 7px 15px;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.02);
}

.hero-stat-num {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 15px;
  font-weight: 800;
  color: var(--emerald-700);
}

.hero-stat-lbl {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 600;
}

/* Executive Summary Box & Table */
.exec-box {
  background: #ffffff;
  border: 1.5px solid #cbd5e1;
  border-radius: 18px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
  padding: 24px 28px;
  margin-bottom: 26px;
}

.exec-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border-card);
}

.exec-header-title {
  font-size: 18.5px;
  font-weight: 800;
  color: var(--text-main);
}

.exec-header-subtitle {
  font-size: 13.5px;
  color: var(--text-muted);
  margin-top: 4px;
}

.exec-card-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 6px;
  letter-spacing: 0.04em;
}

.exec-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  overflow: hidden;
  font-size: 13.5px;
  line-height: 1.65;
  background: #ffffff;
}

.exec-table th {
  background: #f8fafc;
  color: #0f172a;
  font-weight: 800;
  font-size: 13px;
  padding: 13px 16px;
  border-bottom: 2px solid #e2e8f0;
  text-align: left;
  letter-spacing: 0.02em;
}

.exec-table td {
  padding: 16px 18px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: top;
  color: #334155;
}

.exec-table tr:last-child td {
  border-bottom: none;
}

.exec-table tr:hover td {
  background: #fafbfc;
}

/* Metric overrides */
[data-testid="stMetric"] {
  background: #ffffff !important;
  border: 1px solid var(--border-card) !important;
  border-radius: 14px !important;
  padding: 16px 20px !important;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03) !important;
}

[data-testid="stMetricValue"] {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace !important;
  font-weight: 800 !important;
  color: var(--emerald-700) !important;
  font-size: 1.85rem !important;
}

[data-testid="stMetricLabel"] {
  color: var(--text-muted) !important;
  font-weight: 700 !important;
  font-size: 13.5px !important;
}

/* Chapter header */
.chapter-box {
  background: #ffffff;
  border: 1px solid var(--border-card);
  border-left: 5px solid var(--emerald-600);
  border-radius: 14px;
  padding: 20px 24px;
  margin: 18px 0 22px;
  box-shadow: 0 3px 12px rgba(15, 23, 42, 0.03);
}

.chapter-eyebrow {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
  font-weight: 700;
  color: var(--emerald-700);
  letter-spacing: 0.12em;
  margin-bottom: 6px;
}

.chapter-title {
  font-size: 21px;
  font-weight: 800;
  color: var(--text-main);
  margin-bottom: 8px;
}

.chapter-story {
  font-size: 15px;
  color: var(--text-muted);
  line-height: 1.75;
}

.chapter-next {
  margin-top: 14px;
  padding: 12px 16px;
  background: var(--blue-50);
  border: 1px solid var(--blue-border);
  border-radius: 8px;
  font-size: 14px;
  color: #1e40af;
  line-height: 1.65;
}

/* Sequence viewer */
.seq-wrapper {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  margin: 12px 0 16px;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid var(--border-card);
  border-radius: 10px;
}

.seq-residue {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  width: 29px;
  padding: 5px 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-weight: 700;
  font-size: 13.5px;
  color: var(--text-main);
}

.seq-residue small {
  font-size: 9px;
  color: var(--text-light);
  font-weight: 500;
  margin-bottom: 2px;
}

.seq-residue.changed {
  background: var(--emerald-100);
  border-color: var(--emerald-600);
  color: var(--emerald-700);
  font-weight: 800;
}

/* Outer Loop items */
.oloop-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 24px;
  font: 700 12px ui-monospace, monospace;
  letter-spacing: .04em;
  margin: 0 0 16px;
}

.oloop {
  display: flex;
  flex-direction: column;
  margin: 4px 0;
}

.oloop-item {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  position: relative;
  padding-bottom: 14px;
}

.oloop-item:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 17px;
  top: 38px;
  bottom: 0;
  width: 2px;
  background: #e2e8f0;
}

.oloop-dot {
  flex: 0 0 36px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  background: #ffffff;
  border: 2px solid var(--c, var(--emerald-600));
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.06);
  position: relative;
  z-index: 1;
}

.oloop-card {
  flex: 1;
  min-width: 0;
  background: #ffffff;
  border: 1px solid var(--border-card);
  border-left: 4px solid var(--c, var(--emerald-600));
  border-radius: 12px;
  padding: 14px 18px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
}

.oloop-kicker {
  font: 700 11px ui-monospace, monospace;
  letter-spacing: .12em;
  color: var(--c, var(--emerald-600));
  margin-bottom: 4px;
}

.oloop-title {
  font-weight: 750;
  font-size: 15.5px;
  color: var(--text-main);
  margin-bottom: 5px;
  line-height: 1.4;
}

.oloop-detail {
  font-size: 14px;
  color: var(--text-muted);
  line-height: 1.7;
}

.oloop-ref {
  font: 11px ui-monospace, monospace;
  color: var(--text-light);
  margin-top: 8px;
}

/* Event Replayer */
.event-box {
  background: #ffffff;
  border: 1px solid var(--border-card);
  border-radius: 14px;
  padding: 20px;
  margin-top: 10px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
}

.event-human-banner {
  background: #f8fafc;
  border-left: 4px solid var(--emerald-600);
  border-radius: 0 10px 10px 0;
  padding: 14px 18px;
  margin: 12px 0 16px;
}

.event-human-banner-title {
  font-size: 13.5px;
  font-weight: 800;
  color: var(--emerald-700);
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.event-human-banner-text {
  font-size: 14px;
  color: #1e293b;
  line-height: 1.75;
  margin: 0;
}

/* Research Insight Card */
.insight-card {
  background: #ffffff;
  border: 1px solid var(--border-card);
  border-radius: 18px;
  padding: 26px 28px;
  margin-bottom: 26px;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.04);
}

.insight-tag {
  display: inline-block;
  font-size: 12px;
  font-weight: 700;
  padding: 3px 12px;
  border-radius: 6px;
  margin-bottom: 12px;
  letter-spacing: 0.04em;
}

.insight-title {
  font-size: 21px;
  font-weight: 850;
  color: var(--text-main);
  margin-bottom: 10px;
  line-height: 1.35;
}

.insight-summary {
  font-size: 15px;
  color: var(--text-muted);
  line-height: 1.75;
  margin-bottom: 20px;
}

.insight-stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
  margin-bottom: 20px;
}

.insight-stat-item {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px 16px;
}

.insight-stat-val {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 17px;
  font-weight: 800;
  color: var(--text-main);
  margin-bottom: 4px;
}

.insight-stat-lbl {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.insight-stat-desc {
  font-size: 11.5px;
  color: var(--text-light);
  line-height: 1.5;
}

.insight-deepdive {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-left: 4px solid var(--emerald-600);
  border-radius: 0 12px 12px 0;
  padding: 18px 22px;
  margin-top: 14px;
}

.insight-deepdive h4 {
  font-size: 15.5px;
  font-weight: 800;
  color: var(--text-main);
  margin-bottom: 8px;
}

.insight-deepdive-text {
  font-size: 14px;
  color: #334155;
  line-height: 1.8;
}

/* Radio buttons styled as modern pills */
[data-testid="stRadio"] > div {
  gap: 10px !important;
  flex-wrap: wrap !important;
}

[data-testid="stRadio"] label {
  background: #ffffff !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 9999px !important;
  padding: 8px 18px !important;
  color: var(--text-main) !important;
  font-weight: 600 !important;
  font-size: 13.5px !important;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03) !important;
  transition: all 0.2s ease !important;
}

[data-testid="stRadio"] label:hover {
  border-color: var(--emerald-600) !important;
  color: var(--emerald-700) !important;
}

[data-testid="stRadio"] label:has(input:checked) {
  background: var(--emerald-700) !important;
  border-color: var(--emerald-700) !important;
  color: #ffffff !important;
  box-shadow: 0 4px 12px rgba(4, 120, 87, 0.25) !important;
}

[data-testid="stRadio"] label:has(input:checked) p {
  color: #ffffff !important;
  font-weight: 700 !important;
}

.duo {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 16px;
  margin: 14px 0 10px;
}

.duo-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-top: 4px solid var(--c, var(--emerald-600));
  border-radius: 14px;
  padding: 20px 22px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
}

.duo-kicker {
  font: 700 11px ui-monospace, monospace;
  letter-spacing: .14em;
  color: var(--c, var(--emerald-600));
}

.duo-title {
  font-weight: 750;
  font-size: 17px;
  color: var(--text-main);
  margin: 6px 0 8px;
}

.duo-text {
  font-size: 14px;
  color: var(--text-muted);
  line-height: 1.75;
}

.arc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 14px;
  margin: 12px 0;
}

.arc-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-top: 4px solid var(--c, var(--emerald-600));
  border-radius: 12px;
  padding: 16px 18px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
}

.arc-tag {
  font: 700 11px ui-monospace, monospace;
  letter-spacing: .12em;
  color: var(--c, var(--emerald-600));
}

.arc-title {
  font-weight: 750;
  font-size: 15.5px;
  color: var(--text-main);
  margin: 6px 0 6px;
  line-height: 1.45;
}

.arc-detail {
  font-size: 13.5px;
  color: var(--text-muted);
  line-height: 1.7;
}

.arc-ref {
  font: 11px ui-monospace, monospace;
  color: var(--text-light);
  margin-top: 8px;
}

.bounds {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-left: 4px solid #d97706;
  border-radius: 14px;
  padding: 20px 24px;
  margin: 14px 0;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
}

.bounds-title {
  font-weight: 800;
  color: #b45309;
  font-size: 16px;
  margin-bottom: 12px;
}

.bounds ol {
  margin: 0;
  padding-left: 20px;
}

.bounds li {
  font-size: 14px;
  color: #334155;
  line-height: 1.75;
  margin-bottom: 10px;
}

.bounds li b {
  color: #0f172a;
}

@media(max-width:768px){
  .block-container { padding: 1.2rem !important; }
  .hero-title { font-size: 22px; }
  .seq-residue { width: 25px; font-size: 12px; }
}
</style>'''


def inject_style() -> None:
    """注入本视图的卡片/排版样式。挂载在主看板下时只在切到本视图后调用。"""
    st.markdown(_STYLE, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 顶部 Hero 区与 Executive Summary
# ---------------------------------------------------------------------------
def render_hero():
    st.markdown('''<div class="hero-container">
  <div class="hero-eyebrow">🧬 AI4SCIENCE · 蛋白质定向进化科学智能体学术全景看板</div>
  <div class="hero-title">从无约束探索到可验证的科学发现：AI 驱动蛋白质定向进化的诚实边界与工程实践</div>
  <div class="hero-deck">
    基于真实湿实验基准（FLIP-AAV 适应度景观），全景记录 v0.1 到 v0.7 七代算法研发的<b>实证检验、因果归因、认知自证伪与系统演化</b>。<br>
    内环呈现蛋白质工程智能体的微观闭环实验证据链（严格带 SHA-256 密码学存证），外环展示科研专家与 Harness 系统的宏观决策流与方法论演进。
  </div>
  <div class="hero-stats-row">
    <div class="hero-stat-pill"><span class="hero-stat-num">7 代演进</span><span class="hero-stat-lbl">v0.1 → v0.7 闭环演进</span></div>
    <div class="hero-stat-pill"><span class="hero-stat-num">288 步</span><span class="hero-stat-lbl">微观实测预算约束</span></div>
    <div class="hero-stat-pill"><span class="hero-stat-num">8.4162</span><span class="hero-stat-lbl">未测候选池唯一全局真峰</span></div>
    <div class="hero-stat-pill"><span class="hero-stat-num">30 / 30 (100%)</span><span class="hero-stat-lbl">UCB β=3 稳健达峰</span></div>
    <div class="hero-stat-pill"><span class="hero-stat-num">71.88%</span><span class="hero-stat-lbl">冷启动残基对缺测盲区</span></div>
  </div>
</div>''', unsafe_allow_html=True)


def render_executive_summary():
    rows_html = []
    for item in EXECUTIVE_SUMMARY:
        dim = item.get("dimension") or item.get("title") or "核心维度"
        dim_en = item.get("dimension_en") or item.get("num") or "Dimension"
        badge = item.get("badge") or "核心结论"
        badge_bg = item.get("badge_bg") or "#ecfdf5"
        badge_color = item.get("badge_color") or "#059669"
        badge_border = item.get("badge_border") or "#a7f3d0"
        proposition = item.get("proposition") or item.get("title") or ""
        tag = item.get("tag") or item.get("highlight") or ""
        data_contrast = item.get("data_contrast") or item.get("highlight") or ""
        conclusions = item.get("conclusions") or item.get("text") or ""

        dim_html = f'''<div style="font-weight: 800; font-size: 14px; color: #0f172a; margin-bottom: 4px;">{dim}</div>
<div style="font-size: 11px; font-family: ui-monospace, monospace; color: #64748b; margin-bottom: 8px;">{dim_en}</div>
<span class="exec-card-badge" style="background:{badge_bg}; color:{badge_color}; border: 1px solid {badge_border};">{badge}</span>'''

        prop_html = f'''<div style="font-weight: 800; font-size: 14.5px; color: #0f172a; margin-bottom: 6px; line-height: 1.45;">{proposition}</div>
<div style="display: inline-block; font-size: 11.5px; font-weight: 700; color: {badge_color}; background: {badge_bg}; border: 1px solid {badge_border}; padding: 2px 8px; border-radius: 4px;">{tag}</div>'''

        data_html = f'''<div style="font-size: 13px; color: #1e293b; line-height: 1.7; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;">{data_contrast}</div>'''

        conc_html = f'''<div style="font-size: 13.5px; color: #334155; line-height: 1.75;">{conclusions}</div>'''

        row = f'''<tr>
  <td style="background: #fafbfc; border-right: 1px solid #f1f5f9; width: 14%;">{dim_html}</td>
  <td style="border-right: 1px solid #f1f5f9; width: 22%;">{prop_html}</td>
  <td style="border-right: 1px solid #f1f5f9; background: #fafbfc; width: 25%;">{data_html}</td>
  <td style="width: 39%;">{conc_html}</td>
</tr>'''
        rows_html.append(row)

    tbody_html = ''.join(rows_html)
    st.markdown(f'''<div class="exec-box">
  <div class="exec-header">
    <div>
      <div class="exec-header-title">📊 【核心科研发现与系统结论】Executive Summary</div>
      <div class="exec-header-subtitle">基于严密实测对照与不可篡改证据链系统性归纳的计算生物学与人工智能交叉核心结论</div>
    </div>
  </div>
  <div style="overflow-x: auto;">
    <table class="exec-table">
      <thead>
        <tr>
          <th>维度</th>
          <th>核心命题</th>
          <th>实测对照数据</th>
          <th>机理归因与系统性工程结论 (Mechanistic & Systems Conclusions)</th>
        </tr>
      </thead>
      <tbody>{tbody_html}</tbody>
    </table>
  </div>
</div>''', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 版本叙事与外环流
# ---------------------------------------------------------------------------
def render_narrative(version):
    label, title, story, hypothesis = VERSIONS[version]
    st.markdown(f'''<div class="chapter-box">
  <div class="chapter-eyebrow">{version} / {label}</div>
  <div class="chapter-title">{title}</div>
  <div class="chapter-story">{story}</div>
  <div class="chapter-next"><b>🔬 下一步科学假说与技术攻坚：</b>{hypothesis}</div>
</div>''', unsafe_allow_html=True)


def _outer_timeline_html(items):
    rows = []
    for item in items:
        meta = OUTER_KINDS[item['kind']]
        rows.append(
            f'<div class="oloop-item" style="--c:{meta["color"]}">'
            f'<div class="oloop-dot">{meta["icon"]}</div>'
            f'<div class="oloop-card"><div class="oloop-kicker">{meta["label"]}</div>'
            f'<div class="oloop-title">{html.escape(item["title"])}</div>'
            f'<div class="oloop-detail">{html.escape(item["detail"])}</div>'
            f'<div class="oloop-ref">↳ {html.escape(item["ref"])}</div></div></div>')
    return f'<div class="oloop">{"".join(rows)}</div>'


def render_outer_loop(version):
    st.subheader('00 / 外环 · Harness 真实科研决策流')
    legend = '　·　'.join(f'<span style="color:{m["color"]}">{m["icon"]} {m["label"]}</span>' for m in OUTER_KINDS.values())
    st.markdown(f'<div class="oloop-legend">{legend}</div>', unsafe_allow_html=True)
    st.markdown(_outer_timeline_html(OUTER_LOOP[version]), unsafe_allow_html=True)
    st.caption('注：外环事件由 git 提交历史、harness/reports 报告与研究文稿只读萃取沉淀；与内环 SHA-256 实验物理隔离，忠实呈现人机决策演变。')


# ---------------------------------------------------------------------------
# 指标看板
# ---------------------------------------------------------------------------
def render_metrics(metrics):
    baseline = read_json(EVIDENCE / 'baseline.metrics.json')['summary']['final_cum_top10_max']
    data = indicators(metrics, baseline)
    cols = st.columns(4)
    cols[0].metric('🏆 新发现 · 最高适应度', f"{data['best']:.4f}", f"第 {data['peak_round']} 个测定批次达峰", delta_color='off')
    cols[1].metric('🎯 强变体 / 实测预算', f"{data['strong']} / {data['spent']}", f"命中率 {data['rate']:.1%}", delta_color='off')
    cols[2].metric('⚖️ 探索税 · 描述性峰值差', f"{data['gap']:.4f}", '相对 8.4162 确定性参考', delta_color='off')
    cols[3].metric('📈 相对加性基线净增益', f"{data['gain']:+.4f}", '基线 7.5301 · 绝对分值差', delta_color='off')

    st.caption(f"说明：强变体阈值 > {metrics['strong_threshold']}；最高分仅统计本次运行新增测定，排除冷启动已测样本。探索税为 8.4162 − 本次最高分，定量衡量因过度或低效探索付出的机会成本。")

    rows = pd.DataFrame(metrics['rounds'])[['round', 'spent_after', 'cum_top10_max', 'cum_n_strong']]
    chart = alt.Chart(rows).mark_line(
        point=alt.OverlayMarkDef(size=70, filled=True, color='#059669'),
        color='#059669',
        strokeWidth=3
    ).encode(
        x=alt.X('spent_after:Q', title='累积实验预算消耗 (条)'),
        y=alt.Y('cum_top10_max:Q', title='新发现最高适应度', scale=alt.Scale(zero=False)),
        tooltip=[
            alt.Tooltip('round:Q', title='测定批次'),
            alt.Tooltip('spent_after:Q', title='累积测定消耗'),
            alt.Tooltip('cum_top10_max:Q', title='最高适应度', format='.4f'),
            alt.Tooltip('cum_n_strong:Q', title='强变体命中总数'),
        ]
    )
    rule_data = pd.DataFrame([
        {'fitness': 7.5301, 'label': '加性贪心基线 (7.5301)'},
        {'fitness': baseline, 'label': f'确定性交替真峰 ({baseline:.4f})'}
    ])
    rule = alt.Chart(rule_data).mark_rule(strokeDash=[5, 5], color='#94a3b8', strokeWidth=1.5).encode(
        y='fitness:Q',
        tooltip=['label:N', 'fitness:Q']
    )
    st.altair_chart((chart + rule).properties(height=230), width='stretch')


# ---------------------------------------------------------------------------
# 实验事件回放与状态审计
# ---------------------------------------------------------------------------
def render_replay(events, version):
    st.subheader('01 / 实验决策事件回放与状态审计')
    st.caption(f'共 {len(events)} 条原始事件流 · SHA-256 密码学防篡改链校验通过')
    rounds = list(dict.fromkeys(e['round_id'] for e in events if e['round_id'] is not None))
    selected = st.selectbox('日志轮次筛选', ['全部', *rounds], key=f'{version}_round')
    filtered = [e for e in events if selected == '全部' or e['round_id'] == selected]
    if not filtered:
        st.info('该轮次没有匹配的事件记录。'); return

    key = f'{version}_step_{selected}'
    if key not in st.session_state:
        st.session_state[key] = 0

    def move(delta):
        st.session_state[key] = max(0, min(len(filtered)-1, st.session_state[key] + delta))

    c1, c2 = st.columns(2)
    c1.button('← 上一步', on_click=move, args=(-1,), disabled=st.session_state[key] == 0, key=f'{key}_prev')
    c2.button('下一步 →', on_click=move, args=(1,), disabled=st.session_state[key] == len(filtered)-1, key=f'{key}_next')

    i = st.select_slider(
        '决策步骤时间轴',
        options=list(range(len(filtered))),
        format_func=lambda n: f"{n+1}/{len(filtered)} · {filtered[n]['event_type'].split('.')[-1]}",
        key=key
    )
    event = filtered[i]
    st.progress((i + 1) / len(filtered))

    info = interpret_event(event)
    st.markdown(f'''<div class="event-box">
  <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
    <div style="display: flex; align-items: center; gap: 8px;">
      <span style="font-size: 24px;">{info['icon']}</span>
      <span style="font-weight: 800; font-size: 16px; color: #0f172a;">{info['title']}</span>
    </div>
    <span style="font-size: 11.5px; font-weight: 700; background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; padding: 3px 10px; border-radius: 9999px;">{info['badge']}</span>
  </div>
  <div class="event-human-banner">
    <div class="event-human-banner-title">🔬 【实验决策逻辑与状态审计】</div>
    <div class="event-human-banner-text">{info['summary']}</div>
  </div>
  <div style="font-size: 12px; color: #94a3b8; font-family: ui-monospace, monospace;">
    事件序号: #{event['seq']} · 操作者: {event['actor']} · 轮次: {event['round_id']} · 时间戳: {event['ts']}
  </div>
</div>''', unsafe_allow_html=True)

    with st.expander('查看该事件原始 JSON 载荷 (只读审计)'):
        st.json(event, expanded=2)

    with st.expander('查看当前筛选轮次所有事件摘要清单'):
        st.dataframe(pd.DataFrame([{
            '序号': e['seq'],
            '轮次': e['round_id'],
            '事件类型': e['event_type'],
            '操作者': e['actor'],
            '决策逻辑标签': interpret_event(e)['title']
        } for e in filtered]), hide_index=True, width='stretch')

    st.download_button(
        '📥 下载原始不可篡改 JSONL 事件链',
        (EVIDENCE / version / 'agentic.events.jsonl').read_bytes(),
        file_name=f'{version}.events.jsonl',
        mime='application/x-ndjson',
    )


# ---------------------------------------------------------------------------
# 变体与互作检视器
# ---------------------------------------------------------------------------
def render_inspector(metrics, events, version):
    st.subheader('02 / 变体与上位互作检视器')
    catalog = variants(metrics)
    seq = st.selectbox('已测变体 · 各批次 Top 10', list(catalog), format_func=lambda s: f"{catalog[s]['fitness']:.4f} · {s}", key=f'{version}_variant')
    compare = st.selectbox('对比基准变体', list(catalog), index=min(1, len(catalog)-1), key=f'{version}_compare')
    wt = metrics['wild_type']

    st.caption('残基位点索引从 0 开始；绿色高亮块为相对野生型 WT 的氨基酸替换。此处为一维序列示意图。')

    for s in [seq, compare]:
        blocks = ''.join(f'<span class="seq-residue {"changed" if i >= len(wt) or a != wt[i] else ""}"><small>{i}</small>{html.escape(a)}</span>' for i, a in enumerate(s))
        st.markdown(f'<div class="seq-wrapper">{blocks}</div>', unsafe_allow_html=True)

    st.metric('实测适应度差值 · 所选变体 − 对比变体', f"{catalog[seq]['fitness'] - catalog[compare]['fitness']:+.4f}")

    try:
        changes = mutations(seq, wt)
    except ValueError as exc:
        st.warning(str(exc)); return

    st.markdown('**关键突变位点：** ' + (' · '.join(f"`{m['mutation']}`" for m in changes) or '野生型 (WT)'))

    st.markdown('**成对上位互作效应（Pairwise Epistasis）**')
    st.caption('上位效应（Epistasis）定量度量：ε > 0 为正上位性协同增效（双突变适应度显著高于单突变独立加性预期）；ε < 0 为负上位性拮抗冲突（活性悬崖）。定义公式：ε = f(ij) − f(i) − f(j) + f(WT)。')

    pairs = pairwise_effects(seq, wt, read_json(EVIDENCE / 'measured_backgrounds.json'))
    if pairs:
        frame = pd.DataFrame(pairs)
        st.dataframe(frame, hide_index=True, width='stretch')
        valid = frame.dropna(subset=['epsilon']).copy()
        if not valid.empty:
            valid['类型'] = valid['epsilon'].apply(lambda x: '正上位协同 (ε > 0)' if x >= 0 else '负上位拮抗 (ε < 0)')
            bar_chart = alt.Chart(valid).mark_bar().encode(
                x=alt.X('epsilon:Q', title='实测上位效应 ε (正值表示协同增效，负值表示拮抗冲突)'),
                y=alt.Y('pair:N', title=None, sort=None),
                color=alt.Color('epsilon:Q', scale=alt.Scale(domain=[-2, 0, 2], range=['#e11d48', '#94a3b8', '#059669']), legend=None),
                tooltip=[
                    alt.Tooltip('pair:N', title='突变残基对'),
                    alt.Tooltip('epsilon:Q', title='上位效应 ε', format='.4f'),
                    alt.Tooltip('类型:N', title='生物物理效应判定')
                ]
            ).properties(height=max(120, len(valid) * 28))
            st.altair_chart(bar_chart, width='stretch')
    else:
        st.info('至少需要两个氨基酸突变位点才能计算成对上位互作效应。')


# ---------------------------------------------------------------------------
# 外环决策流全景
# ---------------------------------------------------------------------------
def render_panorama():
    st.markdown('''<div class="chapter-box">
  <div class="chapter-eyebrow">OUTER LOOP / HARNESS RESEARCH DECISIONS</div>
  <div class="chapter-title">外环 · Harness 科研决策流全景</div>
  <div class="chapter-story">
    系统呈现 v0.1 至 v0.7 七代研发周期中，科研团队与 Harness 系统如何<b>由实测反差驱动假设修正、人在环干预、因果自证伪与最优参数置信界推导</b>。
  </div>
</div>''', unsafe_allow_html=True)

    duo = ''.join(
        f'<div class="duo-card" style="--c:{m["color"]}"><div class="duo-kicker">{m["icon"]} {key.upper()} LOOP</div>'
        f'<div class="duo-title">{m["title"]}</div><div class="duo-text">{m["text"]}</div></div>'
        for key, m in DUAL_LOOP.items())
    st.markdown(f'<div class="duo">{duo}</div>', unsafe_allow_html=True)

    kinds = st.multiselect(
        '事件类型过滤',
        list(OUTER_KINDS),
        default=list(OUTER_KINDS),
        format_func=lambda k: f'{OUTER_KINDS[k]["icon"]} {OUTER_KINDS[k]["label"]}',
        key='outer_kinds'
    )
    if not kinds:
        st.info('已取消全部事件类型；请勾选至少一类以查看决策流。'); return

    for version, meta in VERSIONS.items():
        items = [e for e in OUTER_LOOP[version] if e['kind'] in kinds]
        if not items:
            continue
        st.markdown(f'''<div style="display: flex; align-items: baseline; gap: 12px; margin: 28px 0 10px; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0;">
  <span style="font: 700 14px ui-monospace, monospace; color: #047857; letter-spacing: .08em;">{version}</span>
  <span style="font-weight: 800; font-size: 18px; color: #0f172a;">{meta[1]}</span>
  <span style="font-size: 13px; color: #64748b;">{meta[0]}</span>
</div>''', unsafe_allow_html=True)
        st.markdown(_outer_timeline_html(items), unsafe_allow_html=True)

    st.subheader('认知演化 · 实证驱动的四次科学认知自证伪与修正')
    st.caption('严谨科学研究的核心价值在于实证导向的自我修正与假设证伪——包括对早期研究假设与误判的公开因果溯源与纠偏。')
    arc = ''.join(
        f'<div class="arc-card" style="--c:{stage["color"]}"><div class="arc-tag">{stage["tag"]}</div>'
        f'<div class="arc-title">{stage["title"]}</div><div class="arc-detail">{stage["detail"]}</div>'
        f'<div class="arc-ref">↳ {stage["ref"]}</div></div>'
        for stage in COGNITION_ARC)
    st.markdown(f'<div class="arc-grid">{arc}</div>', unsafe_allow_html=True)

    st.subheader('诚实边界 · 审慎界定的四大科学有效性防线')
    bounds = ''.join(f'<li><b>{b["title"]}</b> —— {b["detail"]}</li>' for b in HONEST_BOUNDARIES)
    st.markdown(f'<div class="bounds"><div class="bounds-title">🛡️ 学术报告与证据边界由人在环严格界定：明确统计学与工程边界，保障结论可复现性</div><ol>{bounds}</ol></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 核心科研发现与未来方向
# ---------------------------------------------------------------------------
def render_research_insights():
    st.markdown('''<div class="chapter-box" style="border-left-color: #2563eb;">
  <div class="chapter-eyebrow">RESEARCH INSIGHTS & FUTURE BLUEPRINT</div>
  <div class="chapter-title">💡 核心科研发现与系统演进蓝图</div>
  <div class="chapter-story">
    系统性总结研发团队历经闭环实验演进、实证反思证伪与跨尺度理论推导沉淀出的四项核心计算生物学与 AI 交叉科研结论。
  </div>
</div>''', unsafe_allow_html=True)

    for item in RESEARCH_INSIGHTS:
        stats_html = ''.join(
            f'''<div class="insight-stat-item">
  <div class="insight-stat-val">{s["val"]}</div>
  <div class="insight-stat-lbl">{s["label"]}</div>
  <div class="insight-stat-desc">{s["desc"]}</div>
</div>'''
            for s in item['core_data']
        )
        sections_html = ''.join(
            f'''<div class="insight-deepdive">
  <h4>{sec["title"]}</h4>
  <div class="insight-deepdive-text">{sec["content"]}</div>
</div>'''
            for sec in item['sections']
        )
        st.markdown(f'''<div class="insight-card" id="{item["id"]}">
  <span class="insight-tag" style="background:{item["bg"]}; color:{item["color"]}; border: 1px solid {item["border"]};">{item["tag"]}</span>
  <div class="insight-title">{item["title"]}</div>
  <div class="insight-summary">{item["summary"]}</div>
  <div class="insight-stat-grid">{stats_html}</div>
  {sections_html}
</div>''', unsafe_allow_html=True)

    st.divider()
    st.subheader('📑 形式化理论白皮书与学术文稿审阅')
    st.caption('如需查阅形式化数学推导、贝叶斯 UCB 证明与完整实验消融附录，可在此选择并下载 Markdown 原文：')
    files = sorted((EVIDENCE / 'whitepapers').glob('*.md'))
    if files:
        chosen = st.selectbox('选择白皮书文稿', files, format_func=lambda p: p.stem.replace('_', ' '))
        c1, c2 = st.columns([1, 4])
        with c1:
            st.download_button('📥 下载选中文档原文', chosen.read_bytes(), file_name=chosen.name, mime='text/markdown')
        with st.expander(f'在线预览：{chosen.stem}'):
            st.markdown(chosen.read_text(encoding='utf-8'))


# ---------------------------------------------------------------------------
# 主函数与路由
# ---------------------------------------------------------------------------
def main(*, standalone: bool = False):
    """渲染「研究演进」视图。standalone=True 时自己负责 page_config。"""
    if standalone:
        _standalone_page_config()
    inject_style()
    render_hero()
    render_executive_summary()

    tabs_options = [*VERSIONS, '🛰️ 外环全景 · 团队认知演进', '💡 科研认知结晶与未来蓝图']
    version = st.radio(
        '研究时间线与全景导览',
        tabs_options,
        horizontal=True,
        key='version',
        format_func=lambda v: f'{v} · {VERSIONS[v][0]}' if v in VERSIONS else v,
        label_visibility='collapsed'
    )

    if version in ('💡 科研认知结晶与未来蓝图', '理论白皮书'):
        render_research_insights()
        st.divider()
        st.caption('SADE · Research Atlas　/　RESEARCH INSIGHTS & FUTURE BLUEPRINT　/　2026')
        return

    if version == '🛰️ 外环全景 · 团队认知演进':
        render_panorama()
        st.divider()
        st.caption('SADE · Research Atlas　/　OUTER LOOP PANORAMA　/　2026')
        return

    render_narrative(version)
    render_outer_loop(version)

    try:
        data = load_version(version)
    except (OSError, ValueError) as exc:
        st.error(f'证据数据无法读取：{exc}'); return

    if data['metrics'] is None:
        st.info('诊断研究阶段 · 未执行端到端湿实验闭环，因此无新增发现指标、事件回放或本代实测变体。')
        st.subheader('01 / 表征 × 代理模型多路扫描结果')
        st.dataframe(pd.DataFrame(data['scan']['rows']), hide_index=True, width='stretch')
        st.subheader('02 / 真实真峰排名与表达力分析')
        st.bar_chart(
            pd.DataFrame(data['scan']['rows']).assign(model=lambda d: d.feature + ' × ' + d.surrogate).set_index('model')['peak_rank_gate'],
            color='#059669'
        )
        st.caption('说明：排名越前越优。6 组经典加性模型将最优真峰排在 #1283 ~ #2776 位，在 288 次实验预算内完全不可观测。')
    else:
        metrics = data['metrics']
        st.caption(f"运行类型：{'LLM 工具调用实验' if metrics['llm_used'] else '确定性参考运行（非自主回溯）'} · 代理模型: {metrics.get('reference') or metrics.get('surrogate', 'one_hot')} · 初始冷启动: {metrics['cold_start_size']:,} 条 · 未测候选池: {metrics['candidate_pool_size']:,} 条")
        if version == 'v0.5':
            st.warning('证据边界校正：本运行 metrics 记录强变体数为 163；早期总报告表格曾手误写为 82。看板一律以不可篡改原始实测指标为准。')
        if version == 'v0.7':
            st.info('证据边界声明：本页展示 alternating-seed42 确定性交替参考运行；8.4162 是未测候选池唯一真峰，而非包含冷启动样本的历史总库记录。')

        render_metrics(metrics)

        left, right = st.columns([1, 1.15], gap='large')
        with left, st.container(border=True):
            render_replay(data['events'], version)
        with right, st.container(border=True):
            render_inspector(metrics, data['events'], version)

    with st.expander('🔍 证据来源溯源与哈希可复现性验证'):
        manifest = read_json(EVIDENCE / 'provenance.json')
        st.json({k: v for k, v in manifest.items() if k.startswith(version) or k == 'measured_backgrounds.json'}, expanded=2)
        st.caption('所有 JSONL 事件流与 metrics 均通过逐字节快照与 SHA-256 签名存证。背景分数是原始测定表的只读子集。')

    st.divider()
    st.caption('SADE · Research Atlas　/　READ-ONLY SCIENTIFIC EVIDENCE　/　2026')


if __name__ == '__main__':
    main(standalone=True)
