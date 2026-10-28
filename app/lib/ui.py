from __future__ import annotations

from typing import Iterable

import plotly.graph_objects as go
import streamlit as st

from .data import Kpi

# ── Design tokens ─────────────────────────────────────────────────────────────
_BG        = "#0f1923"
_BG2       = "#182535"
_BG3       = "#1f3045"
_BORDER    = "rgba(77,159,255,0.13)"
_BORDER_MID= "rgba(77,159,255,0.25)"
_TEXT      = "#d8eaf7"
_MUTED     = "rgba(216,234,247,0.50)"
_OK        = "#10d98a"
_WARN      = "#f5a623"
_CRIT      = "#ff4757"
_INFO_BLUE = "#4d9fff"

ROLE_PAGES: dict[str, str] = {
    "CEO":  "Home.py",
    "COO":  "pages/06_業務（COO）.py",
    "CFO":  "pages/04_財務（CFO）.py",
    "CDO":  "pages/07_デジタル（CDO）.py",
    "CIO":  "pages/02_テクノロジー（CIO）.py",
    "CSIO": "pages/03_セキュリティ（CSIO）.py",
    "CAIO": "pages/08_AI（CAIO）.py",
    "CRO":  "pages/05_流動性・リスク（CRO）.py",
}
_ROLES = list(ROLE_PAGES)

ROLE_COLORS: dict[str, dict[str, str]] = {
    "CEO":  {"accent": "#4d9fff", "glow": "rgba(77,159,255,0.30)",  "mid": "#93c5fd"},
    "COO":  {"accent": "#818cf8", "glow": "rgba(129,140,248,0.30)", "mid": "#c4b5fd"},
    "CFO":  {"accent": "#10d98a", "glow": "rgba(16,217,138,0.30)",  "mid": "#6ee7b7"},
    "CDO":  {"accent": "#e879f9", "glow": "rgba(232,121,249,0.30)", "mid": "#f0abfc"},
    "CIO":  {"accent": "#06b6d4", "glow": "rgba(6,182,212,0.30)",   "mid": "#67e8f9"},
    "CSIO": {"accent": "#ff4757", "glow": "rgba(255,71,87,0.30)",   "mid": "#fca5a5"},
    "CAIO": {"accent": "#fb923c", "glow": "rgba(251,146,60,0.30)",  "mid": "#fed7aa"},
    "CRO":  {"accent": "#f5a623", "glow": "rgba(245,166,35,0.30)",  "mid": "#fde68a"},
}

_SEV_STYLE = {
    "CRIT": {"bg_badge": _CRIT,      "bg_card": "rgba(255,71,87,0.07)",   "border": "rgba(255,71,87,0.40)",   "label": "CRIT"},
    "WARN": {"bg_badge": _WARN,      "bg_card": "rgba(245,166,35,0.07)",  "border": "rgba(245,166,35,0.40)",  "label": "WARN"},
    "INFO": {"bg_badge": _INFO_BLUE, "bg_card": "rgba(77,159,255,0.05)",  "border": "rgba(77,159,255,0.28)",  "label": "INFO"},
}

_KPI_STATUS = {
    "ok":   {"border": _OK,   "glow": "rgba(16,217,138,0.25)",  "text": _OK},
    "warn": {"border": _WARN, "glow": "rgba(245,166,35,0.25)",  "text": _WARN},
    "crit": {"border": _CRIT, "glow": "rgba(255,71,87,0.25)",   "text": _CRIT},
}

_STATUS_CARD = {
    "crit": {"bg": "linear-gradient(135deg,#6b0f1a 0%,#2d0308 100%)", "glow": _CRIT,  "label": "緊急対応が必要"},
    "warn": {"bg": "linear-gradient(135deg,#6a3800 0%,#2d1800 100%)", "glow": _WARN,  "label": "注意が必要"},
    "ok":   {"bg": "linear-gradient(135deg,#054030 0%,#021a14 100%)", "glow": _OK,    "label": "正常稼働中"},
}


