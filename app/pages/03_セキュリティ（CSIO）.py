from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import plotly.express as px
import streamlit as st

from lib.data import now_jst, wide_to_long
from lib.industry import insurance_alerts, insurance_kpis, insurance_security_timeseries
from lib.ui import (
    _BG2, _BORDER, _CRIT, _INFO_BLUE, _MUTED, _OK, _TEXT, _WARN,
    cockpit_header, gauge_chart, inject_role_theme, kpi_mini_row,
    render_alert_compact, setup_page, status_banner,
)

_GRID = "rgba(77,159,255,0.08)"
_CB = dict(plot_bgcolor=_BG2, paper_bgcolor="rgba(0,0,0,0)",
           font=dict(color=_TEXT, size=10), margin=dict(l=8,r=8,t=6,b=6),
           legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=_TEXT), orientation="h", y=1.08, x=0),
           legend_title_text="",
           xaxis=dict(showgrid=True,gridcolor=_GRID,color=_MUTED,linecolor=_GRID),
           yaxis=dict(showgrid=True,gridcolor=_GRID,color=_MUTED,linecolor=_GRID))

setup_page("セキュリティ・情報（CSIO）", cockpit=True)
inject_role_theme("CSIO")

updated_at  = now_jst().strftime("%Y-%m-%d %H:%M JST")
alerts      = insurance_alerts()
cockpit_header("CSIO", alerts, updated_at)

km = {k.key: k for k in insurance_kpis()}

# ── KPI rows ─────────────────────────────────────────────────────────────────
row1_keys = ["cyber_risk_score", "system_avail", "combined_ratio", "solvency_ratio"]
row2_keys = ["loss_ratio", "claims_ttd", "persistency_rate", "expense_ratio"]
kpi_mini_row([km[k] for k in row1_keys if k in km])
st.write("")
kpi_mini_row([km[k] for k in row2_keys if k in km])
st.write("")

# Status banner for cyber alerts
cyber_alerts = alerts[alerts["領域"].isin(["サイバー", "システム"])].reset_index(drop=True)
status_banner(cyber_alerts)

# ── Main row ──────────────────────────────────────────────────────────────────
col_g, col_c, col_a = st.columns([1.0, 2.6, 1.4], gap="small")

with col_g:
    st.markdown("##### 閾値モニター")
    for key in ("cyber_risk_score", "system_avail", "combined_ratio"):
        if key in km:
            st.plotly_chart(gauge_chart(km[key], height=155), use_container_width=True)

with col_c:
    st.markdown("##### サイバー脅威検知トレンド（30日）")
    sec_ts = insurance_security_timeseries()
    fig_sec = px.bar(
        wide_to_long(sec_ts, "date", ["CRIT", "WARN", "INFO"]),
        x="date", y="value", color="series", barmode="stack",
        color_discrete_map={"CRIT": _CRIT, "WARN": _WARN, "INFO": _INFO_BLUE},
        height=255,
        labels={"value": "件数", "date": "日付", "series": "重要度"},
    )
    fig_sec.update_layout(**{**_CB, "yaxis": {**_CB["yaxis"], "dtick": 1}})
    st.plotly_chart(fig_sec, use_container_width=True)

    # Alert domain distribution
    st.markdown("##### アラート領域分布（全体）")
    domain_counts = alerts.groupby("領域").size().reset_index(name="件数")
    fig2 = px.pie(
        domain_counts, names="領域", values="件数", hole=0.55,
        color_discrete_sequence=[_CRIT, _WARN, _INFO_BLUE, _OK, "#a78bfa", "#fb923c", "#06b6d4", "#e879f9"],
        height=195,
    )
    fig2.update_layout(**{**_CB, "showlegend": True,
                          "legend": dict(bgcolor="rgba(0,0,0,0)", font=dict(color=_TEXT, size=9))})
    fig2.update_traces(textposition="inside", textinfo="percent+label",
                       textfont=dict(color="#ffffff", size=10))
    st.plotly_chart(fig2, use_container_width=True)

with col_a:
    st.markdown("##### サイバーリスク指標")
    csio_items = [
        ("サイバーリスクスコア",        "72 pt",  "目標 >60",      _OK),
        ("外部公開資産 脆弱性",          "3件",    "CVSS >8.0",    _WARN),
        ("代理店ポータル 不正試行",      "412件/日","昨日比 +82%",  _WARN),
        ("EDR エンドポイント適用率",     "99.1%",  "目標 >99%",     _OK),
        ("MFA 適用率（特権ID）",        "100%",   "完全適用",       _OK),
        ("セキュリティパッチ適用率",     "94.8%",  "目標 >95%",     _WARN),
        ("GDPR データ保護影響評価",     "3件 進行中","期限 30日内", _INFO_BLUE),
        ("ペネトレーションテスト",       "完了",   "重大リスク 0件", _OK),
    ]
    rows_html = ""
    for label, value, note, vc in csio_items:
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
    st.markdown("##### 重要アラート（サイバー）")
    render_alert_compact(cyber_alerts, max_height=140)

    st.write("")
    st.markdown("##### 初動確認")
    st.markdown("""
- **影響範囲**: 顧客・契約データ・送金系への到達可能性を確認
- **封じ込め**: 端末隔離・特権ID無効化・外部接続遮断の実施
- **GDPR 72h**: 個人データ侵害は当局へ72時間以内に報告義務
- **EIOPA通知**: 重大インシデントは規制当局への報告を検討
""")
