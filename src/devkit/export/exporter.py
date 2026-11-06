"""Build an export in memory, then stage, check and write it."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from devkit import __version__, frontmatter
from devkit.export.config import ExportConfig
from devkit.export.nav import find_mkdocs_config, load_site, matches_include
from devkit.export.transform import PageNotes, SourcePage, source_tags, transform_page

MANIFEST = "_source.json"


@dataclass(frozen=True)
class Excluded:
    src: str
    reason: str


@dataclass
class ExportResult:
    files: dict[str, bytes] = field(default_factory=dict)
    """Output files, keyed by POSIX path relative to ``content/api/``."""
    pages: list[str] = field(default_factory=list)
    excluded: list[Excluded] = field(default_factory=list)
    notes: dict[str, PageNotes] = field(default_factory=dict)
    deprecated: list[str] = field(default_factory=list)
    long_pages: list[tuple[str, int]] = field(default_factory=list)
    unused_allow: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    source_commit: str | None = None
    source_dirty: bool = False

    def text_files(self) -> dict[str, str]:
        return {p: b.decode("utf-8") for p, b in self.files.items() if p.endswith((".md", ".json"))}


def build_export(source: Path, cfg: ExportConfig) -> ExportResult:
    site = load_site(find_mkdocs_config(source))
    result = ExportResult()
    result.source_commit, result.source_dirty = _source_state(site.config_path.parent)

    existing = frozenset(
        p.relative_to(site.docs_dir).as_posix() for p in site.docs_dir.rglob("*") if p.is_file()
    )
    nav_srcs = {p.src for p in site.pages}

    selected: list[SourcePage] = []
    for nav_page in site.pages:
        if not matches_include(nav_page, cfg.include):
            result.excluded.append(Excluded(nav_page.src, "not matched by include filter"))
            continue
        if nav_page.src not in existing:
            result.errors.append(f"nav entry '{nav_page.src}' does not exist in docs_dir")
            continue
        text = (site.docs_dir / nav_page.src).read_text(encoding="utf-8").replace("\r\n", "\n")
        try:
            parsed = frontmatter.parse(text)
        except frontmatter.FrontMatterError as exc:
            result.errors.append(f"{nav_page.src}: {exc}")
            continue
        meta = parsed.meta or {}
        if "draft" in source_tags(meta):
            result.excluded.append(Excluded(nav_page.src, "tagged draft"))
            continue
        selected.append(
            SourcePage(
                src=nav_page.src,
                label=nav_page.label,
                section=nav_page.section,
                meta=meta,
                body=parsed.body,
            )
        )

    for orphan in sorted(p for p in existing if p.endswith(".md") and p not in nav_srcs):
        result.excluded.append(Excluded(orphan, "not in nav"))

    exported = frozenset(p.src for p in selected)
    used_images: set[str] = set()
    for page in selected:
        output, notes = transform_page(page, exported, cfg.images_allow, existing)
        result.files[page.src] = output.encode("utf-8")
        result.pages.append(page.src)
        result.notes[page.src] = notes
        used_images.update(notes.images_kept)
        if "deprecated" in source_tags(page.meta):
            result.deprecated.append(page.src)
        words = len(page.body.split())
        if words > cfg.long_page_words:
            result.long_pages.append((page.src, words))

    for image in sorted(used_images):
        if image not in existing:
            result.errors.append(f"allowlisted image '{image}' does not exist in docs_dir")
            continue
        result.files[image] = (site.docs_dir / image).read_bytes()
    result.unused_allow = sorted(cfg.images_allow - used_images)

    manifest = {
        "generator": "devkit export",
        "exporter_version": __version__,
        "source_commit": result.source_commit,
        "pages": result.pages,
    }
    result.files[MANIFEST] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    return result


def _source_state(project_dir: Path) -> tuple[str | None, bool]:
    """Last commit touching the docs project, and whether it has uncommitted changes."""

    def git(*args: str) -> str | None:
        try:
            proc = subprocess.run(
                ["git", "-C", str(project_dir), *args],
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError):
            return None
        return proc.stdout.strip()

    commit = git("log", "-1", "--format=%H", "--", ".") or None
    status = git("status", "--porcelain", "--", ".")
    return commit, bool(status)


# --- staging and writing --------------------------------------------------------------


@dataclass(frozen=True)
class Diff:
    added: list[str]
    changed: list[str]
    removed: list[str]

    @property
    def empty(self) -> bool:
        return not (self.added or self.changed or self.removed)


def diff_against(api_dir: Path, files: dict[str, bytes]) -> Diff:
    current = (
        {p.relative_to(api_dir).as_posix(): p for p in api_dir.rglob("*") if p.is_file()}
        if api_dir.is_dir()
        else {}
    )
    added = sorted(set(files) - set(current))
    removed = sorted(set(current) - set(files))
    changed = sorted(p for p in set(files) & set(current) if current[p].read_bytes() != files[p])
    return Diff(added=added, changed=changed, removed=removed)


def stage(repo_content: Path, files: dict[str, bytes]) -> Path:
    """Copy ``content/`` to a temp dir, replacing ``api/`` with ``files``. Caller deletes it."""
    root = Path(tempfile.mkdtemp(prefix="devkit-export-"))
    content = root / "content"
    if repo_content.is_dir():
        shutil.copytree(repo_content, content, ignore=shutil.ignore_patterns("api"))
    else:
        content.mkdir()
    write_api(content / "api", files)
    return root


def write_api(api_dir: Path, files: dict[str, bytes]) -> None:
    if api_dir.exists():
        shutil.rmtree(api_dir)
    for rel, data in sorted(files.items()):
        path = api_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