# ── Page setup ────────────────────────────────────────────────────────────────

def setup_page(title: str, cockpit: bool = False) -> None:
    st.set_page_config(
        page_title=title,
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed" if cockpit else "expanded",
    )
    _inject_css(cockpit=cockpit)


def _inject_css(cockpit: bool = False) -> None:
    extra = """
      /* Cockpit mode: hide Streamlit chrome */
      header[data-testid="stHeader"] { display: none !important; }
      #MainMenu { display: none !important; }
      footer { display: none !important; }
      section[data-testid="stSidebar"] { display: none !important; }
      .block-container {
        padding-top: 0.6rem !important;
        padding-bottom: 0.4rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
        max-width: 100% !important;
      }
    """ if cockpit else ""

    st.markdown(f"""<style>
      :root {{
        --cxo-bg:      {_BG};
        --cxo-bg2:     {_BG2};
        --cxo-bg3:     {_BG3};
        --cxo-border:  {_BORDER};
        --cxo-text:    {_TEXT};
        --cxo-muted:   {_MUTED};
        --cxo-ok:      {_OK};
        --cxo-warn:    {_WARN};
        --cxo-crit:    {_CRIT};
        --cxo-blue:    {_INFO_BLUE};
      }}
      html, body {{ font-size: 14px; line-height: 1.45; -webkit-font-smoothing: antialiased; }}
      .stApp {{ background: {_BG} !important; }}
      section[data-testid="stSidebar"] {{ background: {_BG2} !important; border-right: 1px solid {_BORDER}; }}
      .block-container {{ padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 1600px !important; }}
      hr {{ border-color: {_BORDER} !important; margin: 0.4rem 0 !important; }}
      h2, h3 {{ color: {_TEXT}; letter-spacing: 0.3px; }}
      h2 {{ font-weight: 760; font-size: 1.3rem; }}
      h3 {{
        font-weight: 700; font-size: 0.78rem; text-transform: uppercase;
        letter-spacing: 1.4px; color: {_MUTED}; margin-bottom: 0.4rem !important;
        display: flex; align-items: center; gap: 0.4rem;
      }}
      h3::before {{
        content: ''; display: inline-block; width: 2px; height: 0.95em;
        background: var(--cxo-role-accent, {_INFO_BLUE});
        border-radius: 2px; box-shadow: 0 0 5px var(--cxo-role-glow, rgba(77,159,255,0.4));
        flex-shrink: 0;
      }}
      .cxo-badge {{
        display: inline-block; padding: 0.18rem 0.6rem; border-radius: 999px;
        font-size: 0.8rem; border: 1px solid {_BORDER_MID}; background: {_BG3}; color: {_TEXT};
      }}
      .cxo-muted {{ color: {_MUTED}; }}
      .panel {{
        background: {_BG2}; border: 1px solid {_BORDER};
        border-radius: 0.75rem; padding: 0.65rem 0.8rem;
        height: 100%;
      }}
      /* Role navigation chips (st.page_link) */
      div[data-testid="stPageLink"] a {{
        display: block;
        text-align: center;
        padding: 0.22rem 0.3rem !important;
        border-radius: 0.4rem !important;
        border: 1px solid {_BORDER} !important;
        background: transparent !important;
        color: {_MUTED} !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        text-decoration: none !important;
        transition: border-color 0.15s, color 0.15s, background 0.15s;
      }}
      div[data-testid="stPageLink"] a:hover {{
        border-color: rgba(77,159,255,0.45) !important;
        color: {_TEXT} !important;
        background: rgba(77,159,255,0.07) !important;
      }}
      div[data-testid="stPageLink"] a[aria-current="page"] {{
        border: 1.5px solid var(--cxo-role-accent, {_INFO_BLUE}) !important;
        background: var(--cxo-role-glow, rgba(77,159,255,0.15)) !important;
        color: var(--cxo-role-accent, {_INFO_BLUE}) !important;
        font-weight: 800 !important;
      }}
      {extra}
    </style>""", unsafe_allow_html=True)


