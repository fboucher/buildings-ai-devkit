"""Block list scanning (ADR-0004).

The block list lives in the source repo at ``.devkit/blocklist.txt``. Its contents are
sensitive, so findings are reported by **rule number and location only**, never by the
matched text: export reports become public PR descriptions.

Format: one rule per line. Blank lines and lines starting with ``#`` are ignored.
Lines starting with ``re:`` are case-insensitive regular expressions; all other lines are
case-insensitive literal substrings.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

BLOCKLIST_RELATIVE_PATH = Path(".devkit") / "blocklist.txt"


class BlocklistError(ValueError):
    pass


@dataclass(frozen=True)
class Rule:
    number: int
    """1-based line number in the block list file."""
    pattern: re.Pattern[str]


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    line: int
    rule: int

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: matches block list rule on line {self.rule}"


def load_blocklist(path: Path) -> list[Rule]:
    if not path.is_file():
        raise BlocklistError(
            f"block list not found at '{path}'. The exporter refuses to run without it "
            "(ADR-0004). Create it in the source repo, or pass --blocklist."
        )
    rules: list[Rule] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("re:"):
            try:
                pattern = re.compile(line[3:].strip(), re.IGNORECASE)
            except re.error as exc:
                raise BlocklistError(f"invalid regex on block list line {number}: {exc}") from exc
        else:
            pattern = re.compile(re.escape(line), re.IGNORECASE)
        rules.append(Rule(number=number, pattern=pattern))
    return rules


def scan(files: dict[str, str], rules: list[Rule]) -> list[Finding]:
    findings: list[Finding] = []
    for path, text in files.items():
        for lineno, line in enumerate(text.splitlines(), start=1):
            for rule in rules:
                if rule.pattern.search(line):
                    findings.append(Finding(path=path, line=lineno, rule=rule.number))
    return sorted(findings)


@dataclass(frozen=True)
class GitleaksResult:
    ran: bool
    clean: bool
    detail: str = ""


def run_gitleaks(directory: Path) -> GitleaksResult:
    """Run gitleaks on ``directory`` if it is installed. CI always runs it as well."""
    exe = shutil.which("gitleaks")
    if exe is None:
        return GitleaksResult(ran=False, clean=True, detail="gitleaks not installed; CI will scan")
    proc = subprocess.run(
        [exe, "dir", str(directory), "--no-banner", "--redact", "--exit-code", "1"],
        capture_output=True,
        text=True,
        check=False,
    )
    return GitleaksResult(ran=True, clean=proc.returncode == 0, detail=proc.stdout + proc.stderr)
