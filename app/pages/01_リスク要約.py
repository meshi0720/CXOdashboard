from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))


import plotly.express as px
import streamlit as st

from lib.data import now_jst, sample_alerts, sample_kpis
from lib.ui import (
    _BG2, _CRIT, _INFO_BLUE, _MUTED, _OK, _TEXT, _WARN,
    inject_role_theme, kpi_row, render_alert_table, setup_page, status_banner,
)

_GRID = "rgba(77,159,255,0.08)"
_BASE = dict(plot_bgcolor=_BG2, paper_bgcolor="rgba(0,0,0,0)",
             font=dict(color=_TEXT, size=11), margin=dict(l=10,r=16,t=10,b=10),
             xaxis=dict(showgrid=True,gridcolor=_GRID,color=_MUTED,linecolor=_GRID),
             yaxis=dict(showgrid=True,gridcolor=_GRID,color=_MUTED,linecolor=_GRID))

setup_page("リスク要約")
inject_role_theme("CEO")

st.markdown("## リスク要約")
st.caption(f"更新: {now_jst().strftime('%Y-%m-%d %H:%M JST')}")
st.divider()

alerts = sample_alerts()
kpis   = sample_kpis()
km     = {k.key: k for k in kpis}

status_banner(alerts)

st.write("")

st.markdown("### 主要指標（全社横断）")
key_order = ["pnl_today", "capital_ratio", "liq_coverage", "npl_ratio", "security_risk", "system_avail"]
row = [km[k] for k in key_order if k in km]
kpi_row(row[:3])
st.write("")
kpi_row(row[3:])

st.write("")

left, right = st.columns([0.6, 0.4], gap="large")

with left:
    st.markdown("### 重要アラート（全領域）")
    render_alert_table(alerts)

with right:
    st.markdown("### 領域別アラート分布")
    domain_counts = alerts.groupby("領域").size().reset_index(name="件数")
    fig = px.pie(
        domain_counts, names="領域", values="件数", hole=0.55,
        color_discrete_sequence=[_INFO_BLUE, _WARN, _CRIT, _OK, "#a78bfa"],
        height=270,
    )
    fig.update_layout(
        **{**_BASE,
           "showlegend": True,
           "legend": dict(bgcolor="rgba(0,0,0,0)", font=dict(color=_TEXT), orientation="v", x=1.0, y=0.5)},
    )
    fig.update_traces(textposition="inside", textinfo="percent+label",
                      textfont=dict(color="#ffffff", size=11))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 重要度別内訳")
    sev_counts = alerts.groupby("重要度").size().reset_index(name="件数")
    fig2 = px.bar(
        sev_counts, x="重要度", y="件数", color="重要度",
        color_discrete_map={"CRIT": _CRIT, "WARN": _WARN, "INFO": _INFO_BLUE},
        height=190,
    )
    fig2.update_layout(**{**_BASE, "showlegend": False, "yaxis": {**_BASE["yaxis"], "dtick": 1}})
    st.plotly_chart(fig2, use_container_width=True)
