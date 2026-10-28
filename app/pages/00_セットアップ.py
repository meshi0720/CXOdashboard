"""3-step industry setup wizard."""
from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))


import streamlit as st

from lib.industry import INSURANCE_GROUP
from lib.ui import (
    _BG, _BG2, _BG3, _BORDER, _BORDER_MID, _CRIT, _INFO_BLUE,
    _MUTED, _OK, _TEXT, _WARN,
    cockpit_header, inject_role_theme, setup_page,
)
from lib.data import now_jst, sample_alerts

# ── Page setup ────────────────────────────────────────────────────────────────

setup_page("セットアップ", cockpit=True)
inject_role_theme("CEO")

alerts_df  = sample_alerts()
updated_at = now_jst().strftime("%Y-%m-%d %H:%M JST")
cockpit_header("CEO", alerts_df, updated_at)

# ── Session state ─────────────────────────────────────────────────────────────

if "setup_step" not in st.session_state:
    st.session_state["setup_step"] = 1

cfg = INSURANCE_GROUP

# ── Step indicator ────────────────────────────────────────────────────────────

STEPS = ["業界選択", "データ連携設定", "確認・起動"]
step  = st.session_state["setup_step"]

progress_html = ""
for i, label in enumerate(STEPS, 1):
    if i < step:
        c_bg, c_text, c_border = _OK,        "#000",   _OK
        symbol                 = "✓"
    elif i == step:
        c_bg, c_text, c_border = _INFO_BLUE, "#000",   _INFO_BLUE
        symbol                 = str(i)
    else:
        c_bg, c_text, c_border = "transparent", _MUTED, _BORDER_MID
        symbol                 = str(i)

    connector = (
        f"<div style='flex:1;height:2px;background:"
        f"{'rgba(16,217,138,0.6)' if i < step else _BORDER};margin-top:14px'></div>"
        if i < len(STEPS) else ""
    )
    progress_html += f"""
    <div style="display:flex;flex-direction:column;align-items:center;min-width:80px">
      <div style="width:28px;height:28px;border-radius:50%;
        background:{c_bg};border:2px solid {c_border};
        display:flex;align-items:center;justify-content:center;
        font-size:0.78rem;font-weight:800;color:{c_text}">{symbol}</div>
      <div style="font-size:0.72rem;color:{_MUTED if i != step else _TEXT};
        margin-top:0.3rem;font-weight:{'700' if i == step else '400'}">{label}</div>
    </div>
    {connector}"""

st.html(f"""
<div style="display:flex;align-items:flex-start;gap:0;
  padding:0.8rem 1rem;background:{_BG2};border:1px solid {_BORDER};
  border-radius:0.75rem;margin-bottom:1rem">
  {progress_html}
</div>""")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — 業界選択
# ══════════════════════════════════════════════════════════════════════════════

if step == 1:
    st.markdown("### Step 1 — 業界を選択")

    # Active demo banner
    st.html(f"""
    <div style="
      background:linear-gradient(135deg,rgba(77,159,255,0.12) 0%,rgba(16,217,138,0.06) 100%);
      border:1.5px solid {_INFO_BLUE};border-radius:0.85rem;
      padding:1rem 1.4rem;margin-bottom:1rem;
      display:flex;align-items:center;gap:1.2rem">
      <div style="font-size:2rem">🏢</div>
      <div>
        <div style="font-size:0.72rem;color:{_INFO_BLUE};font-weight:700;
          letter-spacing:1px;text-transform:uppercase;margin-bottom:0.2rem">
          このデモで設定済みの業界</div>
        <div style="font-size:1.05rem;font-weight:800;color:{_TEXT}">
          {cfg.name}</div>
        <div style="font-size:0.8rem;color:{_MUTED};margin-top:0.2rem">
          {cfg.company_desc} &nbsp;｜&nbsp; 本社: {cfg.hq}
          &nbsp;｜&nbsp; 規制: {cfg.regulatory_framework}</div>
      </div>
      <div style="margin-left:auto;flex-shrink:0">
        <span style="background:rgba(16,217,138,0.15);border:1px solid {_OK};
          color:{_OK};padding:0.25rem 0.8rem;border-radius:999px;
          font-size:0.78rem;font-weight:700">✓ 選択済み</span>
      </div>
    </div>""")

    # Industry grid (future options)
    st.html(f"<div style='font-size:0.75rem;color:{_MUTED};margin-bottom:0.6rem;font-weight:600;letter-spacing:0.5px'>TODAY対応予定の業界（準備中）</div>")

    FUTURE_INDUSTRIES = [
        ("🏦", "銀行",         "都市銀行・地方銀行・信用金庫"),
        ("🛡",  "損害保険",    "損保会社・共済組合"),
        ("💚", "生命保険",     "生保会社・共済・年金基金"),
        ("📈", "証券",         "証券会社・投資銀行・資産運用"),
        ("🚗", "自動車メーカー","OEM・Tier1サプライヤー"),
        ("🍽", "飲食サービス", "チェーン・FC展開企業"),
    ]

    cols = st.columns(3, gap="small")
    for idx, (icon, name, desc) in enumerate(FUTURE_INDUSTRIES):
        with cols[idx % 3]:
            st.html(f"""
            <div style="
              background:{_BG3};border:1px solid {_BORDER};
              border-radius:0.65rem;padding:0.75rem 0.9rem;
              opacity:0.55;cursor:not-allowed;margin-bottom:0.5rem">
              <div style="font-size:1.4rem;margin-bottom:0.3rem">{icon}</div>
              <div style="font-size:0.9rem;font-weight:700;color:{_TEXT}">{name}</div>
              <div style="font-size:0.72rem;color:{_MUTED};margin-top:0.15rem">{desc}</div>
              <div style="font-size:0.68rem;color:{_WARN};margin-top:0.4rem;font-weight:600">準備中</div>
            </div>""")

    st.write("")
    if st.button("次のステップへ →", type="primary", use_container_width=False):
        st.session_state["setup_step"] = 2
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — データ連携設定
# ══════════════════════════════════════════════════════════════════════════════

