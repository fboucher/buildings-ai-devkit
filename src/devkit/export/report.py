"""Render the export report (becomes the PR description, so it is public).

Never include matched block list text, internal hostnames or file contents here: only
source paths, counts and rule numbers.
"""

from __future__ import annotations

from devkit import __version__
from devkit.export.exporter import Diff, ExportResult
from devkit.export.sanitize import Finding, GitleaksResult


def render(
    result: ExportResult,
    diff: Diff,
    rules: int,
    findings: list[Finding],
    gitleaks: GitleaksResult,
    validation: list[str],
    tokens: int,
) -> str:
    commit = (result.source_commit or "unknown")[:12]
    dirty = " (uncommitted changes in source)" if result.source_dirty else ""
    lines = [
        "## Docs export report",
        "",
        f"Source commit: `{commit}`{dirty} · exporter {__version__}",
        "",
        "| Exported pages | Added | Changed | Removed | Excluded | `llms-full.txt` |",
        "|---|---|---|---|---|---|",
        f"| {len(result.pages)} | {len(diff.added)} | {len(diff.changed)} | {len(diff.removed)} "
        f"| {len(result.excluded)} | ~{tokens:,} tokens |",
        "",
    ]

    leaked = gitleaks.ran and not gitleaks.clean
    failed = findings or validation or result.errors or leaked
    status = "FAILED" if failed else "passed"
    if not gitleaks.ran:
        scan = "not run locally (CI scans every PR)"
    else:
        scan = "clean" if gitleaks.clean else "**leaks found**"
    lines += [
        f"**Checks: {status}.** Block list: {rules} rule(s), {len(findings)} finding(s). "
        f"gitleaks: {scan}. Validation: {len(validation)} issue(s).",
        "",
    ]

    def section(title: str, items: list[str]) -> None:
        if items:
            lines.extend([f"### {title}", ""])
            lines.extend(f"- {item}" for item in items)
            lines.append("")

    section("Errors", result.errors)
    section("Block list findings", [str(f) for f in findings])
    section("Validation issues", validation)
    section("Added", [f"`{p}`" for p in diff.added])
    section("Changed", [f"`{p}`" for p in diff.changed])
    section("Removed", [f"`{p}`" for p in diff.removed])
    section("Excluded", [f"`{e.src}`: {e.reason}" for e in result.excluded])
    section("Deprecated (kept and labelled)", [f"`{p}`" for p in result.deprecated])

    notes = result.notes
    section(
        "Needs a `description:` upstream (first paragraph used)",
        [f"`{p}`" for p, n in notes.items() if n.description_fallback],
    )
    section(
        "Description truncated to 200 characters",
        [f"`{p}`" for p, n in notes.items() if n.description_truncated],
    )
    section(
        "Links removed (target not exported)",
        [f"`{p}` → `{t}`" for p, n in notes.items() for t in n.links_removed],
    )
    section(
        "Images replaced with alt text",
        [f"`{p}` → `{i}`" for p, n in notes.items() for i in n.images_dropped],
    )
    section(
        "Images copied (allowlisted)",
        sorted({i for n in notes.values() for i in n.images_kept}),
    )
    section("Allowlisted images not used", result.unused_allow)
    section(
        "HTML comments removed",
        [f"`{p}`: {n.comments_removed}" for p, n in notes.items() if n.comments_removed],
    )
    section(
        "Long pages (consider splitting upstream)",
        [f"`{p}`: {w:,} words" for p, w in result.long_pages],
    )
    return "\n".join(lines).rstrip() + "\n"
