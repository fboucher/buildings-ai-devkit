"""Validate pages under ``docs/`` against the front matter and link conventions.

See "Content rules" in CONTRIBUTING.md for the rules enforced here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from devkit import frontmatter

ALLOWED_KEYS = {"title", "description", "section", "tags", "status"}
REQUIRED_KEYS = {"title", "description"}
REQUIRED_KEYS_BY_AREA = {"api": {"section"}}
ALLOWED_STATUS = {"deprecated"}
MAX_DESCRIPTION_LENGTH = 200

_FENCE = re.compile(r"^\s*(```|~~~)")
_INLINE_CODE = re.compile(r"`[^`\n]*`")
_LINK = re.compile(r"\[[^\]\n]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


@dataclass(frozen=True, order=True)
class Issue:
    path: str
    line: int
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


def validate_tree(root: Path) -> tuple[list[Issue], int]:
    """Validate every ``.md`` file under ``root``. Returns (issues, files checked)."""
    root = root.resolve()
    files = sorted(p for p in root.rglob("*.md") if p.is_file())
    issues: list[Issue] = []
    for path in files:
        issues.extend(validate_file(path, root))
    return sorted(issues), len(files)


def validate_file(path: Path, root: Path) -> list[Issue]:
    rel = path.relative_to(root).as_posix()
    text = path.read_text(encoding="utf-8")
    issues: list[Issue] = []

    def add(line: int, message: str) -> None:
        issues.append(Issue(rel, line, message))

    try:
        page = frontmatter.parse(text)
    except frontmatter.FrontMatterError as exc:
        add(1, str(exc))
        return issues

    if page.meta is None:
        add(1, "missing front matter")
    else:
        area = PurePosixPath(rel).parts[0] if "/" in rel else ""
        _check_meta(page.meta, area, add)

    _check_body(page.body, page.body_start_line, path, root, add)
    return issues


def _check_meta(meta: dict, area: str, add) -> None:
    for key in sorted(REQUIRED_KEYS | REQUIRED_KEYS_BY_AREA.get(area, set())):
        if key not in meta:
            add(1, f"missing required front matter key '{key}'")

    for key in sorted(set(meta) - ALLOWED_KEYS):
        add(1, f"unknown front matter key '{key}'")

    for key in ("title", "description", "section"):
        if key in meta and (not isinstance(meta[key], str) or not meta[key].strip()):
            add(1, f"'{key}' must be a non-empty string")

    description = meta.get("description")
    if isinstance(description, str):
        if "\n" in description.strip():
            add(1, "'description' must be a single line")
        if len(description) > MAX_DESCRIPTION_LENGTH:
            add(1, f"'description' is longer than {MAX_DESCRIPTION_LENGTH} characters")

    tags = meta.get("tags")
    if tags is not None and (
        not isinstance(tags, list) or not all(isinstance(t, str) and t for t in tags)
    ):
        add(1, "'tags' must be a list of non-empty strings")

    status = meta.get("status")
    if status is not None and status not in ALLOWED_STATUS:
        add(1, f"'status' must be one of {sorted(ALLOWED_STATUS)}")


def _check_body(body: str, start_line: int, path: Path, root: Path, add) -> None:
    in_fence = False
    for offset, line in enumerate(body.splitlines()):
        lineno = start_line + offset
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if "<!--" in line:
            add(lineno, "HTML comments are not allowed (they are invisible on sites but kept here)")
        for target in _LINK.findall(_INLINE_CODE.sub("", line)):
            problem = _check_link(target, path, root)
            if problem:
                add(lineno, problem)


def _check_link(target: str, path: Path, root: Path) -> str | None:
    if target.startswith("#") or _SCHEME.match(target) or target.startswith("//"):
        return None
    file_part = target.split("#", 1)[0].split("?", 1)[0]
    if not file_part:
        return None
    if file_part.startswith("/"):
        return f"absolute link '{target}' is not allowed; use a relative path"
    resolved = (path.parent / file_part).resolve()
    if not resolved.is_relative_to(root):
        return f"link '{target}' points outside docs/"
    if not resolved.exists():
        return f"broken link '{target}'"
    return None
