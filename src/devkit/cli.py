"""Command line entry point: ``devkit <command>``.

``content/api/`` is produced by the exporter that lives in the source docs repo
(ADR-0003). This tool validates ``content/`` and generates the outputs built from it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from devkit import __version__, llms
from devkit.validate import validate_tree


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
        cfg = llms.load_config(repo / args.config)
    except llms.ConfigError as exc:
        _err(str(exc))
        return 2
    files = llms.generate(repo / "content", cfg)
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
    print(f"Wrote {len(files)} llms file(s) to public/ (llms-full.txt ~{tokens:,} tokens)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="devkit", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="check front matter and links under content/")
    validate.add_argument("--root", default="content", help="content root (default: content)")
    validate.set_defaults(func=_cmd_validate)

    llms_cmd = sub.add_parser("llms", help="generate public/llms.txt and llms-full files")
    llms_cmd.add_argument("--repo", default=".", help="devkit repo root (default: .)")
    llms_cmd.add_argument("--config", default="llms.yml")
    llms_cmd.add_argument("--check", action="store_true", help="fail if committed files differ")
    llms_cmd.set_defaults(func=_cmd_llms)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