def inject_nav_css(_current_role: str = "") -> None:
    """No-op: page_link chip styling is handled in _inject_css."""
    pass


def inject_role_theme(role: str) -> None:
    c = ROLE_COLORS.get(role, ROLE_COLORS["CEO"])
    st.markdown(f"""<style>
      :root {{
        --cxo-role-accent: {c['accent']};
        --cxo-role-glow:   {c['glow']};
        --cxo-role-mid:    {c['mid']};
      }}
      section[data-testid="stSidebar"] {{ border-right: 1px solid {c['glow']}; }}
      .cxo-role-bar {{
        height: 2px;
        background: linear-gradient(90deg, {c['accent']} 0%, {c['mid']} 60%, transparent 100%);
        border-radius: 2px; margin: 0.2rem 0 0.8rem 0;
        box-shadow: 0 0 8px {c['glow']};
      }}
    </style>""", unsafe_allow_html=True)


# ── Cockpit top bar ───────────────────────────────────────────────────────────

def cockpit_topbar(role: str, alerts_df, updated_at: str) -> None:
    """Full-width cockpit header: title | status | time"""
    crit = int((alerts_df["重要度"] == "CRIT").sum())
    warn = int((alerts_df["重要度"] == "WARN").sum())

    if crit:   status_html = f"<span style='color:{_CRIT};font-weight:800'>● CRIT {crit}</span>"
    elif warn: status_html = f"<span style='color:{_WARN};font-weight:700'>▲ WARN {warn}</span>"
    else:      status_html = f"<span style='color:{_OK};font-weight:700'>● 正常</span>"

    st.html(f"""
    <div style="
      display:flex; align-items:center; gap:1.2rem;
      background:{_BG2}; border:1px solid {_BORDER};
      border-radius:0.75rem; padding:0.5rem 1rem;
      margin-bottom:0.3rem;
    ">
      <div style="font-size:1.0rem;font-weight:820;color:{_TEXT};white-space:nowrap;letter-spacing:0.5px">
        🎛&nbsp; Management Cockpit
      </div>
      <div style="margin-left:auto;display:flex;align-items:center;gap:1.2rem;flex-shrink:0">
        <div style="font-size:0.82rem">{status_html}</div>
        <div style="font-size:0.75rem;color:{_MUTED}">{updated_at}</div>
      </div>
    </div>
    """)


# ── Cockpit header (topbar + nav row) ────────────────────────────────────────

def cockpit_header(role: str, alerts_df, updated_at: str) -> None:
    """Shared topbar + role navigation row for all CxO pages."""
    cockpit_topbar(role, alerts_df, updated_at)
    nav_cols = st.columns(len(_ROLES), gap="small")
    for col, r in zip(nav_cols, _ROLES):
        col.page_link(ROLE_PAGES[r], label=r, use_container_width=True)


# ── KPI compact row ───────────────────────────────────────────────────────────

def kpi_mini_row(kpis: Iterable[Kpi]) -> None:
    """Very compact KPI row — designed for cockpit layout."""
    kpis = list(kpis)
    if not kpis:
        return
    cols = st.columns(len(kpis))
    for col, k in zip(cols, kpis):
        s  = _KPI_STATUS.get(k.status, _KPI_STATUS["ok"])
        ds = "↑" if k.delta_1d > 0 else ("↓" if k.delta_1d < 0 else "→")
        col.html(f"""
        <div style="
          background:{_BG2};
          border:1px solid {s['border']};
          border-top:2px solid {s['border']};
          border-radius:0.65rem;
          padding:0.55rem 0.7rem 0.45rem;
          box-shadow:0 0 14px {s['glow']};
          position:relative; overflow:hidden;
        ">
          <div style="position:absolute;top:0;right:0;width:50px;height:50px;
            background:radial-gradient(circle at top right,{s['glow']},transparent 70%);
            pointer-events:none"></div>
          <div style="font-size:0.7rem;color:{_MUTED};font-weight:600;
            text-transform:uppercase;letter-spacing:0.7px;
            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
            margin-bottom:0.3rem">{k.label}</div>
          <div style="font-size:1.7rem;font-weight:820;color:{s['text']};
            line-height:1;letter-spacing:-0.5px;
            text-shadow:0 0 14px {s['glow']}">{k.value:g}<span style="font-size:0.8rem;font-weight:600;opacity:0.8">{k.unit}</span></div>
          <div style="font-size:0.68rem;color:{s['text']};opacity:0.72;margin-top:0.28rem;font-weight:600">
            {ds} {abs(k.delta_1d):g}{k.unit} vs 前日
          </div>
        </div>""")


