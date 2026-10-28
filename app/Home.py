from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import time

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib.ai import QUICK_QUESTIONS, build_context, get_insight
from lib.ai_ceo import (
    RISK_SCENARIOS_CEO,
    build_ceo_context,
    get_risk_scenario_ceo,
)
from lib.data import now_jst, wide_to_long
from lib.industry import (
    insurance_alerts,
    insurance_cat_events,
    insurance_cr_by_segment,
    insurance_financial_monthly,
    insurance_gwp_by_geo,
    insurance_kpis,
    insurance_pnl_waterfall,
    insurance_security_timeseries,
    insurance_solvency_sensitivity,
    insurance_timeseries,
)
from lib.role_md import load_role_markdown
from lib.ui import (
    _BG, _BG2, _BG3, _BORDER, _CRIT, _INFO_BLUE, _MUTED, _OK, _TEXT, _WARN,
    ROLE_COLORS,
    cockpit_header,
    gauge_chart,
    inject_role_theme,
    kpi_mini_row,
    render_alert_compact,
    setup_page,
)

_GRID = "rgba(77,159,255,0.08)"
_CB = dict(
    plot_bgcolor=_BG2,
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color=_TEXT, size=10),
    margin=dict(l=8, r=8, t=6, b=6),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=_TEXT), orientation="h", y=1.08, x=0),
    legend_title_text="",
    xaxis=dict(showgrid=True, gridcolor=_GRID, color=_MUTED, linecolor=_GRID),
    yaxis=dict(showgrid=True, gridcolor=_GRID, color=_MUTED, linecolor=_GRID),
)

