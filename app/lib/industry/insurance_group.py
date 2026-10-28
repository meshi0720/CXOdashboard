"""欧米大手保険持株会社（生損保グループ）モックデータ"""
from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from ..data import Kpi, now_jst
from .config import DataSourceConfig, IndustryConfig, RoleDataConfig

# ── KPI definitions ──────────────────────────────────────────────────────────

def insurance_kpis() -> list[Kpi]:
    return [
        # ── トップライン（元受保険料） ───────────────────────────────────────
        Kpi("gwp_total_ytd",    "元受保険料合計（YTD）",     142.6, "億円",  +2.3,  "ok",   threshold=None,  max_val=None),
        Kpi("gwp_nonlife_ytd",  "元受保険料（損保）YTD",      82.4, "億円",  +1.5,  "ok",   threshold=None,  max_val=None),
        Kpi("gwp_life_ytd",     "元受保険料（生保）YTD",      60.2, "億円",  +0.8,  "ok",   threshold=None,  max_val=None),
        Kpi("gwp_plan_ratio",   "元受保険料 計画比",          103.1, "%",   +0.5,  "ok",   threshold=95.0,  max_val=110.0),
        Kpi("net_premium_growth","正味保険料増収率（YoY）",    4.8,  "%",   +0.1,  "ok",   threshold=0.0,   max_val=12.0),
        # ── ボトムライン ──────────────────────────────────────────────────────
        Kpi("op_profit_ytd",    "事業利益（BOP）YTD",         17.2, "億円",  +0.5,  "ok",   threshold=None,  max_val=None),
        Kpi("net_income_ytd",   "グループ純利益 YTD",          11.8, "億円",  +0.3,  "ok",   threshold=None,  max_val=None),
        Kpi("group_roe",        "グループROE",                 15.5, "%",   +0.3,  "ok",   threshold=12.0,  max_val=25.0),
        # ── 損保引受指標 ──────────────────────────────────────────────────────
        Kpi("combined_ratio",   "コンバインドレシオ",          97.2, "%",   -0.3,  "ok",   threshold=100.0, max_val=115.0),
        Kpi("loss_ratio",       "損害率（損保）",              66.1, "%",   +0.5,  "ok",   threshold=72.0,  max_val=90.0),
        Kpi("expense_ratio",    "費用率",                     31.1, "%",   -0.2,  "ok",   threshold=35.0,  max_val=45.0),
        Kpi("attritional_lr",   "通常損害率（CAT除く）",       63.4, "%",   +0.2,  "ok",   threshold=70.0,  max_val=85.0),
        Kpi("cat_loss_ytd",     "CAT損失 YTD",                  3.2, "億円",  0.0,  "ok",   threshold=8.0,   max_val=15.0),
        Kpi("cat_budget_usage", "CAT予算消化率",               40.0, "%",    0.0,  "ok",   threshold=80.0,  max_val=100.0),
        Kpi("reserve_release",  "前年度準備金リリース",         +1.2, "%",   +0.1,  "ok",   threshold=None,  max_val=None),
        # ── 生保指標 ─────────────────────────────────────────────────────────
        Kpi("nbv_ytd",          "新規事業価値（NBV）YTD",       5.2, "億円",  +0.1,  "ok",   threshold=None,  max_val=None),
        Kpi("nbm",              "新規事業マージン（NBM）",       5.3, "%",   +0.1,  "ok",   threshold=4.5,   max_val=10.0),
        Kpi("persistency_rate", "継続率（生保 13ヶ月）",        93.2, "%",   -0.1,  "ok",   threshold=90.0,  max_val=100.0),
        # ── 資本・運用 ───────────────────────────────────────────────────────
        Kpi("solvency_ratio",   "ソルベンシーⅡ比率（SCR）",  218.5, "%",   +1.2,  "ok",   threshold=150.0, max_val=280.0),
        Kpi("investment_return","運用利回り（ランニング）",      3.4, "%",    0.0,  "ok",   threshold=2.5,   max_val=6.0),
        # ── IT・オペレーション ───────────────────────────────────────────────
        Kpi("claims_ttd",       "保険金支払日数",               8.3, "日",  -0.2,  "ok",   threshold=15.0,  max_val=30.0),
        Kpi("system_avail",     "主要系稼働率",               99.97, "%",   +0.01, "ok",   threshold=99.95, max_val=100.0),
        Kpi("cyber_risk_score", "サイバーリスクスコア",         72.0, "pt",   0.0,  "ok",   threshold=60.0,  max_val=100.0),
    ]


