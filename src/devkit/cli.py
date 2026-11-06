"""Command line entry point: ``devkit <command>``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from devkit import __version__
from devkit.validate import validate_tree


def _cmd_validate(args: argparse.Namespace) -> int:
    root = Path(args.root)
    if not root.is_dir():
        print(f"error: content root '{root}' does not exist", file=sys.stderr)
        return 2
    issues, count = validate_tree(root)
    for issue in issues:
        print(issue)
    if issues:
        print(f"\n{len(issues)} issue(s) in {count} file(s)", file=sys.stderr)
        return 1
    print(f"{count} file(s) OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="devkit", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="check front matter and links under content/")
    validate.add_argument("--root", default="content", help="content root (default: content)")
    validate.set_defaults(func=_cmd_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
