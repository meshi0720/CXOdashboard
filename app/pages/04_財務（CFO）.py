from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))


import time

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib.ai_cfo import (
    QUICK_QUESTIONS_CFO,
    RISK_SCENARIOS,
    build_cfo_context,
    get_cfo_insight,
    get_risk_scenario,
)
from lib.data import now_jst
from lib.industry import (
    insurance_alerts,
    insurance_expense_by_category,
    insurance_financial_monthly,
    insurance_investment_by_class,
    insurance_kpis,
    insurance_pnl_waterfall,
    insurance_solvency_sensitivity,
    insurance_timeseries,
)
from lib.ui import (
    _BG, _BG2, _BG3, _BORDER, _CRIT, _INFO_BLUE, _MUTED, _OK, _TEXT, _WARN,
    cockpit_header, gauge_chart, inject_role_theme, kpi_mini_row, setup_page,
)

_GRID = "rgba(77,159,255,0.08)"
_CFO_ACCENT = "#10d98a"  # CFO role color
_CB = dict(
    plot_bgcolor=_BG2, paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color=_TEXT, size=10), margin=dict(l=8, r=8, t=6, b=6),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=_TEXT), orientation="h", y=1.08, x=0),
    legend_title_text="",
    xaxis=dict(showgrid=True, gridcolor=_GRID, color=_MUTED, linecolor=_GRID),
    yaxis=dict(showgrid=True, gridcolor=_GRID, color=_MUTED, linecolor=_GRID),
)

setup_page("財務（CFO）", cockpit=True)
inject_role_theme("CFO")

# ── Session state ─────────────────────────────────────────────────────────────
if "cfo_drill" not in st.session_state:
    st.session_state["cfo_drill"] = None
if "cfo_risk_scenario" not in st.session_state:
    st.session_state["cfo_risk_scenario"] = None
if "cfo_ai_question" not in st.session_state:
    st.session_state["cfo_ai_question"] = None
if "cfo_ai_response" not in st.session_state:
    st.session_state["cfo_ai_response"] = None

# ── Data ──────────────────────────────────────────────────────────────────────
updated_at = now_jst().strftime("%Y-%m-%d %H:%M JST")
alerts_df  = insurance_alerts()
cockpit_header("CFO", alerts_df, updated_at)

km = {k.key: k for k in insurance_kpis()}

row1_keys = ["solvency_ratio", "op_profit_ytd", "net_income_ytd", "group_roe"]
row2_keys = ["investment_return", "gwp_plan_ratio", "expense_ratio", "combined_ratio"]

