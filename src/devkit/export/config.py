"""Exporter configuration, loaded from ``export.yml`` in this repo.

This file is public. It must never contain internal hostnames, names or other sensitive
values: those belong in the block list, which lives in the source repo (ADR-0004).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class LlmsConfig:
    site_url: str
    title: str
    summary: str
    notes: str = ""
    optional_sections: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExportConfig:
    llms: LlmsConfig
    include: tuple[str, ...] = ("**",)
    images_allow: frozenset[str] = field(default_factory=frozenset)
    long_page_words: int = 2500
    pr_base: str = "main"


class ConfigError(ValueError):
    pass


def load_config(path: Path) -> ExportConfig:
    if not path.is_file():
        raise ConfigError(f"config file '{path}' not found")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ConfigError("config must be a YAML mapping")

    llms = data.get("llms") or {}
    try:
        llms_cfg = LlmsConfig(
            site_url=str(llms["site_url"]).rstrip("/"),
            title=str(llms["title"]),
            summary=" ".join(str(llms["summary"]).split()),
            notes=str(llms.get("notes") or "").strip(),
            optional_sections=tuple(llms.get("optional_sections") or ()),
        )
    except KeyError as exc:
        raise ConfigError(f"missing llms.{exc.args[0]} in config") from exc

    images = data.get("images") or {}
    return ExportConfig(
        llms=llms_cfg,
        include=tuple(data.get("include") or ("**",)),
        images_allow=frozenset(images.get("allow") or ()),
        long_page_words=int(data.get("long_page_words", 2500)),
        pr_base=str(data.get("pr_base", "main")),
    )
