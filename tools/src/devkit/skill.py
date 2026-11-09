"""Generate the Agent Skill and its Claude Code plugin from ``docs/``.

Layout written under ``plugins/<plugin>/``::

    .claude-plugin/plugin.json
    skills/<skill>/SKILL.md            index + how-to (from SKILL.template.md)
    skills/<skill>/references/...      every page of docs/, same paths
    skills/<skill>/scripts/search_docs.py

The skill folder follows the open Agent Skills format (https://agentskills.io), so the
same folder works in Claude Code, GitHub Copilot, Cursor, Codex and claude.ai. ``zip``
packages it for those other agents.
"""

from __future__ import annotations

import json
import re
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

import yaml

from devkit import llms

ASSETS = Path(__file__).resolve().parent / "skill_assets"
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NAME = 64
MAX_DESCRIPTION = 1024
RESERVED = ("claude", "anthropic")
ZIP_DATE = (2026, 1, 1, 0, 0, 0)  # fixed timestamp: identical input -> identical zip


class SkillError(ValueError):
    pass


@dataclass(frozen=True)
class SkillConfig:
    plugin_name: str
    plugin_description: str
    plugin_author: str
    name: str
    description: str
    license: str = ""


def load_config(path: Path) -> SkillConfig:
    if not path.is_file():
        raise SkillError(f"config file '{path}' not found")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    try:
        plugin, skill = data["plugin"], data["skill"]
        cfg = SkillConfig(
            plugin_name=str(plugin["name"]),
            plugin_description=" ".join(str(plugin["description"]).split()),
            plugin_author=str(plugin["author"]),
            name=str(skill["name"]),
            description=" ".join(str(skill["description"]).split()),
            license=" ".join(str(skill.get("license") or "").split()),
        )
    except (KeyError, TypeError) as exc:
        raise SkillError(f"'{path}' is missing a required key: {exc}") from exc
    _check_name(cfg.name, "skill.name")
    _check_name(cfg.plugin_name, "plugin.name")
    if not cfg.description or len(cfg.description) > MAX_DESCRIPTION:
        raise SkillError(f"skill.description must be 1-{MAX_DESCRIPTION} characters")
    return cfg


def _check_name(name: str, key: str) -> None:
    if len(name) > MAX_NAME or not NAME.match(name):
        raise SkillError(f"{key} '{name}' must be lowercase letters, digits and single hyphens")
    if any(word in name for word in RESERVED):
        raise SkillError(f"{key} '{name}' must not contain {' or '.join(RESERVED)}")


def plugin_dir(repo: Path, cfg: SkillConfig) -> Path:
    return repo / "plugins" / cfg.plugin_name


def skill_prefix(cfg: SkillConfig) -> str:
    return f"skills/{cfg.name}"


def generate(docs_dir: Path, cfg: SkillConfig, llms_cfg: llms.LlmsConfig) -> dict[str, bytes]:
    """Return ``{path relative to the plugin dir: bytes}``."""
    entries = llms.collect(docs_dir)
    prefix = skill_prefix(cfg)
    files: dict[str, bytes] = {}

    # No "version": installs track the latest commit, so each export reaches users
    # through `claude plugin update` without a manual version bump.
    manifest = {
        "name": cfg.plugin_name,
        "description": cfg.plugin_description,
        "author": {"name": cfg.plugin_author},
    }
    files[".claude-plugin/plugin.json"] = _json(manifest)

    files[f"{prefix}/SKILL.md"] = render_skill_md(entries, cfg, llms_cfg).encode("utf-8")
    files[f"{prefix}/scripts/search_docs.py"] = (ASSETS / "search_docs.py").read_bytes()
    for entry in entries:
        rel = entry.path.removeprefix("docs/")
        source = docs_dir / rel
        files[f"{prefix}/references/{rel}"] = source.read_bytes()
    return files


def render_skill_md(entries: list[llms.Entry], cfg: SkillConfig, llms_cfg) -> str:
    front = {"name": cfg.name, "description": cfg.description}
    if cfg.license:
        front["license"] = cfg.license
    header = yaml.safe_dump(front, sort_keys=False, allow_unicode=True, width=10_000)
    body = (ASSETS / "SKILL.template.md").read_text(encoding="utf-8")
    return f"---\n{header}---\n\n" + body.replace("{{ pages }}", _index(entries, llms_cfg))


def _index(entries: list[llms.Entry], llms_cfg) -> str:
    if not entries:
        return "No pages yet."
    blocks = []
    for group, items in llms.grouped(entries, llms_cfg):
        title = "Optional (release notes and other background)" if group == llms.OPTIONAL else group
        lines = [f"### {title}", ""]
        for e in items:
            desc = f"(deprecated) {e.description}" if e.deprecated else e.description
            ref = "references/" + e.path.removeprefix("docs/")
            lines.append(f"- [{e.title}]({ref}): {desc}" if desc else f"- [{e.title}]({ref})")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _json(data: dict) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def write(target: Path, files: dict[str, bytes]) -> None:
    """Replace ``target`` (the plugin dir) with exactly ``files``."""
    if target.exists():
        shutil.rmtree(target)
    for rel, data in sorted(files.items()):
        path = target / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def stale(target: Path, files: dict[str, bytes]) -> list[str]:
    current = (
        {p.relative_to(target).as_posix(): p for p in target.rglob("*") if p.is_file()}
        if target.is_dir()
        else {}
    )
    changed = [
        rel
        for rel, data in files.items()
        if rel not in current or current[rel].read_bytes() != data
    ]
    extra = [rel for rel in current if rel not in files]
    return sorted(changed + extra)


def build_zip(files: dict[str, bytes], cfg: SkillConfig, out: Path) -> Path:
    """Zip the skill folder (``<skill>/SKILL.md`` at the zip root) deterministically."""
    prefix = skill_prefix(cfg) + "/"
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in sorted(files):
            if not rel.startswith(prefix):
                continue
            info = zipfile.ZipInfo(f"{cfg.name}/{rel.removeprefix(prefix)}", ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, files[rel])
    return out
