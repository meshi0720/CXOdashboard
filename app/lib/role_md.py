from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import streamlit as st

from .roles import Role, RoleConfig


@dataclass(frozen=True)
class RoleMarkdown:
    config: RoleConfig
    highlights: tuple[str, ...]


def _parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    """Minimal frontmatter parser (no extra dependencies)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    i = 1
    fm_lines: list[str] = []
    while i < len(lines):
        if lines[i].strip() == "---":
            body = "\n".join(lines[i + 1 :]).lstrip("\n")
            fm = _parse_yamlish("\n".join(fm_lines))
            return fm, body
        fm_lines.append(lines[i])
        i += 1
    return {}, text


def _parse_yamlish(fm_text: str) -> dict[str, object]:
    # Subset of YAML: scalar values and simple lists only.
    out: dict[str, object] = {}
    cur_key: str | None = None
    cur_list: list[str] | None = None

    def _commit_list():
        nonlocal cur_key, cur_list
        if cur_key is not None and cur_list is not None:
            out[cur_key] = [s for s in cur_list if s != ""]
        cur_key, cur_list = None, None

    for raw in fm_text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        if line.startswith("  - ") and cur_key and cur_list is not None:
            cur_list.append(line[len("  - ") :].strip())
            continue

        if ":" in line:
            _commit_list()
            key, rest = line.split(":", 1)
            key = key.strip()
            rest = rest.strip()
            if rest == "":
                cur_key = key
                cur_list = []
            else:
                out[key] = rest
            continue

    _commit_list()
    return out


def _role_md_path(role: Role) -> Path:
    return Path(__file__).resolve().parents[1] / "content" / "roles" / f"{role}.md"


def _coerce_str_list(raw: object) -> tuple[str, ...]:
    """Coerce YAML value to tuple[str]: list items, or one inline string (not char-split)."""
    if raw is None:
        return ()
    if isinstance(raw, str):
        s = raw.strip()
        return (s,) if s else ()
    if isinstance(raw, (list, tuple)):
        return tuple(str(x).strip() for x in raw if str(x).strip())
    return ()


@st.cache_data(show_spinner=False)
def load_role_markdown(role: Role) -> RoleMarkdown:
    p = _role_md_path(role)
    text = p.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(text)

    tagline = str(fm.get("tagline", "")).strip()
    kpi_keys = _coerce_str_list(fm.get("home_kpi_keys"))
    trend = _coerce_str_list(fm.get("home_trend_series"))

    cfg = RoleConfig(role=role, home_kpi_keys=kpi_keys, home_trend_series=trend, tagline=tagline)

    highlights = _extract_highlights(body)
    return RoleMarkdown(config=cfg, highlights=highlights)


def _extract_highlights(body_md: str) -> tuple[str, ...]:
    """Extract bullet items under ## ハイライト (max 5)."""
    lines = body_md.splitlines()
    in_section = False
    items: list[str] = []
    for line in lines:
        s = line.strip()
        if s.startswith("## "):
            in_section = s == "## ハイライト"
            continue
        if not in_section:
            continue
        if s.startswith("- "):
            items.append(s[2:].strip())
        elif s.startswith("## "):
            break
        if len(items) >= 5:
            break
    return tuple(items)
