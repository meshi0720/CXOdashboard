from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib.data import now_jst, timeseries_long_for_plot, wide_to_long
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

setup_page("AI（CAIO）", cockpit=True)
inject_role_theme("CAIO")

updated_at = now_jst().strftime("%Y-%m-%d %H:%M JST")
alerts_df  = insurance_alerts()
cockpit_header("CAIO", alerts_df, updated_at)

km = {k.key: k for k in insurance_kpis()}

# ── KPI rows ─────────────────────────────────────────────────────────────────
row1_keys = ["combined_ratio", "claims_ttd", "persistency_rate", "attritional_lr"]
row2_keys = ["expense_ratio", "system_avail", "cyber_risk_score", "net_premium_growth"]
kpi_mini_row([km[k] for k in row1_keys if k in km])
st.write("")
kpi_mini_row([km[k] for k in row2_keys if k in km])
st.write("")

# ── Main row ──────────────────────────────────────────────────────────────────
col_g, col_c, col_a = st.columns([1.0, 2.6, 1.4], gap="small")

with col_g:
    st.markdown("##### 閾値モニター")
    for key in ("claims_ttd", "combined_ratio", "expense_ratio"):
        if key in km:
            st.plotly_chart(gauge_chart(km[key], height=155), use_container_width=True)

with col_c:
    ts = insurance_timeseries()

    # AI model performance (mock data)
    st.markdown("##### AI モデル精度モニタリング（直近30日）")
    import numpy as np
    rng   = np.random.default_rng(99)
    days  = 30
    dates = [now_jst().date() - __import__("datetime").timedelta(days=d) for d in range(days-1, -1, -1)]
    underwriting_acc = np.clip(88 + np.cumsum(rng.normal(0, 0.3, days)), 84, 93)
    claims_auto_acc  = np.clip(91 + np.cumsum(rng.normal(0, 0.25, days)), 87, 95)
    import pandas as pd
    df_ai = pd.DataFrame({"date": dates,
                          "引受AI精度(%)": underwriting_acc,
                          "査定AI精度(%)": claims_auto_acc})
    fig_ai = px.line(
        wide_to_long(df_ai, "date", ["引受AI精度(%)", "査定AI精度(%)"]),
        x="date", y="value", color="series",
        height=245,
        color_discrete_sequence=["#fb923c", "#818cf8"],
    )
    fig_ai.add_hline(y=88, line_dash="dash", line_color=_WARN, line_width=1.2,
                     annotation_text="引受AI 最低基準 88%",
                     annotation_position="bottom right",
                     annotation_font_color=_WARN, annotation_font_size=9)
    fig_ai.update_layout(**_CB)
    st.plotly_chart(fig_ai, use_container_width=True)

    # AI automation rate + impact
    st.markdown("##### AI自動化率 vs 手動審査コスト削減（月次）")
    months = ["1月", "2月", "3月", "4月", "5月(速報)"]
    auto_rate   = [38.2, 39.8, 41.1, 42.0, 42.3]
    cost_saving = [1.2,  1.35, 1.48, 1.55, 0.38]
    fig_auto = go.Figure()
    fig_auto.add_bar(x=months, y=cost_saving,
                     name="コスト削減(億円)", marker_color="rgba(251,146,60,0.65)")
    fig_auto.add_scatter(x=months, y=auto_rate,
                         name="自動化率(%)", mode="lines+markers",
                         line=dict(color="#818cf8", width=2),
                         marker=dict(size=6), yaxis="y2")
    fig_auto.update_layout(**{**_CB, "height": 205,
                              "yaxis2": dict(overlaying="y", side="right",
                                            showgrid=False, color=_MUTED, range=[30, 55])})
    st.plotly_chart(fig_auto, use_container_width=True)

with col_a:
    st.markdown("##### AI施策ポートフォリオ")
    ai_projects = [
        ("引受AIエンジン（損保）",     "本番稼働", "精度 89.2%",  _OK),
        ("保険金査定AI（一般損保）",   "本番稼働", "自動率 42%",  _OK),
        ("生保アンダーライティングAI", "パイロット","精度 84.1%",  _WARN),
        ("不正請求検知モデル",         "本番稼働", "検知率 91%",  _OK),
        ("顧客解約予測モデル",         "開発中",   "2026Q3 予定", _INFO_BLUE),
        ("自然言語 FNOL 処理",        "PoC",      "2026Q4 予定", _INFO_BLUE),
    ]
    rows_html = ""
    for name, status, metric, vc in ai_projects:
        status_colors = {"本番稼働": _OK, "パイロット": _WARN, "開発中": _INFO_BLUE, "PoC": _MUTED}
        sc = status_colors.get(status, _MUTED)
        rows_html += f"""
        <div style="padding:0.35rem 0;border-bottom:1px solid {_BORDER}">
          <div style="display:flex;align-items:center;gap:0.4rem">
            <span style="font-size:0.7rem;color:{_TEXT};flex:1">{name}</span>
            <span style="font-size:0.65rem;background:rgba(77,159,255,0.1);
              border:1px solid {sc};color:{sc};
              padding:0.05rem 0.4rem;border-radius:999px;
              white-space:nowrap;font-weight:600">{status}</span>
          </div>
          <div style="font-size:0.67rem;color:{_MUTED};margin-top:0.15rem">{metric}</div>
        </div>"""
    st.html(f"""<div style="background:{_BG2};border:1px solid {_BORDER};
      border-radius:0.6rem;padding:0.5rem 0.8rem">{rows_html}</div>""")

    st.write("")
    st.markdown("##### 今日の論点")
    st.markdown("""
- **モデルドリフト**: 引受AI・査定AIの精度劣化・入力分布変化の有無
- **AIガバナンス**: EIOPA AI規制（説明責任・バイアス監査）への対応状況
- **ROI検証**: Q1 AI投資対効果（コスト削減 YTD 4.55億円 vs 計画）の評価
""")
