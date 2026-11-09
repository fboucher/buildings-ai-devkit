"""Generate ``llms.txt`` and ``llms-full.txt`` from ``docs/`` (ADR-0007).

Format: https://llmstxt.org. Links point to the raw markdown pages published on GitHub
Pages. API pages keep the source ``nav`` order recorded in ``docs/api/_source.json``.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml

from devkit import frontmatter


@dataclass(frozen=True)
class LlmsConfig:
    site_url: str
    title: str
    summary: str
    notes: str = ""
    optional_sections: tuple[str, ...] = ()


class ConfigError(ValueError):
    pass


def load_config(path: Path) -> LlmsConfig:
    if not path.is_file():
        raise ConfigError(f"config file '{path}' not found")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    try:
        return LlmsConfig(
            site_url=str(data["site_url"]).rstrip("/"),
            title=str(data["title"]),
            summary=" ".join(str(data["summary"]).split()),
            notes=" ".join(str(data.get("notes") or "").split()),
            optional_sections=tuple(data.get("optional_sections") or ()),
        )
    except (KeyError, TypeError) as exc:
        raise ConfigError(f"'{path}' is missing a required key: {exc}") from exc


AREA_TITLES = {"guides": "Guides", "brick": "Brick", "examples": "Examples"}
AREA_ORDER = ("api", "guides", "brick", "examples")
OPTIONAL = "Optional"
SECTION_DIR = "llms-full"


@dataclass(frozen=True)
class Entry:
    path: str
    """Repo-relative POSIX path, e.g. ``docs/api/rest-api/sites.md``."""
    title: str
    description: str
    group: str
    deprecated: bool
    body: str
    section: str


def collect(content_dir: Path) -> list[Entry]:
    content_dir = content_dir.resolve()
    entries: list[Entry] = []
    for area in _areas(content_dir):
        for path in _ordered_pages(content_dir / area):
            rel = path.relative_to(content_dir).as_posix()
            page = frontmatter.parse(path.read_text(encoding="utf-8"))
            meta = page.meta or {}
            section = str(meta.get("section") or AREA_TITLES.get(area, area.title()))
            group = section.split(" / ")[0] if area == "api" else section
            entries.append(
                Entry(
                    path=f"docs/{rel}",
                    title=str(meta.get("title") or path.stem),
                    description=str(meta.get("description") or ""),
                    group=group,
                    deprecated=meta.get("status") == "deprecated",
                    body=page.body.strip("\n"),
                    section=section,
                )
            )
    return entries


def _areas(content_dir: Path) -> list[str]:
    present = sorted(p.name for p in content_dir.iterdir() if p.is_dir())
    known = [a for a in AREA_ORDER if a in present]
    return known + [a for a in present if a not in AREA_ORDER]


def _ordered_pages(area_dir: Path) -> list[Path]:
    pages = sorted(area_dir.rglob("*.md"))
    manifest = area_dir / "_source.json"
    if not manifest.is_file():
        return pages
    order = json.loads(manifest.read_text(encoding="utf-8")).get("pages", [])
    rank = {src: i for i, src in enumerate(order)}
    return sorted(pages, key=lambda p: (rank.get(p.relative_to(area_dir).as_posix(), len(rank)), p))


def _grouped(entries: list[Entry], cfg: LlmsConfig) -> list[tuple[str, list[Entry]]]:
    groups: dict[str, list[Entry]] = {}
    optional: list[Entry] = []
    for entry in entries:
        if entry.group in cfg.optional_sections:
            optional.append(entry)
        else:
            groups.setdefault(entry.group, []).append(entry)
    result = list(groups.items())
    if optional:
        result.append((OPTIONAL, optional))
    return result


def _header(cfg: LlmsConfig) -> str:
    text = f"# {cfg.title}\n\n> {cfg.summary}\n"
    if cfg.notes:
        text += f"\n{cfg.notes}\n"
    return text


def slug(group: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", group.lower()).strip("-") or "section"


def render_index(entries: list[Entry], cfg: LlmsConfig) -> str:
    """The ``llms.txt`` index. ``## Optional`` stays last, as the llms.txt spec expects."""
    grouped = _grouped(entries, cfg)
    parts = [_header(cfg)]
    parts += [_link_list(g, items, cfg) for g, items in grouped if g != OPTIONAL]

    full = [f"- [All pages]({cfg.site_url}/llms-full.txt): every page in one file"]
    full += [
        f"- [{g}]({cfg.site_url}/{SECTION_DIR}/{slug(g)}.txt): full text of this section"
        for g, _ in grouped
    ]
    parts.append("## Full text\n\n" + "\n".join(full) + "\n")

    parts += [_link_list(g, items, cfg) for g, items in grouped if g == OPTIONAL]
    return "\n".join(parts)


def _link_list(group: str, items: list[Entry], cfg: LlmsConfig) -> str:
    lines = [f"## {group}", ""]
    for e in items:
        desc = f"(deprecated) {e.description}" if e.deprecated else e.description
        suffix = f": {desc}" if desc else ""
        lines.append(f"- [{e.title}]({cfg.site_url}/{e.path}){suffix}")
    return "\n".join(lines) + "\n"


def render_full(entries: list[Entry], cfg: LlmsConfig) -> str:
    parts = [_header(cfg)]
    for e in entries:
        meta = [f"path: {e.path}", f"title: {e.title}", f"section: {e.section}"]
        if e.deprecated:
            meta.append("status: deprecated")
        parts.append("---\n" + "\n".join(meta) + "\n---\n\n" + e.body + "\n")
    return "\n".join(parts)


def estimate_tokens(text: str) -> int:
    """Rough estimate (4 characters per token), good enough for size tracking."""
    return len(text) // 4


def generate(content_dir: Path, cfg: LlmsConfig) -> dict[str, str]:
    """Return ``{path relative to public/: text}``."""
    entries = collect(content_dir)
    grouped = _grouped(entries, cfg)
    ordered = [e for _, items in grouped for e in items]
    files = {"llms.txt": render_index(entries, cfg), "llms-full.txt": render_full(ordered, cfg)}
    for group, items in grouped:
        files[f"{SECTION_DIR}/{slug(group)}.txt"] = render_full(items, cfg)
    return files


def write(public_dir: Path, files: dict[str, str]) -> None:
    shutil.rmtree(public_dir / SECTION_DIR, ignore_errors=True)
    for name, text in files.items():
        path = public_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")


def stale(public_dir: Path, files: dict[str, str]) -> list[str]:
    """Generated files whose committed copy differs from ``files``, or should not exist."""
    out = [
        name
        for name, text in files.items()
        if not (public_dir / name).is_file()
        or (public_dir / name).read_text(encoding="utf-8") != text
    ]
    section_dir = public_dir / SECTION_DIR
    if section_dir.is_dir():
        out += [
            f"{SECTION_DIR}/{p.name}"
            for p in sorted(section_dir.iterdir())
            if f"{SECTION_DIR}/{p.name}" not in files
        ]
    return out