def insurance_financial_monthly() -> pd.DataFrame:
    """月次財務サマリー（YTD 2026年1月〜5月速報）。
    スケール: 億円（JPY。国内大手保険グループ想定）。
    """
    months = ["1月", "2月", "3月", "4月", "5月\n(速報)"]
    #                                     Jan    Feb    Mar    Apr    May(partial)
    gwp_nonlife       = [19.5,  17.8,  22.1,  18.3,   4.7]   # 元受保険料（損保）億円
    gwp_life          = [15.8,  13.2,  16.4,  11.6,   3.2]   # 元受保険料（生保）億円
    plan_nonlife      = [18.5,  17.0,  21.0,  17.5,   4.5]   # 計画（損保）
    plan_life         = [14.5,  13.0,  15.5,  11.0,   3.0]   # 計画（生保）
    op_profit         = [ 4.1,   3.8,   4.8,   3.6,   0.9]   # 事業利益（BOP）億円
    op_profit_plan    = [ 3.8,   3.6,   4.5,   3.5,   0.85]  # BOP計画
    loss_ratio        = [65.5,  66.4,  65.1,  67.6,  66.1]   # 損害率 %
    expense_ratio     = [31.3,  31.1,  31.1,  31.2,  31.1]   # 費用率 %
    cat_loss          = [ 0.2,   0.5,   0.8,   1.5,   0.2]   # CAT損失月次 億円

    df = pd.DataFrame({
        "月":               months,
        "元受保険料（損保）": gwp_nonlife,
        "元受保険料（生保）": gwp_life,
        "計画（損保）":       plan_nonlife,
        "計画（生保）":       plan_life,
        "事業利益（BOP）":    op_profit,
        "事業利益計画":       op_profit_plan,
        "損害率(%)":          loss_ratio,
        "費用率(%)":          expense_ratio,
        "コンバインドレシオ":  [lr + er for lr, er in zip(loss_ratio, expense_ratio)],
        "CAT損失(億円)":       cat_loss,
    })
    df["CAT累積(億円)"] = df["CAT損失(億円)"].cumsum()
    return df


def insurance_kpi_map() -> dict[str, Kpi]:
    return {k.key: k for k in insurance_kpis()}


# ── Drill-down data ───────────────────────────────────────────────────────────

def insurance_cr_by_segment() -> pd.DataFrame:
    """コンバインドレシオ：損保種目別内訳"""
    return pd.DataFrame({
        "種目":          ["火災・住宅", "自動車",  "賠償責任", "海上・輸送", "医療費用", "その他"],
        "損害率(%)":     [61.2,         72.4,       58.3,       65.8,         78.2,        63.1],
        "費用率(%)":     [28.5,         32.1,       34.2,       29.8,         33.5,        31.0],
        "保険料シェア(%)": [28,           22,         18,         12,           11,           9],
    })


def insurance_gwp_by_geo() -> pd.DataFrame:
    """元受保険料：地域別内訳（億円）"""
    return pd.DataFrame({
        "地域":       ["欧州（西欧）", "北米",  "欧州（中東欧）", "アジア太平洋", "中東・アフリカ", "その他"],
        "損保(億円)":  [35.2,           18.4,    12.8,             10.2,            4.6,              1.2],
        "生保(億円)":  [28.5,           12.1,    8.3,              8.8,             1.8,              0.7],
        "前年比(%)":  [5.2,            3.4,     8.1,              12.3,            -1.2,             2.8],
    })