def kpi_card_row(kpis: Iterable[Kpi]) -> None:
    kpi_mini_row(kpis)

def kpi_row(kpis: Iterable[Kpi]) -> None:
    kpi_mini_row(kpis)


# ── Alert compact list ────────────────────────────────────────────────────────

def render_alert_compact(df, max_height: int = 260) -> None:
    if df.empty:
        st.html(f"<div style='color:{_MUTED};font-size:0.8rem;padding:0.5rem'>アラートなし</div>")
        return

    status_colors = {"対応中": _CRIT, "監視": _WARN, "完了": _OK, "確認済": _OK}
    rows_html = ""
    for _, row in df.iterrows():
        sev    = (row.get("重要度", "") or "").upper()
        ss     = _SEV_STYLE.get(sev, _SEV_STYLE["INFO"])
        st_txt = row.get("状態", "")
        st_col = status_colors.get(st_txt, _MUTED)
        rows_html += f"""
        <div style="display:flex;align-items:flex-start;gap:0.5rem;
          padding:0.4rem 0;border-bottom:1px solid {_BORDER}">
          <span style="background:{ss['bg_badge']};color:#fff;
            padding:0.1rem 0.42rem;border-radius:999px;
            font-size:0.67rem;font-weight:800;letter-spacing:0.4px;
            white-space:nowrap;flex-shrink:0;margin-top:1px">{ss['label']}</span>
          <div style="flex:1;min-width:0">
            <div style="font-size:0.79rem;color:{_TEXT};line-height:1.35;
              overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{row.get('内容','')}</div>
            <div style="font-size:0.68rem;color:{_MUTED};margin-top:0.1rem;display:flex;gap:0.5rem">
              <span>{row.get('時刻','')}</span>
              <span>{row.get('領域','')}</span>
              <span style="color:{st_col};font-weight:700">{st_txt}</span>
            </div>
          </div>
        </div>"""

    st.html(f"""
    <div style="overflow-y:auto;max-height:{max_height}px;padding-right:0.2rem">
      {rows_html}
    </div>""")


def render_alert_cards(df) -> None:
    render_alert_compact(df)

def render_alert_table(df) -> None:
    render_alert_compact(df)


# ── Status banner (for sub-pages) ─────────────────────────────────────────────