setup_page("Management Cockpit", cockpit=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "ceo_drill" not in st.session_state:
    st.session_state["ceo_drill"] = None
if "ceo_risk_scenario" not in st.session_state:
    st.session_state["ceo_risk_scenario"] = None
if "ai_question" not in st.session_state:
    st.session_state["ai_question"] = None
if "ai_response" not in st.session_state:
    st.session_state["ai_response"] = None

# ── Data ─────────────────────────────────────────────────────────────────────
base_alerts = insurance_alerts()
updated_at  = now_jst().strftime("%Y-%m-%d %H:%M JST")
md          = load_role_markdown("CEO")  # type: ignore[arg-type]
cfg         = md.config

kmap = {k.key: k for k in insurance_kpis()}

_CEO_ROW1 = ["gwp_total_ytd", "op_profit_ytd", "combined_ratio", "solvency_ratio"]
_CEO_ROW2 = ["nbv_ytd", "cat_loss_ytd", "gwp_nonlife_ytd", "gwp_life_ytd"]

# Drill-down available for these keys (others show no button)
_DRILLABLE = {"gwp_total_ytd", "op_profit_ytd", "combined_ratio", "solvency_ratio", "cat_loss_ytd"}

inject_role_theme("CEO")
cockpit_header("CEO", base_alerts, updated_at)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _drill_button_row(keys: list[str]) -> None:
    """Render a row of small drill-down toggle buttons aligned with KPI cards."""
    cols = st.columns(len(keys))
    for col, key in zip(cols, keys):
        with col:
            if key in _DRILLABLE and key in kmap:
                active = st.session_state["ceo_drill"] == key
                label  = "▼ 閉じる" if active else "▶ 詳細"
                if st.button(label, key=f"drill_btn_{key}", use_container_width=True):
                    st.session_state["ceo_drill"] = None if active else key
                    st.session_state["ai_response"] = None  # reset AI if drill changes
                    st.rerun()


def _drill_panel_header(title: str) -> None:
    close_col, _ = st.columns([1, 8])
    with close_col:
        if st.button("✕ 閉じる", key="drill_close"):
            st.session_state["ceo_drill"] = None
            st.rerun()
    st.markdown(f"##### {title}")
    st.html(f"<div style='height:2px;background:linear-gradient(90deg,{_INFO_BLUE},transparent);margin-bottom:0.6rem'></div>")


def _render_drill_combined_ratio() -> None:
    _drill_panel_header("コンバインドレシオ — 損保種目別内訳")
    seg = insurance_cr_by_segment()
    seg["CR(%)"] = seg["損害率(%)"] + seg["費用率(%)"]

    dc1, dc2 = st.columns([1.8, 1.2], gap="small")
    with dc1:
        fig = px.bar(
            wide_to_long(seg, "種目", ["損害率(%)", "費用率(%)"]),
            x="種目", y="value", color="series",
            barmode="stack", height=220,
            color_discrete_sequence=[_CRIT, _WARN],
            labels={"value": "%", "series": ""},
            text_auto=False,
        )
        fig.add_hline(y=100, line_dash="dash", line_color=_OK, line_width=1.5,
                      annotation_text="引受損益分岐 100%",
                      annotation_position="top right",
                      annotation_font_color=_OK, annotation_font_size=9)
        fig.update_layout(**_CB)
        st.plotly_chart(fig, use_container_width=True)

    with dc2:
        rows_html = ""
        for _, r in seg.iterrows():
            cr = r["損害率(%)"] + r["費用率(%)"]
            color = _OK if cr < 100 else _CRIT
            rows_html += (
                f"<div style='display:flex;align-items:center;gap:0.5rem;"
                f"padding:0.3rem 0;border-bottom:1px solid {_BORDER}'>"
                f"<span style='font-size:0.75rem;color:{_MUTED};flex:1'>{r['種目']}</span>"
                f"<span style='font-size:0.75rem;color:{_INFO_BLUE}'>{r['保険料シェア(%)']}%</span>"
                f"<span style='font-size:0.8rem;font-weight:700;color:{color};min-width:52px;text-align:right'>"
                f"{cr:.1f}%</span></div>"
            )
        st.html(f"""
        <div style='background:{_BG2};border:1px solid {_BORDER};border-radius:0.5rem;padding:0.5rem 0.75rem'>
          <div style='font-size:0.68rem;color:{_MUTED};margin-bottom:0.3rem;font-weight:600;letter-spacing:0.5px'>
            種目 &nbsp;｜&nbsp; 保険料シェア &nbsp;｜&nbsp; CR</div>
          {rows_html}
        </div>""")


def _render_drill_gwp() -> None:
    _drill_panel_header("元受保険料 — 地域別内訳（億円）")
    geo = insurance_gwp_by_geo()
    geo["合計(億円)"] = geo["損保(億円)"] + geo["生保(億円)"]
    geo = geo.sort_values("合計(億円)", ascending=False)

    dc1, dc2 = st.columns([1.8, 1.2], gap="small")
    with dc1:
        fig = px.bar(
            wide_to_long(geo, "地域", ["損保(億円)", "生保(億円)"]),
            x="地域", y="value", color="series",
            barmode="stack", height=220,
            color_discrete_sequence=[_INFO_BLUE, "#10d98a"],
            labels={"value": "億円", "series": ""},
        )
        fig.update_layout(**_CB)
        st.plotly_chart(fig, use_container_width=True)

    with dc2:
        rows_html = ""
        for _, r in geo.iterrows():
            yoy_color = _OK if r["前年比(%)"] >= 0 else _CRIT
            yoy_sign  = "+" if r["前年比(%)"] >= 0 else ""
            rows_html += (
                f"<div style='display:flex;align-items:center;gap:0.5rem;"
                f"padding:0.3rem 0;border-bottom:1px solid {_BORDER}'>"
                f"<span style='font-size:0.72rem;color:{_MUTED};flex:1'>{r['地域']}</span>"
                f"<span style='font-size:0.78rem;font-weight:700;color:{_TEXT};min-width:52px;text-align:right'>"
                f"{r['合計(億円)']:.1f}億円</span>"
                f"<span style='font-size:0.72rem;color:{yoy_color};min-width:48px;text-align:right'>"
                f"{yoy_sign}{r['前年比(%)']:.1f}%</span></div>"
            )
        st.html(f"""
        <div style='background:{_BG2};border:1px solid {_BORDER};border-radius:0.5rem;padding:0.5rem 0.75rem'>
          <div style='font-size:0.68rem;color:{_MUTED};margin-bottom:0.3rem;font-weight:600;letter-spacing:0.5px'>
            地域 &nbsp;｜&nbsp; 合計 &nbsp;｜&nbsp; 前年比</div>
          {rows_html}
        </div>""")


def _render_drill_solvency() -> None:
    _drill_panel_header("ソルベンシーⅡ比率 — シナリオ感応度分析")
    sens = insurance_solvency_sensitivity()

    dc1, dc2 = st.columns([2, 1], gap="small")
    with dc1:
        colors = [
            _OK if v >= 200 else (_WARN if v >= 150 else _CRIT)
            for v in sens["SCR比率(%)"]
        ]
        fig = go.Figure()
        fig.add_bar(
            x=sens["シナリオ"], y=sens["SCR比率(%)"],
            marker_color=colors,
            marker_line=dict(width=0),
            text=[f"{v:.1f}%" for v in sens["SCR比率(%)"]],
            textposition="outside",
            textfont=dict(color=_TEXT, size=9),
        )
        fig.add_hline(y=150, line_dash="dash", line_color=_CRIT, line_width=1.5,
                      annotation_text="規制最低 100%+バッファー 150%",
                      annotation_position="top right",
                      annotation_font_color=_CRIT, annotation_font_size=9)
        fig.add_hline(y=100, line_dash="dot", line_color=_WARN, line_width=1,
                      annotation_text="規制最低 100%",
                      annotation_position="bottom right",
                      annotation_font_color=_WARN, annotation_font_size=9)
        fig.update_layout(**{**_CB, "height": 230, "yaxis": {**_CB["yaxis"], "range": [0, 260]}})
        st.plotly_chart(fig, use_container_width=True)

    with dc2:
        rows_html = ""
        for _, r in sens.iterrows():
            v = r["影響(pp)"]
            color = _OK if v >= 0 else (_WARN if v > -30 else _CRIT)
            sign  = "+" if v > 0 else ""
            rows_html += (
                f"<div style='display:flex;align-items:center;gap:0.5rem;"
                f"padding:0.3rem 0;border-bottom:1px solid {_BORDER}'>"
                f"<span style='font-size:0.7rem;color:{_MUTED};flex:1;line-height:1.3'>{r['シナリオ']}</span>"
                f"<span style='font-size:0.78rem;font-weight:700;color:{color};min-width:60px;text-align:right'>"
                f"{sign}{v:.1f}pp</span></div>"
            )
        st.html(f"""
        <div style='background:{_BG2};border:1px solid {_BORDER};border-radius:0.5rem;padding:0.5rem 0.75rem'>
          <div style='font-size:0.68rem;color:{_MUTED};margin-bottom:0.3rem;font-weight:600'>
            シナリオ &nbsp;｜&nbsp; SCR比率への影響</div>
          {rows_html}
        </div>""")


def _render_drill_bop() -> None:
    _drill_panel_header("事業利益（BOP）— P&L ウォーターフォール（YTD 億円）")
    wf = insurance_pnl_waterfall()

    colors_map = {"absolute": _INFO_BLUE, "total": _OK, "relative": None}
    marker_colors = []
    for _, r in wf.iterrows():
        if r["measure"] == "absolute":
            marker_colors.append(_INFO_BLUE)
        elif r["measure"] == "total":
            marker_colors.append(_OK)
        else:
            marker_colors.append(_OK if r["金額(億円)"] >= 0 else _CRIT)

    fig = go.Figure(go.Waterfall(
        x=wf["項目"].tolist(),
        y=wf["金額(億円)"].tolist(),
        measure=wf["measure"].tolist(),
        connector=dict(line=dict(color=_BORDER, width=1, dash="dot")),
        increasing=dict(marker=dict(color=_OK)),
        decreasing=dict(marker=dict(color=_CRIT)),
        totals=dict(marker=dict(color=_INFO_BLUE)),
        text=[f"{v:+.1f}" for v in wf["金額(億円)"]],
        textposition="outside",
        textfont=dict(color=_TEXT, size=9),
    ))
    fig.update_layout(**{
        **_CB,
        "height": 250,
        "plot_bgcolor": _BG2,
        "xaxis": {**_CB["xaxis"], "tickangle": -20, "tickfont": {"size": 9}},
    })
    st.plotly_chart(fig, use_container_width=True)


def _render_drill_cat() -> None:
    _drill_panel_header("CAT損失 — イベント別明細（YTD）")
    ev = insurance_cat_events()

    dc1, dc2 = st.columns([1.6, 1.4], gap="small")
    with dc1:
        fig = go.Figure()
        fig.add_bar(
            x=ev["イベント"], y=ev["グロス損失(億円)"],
            name="グロス損失", marker_color=f"rgba(255,71,87,0.55)",
            marker_line=dict(color=_CRIT, width=1),
        )
        fig.add_bar(
            x=ev["イベント"], y=ev["純損失(億円)"],
            name="純損失（再保後）", marker_color=f"rgba(245,166,35,0.7)",
            marker_line=dict(color=_WARN, width=1),
        )
        budget_remaining = 8.0 - ev["純損失(億円)"].sum()
        fig.update_layout(**{
            **_CB,
            "height": 230,
            "barmode": "overlay",
            "xaxis": {**_CB["xaxis"], "tickfont": {"size": 8}},
        })
        st.plotly_chart(fig, use_container_width=True)

    with dc2:
        total_gross = ev["グロス損失(億円)"].sum()
        total_net   = ev["純損失(億円)"].sum()
        budget_pct  = total_net / 8.0 * 100

        st.html(f"""
        <div style='background:{_BG2};border:1px solid {_BORDER};border-radius:0.5rem;padding:0.6rem 0.8rem;margin-bottom:0.5rem'>
          <div style='font-size:0.68rem;color:{_MUTED};margin-bottom:0.4rem;font-weight:600'>YTD サマリー</div>
          <div style='display:flex;justify-content:space-between;margin-bottom:0.25rem'>
            <span style='font-size:0.72rem;color:{_MUTED}'>グロス損失合計</span>
            <span style='font-size:0.82rem;font-weight:700;color:{_CRIT}'>{total_gross:.2f}億円</span>
          </div>
          <div style='display:flex;justify-content:space-between;margin-bottom:0.25rem'>
            <span style='font-size:0.72rem;color:{_MUTED}'>純損失合計（再保後）</span>
            <span style='font-size:0.82rem;font-weight:700;color:{_WARN}'>{total_net:.2f}億円</span>
          </div>
          <div style='display:flex;justify-content:space-between;margin-bottom:0.25rem'>
            <span style='font-size:0.72rem;color:{_MUTED}'>年間CAT予算消化率</span>
            <span style='font-size:0.82rem;font-weight:700;color:{"#f5a623" if budget_pct < 70 else _CRIT}'>{budget_pct:.1f}%</span>
          </div>
          <div style='display:flex;justify-content:space-between'>
            <span style='font-size:0.72rem;color:{_MUTED}'>残余予算</span>
            <span style='font-size:0.82rem;font-weight:700;color:{_OK}'>{8.0 - total_net:.2f}億円</span>
          </div>
        </div>""")

        rows_html = ""
        for _, r in ev.iterrows():
            rows_html += (
                f"<div style='font-size:0.7rem;color:{_MUTED};padding:0.25rem 0;"
                f"border-bottom:1px solid {_BORDER};display:flex;gap:0.5rem'>"
                f"<span style='flex:1'>{r['イベント']}</span>"
                f"<span style='color:{_WARN}'>{r['純損失(億円)']:.2f}億円</span>"
                f"<span style='color:{_INFO_BLUE};min-width:38px;text-align:right'>"
                f"回収{r['回収率(%)']:.0f}%</span></div>"
            )
        st.html(f"""
        <div style='background:{_BG2};border:1px solid {_BORDER};border-radius:0.5rem;
          padding:0.5rem 0.75rem;max-height:130px;overflow-y:auto'>
          {rows_html}
        </div>""")


def _render_drill(key: str) -> None:
    with st.container():
        st.html(f"<div style='background:{_BG2};border:1px solid {_INFO_BLUE};"
                f"border-radius:0.65rem;padding:0.65rem 0.85rem;margin:0.3rem 0 0.5rem'>")
        if key == "combined_ratio":
            _render_drill_combined_ratio()
        elif key == "gwp_total_ytd":
            _render_drill_gwp()
        elif key == "solvency_ratio":
            _render_drill_solvency()
        elif key == "op_profit_ytd":
            _render_drill_bop()
        elif key == "cat_loss_ytd":
            _render_drill_cat()
        st.html("</div>")


# ── KPI row 1: Top-line & Bottom-line ────────────────────────────────────────
kpi_mini_row([kmap[k] for k in _CEO_ROW1 if k in kmap])
_drill_button_row(_CEO_ROW1)

if st.session_state["ceo_drill"] in {k for k in _CEO_ROW1 if k in _DRILLABLE}:
    _render_drill(st.session_state["ceo_drill"])

st.write("")

# ── KPI row 2 ─────────────────────────────────────────────────────────────────
kpi_mini_row([kmap[k] for k in _CEO_ROW2 if k in kmap])
_drill_button_row(_CEO_ROW2)

if st.session_state["ceo_drill"] in {k for k in _CEO_ROW2 if k in _DRILLABLE}:
    _render_drill(st.session_state["ceo_drill"])

st.write("")

# ── Main row: gauges | monthly charts | alerts + P&L ─────────────────────────
col_g, col_c, col_a = st.columns([1.0, 2.6, 1.4], gap="small")

with col_g:
    st.markdown("##### 閾値モニター")
    for key in ("combined_ratio", "solvency_ratio", "attritional_lr"):
        if key in kmap:
            st.plotly_chart(gauge_chart(kmap[key], height=155), use_container_width=True)

with col_c:
    monthly = insurance_financial_monthly()

    st.markdown("##### 元受保険料（月次・損保 / 生保）　単位: 億円")
    fig_gwp = px.bar(
        wide_to_long(monthly, "月", ["元受保険料（損保）", "元受保険料（生保）"]),
        x="月", y="value", color="series",
        barmode="stack", height=255,
        color_discrete_sequence=["#4d9fff", "#10d98a"],
        labels={"value": "億円", "月": "", "series": "セグメント"},
    )
    plan_total = (monthly["計画（損保）"] + monthly["計画（生保）"]).tolist()
    fig_gwp.add_scatter(
        x=monthly["月"].tolist(), y=plan_total,
        mode="lines+markers", name="計画合計",
        line=dict(color=_WARN, dash="dash", width=1.8),
        marker=dict(size=5, color=_WARN),
    )
    fig_gwp.update_layout(**_CB)
    st.plotly_chart(fig_gwp, use_container_width=True)

    st.markdown("##### コンバインドレシオ内訳（月次）")
    fig_cr = px.bar(
        wide_to_long(monthly, "月", ["損害率(%)", "費用率(%)"]),
        x="月", y="value", color="series",
        barmode="stack", height=195,
        color_discrete_sequence=["#ff4757", "#f5a623"],
        labels={"value": "%", "月": "", "series": ""},
        text_auto=False,
    )
    fig_cr.add_scatter(
        x=monthly["月"].tolist(),
        y=monthly["コンバインドレシオ"].tolist(),
        mode="lines+markers", name="CR合計",
        line=dict(color=_TEXT, width=1.2, dash="dot"),
        marker=dict(size=4),
    )
    fig_cr.add_hline(
        y=100, line_dash="dash", line_color=_OK, line_width=1.5,
        annotation_text="引受損益分岐 100%",
        annotation_position="bottom right",
        annotation_font_color=_OK, annotation_font_size=9,
    )
    fig_cr.update_layout(**_CB)
    st.plotly_chart(fig_cr, use_container_width=True)

with col_a:
    crit_c = int((base_alerts["重要度"] == "CRIT").sum())
    warn_c = int((base_alerts["重要度"] == "WARN").sum())
    st.markdown("##### 重要アラート（24h）")
    st.html(
        f"<div style='margin:-0.35rem 0 0.4rem;font-size:0.75rem;color:{_MUTED}'>"
        f"CRIT&nbsp;<b style='color:{_CRIT}'>{crit_c}</b>"
        f"&nbsp;&nbsp;WARN&nbsp;<b style='color:{_WARN}'>{warn_c}</b></div>"
    )
    render_alert_compact(base_alerts, max_height=220)

    st.write("")
    st.markdown("##### P&L サマリー（YTD 概算）")

    pnl_rows = [
        ("元受保険料合計",    "142.6億円", f"計画比 <b style='color:{_OK}'>+3.1%</b>"),
        ("正味収入保険料",    "128.1億円", "再保険後"),
        ("引受損益（損保）",  "+2.8億円",  f"CoR <b style='color:{_OK}'>97.2%</b>"),
        ("生保事業利益",      "+5.6億円",  f"NBM <b style='color:{_OK}'>5.3%</b>"),
        ("投資収益",          "+11.6億円", "利回り 3.4%"),
        ("その他・持株費用",  "−2.8億円",  "—"),
        ("事業利益（BOP）",   "17.2億円",  f"計画比 <b style='color:{_OK}'>+4.2%</b>"),
        ("グループ純利益",    "11.8億円",  f"ROE <b style='color:{_OK}'>15.5%</b>"),
    ]
    rows_html = ""
    for label, value, note in pnl_rows:
        is_subtotal = label in ("事業利益（BOP）", "グループ純利益")
        border_top  = f"border-top:1px solid {_INFO_BLUE};" if is_subtotal else ""
        val_color   = _INFO_BLUE if is_subtotal else _TEXT
        rows_html += f"""
        <div style="display:flex;align-items:center;gap:0.4rem;
          padding:0.28rem 0;border-bottom:1px solid {_BORDER};{border_top}">
          <span style="font-size:0.7rem;color:{_MUTED};flex:1">{label}</span>
          <span style="font-size:0.8rem;font-weight:{'800' if is_subtotal else '600'};
            color:{val_color};white-space:nowrap">{value}</span>
          <span style="font-size:0.65rem;color:{_MUTED};min-width:80px;
            text-align:right">{note}</span>
        </div>"""
    st.html(f"""
    <div style="background:{_BG2};border:1px solid {_BORDER};
      border-radius:0.6rem;padding:0.5rem 0.75rem">
      {rows_html}
    </div>""")

    st.write("")
    st.markdown("##### 本日のポイント")
    if md.highlights:
        items = "".join(
            f"<div style='font-size:0.72rem;color:{_MUTED};line-height:1.65;padding:0.08rem 0'>"
            f"<span style='color:{_INFO_BLUE}'>▶</span>&nbsp;{h}</div>"
            for h in md.highlights[:4]
        )
        st.html(items)

# ── Bottom bar ────────────────────────────────────────────────────────────────
st.write("")
bc1, bc2, bc3 = st.columns(3, gap="small")

with bc1:
    st.markdown("##### サイバー脅威検知（30日）")
    sec_ts = insurance_security_timeseries()
    figb1 = px.bar(
        wide_to_long(sec_ts, "date", ["CRIT", "WARN", "INFO"]),
        x="date", y="value", color="series", barmode="stack",
        color_discrete_map={"CRIT": _CRIT, "WARN": _WARN, "INFO": _INFO_BLUE},
        height=200, labels={"value": "件数", "date": "", "series": "重要度"},
    )
    figb1.update_layout(**{**_CB, "yaxis": {**_CB["yaxis"], "dtick": 1}})
    st.plotly_chart(figb1, use_container_width=True)

with bc2:
    st.markdown("##### アラート領域分布")
    domain_counts = base_alerts.groupby("領域").size().reset_index(name="件数")
    figb2 = px.pie(
        domain_counts, names="領域", values="件数", hole=0.52,
        color_discrete_sequence=[_CRIT, _WARN, _INFO_BLUE, _OK, "#a78bfa", "#fb923c", "#06b6d4", "#e879f9"],
        height=200,
    )
    figb2.update_layout(**{**_CB, "showlegend": True,
                           "legend": dict(bgcolor="rgba(0,0,0,0)", font=dict(color=_TEXT, size=9),
                                          orientation="v", x=1.0, y=0.5)})
    figb2.update_traces(textposition="inside", textinfo="percent+label",
                        textfont=dict(color="#ffffff", size=9))
    st.plotly_chart(figb2, use_container_width=True)

with bc3:
    st.markdown("##### CAT損失累積 vs 年間予算（月次）　単位: 億円")
    monthly3 = insurance_financial_monthly()
    fig_cat = go.Figure()
    fig_cat.add_bar(
        x=monthly3["月"], y=monthly3["CAT損失(億円)"],
        name="CAT月次", marker_color=f"rgba(255,71,87,0.55)",
        marker_line=dict(color=_CRIT, width=1),
    )
    fig_cat.add_scatter(
        x=monthly3["月"], y=monthly3["CAT累積(億円)"],
        name="累積損失", mode="lines+markers",
        line=dict(color=_WARN, width=2),
        marker=dict(size=6, color=_WARN),
    )
    fig_cat.add_hline(
        y=8.0, line_dash="dash", line_color=_CRIT, line_width=1.5,
        annotation_text="年間CAT予算 8.0億円",
        annotation_position="top right",
        annotation_font_color=_CRIT, annotation_font_size=9,
    )
    fig_cat.update_layout(**{**_CB, "height": 200, "legend_title_text": ""})
    st.plotly_chart(fig_cat, use_container_width=True)


# ── AI Insights ───────────────────────────────────────────────────────────────
st.write("")
st.html(f"""
<div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.4rem">
  <div style="font-size:1.1rem">🤖</div>
  <div style="font-size:0.9rem;font-weight:800;color:{_TEXT};letter-spacing:0.3px">
    AI インサイト — グローバルリスク・経営判断支援</div>
  <div style="font-size:0.72rem;color:{_MUTED};margin-left:0.4rem">
    影響領域・方向・理由を構造化（モック）</div>
</div>
<div style="height:1px;background:linear-gradient(90deg,{_INFO_BLUE},transparent);margin-bottom:0.6rem"></div>
""")

# ── Section 1: Risk Scenario Selector ─────────────────────────────────────────
st.html(f"<div style='font-size:0.75rem;color:{_MUTED};font-weight:700;"
        f"letter-spacing:0.8px;text-transform:uppercase;margin-bottom:0.4rem'>"
        f"🌐 グローバルリスクシナリオを選択</div>")

for row_start in range(0, len(RISK_SCENARIOS_CEO), 4):
    row_scenarios = RISK_SCENARIOS_CEO[row_start:row_start + 4]
    rcols = st.columns(len(row_scenarios), gap="small")
    for col, s in zip(rcols, row_scenarios):
        with col:
            active = st.session_state["ceo_risk_scenario"] == s["key"]
            if st.button(
                f"{s['icon']} {s['label']}",
                key=f"ceo_risk_{s['key']}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                if active:
                    st.session_state["ceo_risk_scenario"] = None
                    st.session_state["ai_question"]       = None
                    st.session_state["ai_response"]       = None
                else:
                    st.session_state["ceo_risk_scenario"] = s["key"]
                    st.session_state["ai_question"]       = f"[RISK] {s['key']}"
                    st.session_state["ai_response"]       = None
                st.rerun()

st.write("")

# ── Section 2: Quick questions ────────────────────────────────────────────────
st.html(f"<div style='font-size:0.75rem;color:{_MUTED};font-weight:700;"
        f"letter-spacing:0.8px;text-transform:uppercase;margin-bottom:0.4rem'>"
        f"💬 CEO クイック質問</div>")
ai_cols = st.columns(len(QUICK_QUESTIONS), gap="small")
for col, q in zip(ai_cols, QUICK_QUESTIONS):
    with col:
        if st.button(q, key=f"ai_quick_{q}", use_container_width=True):
            st.session_state["ceo_risk_scenario"] = None
            st.session_state["ai_question"]       = q
            st.session_state["ai_response"]       = None
            st.rerun()

# ── Section 3: Custom input ───────────────────────────────────────────────────
custom_q = st.text_input(
    "カスタム質問",
    placeholder="例：ハリケーン上陸シナリオで来月の取締役会向け説明をまとめて",
    label_visibility="collapsed",
)
send_col, _ = st.columns([1, 8])
with send_col:
    if st.button("送信 →", type="primary", use_container_width=True):
        if custom_q.strip():
            st.session_state["ceo_risk_scenario"] = None
            st.session_state["ai_question"]       = custom_q.strip()
            st.session_state["ai_response"]       = None
            st.rerun()

# ── Response area ─────────────────────────────────────────────────────────────
question  = st.session_state.get("ai_question")
risk_key  = st.session_state.get("ceo_risk_scenario")

if question:
    label = ""
    if risk_key:
        s = next((s for s in RISK_SCENARIOS_CEO if s["key"] == risk_key), None)
        if s:
            label = f"{s['icon']} リスクシナリオ: **{s['label']}**"
    else:
        label = f"▶ {question}"

    if label:
        st.html(f"<div style='font-size:0.72rem;color:{_MUTED};margin:0.4rem 0 0.2rem'>{label}</div>")

    response_box = st.empty()

    if st.session_state.get("ai_response"):
        response_box.markdown(st.session_state["ai_response"])
    else:
        ctx = build_ceo_context(kmap, base_alerts)
        if risk_key and question.startswith("[RISK]"):
            text = get_risk_scenario_ceo(risk_key, ctx)
        else:
            text = get_insight(question, build_context(kmap, base_alerts))
        words = text.split(" ")
        displayed = ""
        for i, word in enumerate(words):
            displayed += ("" if i == 0 else " ") + word
            response_box.markdown(displayed + " ▌")
            time.sleep(0.025)
        response_box.markdown(displayed)
        st.session_state["ai_response"] = displayed

    if st.button("クリア", key="ai_clear"):
        st.session_state["ceo_risk_scenario"] = None
        st.session_state["ai_question"]       = None
        st.session_state["ai_response"]       = None
        st.rerun()