_DRILLABLE_CFO = {"solvency_ratio", "op_profit_ytd", "investment_return", "expense_ratio"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _drill_button_row(keys: list[str]) -> None:
    cols = st.columns(len(keys))
    for col, key in zip(cols, keys):
        with col:
            if key in _DRILLABLE_CFO and key in km:
                active = st.session_state["cfo_drill"] == key
                label  = "▼ 閉じる" if active else "▶ 詳細"
                if st.button(label, key=f"cfo_drill_{key}", use_container_width=True):
                    st.session_state["cfo_drill"] = None if active else key
                    st.rerun()


def _drill_panel_header(title: str) -> None:
    close_col, _ = st.columns([1, 8])
    with close_col:
        if st.button("✕ 閉じる", key=f"cfo_close_{title[:6]}"):
            st.session_state["cfo_drill"] = None
            st.rerun()
    st.markdown(f"##### {title}")
    st.html(f"<div style='height:2px;background:linear-gradient(90deg,{_CFO_ACCENT},transparent);margin-bottom:0.6rem'></div>")


def _render_drill_solvency() -> None:
    _drill_panel_header("ソルベンシーⅡ比率 — シナリオ感応度")
    sens = insurance_solvency_sensitivity()

    dc1, dc2 = st.columns([2, 1], gap="small")
    with dc1:
        colors = [_OK if v >= 200 else (_WARN if v >= 150 else _CRIT) for v in sens["SCR比率(%)"]]
        fig = go.Figure()
        fig.add_bar(
            x=sens["シナリオ"], y=sens["SCR比率(%)"],
            marker_color=colors, marker_line=dict(width=0),
            text=[f"{v:.1f}%" for v in sens["SCR比率(%)"]],
            textposition="outside", textfont=dict(color=_TEXT, size=9),
        )
        fig.add_hline(y=180, line_dash="dash", line_color=_WARN, line_width=1.5,
                      annotation_text="社内目標下限 180%", annotation_position="top right",
                      annotation_font_color=_WARN, annotation_font_size=9)
        fig.add_hline(y=100, line_dash="dot", line_color=_CRIT, line_width=1,
                      annotation_text="規制最低 100%", annotation_position="bottom right",
                      annotation_font_color=_CRIT, annotation_font_size=9)
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
            シナリオ別 SCR比率影響</div>
          {rows_html}
        </div>""")


def _render_drill_bop() -> None:
    _drill_panel_header("事業利益（BOP）— P&L ウォーターフォール（YTD 億円）")
    wf = insurance_pnl_waterfall()

    fig = go.Figure(go.Waterfall(
        x=wf["項目"].tolist(),
        y=wf["金額(億円)"].tolist(),
        measure=wf["measure"].tolist(),
        connector=dict(line=dict(color=_BORDER, width=1, dash="dot")),
        increasing=dict(marker=dict(color=_OK)),
        decreasing=dict(marker=dict(color=_CRIT)),
        totals=dict(marker=dict(color=_CFO_ACCENT)),
        text=[f"{v:+.1f}" for v in wf["金額(億円)"]],
        textposition="outside",
        textfont=dict(color=_TEXT, size=9),
    ))
    fig.update_layout(**{**_CB, "height": 250,
                         "xaxis": {**_CB["xaxis"], "tickangle": -20, "tickfont": {"size": 9}}})
    st.plotly_chart(fig, use_container_width=True)


def _render_drill_investment() -> None:
    _drill_panel_header("運用利回り — アセットクラス別内訳")
    inv = insurance_investment_by_class()
    inv_sorted = inv.sort_values("残高(億円)", ascending=False)

    dc1, dc2 = st.columns([1.8, 1.2], gap="small")
    with dc1:
        fig = go.Figure()
        fig.add_bar(
            x=inv_sorted["アセットクラス"], y=inv_sorted["残高(億円)"],
            name="残高（左軸）", marker_color="rgba(77,159,255,0.50)",
            marker_line=dict(color=_INFO_BLUE, width=1),
        )
        fig.add_scatter(
            x=inv_sorted["アセットクラス"], y=inv_sorted["利回り(%)"],
            name="利回り（右軸）", mode="markers",
            marker=dict(size=10, color=_CFO_ACCENT, symbol="diamond"),
            yaxis="y2",
        )
        fig.update_layout(**{
            **_CB, "height": 230,
            "yaxis":  {**_CB["yaxis"], "title": "残高（億円）"},
            "yaxis2": {"overlaying": "y", "side": "right", "title": "利回り（%）",
                       "showgrid": False, "color": _MUTED, "range": [0, 12]},
            "xaxis":  {**_CB["xaxis"], "tickfont": {"size": 8}},
        })
        st.plotly_chart(fig, use_container_width=True)

    with dc2:
        portfolio_return = sum(r["残高(億円)"] * r["利回(%)"] for _, r in
                               inv.assign(**{"利回(%)": inv["利回り(%)"]}).iterrows()) / inv["残高(億円)"].sum()
        st.html(f"""
        <div style='background:{_BG2};border:1px solid {_CFO_ACCENT};border-radius:0.5rem;
          padding:0.5rem 0.75rem;margin-bottom:0.5rem;text-align:center'>
          <div style='font-size:0.68rem;color:{_MUTED};margin-bottom:0.2rem'>加重平均利回り</div>
          <div style='font-size:1.6rem;font-weight:800;color:{_CFO_ACCENT}'>{portfolio_return:.2f}%</div>
          <div style='font-size:0.68rem;color:{_MUTED}'>総残高 {inv["残高(億円)"].sum():.1f}億円</div>
        </div>""")

        rows_html = ""
        for _, r in inv.sort_values("利回り(%)", ascending=False).iterrows():
            yoy_color = _OK if r["前年比(pp)"] >= 0 else _CRIT
            yoy_sign  = "+" if r["前年比(pp)"] >= 0 else ""
            rows_html += (
                f"<div style='display:flex;align-items:center;gap:0.4rem;"
                f"padding:0.25rem 0;border-bottom:1px solid {_BORDER}'>"
                f"<span style='font-size:0.68rem;color:{_MUTED};flex:1;line-height:1.3'>{r['アセットクラス']}</span>"
                f"<span style='font-size:0.75rem;font-weight:700;color:{_CFO_ACCENT};min-width:38px;text-align:right'>"
                f"{r['利回り(%)']:.1f}%</span>"
                f"<span style='font-size:0.68rem;color:{yoy_color};min-width:40px;text-align:right'>"
                f"{yoy_sign}{r['前年比(pp)']:.1f}pp</span></div>"
            )
        st.html(f"""
        <div style='background:{_BG2};border:1px solid {_BORDER};border-radius:0.5rem;
          padding:0.4rem 0.6rem;max-height:150px;overflow-y:auto'>
          {rows_html}
        </div>""")


def _render_drill_expense() -> None:
    _drill_panel_header("費用率 — カテゴリ別内訳（YTD）")
    exp = insurance_expense_by_category()

    dc1, dc2 = st.columns([1.8, 1.2], gap="small")
    with dc1:
        colors = [_OK if r["計画比(%)"] <= 0 else (_WARN if r["計画比(%)"] < 3 else _CRIT)
                  for _, r in exp.iterrows()]
        fig = px.bar(
            exp, x="カテゴリ", y="金額(億円)", height=230,
            color="カテゴリ",
            color_discrete_sequence=[_INFO_BLUE, "#818cf8", "#06b6d4", _CFO_ACCENT,
                                      _WARN, _CRIT, _MUTED],
            labels={"金額(億円)": "億円", "カテゴリ": ""},
        )
        fig.update_layout(**{**_CB, "showlegend": False,
                             "xaxis": {**_CB["xaxis"], "tickfont": {"size": 8}}})
        st.plotly_chart(fig, use_container_width=True)

    with dc2:
        total = exp["金額(億円)"].sum()
        rows_html = ""
        for _, r in exp.iterrows():
            plan_color = _OK if r["計画比(%)"] <= 0 else (_WARN if r["計画比(%)"] < 3 else _CRIT)
            plan_sign  = "+" if r["計画比(%)"] > 0 else ""
            rows_html += (
                f"<div style='padding:0.28rem 0;border-bottom:1px solid {_BORDER}'>"
                f"<div style='display:flex;align-items:center;gap:0.4rem'>"
                f"<span style='font-size:0.7rem;color:{_MUTED};flex:1;line-height:1.2'>{r['カテゴリ']}</span>"
                f"<span style='font-size:0.75rem;font-weight:700;color:{_TEXT}'>{r['金額(億円)']:.1f}億円</span>"
                f"<span style='font-size:0.68rem;color:{plan_color};min-width:48px;text-align:right'>"
                f"計画比{plan_sign}{r['計画比(%)']:.1f}%</span></div>"
                f"<div style='height:3px;background:rgba(77,159,255,0.15);border-radius:2px;margin-top:3px'>"
                f"<div style='height:3px;width:{r['金額(億円)']/total*100:.0f}%;background:{_INFO_BLUE};border-radius:2px'></div>"
                f"</div></div>"
            )
        st.html(f"""
        <div style='background:{_BG2};border:1px solid {_BORDER};border-radius:0.5rem;
          padding:0.5rem 0.75rem;max-height:230px;overflow-y:auto'>
          <div style='font-size:0.68rem;color:{_MUTED};margin-bottom:0.3rem;font-weight:600'>
            合計: {total:.1f}億円 &nbsp;｜&nbsp; 費用率 {km["expense_ratio"].value:.1f}%</div>
          {rows_html}
        </div>""")


def _render_drill(key: str) -> None:
    st.html(f"<div style='background:{_BG2};border:1px solid {_CFO_ACCENT};"
            f"border-radius:0.65rem;padding:0.65rem 0.85rem;margin:0.3rem 0 0.5rem'>")
    if key == "solvency_ratio":
        _render_drill_solvency()
    elif key == "op_profit_ytd":
        _render_drill_bop()
    elif key == "investment_return":
        _render_drill_investment()
    elif key == "expense_ratio":
        _render_drill_expense()
    st.html("</div>")


# ── KPI rows ──────────────────────────────────────────────────────────────────
kpi_mini_row([km[k] for k in row1_keys if k in km])
_drill_button_row(row1_keys)

if st.session_state["cfo_drill"] in {k for k in row1_keys if k in _DRILLABLE_CFO}:
    _render_drill(st.session_state["cfo_drill"])

st.write("")
kpi_mini_row([km[k] for k in row2_keys if k in km])
_drill_button_row(row2_keys)

if st.session_state["cfo_drill"] in {k for k in row2_keys if k in _DRILLABLE_CFO}:
    _render_drill(st.session_state["cfo_drill"])

st.write("")

# ── Main row ──────────────────────────────────────────────────────────────────
col_g, col_c, col_a = st.columns([1.0, 2.6, 1.4], gap="small")

with col_g:
    st.markdown("##### 閾値モニター")
    for key in ("solvency_ratio", "combined_ratio", "expense_ratio"):
        if key in km:
            st.plotly_chart(gauge_chart(km[key], height=155), use_container_width=True)

with col_c:
    monthly = insurance_financial_monthly()

    st.markdown("##### 事業利益（BOP）月次実績 vs 計画　単位: 億円")
    fig_bop = go.Figure()
    fig_bop.add_bar(x=monthly["月"], y=monthly["事業利益計画"],
                    name="計画", marker_color="rgba(77,159,255,0.22)",
                    marker_line=dict(color=_INFO_BLUE, width=1))
    fig_bop.add_bar(x=monthly["月"], y=monthly["事業利益（BOP）"],
                    name="実績", marker_color="rgba(16,217,138,0.65)",
                    marker_line=dict(color=_OK, width=1))
    fig_bop.update_layout(**{**_CB, "height": 240, "barmode": "group"})
    st.plotly_chart(fig_bop, use_container_width=True)

    st.markdown("##### ソルベンシーⅡ比率トレンド（90日）")
    ts = insurance_timeseries()
    fig_sol = px.area(ts, x="date", y="ソルベンシー比率", height=200,
                      color_discrete_sequence=[_CFO_ACCENT])
    fig_sol.update_traces(opacity=0.22, selector={"fill": "tozeroy"})
    fig_sol.add_hline(y=180, line_dash="dash", line_color=_WARN, line_width=1.5,
                      annotation_text="社内目標下限 180%",
                      annotation_position="top right",
                      annotation_font_color=_WARN, annotation_font_size=9)
    fig_sol.add_hline(y=100, line_dash="dot", line_color=_CRIT, line_width=1,
                      annotation_text="規制最低 100%",
                      annotation_position="bottom right",
                      annotation_font_color=_CRIT, annotation_font_size=9)
    fig_sol.update_layout(**{**_CB,
                              "yaxis": {**_CB["yaxis"], "range": [140, 250]},
                              "showlegend": False})
    st.plotly_chart(fig_sol, use_container_width=True)

with col_a:
    st.markdown("##### 投資ポートフォリオ構成")
    alloc_labels = ["社債", "国債・政府債", "プライベートクレジット",
                    "株式", "不動産・インフラ", "モーゲージ", "現金・その他"]
    alloc_values = [35, 28, 12, 8, 8, 6, 3]
    alloc_colors = [_INFO_BLUE, "#818cf8", "#06b6d4", _CFO_ACCENT, _WARN, "#fb923c", _MUTED]
    fig_alloc = px.pie(
        names=alloc_labels, values=alloc_values, hole=0.55,
        color_discrete_sequence=alloc_colors, height=210,
    )
    fig_alloc.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=_TEXT, size=9), margin=dict(l=0, r=0, t=4, b=4),
        showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=_TEXT, size=9),
                    orientation="v", x=1.0, y=0.5),
        legend_title_text="",
    )
    fig_alloc.update_traces(textposition="inside", textinfo="percent",
                            textfont=dict(color="#fff", size=9))
    st.plotly_chart(fig_alloc, use_container_width=True)

    st.markdown("##### 資本・収益指標")
    ratios = [
        ("ソルベンシーⅡ（SCR）",   "218.5%", "目標 >180%",  _OK),
        ("グループROE",            "15.5%",  "目標 >12%",   _OK),
        ("事業利益率（BOP/GWP）",  "12.1%",  "前年 11.4%",  _OK),
        ("運用利回り（ランニング）", "3.4%",   "前年 3.1%",   _OK),
        ("配当性向（見通し）",      "55%",    "前年 52%",    _INFO_BLUE),
        ("EIOPAレポート",          "5営業日後","Q1 提出期限", _WARN),
    ]
    rows_html = ""
    for label, value, note, vc in ratios:
        rows_html += f"""
        <div style="display:flex;align-items:center;gap:0.3rem;
          padding:0.28rem 0;border-bottom:1px solid {_BORDER}">
          <span style="font-size:0.7rem;color:{_MUTED};flex:1">{label}</span>
          <span style="font-size:0.8rem;font-weight:700;color:{vc};white-space:nowrap">{value}</span>
          <span style="font-size:0.65rem;color:{_MUTED};min-width:70px;text-align:right">{note}</span>
        </div>"""
    st.html(f"""<div style="background:{_BG2};border:1px solid {_BORDER};
      border-radius:0.6rem;padding:0.5rem 0.75rem">{rows_html}</div>""")

    st.write("")
    st.markdown("##### 今日の論点")
    st.markdown("""
- **SCR余力**: 市場変動後のソルベンシー比率推移と翌週見込み
- **BOP進捗**: 月次・YTD計画比と下半期ガイダンス修正の要否
- **EIOPA報告**: Q1 Solvency II定量報告（QRT）の提出準備状況
- **再保険費用**: 主要プロテクションの更改価格と予算影響
""")