def status_banner(alerts_df, updated_at: str = "") -> None:
    crit = int((alerts_df["重要度"] == "CRIT").sum())
    warn = int((alerts_df["重要度"] == "WARN").sum())
    info = int((alerts_df["重要度"] == "INFO").sum())

    if crit > 0:   key, icon = "crit", "🔴"
    elif warn > 0: key, icon = "warn", "🟡"
    else:          key, icon = "ok",   "🟢"

    c = _STATUS_CARD[key]
    headline = {"crit": f"重大アラート {crit}件 — 即時対応が必要です",
                "warn": f"警告 {warn}件 — しきい値接近または要注意事項があります",
                "ok":   "全システム正常稼働中"}[key]

    chips = []
    if crit: chips.append(f"<span style='background:rgba(255,71,87,0.22);border:1px solid rgba(255,71,87,0.45);padding:0.1rem 0.6rem;border-radius:999px;font-weight:700;font-size:0.78rem'>● CRIT {crit}件</span>")
    if warn: chips.append(f"<span style='background:rgba(245,166,35,0.18);border:1px solid rgba(245,166,35,0.4);padding:0.1rem 0.6rem;border-radius:999px;font-size:0.78rem'>▲ WARN {warn}件</span>")
    if info: chips.append(f"<span style='background:rgba(77,159,255,0.12);border:1px solid rgba(77,159,255,0.3);padding:0.1rem 0.6rem;border-radius:999px;font-size:0.78rem'>◆ INFO {info}件</span>")

    time_span = f"<span style='opacity:0.55;font-size:0.78rem;margin-left:0.3rem'>{updated_at}</span>" if updated_at else ""
    st.html(f"""
    <div style="background:{c['bg']};border:1px solid {c['glow']};
      border-radius:0.85rem;padding:1rem 1.5rem;display:flex;align-items:center;gap:1.4rem;
      margin-bottom:1rem;box-shadow:0 0 22px {c['glow']},0 3px 12px rgba(0,0,0,0.4)">
      <div style="font-size:2.2rem;filter:drop-shadow(0 0 6px {c['glow']})">{icon}</div>
      <div>
        <div style="font-size:1.1rem;font-weight:800;color:{_TEXT};margin-bottom:0.3rem">{headline}</div>
        <div style="display:flex;gap:0.5rem;flex-wrap:wrap;align-items:center">
          {"".join(chips)}
          {time_span}
        </div>
      </div>
    </div>""")


# ── Gauge chart ───────────────────────────────────────────────────────────────

def gauge_chart(kpi: Kpi, height: int = 180) -> go.Figure:
    sc    = {"ok": _OK, "warn": _WARN, "crit": _CRIT}.get(kpi.status, _INFO_BLUE)
    max_v = kpi.max_val if kpi.max_val is not None else kpi.value * 1.5
    thr   = kpi.threshold

    steps = []
    if thr is not None:
        d = max(0.0, thr * 0.75)
        steps = [
            {"range": [0, d],      "color": "rgba(255,71,87,0.07)"},
            {"range": [d, thr],    "color": "rgba(245,166,35,0.10)"},
            {"range": [thr, max_v],"color": "rgba(16,217,138,0.09)"},
        ]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=kpi.value,
        number={"suffix": kpi.unit, "font": {"size": 18, "color": sc}},
        title={"text": kpi.label, "font": {"size": 11, "color": _MUTED}},
        gauge={
            "axis": {"range": [0, max_v], "tickwidth": 1, "tickcolor": _MUTED,
                     "tickfont": {"color": _MUTED, "size": 9}},
            "bar": {"color": sc, "thickness": 0.26},
            "bgcolor": _BG3, "borderwidth": 0,
            "steps": steps,
            **( {"threshold": {"line": {"color": _TEXT, "width": 2},
                               "thickness": 0.75, "value": thr}} if thr is not None else {}),
        },
    ))
    fig.update_layout(
        height=height, margin=dict(l=16, r=16, t=36, b=4),
        paper_bgcolor=_BG2, font={"family": "sans-serif", "color": _TEXT},
    )
    return fig


# ── Header (sub-pages) ────────────────────────────────────────────────────────

def severity_color(sev: str) -> str:
    s = (sev or "").upper()
    if s in {"CRIT","CRITICAL"}: return _CRIT
    if s in {"WARN","WARNING"}:  return _WARN
    return _INFO_BLUE


def cxo_header(role: str, updated_at: str) -> None:
    left, right = st.columns([0.72, 0.28])
    with left:
        st.markdown("## CXOダッシュボード")
        st.html('<div class="cxo-role-bar"></div>')
        st.html(
            f'<span class="cxo-badge">ロール: <b>{role}</b></span> '
            f'<span class="cxo-badge">更新: <b>{updated_at}</b></span>'
        )
    with right:
        st.html(f'<div class="cxo-muted" style="text-align:right;padding-top:0.4rem;font-size:0.8rem">重要指標は「変化」と「逸脱」を優先表示</div>')
