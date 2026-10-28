from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))


import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib.data import now_jst
from lib.industry import insurance_alerts, insurance_kpis, insurance_timeseries
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

setup_page("テクノロジー（CIO）", cockpit=True)
inject_role_theme("CIO")

updated_at = now_jst().strftime("%Y-%m-%d %H:%M JST")
alerts_df  = insurance_alerts()
cockpit_header("CIO", alerts_df, updated_at)

km = {k.key: k for k in insurance_kpis()}

# ── KPI rows ─────────────────────────────────────────────────────────────────
row1_keys = ["system_avail", "cyber_risk_score", "claims_ttd", "expense_ratio"]
row2_keys = ["combined_ratio", "net_premium_growth", "persistency_rate", "solvency_ratio"]
kpi_mini_row([km[k] for k in row1_keys if k in km])
st.write("")
kpi_mini_row([km[k] for k in row2_keys if k in km])
st.write("")

# ── Main row ──────────────────────────────────────────────────────────────────
col_g, col_c, col_a = st.columns([1.0, 2.6, 1.4], gap="small")

with col_g:
    st.markdown("##### 閾値モニター")
    for key in ("system_avail", "cyber_risk_score", "claims_ttd"):
        if key in km:
            st.plotly_chart(gauge_chart(km[key], height=155), use_container_width=True)

with col_c:
    ts = insurance_timeseries()

    st.markdown("##### 主要系稼働率トレンド（90日）")
    fig_avail = px.area(ts, x="date", y="主要系稼働率(%)", height=250,
                        color_discrete_sequence=["#06b6d4"])
    fig_avail.update_traces(opacity=0.22, selector={"fill": "tozeroy"})
    fig_avail.add_hline(y=99.95, line_dash="dash", line_color=_WARN, line_width=1.5,
                        annotation_text="SLA 99.95%",
                        annotation_position="bottom right",
                        annotation_font_color=_WARN, annotation_font_size=9)
    fig_avail.update_layout(**{**_CB, "yaxis": {**_CB["yaxis"], "range": [99.85, 100.02]}})
    st.plotly_chart(fig_avail, use_container_width=True)

    # IT project portfolio (hardcoded mock)
    st.markdown("##### ITプロジェクト進捗サマリー")
    projects = [
        ("コアシステム近代化（Guidewire）",  78, _OK,       "2026Q3"),
        ("クラウド移行（Azure）フェーズ2",   55, _OK,       "2026Q4"),
        ("代理店ポータル刷新",               88, _OK,       "2026Q2"),
        ("AI引受エンジン統合",               40, _WARN,     "2027Q1"),
        ("計理システムリプレイス（Prophet）", 22, _CRIT,     "2027Q4"),
    ]
    rows_html = ""
    for name, pct, color, deadline in projects:
        bar = f"<div style='height:4px;width:{pct}%;background:{color};border-radius:2px;margin-top:3px'></div>"
        rows_html += f"""
        <div style="padding:0.35rem 0;border-bottom:1px solid {_BORDER}">
          <div style="display:flex;justify-content:space-between;margin-bottom:1px">
            <span style="font-size:0.72rem;color:{_TEXT}">{name}</span>
            <span style="font-size:0.7rem;color:{color};font-weight:700">{pct}% / 完了予定 {deadline}</span>
          </div>
          <div style="width:100%;height:4px;background:rgba(77,159,255,0.12);border-radius:2px">
            {bar}
          </div>
        </div>"""
    st.html(f"""<div style="background:{_BG2};border:1px solid {_BORDER};
      border-radius:0.6rem;padding:0.5rem 0.8rem">{rows_html}</div>""")

with col_a:
    st.markdown("##### IT運用指標")
    it_items = [
        ("主要系稼働率（当日）",    "99.97%", "SLA 99.95%",  _OK),
        ("インシデント MTTR",       "48分",   "目標 <90分",   _OK),
        ("変更成功率",              "98.2%",  "前月 97.8%",   _OK),
        ("オープンインシデント",     "7件",    "P1:0 / P2:2",  _WARN),
        ("ITコスト対GWP比",         "3.8%",   "目標 <4.0%",   _OK),
        ("クラウドコスト対計画",    "+4.2%",  "オーバーラン",  _WARN),
        ("SaaS契約更改（90日内）",  "3件",    "総額 1.2億円",  _INFO_BLUE),
    ]
    rows_html = ""
    for label, value, note, vc in it_items:
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
    sys_alerts = alerts_df[alerts_df["領域"].isin(["システム", "サイバー"])].reset_index(drop=True)
    st.markdown("##### システムアラート")
    render_alert_compact(sys_alerts, max_height=150)

    st.write("")
    st.markdown("##### 今日の確認事項")
    st.markdown("""
- **基幹系稼働**: Guidewire / 計理システム / 代理店ポータルの稼働状況
- **変更管理**: 週次リリース結果・ロールバック可否の確認
- **クラウドコスト**: Azure予算超過の要因分析と是正措置
""")
