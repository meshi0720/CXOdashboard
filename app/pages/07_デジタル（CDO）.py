from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))


import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib.data import now_jst, timeseries_long_for_plot
from lib.industry import insurance_alerts, insurance_financial_monthly, insurance_kpis, insurance_timeseries
from lib.ui import (
    _BG2, _BORDER, _CRIT, _INFO_BLUE, _MUTED, _OK, _TEXT, _WARN,
    cockpit_header, gauge_chart, inject_role_theme, kpi_mini_row,
    render_alert_compact, setup_page,
)

_GRID = "rgba(77,159,255,0.08)"
_CB = dict(plot_bgcolor=_BG2, paper_bgcolor="rgba(0,0,0,0)",
           font=dict(color=_TEXT, size=10), margin=dict(l=8,r=8,t=6,b=6),
           legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=_TEXT), orientation="h", y=1.08, x=0),
           legend_title_text="",
           xaxis=dict(showgrid=True,gridcolor=_GRID,color=_MUTED,linecolor=_GRID),
           yaxis=dict(showgrid=True,gridcolor=_GRID,color=_MUTED,linecolor=_GRID))

setup_page("デジタル（CDO）", cockpit=True)
inject_role_theme("CDO")

updated_at = now_jst().strftime("%Y-%m-%d %H:%M JST")
alerts_df  = insurance_alerts()
cockpit_header("CDO", alerts_df, updated_at)

km = {k.key: k for k in insurance_kpis()}

# ── KPI rows ─────────────────────────────────────────────────────────────────
row1_keys = ["system_avail", "persistency_rate", "net_premium_growth", "combined_ratio"]
row2_keys = ["expense_ratio", "cyber_risk_score", "claims_ttd", "gwp_plan_ratio"]
kpi_mini_row([km[k] for k in row1_keys if k in km])
st.write("")
kpi_mini_row([km[k] for k in row2_keys if k in km])
st.write("")

# ── Main row ──────────────────────────────────────────────────────────────────
col_g, col_c, col_a = st.columns([1.0, 2.6, 1.4], gap="small")

with col_g:
    st.markdown("##### 閾値モニター")
    for key in ("system_avail", "persistency_rate", "cyber_risk_score"):
        if key in km:
            st.plotly_chart(gauge_chart(km[key], height=155), use_container_width=True)

with col_c:
    ts = insurance_timeseries()

    st.markdown("##### デジタルチャネル申込比率 vs 継続率（月次）")
    monthly = insurance_financial_monthly()
    # Mock digital channel adoption (growing over time)
    digital_ratio = [32.1, 33.4, 34.8, 35.2, 35.9]
    fig_digi = go.Figure()
    fig_digi.add_bar(x=monthly["月"], y=digital_ratio,
                     name="デジタル申込比率(%)", marker_color="rgba(232,121,249,0.65)")
    fig_digi.add_hline(y=40, line_dash="dash", line_color=_WARN, line_width=1.2,
                       annotation_text="目標 40%",
                       annotation_position="top right",
                       annotation_font_color=_WARN, annotation_font_size=9)
    fig_digi.update_layout(**{**_CB, "height": 240,
                              "yaxis": {**_CB["yaxis"], "range": [0, 50], "title": "%"}})
    st.plotly_chart(fig_digi, use_container_width=True)

    st.markdown("##### 継続率 × 主要系稼働率トレンド（90日）")
    long, _ = timeseries_long_for_plot(ts, ("継続率(%)(生保)", "主要系稼働率(%)"))
    if not long.empty:
        fig_per = px.area(long, x="date", y="value", color="series",
                          height=210,
                          color_discrete_sequence=["#e879f9", "#06b6d4"])
        fig_per.update_traces(opacity=0.20, selector={"fill": "tozeroy"})
        fig_per.update_layout(**_CB)
        st.plotly_chart(fig_per, use_container_width=True)

with col_a:
    st.markdown("##### デジタル・データ指標")
    cdo_items = [
        ("デジタル申込比率",           "35.9%", "目標 40%",      _WARN),
        ("代理店ポータル日次訪問者",   "12,480", "前日比 +3.2%", _OK),
        ("オンライン見積→成約率",      "18.4%", "前月 17.2%",   _OK),
        ("データパイプライン異常",      "0件",   "正常",          _OK),
        ("データ品質スコア（総合）",    "91.2pt","目標 >90",      _OK),
        ("顧客NPS（デジタル）",        "+42",   "業界平均 +35",  _OK),
        ("APIレイテンシ P99",          "182ms", "SLA <300ms",   _OK),
        ("マーテックROI",              "+12.3%","Q1 CAC改善",   _OK),
    ]
    rows_html = ""
    for label, value, note, vc in cdo_items:
        rows_html += f"""
        <div style="display:flex;align-items:center;gap:0.3rem;
          padding:0.28rem 0;border-bottom:1px solid {_BORDER}">
          <span style="font-size:0.7rem;color:{_MUTED};flex:1">{label}</span>
          <span style="font-size:0.8rem;font-weight:700;color:{vc};white-space:nowrap">{value}</span>
          <span style="font-size:0.65rem;color:{_MUTED};min-width:66px;text-align:right">{note}</span>
        </div>"""
    st.html(f"""<div style="background:{_BG2};border:1px solid {_BORDER};
      border-radius:0.6rem;padding:0.5rem 0.75rem">{rows_html}</div>""")

    st.write("")
    st.markdown("##### 今日の論点")
    st.markdown("""
- **デジタル申込**: 目標 40% に対し 35.9% — 残ギャップ解消施策のレビュー
- **データ品質**: 契約・損害データの異常検知・パイプライン障害の有無
- **顧客体験**: NPS スコアの直近トレンドとデジタルジャーニー改善優先順位
""")