def insurance_solvency_sensitivity() -> pd.DataFrame:
    """ソルベンシーⅡ比率：シナリオ感応度"""
    return pd.DataFrame({
        "シナリオ":   ["現状",   "株価 −20%", "金利 +100bp", "金利 −100bp", "巨大CAT(10億円)", "複合ストレス"],
        "SCR比率(%)": [218.5,    195.2,        224.8,         201.3,          186.4,            162.7],
        "影響(pp)":   [0.0,      -23.3,        +6.3,          -17.2,          -32.1,            -55.8],
    })


def insurance_cat_events() -> pd.DataFrame:
    """CAT損失：イベント別明細（YTD）"""
    return pd.DataFrame({
        "イベント":         ["欧州洪水（3月）", "米国トルネード（4月）", "地中海嵐（2月）", "日本地震（1月）", "その他小口"],
        "グロス損失(億円)":  [0.85,              1.52,                    0.42,              0.18,             0.23],
        "再保険回収(億円)":  [0.53,              0.74,                    0.21,              0.10,             0.08],
        "純損失(億円)":      [0.32,              0.78,                    0.21,              0.08,             0.15],
        "回収率(%)":        [62.4,              48.7,                    50.0,              55.6,             34.8],
    })


def insurance_investment_by_class() -> pd.DataFrame:
    """投資ポートフォリオ：アセットクラス別収益内訳"""
    return pd.DataFrame({
        "アセットクラス": ["社債", "国債・政府債", "プライベートクレジット", "株式", "不動産・インフラ", "モーゲージ", "現金・その他"],
        "残高(億円)":      [44.8,   35.8,            15.3,                    10.2,   10.2,              7.7,          3.8],
        "利回り(%)":      [4.1,    3.2,             5.8,                     8.4,    6.2,               4.5,          1.8],
        "前年比(pp)":     [+0.3,   +0.2,            +0.5,                    +1.2,   -0.1,              +0.2,         -0.2],
        "配分(%)":        [35,     28,              12,                      8,      8,                 6,            3],
    })


def insurance_expense_by_category() -> pd.DataFrame:
    """費用内訳：カテゴリ別（YTD 億円）"""
    return pd.DataFrame({
        "カテゴリ":          ["損害査定費", "人件費・代理店手数料", "IT・デジタル投資", "一般管理費", "マーケティング", "コンプライアンス・規制", "その他"],
        "金額(億円)":         [14.2,         10.8,                   6.4,               4.1,         2.8,              1.5,                    0.9],
        "費用率貢献(pp)":    [11.1,         8.4,                    5.0,               3.2,         2.2,              1.2,                    0.7],
        "前年比(%)":         [+2.1,         +3.5,                   +8.2,              +1.8,        -1.2,             +5.6,                   +2.3],
        "計画比(%)":         [-1.2,         +2.1,                   +4.5,              -0.8,        -3.1,             +1.2,                   +0.5],
    })


def insurance_pnl_waterfall() -> pd.DataFrame:
    """P&L ウォーターフォール（YTD 億円）"""
    return pd.DataFrame({
        "項目": [
            "元受保険料合計", "再保険料コスト", "正味収入保険料",
            "保険金支払", "事業費", "引受損益（損保）",
            "生保事業利益", "投資収益", "持株費用", "事業利益（BOP）",
        ],
        "金額(億円)": [142.6, -14.5, 128.1, -84.7, -39.8, 3.6, 5.6, 11.6, -3.6, 17.2],
        "measure":   [
            "absolute", "relative", "total",
            "relative", "relative", "total",
            "relative", "relative", "relative", "total",
        ],
    })


# ── Timeseries ────────────────────────────────────────────────────────────────

