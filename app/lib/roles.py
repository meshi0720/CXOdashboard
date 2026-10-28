from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Role = Literal["CEO", "COO", "CFO", "CDO", "CIO", "CSIO", "CAIO", "CRO"]


@dataclass(frozen=True)
class RoleConfig:
    role: Role
    home_kpi_keys: tuple[str, ...]
    home_trend_series: tuple[str, ...]
    tagline: str


ROLE_CONFIGS: dict[Role, RoleConfig] = {
    "CEO": RoleConfig(
        role="CEO",
        home_kpi_keys=("pnl_today", "capital_ratio", "liq_coverage", "security_risk", "system_avail", "npl_ratio"),
        home_trend_series=("市場ストレス指数", "資金流出圧力"),
        tagline="全社の重要度順に要約（損益・健全性・流動性・重大インシデント）",
    ),
    "COO": RoleConfig(
        role="COO",
        home_kpi_keys=("system_avail", "pnl_today", "capital_ratio", "liq_coverage", "security_risk", "npl_ratio"),
        home_trend_series=("主要系稼働率(%)",),
        tagline="業務継続・オペレーション効率・主要系稼働を優先表示",
    ),
    "CFO": RoleConfig(
        role="CFO",
        home_kpi_keys=("pnl_today", "capital_ratio", "liq_coverage", "npl_ratio", "system_avail", "security_risk"),
        home_trend_series=("市場ストレス指数",),
        tagline="損益と資本・流動性の変化を優先表示",
    ),
    "CDO": RoleConfig(
        role="CDO",
        home_kpi_keys=("system_avail", "pnl_today", "security_risk", "capital_ratio", "liq_coverage", "npl_ratio"),
        home_trend_series=("市場ストレス指数", "主要系稼働率(%)"),
        tagline="デジタル変革進捗・データ資産・DX施策の実効性を優先表示",
    ),
    "CIO": RoleConfig(
        role="CIO",
        home_kpi_keys=("system_avail", "security_risk", "liq_coverage", "capital_ratio", "pnl_today", "npl_ratio"),
        home_trend_series=("主要系稼働率(%)",),
        tagline="稼働率・変更/障害・主要リスクを優先表示",
    ),
    "CSIO": RoleConfig(
        role="CSIO",
        home_kpi_keys=("security_risk", "system_avail", "liq_coverage", "capital_ratio", "npl_ratio", "pnl_today"),
        home_trend_series=("市場ストレス指数",),
        tagline="重大アラートと検知/封じ込め・情報セキュリティ状況を最優先",
    ),
    "CAIO": RoleConfig(
        role="CAIO",
        home_kpi_keys=("pnl_today", "system_avail", "security_risk", "capital_ratio", "liq_coverage", "npl_ratio"),
        home_trend_series=("市場ストレス指数", "主要系稼働率(%)"),
        tagline="AI施策の進捗・AIリスク・モデル品質・倫理ガバナンスを優先表示",
    ),
    "CRO": RoleConfig(
        role="CRO",
        home_kpi_keys=("liq_coverage", "npl_ratio", "capital_ratio", "pnl_today", "security_risk", "system_avail"),
        home_trend_series=("資金流出圧力", "市場ストレス指数"),
        tagline="流動性・信用・市場リスクの逸脱を先に見る",
    ),
}


def get_role_config(role: Role) -> RoleConfig:
    try:
        from .role_md import load_role_markdown
        return load_role_markdown(role).config
    except Exception:
        return ROLE_CONFIGS[role]