elif step == 2:
    st.markdown("### Step 2 — データ連携設定")
    st.html(f"<div style='font-size:0.8rem;color:{_MUTED};margin-bottom:0.8rem'>"
            f"各 CxO が参照するデータソースの接続状況を確認します。"
            f"</div>")

    SOURCE_TYPE_ICON = {
        "database":  "🗄",
        "api":       "🔌",
        "streaming": "⚡",
        "file":      "📁",
    }
    STATUS_STYLE = {
        "接続済":  {"bg": "rgba(16,217,138,0.12)", "border": _OK,   "text": _OK,   "label": "接続済"},
        "設定中":  {"bg": "rgba(245,166,35,0.10)", "border": _WARN, "text": _WARN, "label": "設定中"},
        "未接続":  {"bg": "rgba(255,71,87,0.08)",  "border": _CRIT, "text": _CRIT, "label": "未接続"},
    }

    # Data source cards
    sources = list(cfg.data_sources.values())
    col1, col2 = st.columns(2, gap="small")

    for i, ds in enumerate(sources):
        col = col1 if i % 2 == 0 else col2
        ss  = STATUS_STYLE.get(ds.status, STATUS_STYLE["接続済"])
        icon = SOURCE_TYPE_ICON.get(ds.source_type, "📦")
        roles_str = " / ".join(ds.roles)

        with col:
            st.html(f"""
            <div style="
              background:{_BG2};border:1px solid {ss['border']};
              border-left:3px solid {ss['border']};
              border-radius:0.6rem;padding:0.7rem 0.9rem;margin-bottom:0.55rem">
              <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.3rem">
                <span style="font-size:1rem">{icon}</span>
                <span style="font-size:0.88rem;font-weight:700;color:{_TEXT}">{ds.name}</span>
                <span style="margin-left:auto;background:{ss['bg']};
                  border:1px solid {ss['border']};color:{ss['text']};
                  padding:0.1rem 0.55rem;border-radius:999px;
                  font-size:0.67rem;font-weight:700">{ss['label']}</span>
              </div>
              <div style="font-size:0.72rem;color:{_MUTED};margin-bottom:0.25rem">
                <b style="color:{_TEXT}">{ds.system}</b>
              </div>
              <div style="font-size:0.72rem;color:{_MUTED};margin-bottom:0.25rem">
                {ds.description}
              </div>
              <div style="display:flex;gap:0.6rem;font-size:0.68rem">
                <span style="color:{_INFO_BLUE}">🕑 {ds.refresh}</span>
                <span style="color:{_MUTED}">対象: {roles_str}</span>
              </div>
            </div>""")

    st.write("")

    # Role → data source summary
    st.markdown("##### CxO別 データソースマッピング")
    role_cols = st.columns(4, gap="small")
    roles_list = list(cfg.roles.values())
    for idx, role_cfg in enumerate(roles_list):
        with role_cols[idx % 4]:
            sources_list = "".join(
                f"<div style='font-size:0.67rem;color:{_MUTED};padding:0.1rem 0;border-bottom:1px solid {_BORDER}'>"
                f"{cfg.data_sources[k].name}</div>"
                for k in role_cfg.data_source_keys if k in cfg.data_sources
            )
            st.html(f"""
            <div style="background:{_BG2};border:1px solid {_BORDER};
              border-radius:0.55rem;padding:0.55rem 0.7rem;margin-bottom:0.5rem">
              <div style="font-size:0.8rem;font-weight:800;color:{_INFO_BLUE};
                margin-bottom:0.35rem">{role_cfg.role}</div>
              <div style="font-size:0.68rem;color:{_MUTED};margin-bottom:0.3rem">
                {role_cfg.title_jp}</div>
              {sources_list}
            </div>""")

    st.write("")
    nav1, nav2, _ = st.columns([1, 1, 5])
    with nav1:
        if st.button("← 戻る", use_container_width=True):
            st.session_state["setup_step"] = 1
            st.rerun()
    with nav2:
        if st.button("次のステップへ →", type="primary", use_container_width=True):
            st.session_state["setup_step"] = 3
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — 確認・起動
# ══════════════════════════════════════════════════════════════════════════════

