"""Command line entry point: ``devkit <command>``."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from devkit import __version__, llms
from devkit.export import gitpr
from devkit.export.config import ConfigError, load_config
from devkit.export.exporter import build_export, diff_against, stage, write_api
from devkit.export.nav import NavError
from devkit.export.report import render
from devkit.export.sanitize import (
    BLOCKLIST_RELATIVE_PATH,
    BlocklistError,
    load_blocklist,
    run_gitleaks,
    scan,
)
from devkit.validate import validate_tree

REPORT_PATH = Path(".export-tmp") / "export-report.md"


def _err(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)


def _cmd_validate(args: argparse.Namespace) -> int:
    root = Path(args.root)
    if not root.is_dir():
        _err(f"content root '{root}' does not exist")
        return 2
    issues, count = validate_tree(root)
    for issue in issues:
        print(issue)
    if issues:
        print(f"\n{len(issues)} issue(s) in {count} file(s)", file=sys.stderr)
        return 1
    print(f"{count} file(s) OK")
    return 0


def _cmd_llms(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    try:
        cfg = load_config(repo / args.config)
    except ConfigError as exc:
        _err(str(exc))
        return 2
    files = llms.generate(repo / "content", cfg.llms)
    public = repo / "public"
    if args.check:
        stale = llms.stale(public, files)
        if stale:
            _err(f"out of date: {', '.join(stale)}. Run 'uv run devkit llms' and commit.")
            return 1
        print("llms files up to date")
        return 0
    llms.write(public, files)
    tokens = llms.estimate_tokens(files["llms-full.txt"])
    print(f"Wrote public/llms.txt and public/llms-full.txt (~{tokens:,} tokens)")
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    source = Path(args.source).resolve()
    if args.pr and args.out:
        _err("--pr and --out cannot be combined")
        return 2
    try:
        cfg = load_config(repo / args.config)
        blocklist = Path(args.blocklist) if args.blocklist else source / BLOCKLIST_RELATIVE_PATH
        rules = load_blocklist(blocklist)
        if args.pr:
            gitpr.preflight(repo)
        result = build_export(source, cfg)
    except (ConfigError, BlocklistError, NavError, gitpr.PrError) as exc:
        _err(str(exc))
        return 2
    if args.pr and result.source_dirty:
        _err("the source docs have uncommitted changes; commit them before using --pr")
        return 2

    out_root = Path(args.out).resolve() if args.out else repo
    staged = stage(repo / "content", result.files)
    try:
        llms_files = llms.generate(staged / "content", cfg.llms)
        texts = {f"content/api/{p}": t for p, t in result.text_files().items()}
        texts |= {f"public/{name}": t for name, t in llms_files.items()}
        findings = scan(texts, rules)
        gitleaks = run_gitleaks(staged)
        validation = [str(i) for i in validate_tree(staged / "content")[0]]
    finally:
        shutil.rmtree(staged, ignore_errors=True)

    diff = diff_against(out_root / "content" / "api", result.files)
    tokens = llms.estimate_tokens(llms_files["llms-full.txt"])
    report = render(result, diff, len(rules), findings, gitleaks, validation, tokens)
    report_path = out_root / REPORT_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8", newline="\n")

    problems = [*result.errors, *(str(f) for f in findings), *validation]
    if gitleaks.ran and not gitleaks.clean:
        problems.append("gitleaks found possible secrets (run gitleaks locally for details)")
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        _err(f"export blocked; nothing was written. Report: {report_path}")
        return 1

    write_api(out_root / "content" / "api", result.files)
    llms.write(out_root / "public", llms_files)
    print(
        f"Exported {len(result.pages)} page(s): {len(diff.added)} added, "
        f"{len(diff.changed)} changed, {len(diff.removed)} removed, "
        f"{len(result.excluded)} excluded. llms-full.txt ~{tokens:,} tokens."
    )
    print(f"Report: {report_path}")

    if args.pr:
        try:
            if not gitpr.has_changes(repo):
                print("No changes; no PR opened.")
                return 0
            print(gitpr.open_pr(repo, result.source_commit, report_path, cfg.pr_base))
        except gitpr.PrError as exc:
            _err(str(exc))
            return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="devkit", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="check front matter and links under content/")
    validate.add_argument("--root", default="content", help="content root (default: content)")
    validate.set_defaults(func=_cmd_validate)

    llms_cmd = sub.add_parser("llms", help="generate public/llms.txt and public/llms-full.txt")
    llms_cmd.add_argument("--repo", default=".", help="devkit repo root (default: .)")
    llms_cmd.add_argument("--config", default="export.yml")
    llms_cmd.add_argument("--check", action="store_true", help="fail if committed files differ")
    llms_cmd.set_defaults(func=_cmd_llms)

    export = sub.add_parser("export", help="export source MkDocs docs into content/api/")
    export.add_argument("--source", required=True, help="root of the source docs repo")
    export.add_argument("--repo", default=".", help="devkit repo root (default: .)")
    export.add_argument("--config", default="export.yml")
    export.add_argument(
        "--blocklist", help=f"block list path (default: <source>/{BLOCKLIST_RELATIVE_PATH})"
    )
    export.add_argument("--out", help="write to this directory instead of the repo (dry run)")
    export.add_argument("--pr", action="store_true", help="commit to a branch and open a PR")
    export.set_defaults(func=_cmd_export)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
