"""Read the published page list from a MkDocs ``mkdocs.yml`` ``nav`` (ADR-0004)."""

from __future__ import annotations

import fnmatch
import posixpath
from dataclasses import dataclass
from pathlib import Path

import yaml


class NavError(ValueError):
    pass


@dataclass(frozen=True)
class NavPage:
    label: str
    src: str
    """Path relative to ``docs_dir``, POSIX style."""
    parents: tuple[str, ...]

    @property
    def section(self) -> str:
        return " / ".join(self.parents) if self.parents else self.label

    @property
    def nav_key(self) -> str:
        """Slash-joined nav path used by ``include`` patterns, e.g. ``REST API/Endpoints/Sites``."""
        return "/".join((*self.parents, self.label))


@dataclass(frozen=True)
class MkDocsSite:
    config_path: Path
    docs_dir: Path
    pages: tuple[NavPage, ...]


class _TolerantLoader(yaml.SafeLoader):
    """SafeLoader that accepts MkDocs-specific tags (``!ENV``, ``!!python/name:``...)."""


def _any_tag(loader: yaml.SafeLoader, _suffix: str, node: yaml.Node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_mapping(node)


_TolerantLoader.add_multi_constructor("!", _any_tag)
_TolerantLoader.add_multi_constructor("tag:yaml.org,2002:python/", _any_tag)


def find_mkdocs_config(source: Path) -> Path:
    """Find ``mkdocs.yml`` at the source root or exactly one level below it."""
    candidates = [source / "mkdocs.yml"] if (source / "mkdocs.yml").is_file() else []
    if not candidates:
        candidates = sorted(source.glob("*/mkdocs.yml"))
    if len(candidates) != 1:
        found = ", ".join(str(c) for c in candidates) or "none"
        raise NavError(f"expected exactly one mkdocs.yml under '{source}', found: {found}")
    return candidates[0]


def load_site(config_path: Path) -> MkDocsSite:
    data = yaml.load(config_path.read_text(encoding="utf-8"), Loader=_TolerantLoader)  # noqa: S506
    if not isinstance(data, dict):
        raise NavError(f"'{config_path}' is not a YAML mapping")
    nav = data.get("nav")
    if not isinstance(nav, list):
        raise NavError(f"'{config_path}' has no 'nav' list")
    docs_dir = (config_path.parent / str(data.get("docs_dir", "docs"))).resolve()

    pages: list[NavPage] = []
    seen: set[str] = set()
    _walk(nav, (), pages, seen)
    return MkDocsSite(config_path=config_path, docs_dir=docs_dir, pages=tuple(pages))


def _walk(items: list, parents: tuple[str, ...], out: list[NavPage], seen: set[str]) -> None:
    for item in items:
        if isinstance(item, str):
            _add(posixpath.splitext(posixpath.basename(item))[0], item, parents, out, seen)
        elif isinstance(item, dict):
            for label, value in item.items():
                if isinstance(value, list):
                    _walk(value, (*parents, str(label)), out, seen)
                elif isinstance(value, str):
                    _add(str(label), value, parents, out, seen)


def _add(label: str, target: str, parents, out: list[NavPage], seen: set[str]) -> None:
    if "://" in target or not target.endswith(".md"):
        return  # external link or non-page entry
    src = posixpath.normpath(target.lstrip("/"))
    if src in seen:
        return
    seen.add(src)
    out.append(NavPage(label=label.strip(), src=src, parents=parents))


def matches_include(page: NavPage, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatchcase(page.nav_key, pattern) for pattern in patterns)
