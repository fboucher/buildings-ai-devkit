"""Minimal YAML front matter parsing for markdown pages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml

DELIMITER = "---"


class FrontMatterError(ValueError):
    """Raised when a front matter block exists but cannot be parsed."""


@dataclass(frozen=True)
class Page:
    meta: dict[str, Any] | None
    """Parsed front matter, or ``None`` when the page has no front matter block."""
    body: str
    body_start_line: int
    """1-based line number in the original file where ``body`` begins."""


def parse(text: str) -> Page:
    """Split ``text`` into front matter and body.

    Front matter must start on the first line with ``---`` and end with a line that is
    exactly ``---``.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip() != DELIMITER:
        return Page(meta=None, body=text, body_start_line=1)

    for index in range(1, len(lines)):
        if lines[index].rstrip() == DELIMITER:
            raw = "".join(lines[1:index])
            try:
                meta = yaml.safe_load(raw) if raw.strip() else {}
            except yaml.YAMLError as exc:
                raise FrontMatterError(f"invalid YAML in front matter: {exc}") from exc
            if not isinstance(meta, dict):
                raise FrontMatterError("front matter must be a YAML mapping")
            return Page(meta=meta, body="".join(lines[index + 1 :]), body_start_line=index + 2)

    raise FrontMatterError("front matter block is not closed with '---'")
