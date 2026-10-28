"""Mock AI insights — rule-based dynamic generation.

Production swap: replace _mock_insight() body with a Claude API call.
"""
from __future__ import annotations

import pandas as pd

from .data import Kpi

QUICK_QUESTIONS = [
    "来月のリスクシナリオと優先対応を教えて",
    "投資家向けエグゼクティブサマリーを作成",
    "コンバインドレシオ悪化時の損益インパクトを試算",
    "取締役会に報告すべき事項をまとめて",
]


def build_context(kpi_map: dict[str, Kpi], alerts_df: pd.DataFrame) -> dict:
    return {
        "kpis": {
            k: {"value": v.value, "unit": v.unit, "status": v.status, "delta": v.delta_1d}
            for k, v in kpi_map.items()
        },
        "crit_count": int((alerts_df["重要度"] == "CRIT").sum()),
        "warn_count":  int((alerts_df["重要度"] == "WARN").sum()),
    }


def get_insight(question: str, ctx: dict) -> str:
    """Return full insight text. Swap this function for the real API in production."""
    return _mock_insight(question, ctx)


# ── Rule-based responses ──────────────────────────────────────────────────────

def _mock_insight(question: str, ctx: dict) -> str:
    kpis = ctx.get("kpis", {})
    cr   = kpis.get("combined_ratio",  {}).get("value", 97.2)
    sol  = kpis.get("solvency_ratio",  {}).get("value", 218.5)
    gwp  = kpis.get("gwp_total_ytd",   {}).get("value", 142.6)
    cat  = kpis.get("cat_loss_ytd",    {}).get("value", 3.2)
    bop  = kpis.get("op_profit_ytd",   {}).get("value", 17.2)
    crit = ctx.get("crit_count", 0)
    warn = ctx.get("warn_count", 0)

    if "来月" in question or "リスク" in question:
        return _risk_scenario(cr, sol, cat, crit, warn)
    if "投資家" in question or "サマリー" in question:
        return _investor_summary(gwp, bop, cr, sol)
    if "コンバインドレシオ" in question or "損益インパクト" in question:
        return _cr_impact(cr, bop, gwp)
    if "取締役会" in question or "報告" in question:
        return _board_report(cr, sol, cat, crit, gwp, bop)
    return _general_insight(cr, sol, gwp, bop, crit)


def _risk_scenario(cr: float, sol: float, cat: float, crit: int, warn: int) -> str:
    items = []
    if cr > 98:
        items.append(
            f"コンバインドレシオが **{cr:.1f}%** と引受損益分岐点（100%）に接近しています。"
            "大口損害やCAT損失が重なると単月赤字転落リスクがあります。"
        )
    if cat > 4:
        items.append(
            f"CAT損失が年間予算（8.0億円）の **{cat/8*100:.0f}%** に達しています。"
            "ハリケーンシーズン到来前に再保険カバーのレイヤー確認を推奨します。"
        )
    if crit > 0:
        items.append(
            f"**CRITアラート {crit}件** が対応中です。"
            "特にサイバー横展開挙動は業務継続計画（BCP）の発動基準を即確認してください。"
        )
    if sol < 180:
        items.append(
            f"ソルベンシーⅡ比率が **{sol:.1f}%** と低下傾向にあります。"
            "資本バッファーの維持を最優先としてください。"
        )
    if not items:
        items.append("現時点で主要指標はすべて正常範囲内にあります。追加リスクは確認されていません。")

    priorities = ["再保険カバー条件の再確認（自然災害・サイバー領域）"]
    if crit > 0:
        priorities.insert(0, f"CRITアラート（{crit}件）の根本原因分析と再発防止策の確定")
    priorities.append("Q2決算見込みの取締役会向け事前ブリーフィング準備")

    body  = "\n\n".join(f"- {it}" for it in items)
    plist = "\n".join(f"{i+1}. {p}" for i, p in enumerate(priorities))
    return (
        "### 来月のリスクシナリオ分析\n\n"
        + body
        + f"\n\n**優先対応アクション：**\n\n{plist}"
    )


def _investor_summary(gwp: float, bop: float, cr: float, sol: float) -> str:
    gwp_tag = "+3.1%（計画超）" if gwp > 140 else "計画比やや未達"
    bop_tag = "+4.2%（計画超）" if bop > 16  else "計画比やや未達"
    return (
        "### 投資家向けエグゼクティブサマリー（YTD）\n\n"
        f"**📈 業績ハイライト**  \n"
        f"元受保険料 {gwp:.1f}億円（{gwp_tag}）。損保・生保ともに堅調な新契約獲得が継続。"
        f"事業利益（BOP）{bop:.1f}億円（{bop_tag}）。\n\n"
        f"**🛡 引受品質**  \n"
        f"コンバインドレシオ {cr:.1f}% — 業界ベンチマーク（98〜101%）を下回る良好な水準。"
        f"通常損害率（CAT除く）63.4% は過去3年平均と同水準を維持。\n\n"
        f"**💰 資本健全性**  \n"
        f"ソルベンシーⅡ比率 {sol:.1f}% — 規制最低（100%）の2倍超。"
        f"配当余力・自社株買いの継続検討が可能な水準。\n\n"
        f"**⚠️ 留意点**  \n"
        f"サイバーインシデント（対応中）のモニタリング継続。"
        f"下半期のCAT・気候変動リスクに備え再保険カバー余力を確保済み。"
    )