elif step == 3:
    st.markdown("### Step 3 — 確認・起動")

    connected  = sum(1 for ds in cfg.data_sources.values() if ds.status == "接続済")
    total_ds   = len(cfg.data_sources)
    total_kpis = len(set(k for r in cfg.roles.values() for k in r.kpi_keys))
    total_roles = len(cfg.roles)

    # Summary cards
    s1, s2, s3, s4 = st.columns(4, gap="small")
    for col, label, value, unit in [
        (s1, "業界・会社形態",  cfg.company_type, ""),
        (s2, "データソース数",  f"{connected}/{total_ds}", "接続済"),
        (s3, "KPI指標数",      str(total_kpis), "指標"),
        (s4, "CxOロール数",    str(total_roles), "ロール"),
    ]:
        with col:
            st.html(f"""
            <div style="background:{_BG2};border:1px solid {_BORDER};
              border-top:2px solid {_OK};border-radius:0.65rem;
              padding:0.7rem 0.9rem;text-align:center">
              <div style="font-size:0.7rem;color:{_MUTED};margin-bottom:0.3rem">{label}</div>
              <div style="font-size:1.4rem;font-weight:800;color:{_OK};line-height:1">
                {value}</div>
              <div style="font-size:0.72rem;color:{_MUTED};margin-top:0.15rem">{unit}</div>
            </div>""")

    st.write("")

    # Role readiness table
    st.markdown("##### ロール別 準備状況")
    rows_html = ""
    for role_cfg in cfg.roles.values():
        kpi_count = len(role_cfg.kpi_keys)
        ds_count  = len(role_cfg.data_source_keys)
        focus     = "・".join(role_cfg.focus_areas[:2])
        rows_html += f"""
        <div style="display:flex;align-items:center;gap:0.8rem;
          padding:0.45rem 0;border-bottom:1px solid {_BORDER}">
          <span style="font-weight:700;color:{_INFO_BLUE};min-width:45px">{role_cfg.role}</span>
          <span style="font-size:0.8rem;color:{_MUTED};min-width:130px">{role_cfg.title_jp}</span>
          <span style="font-size:0.75rem;color:{_TEXT};flex:1">{focus}</span>
          <span style="font-size:0.72rem;color:{_MUTED}">KPI {kpi_count}指標 / DS {ds_count}件</span>
          <span style="background:rgba(16,217,138,0.12);border:1px solid {_OK};color:{_OK};
            padding:0.08rem 0.5rem;border-radius:999px;font-size:0.67rem;font-weight:700">準備完了</span>
        </div>"""

    st.html(f"""
    <div style="background:{_BG2};border:1px solid {_BORDER};
      border-radius:0.65rem;padding:0.6rem 0.9rem;margin-bottom:1rem">
      {rows_html}
    </div>""")

    # Launch button
    st.html(f"<div style='text-align:center;padding:0.5rem 0;font-size:0.82rem;color:{_MUTED}'>"
            f"全 {total_roles} ロールのデータが接続済みです。ダッシュボードを起動できます。</div>")

    nav1, launch_col, nav3 = st.columns([1, 2, 1])
    with nav1:
        if st.button("← 戻る", use_container_width=True):
            st.session_state["setup_step"] = 2
            st.rerun()
    with launch_col:
        if st.button("🚀  ダッシュボードを起動", type="primary", use_container_width=True):
            st.switch_page("Home.py")