# ── AI Insights ───────────────────────────────────────────────────────────────
st.write("")
st.html(f"""
<div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.4rem">
  <div style="font-size:1.1rem">🤖</div>
  <div style="font-size:0.9rem;font-weight:800;color:{_TEXT};letter-spacing:0.3px">
    AI インサイト — グローバルリスク・財務影響分析</div>
  <div style="font-size:0.72rem;color:{_MUTED};margin-left:0.4rem">
    指標への影響・変化幅・理由を構造化（モック）</div>
</div>
<div style="height:1px;background:linear-gradient(90deg,{_CFO_ACCENT},transparent);margin-bottom:0.6rem"></div>
""")

# ── Section 1: Risk Scenario Selector ─────────────────────────────────────────
st.html(f"<div style='font-size:0.75rem;color:{_MUTED};font-weight:700;"
        f"letter-spacing:0.8px;text-transform:uppercase;margin-bottom:0.4rem'>"
        f"🌐 グローバルリスクシナリオを選択</div>")

# 4 scenarios per row
for row_start in range(0, len(RISK_SCENARIOS), 4):
    row_scenarios = RISK_SCENARIOS[row_start:row_start + 4]
    rcols = st.columns(len(row_scenarios), gap="small")
    for col, s in zip(rcols, row_scenarios):
        with col:
            active = st.session_state["cfo_risk_scenario"] == s["key"]
            if active:
                btn_style = f"background:{s['color']};color:#000;font-weight:800"
            else:
                btn_style = ""
            if st.button(
                f"{s['icon']} {s['label']}",
                key=f"risk_{s['key']}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                if active:
                    st.session_state["cfo_risk_scenario"] = None
                    st.session_state["cfo_ai_question"]   = None
                    st.session_state["cfo_ai_response"]   = None
                else:
                    st.session_state["cfo_risk_scenario"] = s["key"]
                    st.session_state["cfo_ai_question"]   = f"[RISK] {s['key']}"
                    st.session_state["cfo_ai_response"]   = None
                st.rerun()

st.write("")

# ── Section 2: Quick questions ────────────────────────────────────────────────
st.html(f"<div style='font-size:0.75rem;color:{_MUTED};font-weight:700;"
        f"letter-spacing:0.8px;text-transform:uppercase;margin-bottom:0.4rem'>"
        f"💬 CFO クイック質問</div>")
q_cols = st.columns(len(QUICK_QUESTIONS_CFO), gap="small")
for col, q in zip(q_cols, QUICK_QUESTIONS_CFO):
    with col:
        if st.button(q, key=f"cfo_quick_{q}", use_container_width=True):
            st.session_state["cfo_risk_scenario"] = None
            st.session_state["cfo_ai_question"]   = q
            st.session_state["cfo_ai_response"]   = None
            st.rerun()

# ── Section 3: Custom input ───────────────────────────────────────────────────
custom_q = st.text_input(
    "カスタム質問",
    placeholder="例：金利上昇と株価急落が同時発生した場合のSCR比率への影響は？",
    label_visibility="collapsed",
)
send_col, _ = st.columns([1, 8])
with send_col:
    if st.button("送信 →", type="primary", use_container_width=True):
        if custom_q.strip():
            st.session_state["cfo_risk_scenario"] = None
            st.session_state["cfo_ai_question"]   = custom_q.strip()
            st.session_state["cfo_ai_response"]   = None
            st.rerun()

# ── Response area ─────────────────────────────────────────────────────────────
question   = st.session_state.get("cfo_ai_question")
risk_key   = st.session_state.get("cfo_risk_scenario")

if question:
    ctx = build_cfo_context(km, alerts_df)

    # Label the active question/scenario
    label = ""
    if risk_key:
        s = next((s for s in RISK_SCENARIOS if s["key"] == risk_key), None)
        if s:
            label = f"{s['icon']} リスクシナリオ: **{s['label']}**"
    elif question:
        label = f"▶ {question}"

    if label:
        st.html(f"<div style='font-size:0.72rem;color:{_MUTED};margin:0.4rem 0 0.2rem'>{label}</div>")

    response_box = st.empty()

    if st.session_state.get("cfo_ai_response"):
        response_box.markdown(st.session_state["cfo_ai_response"])
    else:
        # Generate response
        if risk_key and question.startswith("[RISK]"):
            text = get_risk_scenario(risk_key, ctx)
        else:
            text = get_cfo_insight(question, ctx)

        # Typewriter animation word-by-word
        words = text.split(" ")
        displayed = ""
        for i, word in enumerate(words):
            displayed += ("" if i == 0 else " ") + word
            response_box.markdown(displayed + " ▌")
            time.sleep(0.025)
        response_box.markdown(displayed)
        st.session_state["cfo_ai_response"] = displayed

    if st.button("クリア", key="cfo_ai_clear"):
        st.session_state["cfo_risk_scenario"] = None
        st.session_state["cfo_ai_question"]   = None
        st.session_state["cfo_ai_response"]   = None
        st.rerun()
