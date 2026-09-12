"""Render numeric analysis thresholds into SQL models."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

TOKEN_RE = re.compile(r"{{\s*([A-Z][A-Z0-9_]*)\s*}}")


def _flatten(values: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, value in values.items():
        name = f"{prefix}_{key}" if prefix else key
        if isinstance(value, dict):
            flattened.update(_flatten(value, name))
        else:
            flattened[name.upper()] = value
    return flattened


def load_thresholds(path: Path) -> dict[str, Any]:
    values = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(values, dict):
        raise ValueError("threshold configuration root must be a mapping")
    flattened = _flatten(values)
    if not flattened:
        raise ValueError("threshold configuration must not be empty")
    return flattened


def _sql_literal(value: Any) -> str:
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return format(value, ".15g")
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    raise TypeError(f"unsupported threshold type: {type(value).__name__}")


def render_sql_text(sql_text: str, thresholds: dict[str, Any]) -> str:
    tokens = set(TOKEN_RE.findall(sql_text))
    missing = sorted(tokens - set(thresholds))
    if missing:
        raise KeyError(f"missing threshold configuration: {', '.join(missing)}")
    return TOKEN_RE.sub(
        lambda match: _sql_literal(thresholds[match.group(1)]),
        sql_text,
    )


def render_sql_file(sql_path: Path, thresholds_path: Path) -> str:
    thresholds = load_thresholds(thresholds_path)
    return render_sql_text(sql_path.read_text(encoding="utf-8"), thresholds)
