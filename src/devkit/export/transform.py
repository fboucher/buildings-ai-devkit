"""Transform one source page into its agent-optimised form (ADR-0005).

Pure functions only: no file system access, so the transform is easy to test and
deterministic by construction.
"""

from __future__ import annotations

import posixpath
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import yaml

from devkit.validate import MAX_DESCRIPTION_LENGTH

DEPRECATED_NOTICE = (
    "> **Deprecated.** This feature is deprecated. Do not use it for new integrations."
)

_FENCE = re.compile(r"^\s*(```|~~~)")
_INLINE_CODE = re.compile(r"(`+)(?:(?!\1).)+?\1")
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_TARGET = r"\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)"
_IMAGE = re.compile(r"!\[([^\]\n]*)\]" + _TARGET)
_LINK = re.compile(r"(?<!!)\[([^\]\n]*)\]" + _TARGET)
_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


@dataclass
class PageNotes:
    """What the transform did to one page, for the export report."""

    description_fallback: bool = False
    description_truncated: bool = False
    comments_removed: int = 0
    images_dropped: list[str] = field(default_factory=list)
    images_kept: list[str] = field(default_factory=list)
    links_removed: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SourcePage:
    src: str
    label: str
    section: str
    meta: dict[str, Any]
    body: str


def transform_page(
    page: SourcePage,
    exported: frozenset[str],
    images_allow: frozenset[str],
    existing_files: frozenset[str],
) -> tuple[str, PageNotes]:
    """Return the output markdown for ``page`` and notes about what changed.

    ``exported`` holds the ``src`` paths of every page in this export, ``existing_files``
    every file under the source ``docs_dir`` (POSIX paths relative to it).
    """
    notes = PageNotes()
    body = page.body.replace("\r\n", "\n")

    def rewrite(text: str) -> str:
        text, count = _COMMENT.subn("", text)
        notes.comments_removed += count
        text = _IMAGE.sub(lambda m: _image(m, page.src, images_allow, notes), text)
        return _LINK.sub(lambda m: _link(m, page.src, exported, existing_files, notes), text)

    body = _outside_code(body, rewrite)

    tags = _tags(page.meta)
    meta: dict[str, Any] = {
        "title": page.label,
        "description": _description(page.meta, body, page.label, notes),
        "section": page.section,
    }
    if tags:
        meta["tags"] = tags
    deprecated = "deprecated" in tags
    if deprecated:
        meta["status"] = "deprecated"

    front = yaml.safe_dump(
        meta, sort_keys=False, allow_unicode=True, width=10_000, default_flow_style=False
    )
    body = body.strip("\n")
    if deprecated:
        body = f"{DEPRECATED_NOTICE}\n\n{body}"
    return f"---\n{front}---\n\n{body}\n", notes


def source_tags(meta: dict[str, Any] | None) -> list[str]:
    return _tags(meta or {})


def _tags(meta: dict[str, Any]) -> list[str]:
    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    return [str(t).strip() for t in tags if str(t).strip()]


# --- code-aware rewriting -------------------------------------------------------------


def _outside_code(body: str, fn: Callable[[str], str]) -> str:
    """Apply ``fn`` to text outside fenced code blocks and inline code spans."""
    out: list[str] = []
    chunk: list[str] = []
    in_fence = False

    def flush() -> None:
        if chunk:
            out.append(_outside_inline_code("".join(chunk), fn))
            chunk.clear()

    for line in body.splitlines(keepends=True):
        if _FENCE.match(line):
            if not in_fence:
                flush()
            in_fence = not in_fence
            out.append(line)
        elif in_fence:
            out.append(line)
        else:
            chunk.append(line)
    flush()
    return "".join(out)


def _outside_inline_code(text: str, fn: Callable[[str], str]) -> str:
    spans: list[str] = []

    def stash(match: re.Match[str]) -> str:
        spans.append(match.group(0))
        return f"\x00{len(spans) - 1}\x00"

    protected = _INLINE_CODE.sub(stash, text)
    return re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], fn(protected))


# --- images and links -----------------------------------------------------------------


def _resolve(src: str, target: str) -> str:
    return posixpath.normpath(posixpath.join(posixpath.dirname(src), target))


def _image(m: re.Match[str], src: str, allow: frozenset[str], notes: PageNotes) -> str:
    alt, target = m.group(1).strip(), m.group(2)
    resolved = target if _SCHEME.match(target) else _resolve(src, target)
    if resolved in allow:
        notes.images_kept.append(resolved)
        return m.group(0)
    notes.images_dropped.append(resolved)
    return f"*[Image: {alt}]*" if alt else "*[Image]*"


def _link(
    m: re.Match[str],
    src: str,
    exported: frozenset[str],
    existing: frozenset[str],
    notes: PageNotes,
) -> str:
    text, target = m.group(1), m.group(2)
    if target.startswith("#") or target.startswith("//") or _SCHEME.match(target):
        return m.group(0)
    path, sep, anchor = target.partition("#")
    path = path.split("?", 1)[0]
    resolved = _resolve(src, path)

    candidates = [resolved]
    if not resolved.endswith(".md"):
        candidates = [f"{resolved}.md", f"{resolved}/index.md", resolved]
    for candidate in candidates:
        if candidate in exported:
            new = posixpath.relpath(candidate, posixpath.dirname(src) or ".")
            return f"[{text}]({new}{sep}{anchor})"

    notes.links_removed.append(target)
    return text


# --- description ----------------------------------------------------------------------

_SKIP_PARAGRAPH = re.compile(r"^\s*(#|>|\||<|\*\[Image|[-*+]\s|\d+[.)]\s|---|===)")


def _description(meta: dict[str, Any], body: str, label: str, notes: PageNotes) -> str:
    raw = meta.get("description")
    if isinstance(raw, str) and raw.strip():
        text = _clean_inline(raw)
    else:
        notes.description_fallback = True
        text = _first_paragraph(body) or label
    if len(text) > MAX_DESCRIPTION_LENGTH:
        notes.description_truncated = True
        text = _shorten(text)
    return text


_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _shorten(text: str) -> str:
    """Keep whole sentences that fit; fall back to a word cut with an ellipsis."""
    kept = ""
    for sentence in _SENTENCE_END.split(text):
        candidate = f"{kept} {sentence}".strip()
        if len(candidate) > MAX_DESCRIPTION_LENGTH:
            break
        kept = candidate
    if kept:
        return kept
    cut = text[: MAX_DESCRIPTION_LENGTH - 1].rsplit(" ", 1)[0].rstrip(",;:.")
    return f"{cut}…"


def _first_paragraph(body: str) -> str:
    in_fence = False
    paragraph: list[str] = []
    for line in body.splitlines():
        if _FENCE.match(line):
            in_fence = not in_fence
            if paragraph:
                break
            continue
        if in_fence:
            continue
        if not line.strip():
            if paragraph:
                break
            continue
        if not paragraph and _SKIP_PARAGRAPH.match(line):
            continue
        if paragraph and _SKIP_PARAGRAPH.match(line):
            break
        paragraph.append(line.strip())
    return _clean_inline(" ".join(paragraph))


def _clean_inline(text: str) -> str:
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"(\*\*|__|`)", "", text)
    text = re.sub(r"(?<!\w)[*_](\S.*?\S|\S)[*_](?!\w)", r"\1", text)
    return " ".join(text.split())