def _cr_impact(cr: float, bop: float, gwp: float) -> str:
    pp = gwp * 0.01
    rows = [
        ("ベース（現状）",    cr,     0.0),
        ("軽度悪化（+3pp）", cr+3,  -pp*3),
        ("損益分岐（100%）", 100.0, -gwp*(100-cr)/100),
        ("重大悪化（+8pp）", cr+8,  -pp*8),
    ]
    table = "| シナリオ | CR | 利益への影響 |\n|---|---|---|\n"
    for label, ratio, impact in rows:
        sign = f"▼ {abs(impact):.1f}億円" if impact < 0 else "± 0"
        table += f"| {label} | {ratio:.1f}% | **{sign}** |\n"

    return (
        "### コンバインドレシオ感応度分析\n\n"
        f"現在 **{cr:.1f}%**（引受損益は黒字）\n\n"
        + table
        + "\n**主な損害率上昇要因と対策：**\n\n"
        "- 自然災害（CAT）：再保険カバーで一定額まで吸収可能\n"
        "- 大口損害：積立超過準備金（前年度リリース +1.2%）で緩衝\n"
        "- インフレ：クレームインフレ対応として保険料改定サイクルを短縮化済み"
    )


def _board_report(cr: float, sol: float, cat: float, crit: int, gwp: float, bop: float) -> str:
    urgent = []
    if crit > 0:
        urgent.append(f"サイバーインシデント（CRIT {crit}件対応中）— BCP発動基準・外部開示要否を確認")
    if cat > 4:
        urgent.append(f"CAT損失 {cat:.1f}億円（予算消化率 {cat/8*100:.0f}%）— 下半期リスク見通しを共有")
    urgent_text = "\n".join(f"- {u}" for u in urgent) if urgent else "- 本日時点で緊急報告事項なし"

    return (
        "### 取締役会報告事項（本日時点）\n\n"
        f"**🔴 緊急報告事項**\n\n{urgent_text}\n\n"
        f"**📊 定例報告事項**\n\n"
        f"- YTD元受保険料 {gwp:.1f}億円（計画比 +3.1%）— 増収基調が継続\n"
        f"- 事業利益（BOP）{bop:.1f}億円 — Q2着地見込みを次回前に最終化\n"
        f"- コンバインドレシオ {cr:.1f}% — 引受品質は良好、下半期モニタリング継続\n\n"
        f"**🏛 ガバナンス・資本政策**\n\n"
        f"- ソルベンシーⅡ比率 {sol:.1f}% — 自社株買い・増配の検討余地あり\n"
        f"- サイバーリスク対応ポリシーの取締役会承認を次回議題に追加を推奨\n\n"
        f"**取締役会の判断を求める事項：**\n\n"
        f"1. 上半期業績プレスリリースの開示タイミング承認\n"
        f"2. サイバーインシデントの規制報告義務・外部開示要否の確認\n"
        f"3. 下半期のCAT再保険追加手配の可否判断"
    )


def _general_insight(cr: float, sol: float, gwp: float, bop: float, crit: int) -> str:
    watch = (
        f"CRITアラート {crit}件が対応中。迅速な収束を確認してください。"
        if crit > 0 else
        "CAT損失は予算範囲内ですが、下半期のハリケーンシーズンに引き続き注意が必要です。"
    )
    return (
        "### 現状分析サマリー\n\n"
        "主要指標はおおむね良好な水準にあります。\n\n"
        f"**強み：**\n\n"
        f"- 元受保険料 {gwp:.1f}億円 で計画超過、引受成長が継続\n"
        f"- コンバインドレシオ {cr:.1f}% で引受品質を維持\n"
        f"- ソルベンシー比率 {sol:.1f}% で十分な資本余力を確保\n\n"
        f"**注視点：**\n\n"
        f"- {watch}\n"
        f"- 投資収益（3.4%）は市場金利動向に左右される可能性あり\n\n"
        "**CEO判断のポイント：**\n\n"
        "資本余力が高い現状は、M&A・新規市場参入・増配のいずれにも動きやすい局面です。"
        "下半期のCAT・サイバーリスクを踏まえ、資本活用の優先順位を明確化する好機と言えます。"
    )
