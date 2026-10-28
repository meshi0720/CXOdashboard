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
    cockpit_header, gauge_chart, inject_role_theme, kpi_mini_row, setup_page,
)

_GRID = "rgba(77,159,255,0.08)"
_CB = dict(plot_bgcolor=_BG2, paper_bgcolor="rgba(0,0,0,0)",
           font=dict(color=_TEXT, size=10), margin=dict(l=8,r=8,t=6,b=6),
           legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=_TEXT), orientation="h", y=1.08, x=0),
           legend_title_text="",
           xaxis=dict(showgrid=True,gridcolor=_GRID,color=_MUTED,linecolor=_GRID),
           yaxis=dict(showgrid=True,gridcolor=_GRID,color=_MUTED,linecolor=_GRID))

setup_page("流動性・リスク（CRO）", cockpit=True)
inject_role_theme("CRO")

updated_at = now_jst().strftime("%Y-%m-%d %H:%M JST")
alerts_df  = insurance_alerts()
cockpit_header("CRO", alerts_df, updated_at)

km = {k.key: k for k in insurance_kpis()}

# ── KPI rows ─────────────────────────────────────────────────────────────────
row1_keys = ["combined_ratio", "cat_loss_ytd", "loss_ratio", "attritional_lr"]
row2_keys = ["solvency_ratio", "cat_budget_usage", "expense_ratio", "reserve_release"]
kpi_mini_row([km[k] for k in row1_keys if k in km])
st.write("")
kpi_mini_row([km[k] for k in row2_keys if k in km])
st.write("")

# ── Main row ──────────────────────────────────────────────────────────────────
col_g, col_c, col_a = st.columns([1.0, 2.6, 1.4], gap="small")

with col_g:
    st.markdown("##### 閾値モニター")
    for key in ("combined_ratio", "solvency_ratio", "attritional_lr"):
        if key in km:
            st.plotly_chart(gauge_chart(km[key], height=155), use_container_width=True)

with col_c:
    monthly = insurance_financial_monthly()

    # CR decomposition with CAT highlighted
    st.markdown("##### コンバインドレシオ内訳（月次）　通常損害率 / CAT / 費用率")
    # Compute attritional loss ratio (loss ratio minus approximate CAT rate)
    gwp_nl = monthly["元受保険料（損保）"]
    cat_rate = (monthly["CAT損失(億円)"] / gwp_nl * 100).round(1)
    attritional = (monthly["損害率(%)"] - cat_rate).round(1)

    fig_cr = go.Figure()
    fig_cr.add_bar(x=monthly["月"], y=attritional,
                   name="通常損害率", marker_color="rgba(245,166,35,0.70)")
    fig_cr.add_bar(x=monthly["月"], y=cat_rate,
                   name="CAT損害率", marker_color="rgba(255,71,87,0.80)")
    fig_cr.add_bar(x=monthly["月"], y=monthly["費用率(%)"],
                   name="費用率", marker_color="rgba(77,159,255,0.55)")
    fig_cr.add_scatter(x=monthly["月"], y=monthly["コンバインドレシオ"],
                       mode="lines+markers", name="CR合計",
                       line=dict(color=_TEXT, width=1.4, dash="dot"),
                       marker=dict(size=5))
    fig_cr.add_hline(y=100, line_dash="dash", line_color=_OK, line_width=1.5,
                     annotation_text="引受損益分岐 100%",
                     annotation_position="bottom right",
                     annotation_font_color=_OK, annotation_font_size=9)
    fig_cr.update_layout(**{**_CB, "height": 255, "barmode": "stack"})
    st.plotly_chart(fig_cr, use_container_width=True)

    # CAT accumulation vs budget
    st.markdown("##### CAT損失累積 vs 年間予算　単位: 億円")
    fig_cat = go.Figure()
    fig_cat.add_bar(x=monthly["月"], y=monthly["CAT損失(億円)"],
                    name="CAT月次", marker_color="rgba(255,71,87,0.55)",
                    marker_line=dict(color=_CRIT, width=1))
    fig_cat.add_scatter(x=monthly["月"], y=monthly["CAT累積(億円)"],
                        name="累積", mode="lines+markers",
                        line=dict(color=_WARN, width=2),
                        marker=dict(size=7, color=_WARN))
    fig_cat.add_hline(y=8.0, line_dash="dash", line_color=_CRIT, line_width=1.5,
                      annotation_text="年間CAT予算 8.0億円",
                      annotation_position="top right",
                      annotation_font_color=_CRIT, annotation_font_size=9)
    fig_cat.add_hline(y=5.0, line_dash="dot", line_color=_WARN, line_width=1,
                      annotation_text="アーリーワーニング 5.0億円",
                      annotation_position="bottom right",
                      annotation_font_color=_WARN, annotation_font_size=9)
    fig_cat.update_layout(**{**_CB, "height": 195})
    st.plotly_chart(fig_cat, use_container_width=True)

with col_a:
    # Risk exposure summary
    st.markdown("##### リスク管理指標")
    risk_items = [
        ("コンバインドレシオ",        "97.2%",  "目標 <100%",   _OK),
        ("通常損害率（CAT除く）",      "63.4%",  "前年 64.1%",   _OK),
        ("CAT損失 YTD",              "3.2億円", "予算比 40%",   _OK),
        ("ソルベンシーⅡ（SCR）",      "218.5%", "目標 >180%",   _OK),
        ("前年度準備金リリース",       "+1.2%",  "保守的な準備金", _OK),
        ("再保険保護（XL発動水準）",   "5.0億円", "未到達",        _INFO_BLUE),
        ("ORSA シナリオ最悪ケース",   "168%",   "SCR比率",      _INFO_BLUE),
    ]
    rows_html = ""
    for label, value, note, vc in risk_items:
        rows_html += f"""
        <div style="display:flex;align-items:center;gap:0.3rem;
          padding:0.28rem 0;border-bottom:1px solid {_BORDER}">
          <span style="font-size:0.7rem;color:{_MUTED};flex:1">{label}</span>
          <span style="font-size:0.8rem;font-weight:700;color:{vc};white-space:nowrap">{value}</span>
          <span style="font-size:0.65rem;color:{_MUTED};min-width:72px;text-align:right">{note}</span>
        </div>"""
    st.html(f"""<div style="background:{_BG2};border:1px solid {_BORDER};
      border-radius:0.6rem;padding:0.5rem 0.75rem">{rows_html}</div>""")

    st.write("")

    # Active risk alerts
    risk_alerts = alerts_df[alerts_df["領域"].isin(["引受リスク", "資本・ソルベンシー", "コンプライアンス"])].reset_index(drop=True)
    st.markdown("##### 引受・資本リスクアラート")
    if not risk_alerts.empty:
        from lib.ui import render_alert_compact
        render_alert_compact(risk_alerts, max_height=160)

    st.write("")
    st.markdown("##### 今日の論点")
    st.markdown("""
- **CAT累積**: ハリケーン/台風シーズン前の残余予算と再保険発動水準
- **ORSA更新**: ストレスシナリオ（金利+100bp/CAT2件同時）の資本影響
- **準備金**: 前年度ロスランオフの方向性と Q2 アクチュアリーレビュー
- **再保険更改**: 7月・1月更改に向けた交渉戦略とコスト見込み
""")
