"""The optional ``--pr`` flow: branch, commit, push, open a PR (ADR-0005)."""

from __future__ import annotations

import datetime as dt
import shutil
import subprocess
from pathlib import Path

GENERATED_PATHS = ("content/api", "public")


class PrError(RuntimeError):
    pass


def _run(repo: Path, *args: str) -> str:
    proc = subprocess.run(args, cwd=repo, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise PrError(f"'{' '.join(args)}' failed:\n{proc.stdout}{proc.stderr}".rstrip())
    return proc.stdout.strip()


def preflight(repo: Path) -> None:
    if shutil.which("gh") is None:
        raise PrError("--pr needs the GitHub CLI ('gh') on PATH")
    if _run(repo, "git", "status", "--porcelain"):
        raise PrError("--pr needs a clean working tree in this repo; commit or stash first")


def has_changes(repo: Path) -> bool:
    return bool(_run(repo, "git", "status", "--porcelain", "--", *GENERATED_PATHS))


def branch_name(source_commit: str | None, today: dt.date | None = None) -> str:
    today = today or dt.date.today()
    return f"export/{today.isoformat()}-{(source_commit or 'unknown')[:7]}"


def open_pr(repo: Path, source_commit: str | None, report: Path, base: str) -> str:
    branch = branch_name(source_commit)
    short = (source_commit or "unknown")[:7]
    title = f"Docs export {dt.date.today().isoformat()} (source {short})"
    _run(repo, "git", "switch", "-c", branch)
    _run(repo, "git", "add", "--all", "--", *GENERATED_PATHS)
    _run(repo, "git", "commit", "-m", title)
    _run(repo, "git", "push", "-u", "origin", branch)
    return _run(
        repo, "gh", "pr", "create", "--base", base, "--title", title, "--body-file", str(report)
    )
