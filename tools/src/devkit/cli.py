"""Command line entry point: ``devkit <command>``.

``docs/api/`` is produced by the exporter that lives in the source docs repo.
This tool validates ``docs/`` and generates the outputs built from it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from devkit import __version__, llms, skill
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
    files = llms.generate(repo / "docs", cfg)
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


def _cmd_skill(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    try:
        cfg = skill.load_config(repo / args.config)
        llms_cfg = llms.load_config(repo / args.llms_config)
    except (skill.SkillError, llms.ConfigError) as exc:
        _err(str(exc))
        return 2
    files = skill.generate(repo / "docs", cfg, llms_cfg)
    target = skill.plugin_dir(repo, cfg)
    if args.check:
        stale = skill.stale(target, files)
        if stale:
            shown = ", ".join(stale[:5]) + (" ..." if len(stale) > 5 else "")
            _err(f"skill out of date: {shown}. Run 'uv run --project tools devkit skill'.")
            return 1
        print("skill up to date")
        return 0
    if args.zip:
        out = skill.build_zip(files, cfg, Path(args.zip))
        print(f"Wrote {out}")
        return 0
    skill.write(target, files)
    pages = sum(1 for p in files if "/references/" in p)
    print(f"Wrote skill '{cfg.name}' with {pages} reference page(s) to {target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="devkit", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="check front matter and links under docs/")
    validate.add_argument("--root", default="docs", help="content root (default: docs)")
    validate.set_defaults(func=_cmd_validate)

    llms_cmd = sub.add_parser("llms", help="generate public/llms.txt and llms-full files")
    llms_cmd.add_argument("--repo", default=".", help="devkit repo root (default: .)")
    llms_cmd.add_argument("--config", default="tools/llms.yml")
    llms_cmd.add_argument("--check", action="store_true", help="fail if committed files differ")
    llms_cmd.set_defaults(func=_cmd_llms)

    skill_cmd = sub.add_parser("skill", help="generate the Agent Skill / Claude Code plugin")
    skill_cmd.add_argument("--repo", default=".", help="devkit repo root (default: .)")
    skill_cmd.add_argument("--config", default="tools/skill.yml")
    skill_cmd.add_argument("--llms-config", default="tools/llms.yml")
    group = skill_cmd.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="fail if committed files differ")
    group.add_argument("--zip", help="write the skill folder as a zip to this path instead")
    skill_cmd.set_defaults(func=_cmd_skill)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
