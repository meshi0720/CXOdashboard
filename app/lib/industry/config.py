from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DataSourceConfig:
    key: str
    name: str
    system: str
    source_type: str          # "database" | "api" | "streaming" | "file"
    description: str
    roles: list[str]
    refresh: str = "日次"
    status: str = "接続済"    # "接続済" | "設定中" | "未接続"
    tables: list[str] = field(default_factory=list)


@dataclass
class RoleDataConfig:
    role: str
    title_jp: str
    kpi_keys: list[str]
    data_source_keys: list[str]
    focus_areas: list[str]


@dataclass
class IndustryConfig:
    id: str
    name: str
    company_type: str
    company_desc: str
    hq: str
    regulatory_framework: str
    data_sources: dict[str, DataSourceConfig]
    roles: dict[str, RoleDataConfig]