def insurance_timeseries(days: int = 90, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    end = now_jst().date()
    dates = pd.date_range(end=end, periods=days, freq="D")

    combined_ratio = np.clip(
        97.2 + np.cumsum(rng.normal(0, 0.15, days)), 92.0, 104.0
    )
    solvency = np.clip(
        218.0 + np.cumsum(rng.normal(0, 0.6, days)), 195.0, 240.0
    )
    system_avail = np.clip(
        99.96 + rng.normal(0, 0.01, days), 99.88, 100.0
    )
    cat_daily = np.where(rng.random(days) > 0.93, rng.uniform(0.1, 0.6, days), 0.0)
    cat_ytd = np.cumsum(cat_daily)
    investment_return = np.clip(
        3.4 + np.cumsum(rng.normal(0, 0.04, days)), 2.8, 4.5
    )
    loss_ratio = np.clip(
        66.0 + np.cumsum(rng.normal(0, 0.12, days)), 61.0, 74.0
    )
    persistency = np.clip(
        93.2 + np.cumsum(rng.normal(0, 0.03, days)), 91.0, 95.0
    )

    return pd.DataFrame({
        "date":              dates,
        "コンバインドレシオ": combined_ratio,
        "ソルベンシー比率":   solvency,
        "主要系稼働率(%)":    system_avail,
        "CAT損失累積(億円)":   cat_ytd,
        "運用利回り(%)":      investment_return,
        "損害率(%)":          loss_ratio,
        "継続率(%)(生保)":    persistency,
    })


def insurance_security_timeseries(days: int = 30, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    end = now_jst().date()
    dates = pd.date_range(end=end, periods=days, freq="D")
    crit = rng.integers(0, 2, size=days).astype(float)
    warn = rng.integers(0, 5, size=days).astype(float)
    info = rng.integers(1, 8, size=days).astype(float)
    return pd.DataFrame({"date": dates, "CRIT": crit, "WARN": warn, "INFO": info})


# ── Alerts ────────────────────────────────────────────────────────────────────

def insurance_alerts() -> pd.DataFrame:
    t = now_jst()
    rows = [
        {"時刻": (t - timedelta(minutes=22)).strftime("%H:%M"),          "重要度": "CRIT", "領域": "引受リスク",       "内容": "台風12号上陸シナリオ — 想定CAT損失 最大1.8億円（モデル試算中）",         "状態": "対応中"},
        {"時刻": (t - timedelta(minutes=55)).strftime("%H:%M"),          "重要度": "CRIT", "領域": "サイバー",         "内容": "代理店ポータルへの不正アクセス試行を検知（IPブロック済・調査中）",     "状態": "対応中"},
        {"時刻": (t - timedelta(hours=1, minutes=18)).strftime("%H:%M"), "重要度": "WARN", "領域": "資本・ソルベンシー","内容": "SCR所要資本が先週比 +2.3%上昇 — 市場リスク要因（金利上昇）",           "状態": "監視"},
        {"時刻": (t - timedelta(hours=2, minutes=5)).strftime("%H:%M"),  "重要度": "WARN", "領域": "生保",             "内容": "特定商品の解約率が前月比 +1.2pt — 競合キャンペーン影響を調査中",       "状態": "監視"},
        {"時刻": (t - timedelta(hours=2, minutes=40)).strftime("%H:%M"), "重要度": "WARN", "領域": "コンプライアンス", "内容": "EIOPA四半期報告（Solvency II）提出期限まで 5営業日",                  "状態": "監視"},
        {"時刻": (t - timedelta(hours=4, minutes=10)).strftime("%H:%M"), "重要度": "INFO", "領域": "損保",             "内容": "大口法人保険更改手続き完了 — 年間保険料 23億円",                    "状態": "完了"},
        {"時刻": (t - timedelta(hours=6, minutes=25)).strftime("%H:%M"), "重要度": "INFO", "領域": "システム",         "内容": "保険計理バッチ（四半期準備金計算）正常完了（所要時間: 4h12m）",        "状態": "完了"},
        {"時刻": (t - timedelta(hours=8, minutes=0)).strftime("%H:%M"),  "重要度": "INFO", "領域": "投資",             "内容": "債券ポートフォリオ デュレーション調整完了（目標値±0.08年以内）",       "状態": "確認済"},
    ]
    return pd.DataFrame(rows)


# ── Industry config ───────────────────────────────────────────────────────────

INSURANCE_GROUP = IndustryConfig(
    id="insurance_group",
    name="保険持株会社（生損保グループ）",
    company_type="保険持株会社",
    company_desc="欧米型の保険持株会社。傘下に損害保険・生命保険子会社を持つグループ経営体制。",
    hq="フランクフルト（欧州本社）",
    regulatory_framework="Solvency II（EU）/ IAIS ICS",
    data_sources={
        "group_financials": DataSourceConfig(
            key="group_financials",
            name="グループ財務DWH",
            system="Oracle Financials / SAP BW",
            source_type="database",
            description="持株会社連結P&L・BS・CF（日次速報／月次確定）",
            roles=["CEO", "CFO"],
            refresh="日次（速報）／月次（確定）",
            tables=["consolidated_pnl", "balance_sheet", "cash_flow", "segment_report"],
        ),
        "actuarial": DataSourceConfig(
            key="actuarial",
            name="計理・準備金システム",
            system="ResQ / Prophet",
            source_type="database",
            description="責任準備金・SCR計算・保険数理モデル出力",
            roles=["CFO", "CRO"],
            refresh="週次（試算）／四半期（確定）",
            tables=["reserve_summary", "scr_calculation", "orsa_output"],
        ),
        "claims_mgmt": DataSourceConfig(
            key="claims_mgmt",
            name="損害査定・支払システム",
            system="Guidewire ClaimCenter",
            source_type="database",
            description="損害サマリー・CAT集計・支払処理トラッキング・訴訟管理",
            roles=["COO", "CRO"],
            refresh="日次",
            tables=["claim_summary", "cat_accumulation", "payment_tracking"],
        ),
        "policy_admin": DataSourceConfig(
            key="policy_admin",
            name="保険証券管理",
            system="Guidewire PolicyCenter / LifeSys",
            source_type="database",
            description="契約情報・継続率・解約分析・新契約進捗・代理店成績",
            roles=["CEO", "COO", "CFO"],
            refresh="日次",
            tables=["policy_summary", "lapse_analysis", "new_business", "agent_performance"],
        ),
        "investment": DataSourceConfig(
            key="investment",
            name="資産運用システム",
            system="BlackRock Aladdin",
            source_type="api",
            description="投資P&L・ポートフォリオリスク・デュレーション・VaR・クレジット格付",
            roles=["CFO", "CRO"],
            refresh="日次（リアルタイム）",
            tables=[],
        ),
        "solvency_reporting": DataSourceConfig(
            key="solvency_reporting",
            name="ソルベンシーⅡ報告",
            system="Moody's RMS / 社内SCRエンジン",
            source_type="api",
            description="SCR・MCR・ORSA指標（日次試算・四半期確定）、EIOPA提出データ",
            roles=["CEO", "CFO", "CRO"],
            refresh="日次（試算）",
            tables=[],
        ),
        "siem": DataSourceConfig(
            key="siem",
            name="SIEMプラットフォーム",
            system="Splunk Enterprise Security",
            source_type="streaming",
            description="セキュリティイベント・脅威インテリジェンス・インシデント管理",
            roles=["CSIO", "CIO"],
            refresh="リアルタイム",
            tables=[],
        ),
        "digital_analytics": DataSourceConfig(
            key="digital_analytics",
            name="デジタル顧客チャネル",
            system="Adobe Analytics / Salesforce",
            source_type="api",
            description="オンライン申込・代理店ポータル稼働・NPS・チャネル別転換率",
            roles=["CDO", "COO"],
            refresh="日次",
            tables=[],
        ),
        "ai_mlops": DataSourceConfig(
            key="ai_mlops",
            name="AI・MLOpsプラットフォーム",
            system="Azure ML / Databricks",
            source_type="api",
            description="引受AIモデル精度・保険金査定自動化率・ドリフト監視・プロジェクトROI",
            roles=["CAIO", "CDO"],
            refresh="日次",
            tables=[],
        ),
        "it_monitoring": DataSourceConfig(
            key="it_monitoring",
            name="ITインフラ監視",
            system="Dynatrace / ServiceNow",
            source_type="streaming",
            description="主要系稼働率・インシデント管理・変更管理・SLA追跡",
            roles=["CIO", "COO"],
            refresh="リアルタイム",
            tables=[],
        ),
    },
    roles={
        "CEO": RoleDataConfig(
            role="CEO",
            title_jp="グループCEO",
            kpi_keys=["combined_ratio", "solvency_ratio", "net_premium_growth", "group_roe", "cat_loss_ytd", "investment_return"],
            data_source_keys=["group_financials", "policy_admin", "solvency_reporting"],
            focus_areas=["グループ収益性", "資本十分性（Solvency II）", "M&A・戦略投資", "中期計画進捗"],
        ),
        "CFO": RoleDataConfig(
            role="CFO",
            title_jp="グループCFO",
            kpi_keys=["solvency_ratio", "investment_return", "group_roe", "cat_loss_ytd", "expense_ratio", "net_premium_growth"],
            data_source_keys=["group_financials", "actuarial", "investment", "solvency_reporting"],
            focus_areas=["ソルベンシー資本管理", "運用P&L", "再保険コスト", "EIOPA規制報告"],
        ),
        "CRO": RoleDataConfig(
            role="CRO",
            title_jp="グループCRO",
            kpi_keys=["combined_ratio", "cat_loss_ytd", "loss_ratio", "solvency_ratio", "expense_ratio", "investment_return"],
            data_source_keys=["actuarial", "claims_mgmt", "investment", "solvency_reporting"],
            focus_areas=["引受リスク管理", "CAT・巨大災害", "市場・信用リスク", "ORSA"],
        ),
        "COO": RoleDataConfig(
            role="COO",
            title_jp="グループCOO",
            kpi_keys=["claims_ttd", "expense_ratio", "persistency_rate", "loss_ratio", "system_avail", "net_premium_growth"],
            data_source_keys=["claims_mgmt", "policy_admin", "digital_analytics", "it_monitoring"],
            focus_areas=["保険金支払オペレーション", "代理店管理", "費用管理", "業務継続"],
        ),
        "CIO": RoleDataConfig(
            role="CIO",
            title_jp="グループCIO",
            kpi_keys=["system_avail", "cyber_risk_score", "combined_ratio", "expense_ratio", "claims_ttd", "net_premium_growth"],
            data_source_keys=["it_monitoring", "siem", "digital_analytics"],
            focus_areas=["基幹系稼働率", "コアシステム近代化", "クラウド移行", "IT投資ROI"],
        ),
        "CSIO": RoleDataConfig(
            role="CSIO",
            title_jp="グループCSIO",
            kpi_keys=["cyber_risk_score", "system_avail", "combined_ratio", "loss_ratio", "claims_ttd", "solvency_ratio"],
            data_source_keys=["siem", "it_monitoring"],
            focus_areas=["サイバーリスク", "代理店ポータルセキュリティ", "顧客データ保護", "GDPR対応"],
        ),
        "CDO": RoleDataConfig(
            role="CDO",
            title_jp="グループCDO",
            kpi_keys=["system_avail", "persistency_rate", "expense_ratio", "combined_ratio", "net_premium_growth", "cyber_risk_score"],
            data_source_keys=["digital_analytics", "ai_mlops", "policy_admin"],
            focus_areas=["デジタル申込比率", "データ品質", "顧客体験（NPS）", "DXロードマップ"],
        ),
        "CAIO": RoleDataConfig(
            role="CAIO",
            title_jp="グループCAIO",
            kpi_keys=["combined_ratio", "claims_ttd", "persistency_rate", "expense_ratio", "system_avail", "cyber_risk_score"],
            data_source_keys=["ai_mlops", "claims_mgmt", "digital_analytics"],
            focus_areas=["引受AIモデル精度", "保険金査定自動化", "AIガバナンス", "AI施策ROI"],
        ),
    },
)
