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

setup_page("業務（COO）", cockpit=True)
inject_role_theme("COO")

updated_at = now_jst().strftime("%Y-%m-%d %H:%M JST")
alerts_df  = insurance_alerts()
cockpit_header("COO", alerts_df, updated_at)

km = {k.key: k for k in insurance_kpis()}

# ── KPI rows ─────────────────────────────────────────────────────────────────
row1_keys = ["claims_ttd", "expense_ratio", "persistency_rate", "loss_ratio"]
row2_keys = ["system_avail", "net_premium_growth", "combined_ratio", "cat_budget_usage"]
kpi_mini_row([km[k] for k in row1_keys if k in km])
st.write("")
kpi_mini_row([km[k] for k in row2_keys if k in km])
st.write("")

# ── Main row ──────────────────────────────────────────────────────────────────
col_g, col_c, col_a = st.columns([1.0, 2.6, 1.4], gap="small")

with col_g:
    st.markdown("##### 閾値モニター")
    for key in ("claims_ttd", "persistency_rate", "expense_ratio"):
        if key in km:
            st.plotly_chart(gauge_chart(km[key], height=155), use_container_width=True)

with col_c:
    monthly = insurance_financial_monthly()
    ts      = insurance_timeseries()

    # Claims settlement days + monthly GWP pace
    st.markdown("##### 元受保険料（損保/生保）月次推移 と 費用率　単位: 億円 / %")
    fig_ops = go.Figure()
    fig_ops.add_bar(x=monthly["月"], y=monthly["元受保険料（損保）"],
                    name="損保 GWP", marker_color="rgba(77,159,255,0.65)")
    fig_ops.add_bar(x=monthly["月"], y=monthly["元受保険料（生保）"],
                    name="生保 GWP", marker_color="rgba(16,217,138,0.55)")
    fig_ops.add_scatter(x=monthly["月"], y=monthly["費用率(%)"],
                        name="費用率(%)", mode="lines+markers",
                        line=dict(color=_WARN, width=2),
                        marker=dict(size=6), yaxis="y2")
    fig_ops.update_layout(
        **{**_CB, "height": 250, "barmode": "stack",
           "yaxis2": dict(overlaying="y", side="right", showgrid=False,
                          color=_MUTED, range=[28, 36])})
    st.plotly_chart(fig_ops, use_container_width=True)

    # Persistency rate 90-day trend
    st.markdown("##### 継続率（生保 13ヶ月）トレンド（90日）")
    fig_per = px.area(ts, x="date", y="継続率(%)(生保)", height=200,
                      color_discrete_sequence=["#818cf8"])
    fig_per.update_traces(opacity=0.22, selector={"fill": "tozeroy"})
    fig_per.add_hline(y=90.0, line_dash="dash", line_color=_WARN, line_width=1.5,
                      annotation_text="社内しきい値 90%",
                      annotation_position="bottom right",
                      annotation_font_color=_WARN, annotation_font_size=9)
    fig_per.update_layout(**{**_CB, "yaxis": {**_CB["yaxis"], "range": [88, 96]}})
    st.plotly_chart(fig_per, use_container_width=True)

with col_a:
    # Operational KPIs
    st.markdown("##### オペレーション指標")
    ops_items = [
        ("保険金支払日数（平均）",    "8.3日",   "SLA ≤15日",    _OK),
        ("保険金AI自動決済率",        "42%",    "目標 50%",     _WARN),
        ("大口案件（>1億円）滞留",   "3件",     "要レビュー",   _WARN),
        ("代理店ポータル稼働率",      "99.94%",  "SLA 99.9%",   _OK),
        ("解約率（当月）",            "0.52%",   "前月 0.41%",  _WARN),
        ("新契約引受承認率",          "87.3%",   "前月 86.8%",  _OK),
        ("苦情受付（当月）",          "128件",   "前月 115件",   _WARN),
    ]
    rows_html = ""
    for label, value, note, vc in ops_items:
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

    ops_alerts = alerts_df[alerts_df["領域"].isin(["引受リスク", "損保", "システム", "生保"])].reset_index(drop=True)
    st.markdown("##### 業務アラート")
    render_alert_compact(ops_alerts, max_height=140)

    st.write("")
    st.markdown("##### 今日の確認事項")
    st.markdown("""
- **CAT支払**: 台風・洪水案件の損害査定進捗・支払見込み総額
- **解約急増**: 特定商品・地域の解約トレンドと競合対策
- **費用管理**: 費用率の月次乖離要因と下半期コスト削減施策
""")
