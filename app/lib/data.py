from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

import numpy as np
import pandas as pd


TZ_JST = timezone(timedelta(hours=9))


@dataclass(frozen=True)
class Kpi:
    key: str
    label: str
    value: float
    unit: str
    delta_1d: float
    status: Literal["ok", "warn", "crit"]
    threshold: float | None = None   # 警戒閾値（ゲージの目盛り）
    max_val: float | None = None     # ゲージ最大値


def now_jst() -> datetime:
    return datetime.now(tz=TZ_JST)


def sample_kpis() -> list[Kpi]:
    return [
        Kpi("capital_ratio", "自己資本比率",       12.4,  "%",   -0.1,  "ok",   threshold=8.0,   max_val=20.0),
        Kpi("liq_coverage",  "流動性カバレッジ(LCR)", 138.0, "%",   -3.2,  "warn", threshold=100.0, max_val=200.0),
        Kpi("npl_ratio",     "不良債権比率(NPL)",   1.12,  "%",    0.05, "warn", threshold=2.0,   max_val=5.0),
        Kpi("system_avail",  "主要系稼働率(当日)",  99.98, "%",   -0.01, "ok",   threshold=99.95, max_val=100.0),
        Kpi("security_risk", "セキュリティ重要アラート(24h)", 2, "件", 1, "crit", threshold=1.0,   max_val=10.0),
        Kpi("pnl_today",     "当日損益(概算)",      1.8,   "億円",  0.6,  "ok",   threshold=None,  max_val=None),
    ]


def kpi_map() -> dict[str, Kpi]:
    return {k.key: k for k in sample_kpis()}


def sample_alerts() -> pd.DataFrame:
    t = now_jst()
    rows = [
        {"時刻": (t - timedelta(minutes=18)).strftime("%H:%M"),  "重要度": "CRIT", "領域": "セキュリティ", "内容": "EDRで疑わしい横展開挙動を検知（端末隔離済み・調査中）",         "状態": "対応中"},
        {"時刻": (t - timedelta(minutes=42)).strftime("%H:%M"),  "重要度": "CRIT", "領域": "システム",     "内容": "勘定系バッチ処理タイムアウト — 影響: 決済遅延 約200件",          "状態": "対応中"},
        {"時刻": (t - timedelta(hours=1, minutes=10)).strftime("%H:%M"), "重要度": "WARN", "領域": "流動性", "内容": "LCRが社内しきい値（120%）に接近: 現在 138%（翌営業日 見込み 122%）", "状態": "監視"},
        {"時刻": (t - timedelta(hours=2, minutes=5)).strftime("%H:%M"),  "重要度": "WARN", "領域": "セキュリティ", "内容": "特権IDの深夜ログイン検知 — 本人確認中",                    "状態": "監視"},
        {"時刻": (t - timedelta(hours=2, minutes=55)).strftime("%H:%M"), "重要度": "WARN", "領域": "市場リスク", "内容": "USD/JPY ボラティリティ急上昇 — VaR限度の88%に到達",           "状態": "監視"},
        {"時刻": (t - timedelta(hours=3, minutes=30)).strftime("%H:%M"), "重要度": "INFO", "領域": "システム",  "内容": "外部API（決済ゲートウェイ）レイテンシ増加 — 自動リトライで回復", "状態": "完了"},
        {"時刻": (t - timedelta(hours=5, minutes=40)).strftime("%H:%M"), "重要度": "INFO", "領域": "システム",  "内容": "夜間バッチ遅延 15分 — 翌朝処理に影響なし",                      "状態": "完了"},
        {"時刻": (t - timedelta(hours=7, minutes=12)).strftime("%H:%M"), "重要度": "INFO", "領域": "信用リスク", "内容": "大口先の格付け見直し通知受信 — 与信審査チームに共有済み",       "状態": "確認済"},
    ]
    return pd.DataFrame(rows)


def filter_alerts(
    df: pd.DataFrame,
    severities: set[str] | None = None,
    domains: set[str] | None = None,
    statuses: set[str] | None = None,
) -> pd.DataFrame:
    out = df.copy()
    if severities:
        out = out[out["重要度"].isin(sorted(severities))]
    if domains:
        out = out[out["領域"].isin(sorted(domains))]
    if statuses:
        out = out[out["状態"].isin(sorted(statuses))]
    return out.reset_index(drop=True)


def sample_security_timeseries(days: int = 30, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    end = now_jst().date()
    dates = pd.date_range(end=end, periods=days, freq="D")
    crit = rng.integers(0, 3, size=days).astype(float)
    warn = rng.integers(0, 6, size=days).astype(float)
    info = rng.integers(1, 10, size=days).astype(float)
    return pd.DataFrame({"date": dates, "CRIT": crit, "WARN": warn, "INFO": info})


def sample_timeseries(days: int = 90, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    end = now_jst().date()
    dates = pd.date_range(end=end, periods=days, freq="D")

    base = np.cumsum(rng.normal(0, 0.25, size=days)) + 100
    stress = np.maximum(0, rng.normal(0.8, 0.6, size=days))
    availability = np.clip(99.96 + rng.normal(0, 0.01, size=days), 99.90, 100.0)

    return pd.DataFrame(
        {
            "date": dates,
            "市場ストレス指数": base,
            "資金流出圧力": stress,
            "主要系稼働率(%)": availability,
        }
    )

_TIMESERIES_COL_ALIASES: dict[str, str] = {
    "市場ストレス指数(仮)": "市場ストレス指数",
    "資金流出圧力(仮)": "資金流出圧力",
}


def resolve_timeseries_column(df: pd.DataFrame, name: str) -> str | None:
    if name in df.columns:
        return name
    mapped = _TIMESERIES_COL_ALIASES.get(name)
    if mapped and mapped in df.columns:
        return mapped
    return None


def wide_to_long(
    df: pd.DataFrame,
    x: str,
    y_cols: list[str] | tuple[str, ...],
    *,
    var_name: str = "series",
    value_name: str = "value",
) -> pd.DataFrame:
    """Melt wide columns so Plotly Express does not treat y=[colA, colB] as length-2 data."""
    resolved: list[str] = []
    seen: set[str] = set()
    for w in y_cols:
        col = resolve_timeseries_column(df, str(w).strip())
        if col is None or col in seen:
            continue
        resolved.append(col)
        seen.add(col)
    if not resolved or x not in df.columns:
        return pd.DataFrame(columns=[x, var_name, value_name])
    return df[[x] + resolved].melt(id_vars=x, var_name=var_name, value_name=value_name)


def timeseries_long_for_plot(
    df: pd.DataFrame, wanted: tuple[str, ...]
) -> tuple[pd.DataFrame, list[str]]:
    """Return long-form (date, series, value) for px.line; avoids wide-form y=list quirks."""
    missing = [w for w in wanted if resolve_timeseries_column(df, w.strip()) is None]
    long = wide_to_long(df, "date", wanted)
    return long, missing
