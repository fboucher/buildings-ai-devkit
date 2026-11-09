import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
import yaml

from devkit import skill
from devkit.cli import main

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = "plugins/buildings-ai-devkit/skills/building-data-platform-api"


def page(title: str, description: str, section: str | None, body: str, extra: str = "") -> str:
    lines = ["---", f"title: {title}", f"description: {description}"]
    if section:
        lines.append(f"section: {section}")
    if extra:
        lines.append(extra)
    return "\n".join([*lines, "---", "", f"# {title}", "", body, ""])


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "tools").mkdir(parents=True)
    for name in ("llms.yml", "skill.yml"):
        shutil.copy(REPO_ROOT / "tools" / name, root / "tools" / name)
    files = {
        "api/rest-api/authentication.md": page(
            "Authentication", "Get a token.", "REST API / Overview", "Use OAuth client credentials."
        ),
        "api/rest-api/historicalvalues.md": page(
            "Historical Values",
            "Read historical values.",
            "REST API / Endpoints",
            "GET historical values with pagination using pageSize and pageToken.",
        ),
        "api/bdp/map-file.md": page(
            "Map File", "Old map file.", "Concepts / Integration", "Legacy.", "status: deprecated"
        ),
        "api/release-notes/v1.md": page("1.0", "First release.", "Release Notes", "Notes."),
        "guides/start.md": page("Start", "A guide.", None, "Steps."),
    }
    for rel, text in files.items():
        path = root / "docs" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    manifest = {
        "pages": [
            "rest-api/authentication.md",
            "rest-api/historicalvalues.md",
            "bdp/map-file.md",
            "release-notes/v1.md",
        ]
    }
    (root / "docs" / "api" / "_source.json").write_text(json.dumps(manifest))
    return root


def run(repo: Path, *args: str) -> int:
    return main(["skill", "--repo", str(repo), *args])


def test_generates_plugin_and_skill(repo: Path) -> None:
    assert run(repo) == 0
    plugin = repo / "plugins" / "buildings-ai-devkit"
    manifest = json.loads((plugin / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "buildings-ai-devkit"

    skill_dir = repo / SKILL_DIR
    files = sorted(p.relative_to(skill_dir).as_posix() for p in skill_dir.rglob("*") if p.is_file())
    assert files == [
        "SKILL.md",
        "references/api/bdp/map-file.md",
        "references/api/release-notes/v1.md",
        "references/api/rest-api/authentication.md",
        "references/api/rest-api/historicalvalues.md",
        "references/guides/start.md",
        "scripts/search_docs.py",
    ]
    assert (skill_dir / "references/api/rest-api/authentication.md").read_bytes() == (
        repo / "docs/api/rest-api/authentication.md"
    ).read_bytes()


def test_skill_md(repo: Path) -> None:
    assert run(repo) == 0
    text = (repo / SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    front = yaml.safe_load(text.split("---\n")[1])
    assert front["name"] == "building-data-platform-api"
    assert 0 < len(front["description"]) <= 1024
    assert set(front) <= {"name", "description", "license", "compatibility", "metadata"}
    assert "{{ pages }}" not in text
    assert len(text.splitlines()) < 500

    rest = "- [Authentication](references/api/rest-api/authentication.md): Get a token."
    assert rest in text
    assert "- [Map File](references/api/bdp/map-file.md): (deprecated) Old map file." in text
    headings = [line for line in text.splitlines() if line.startswith("### ")]
    assert headings == [
        "### REST API",
        "### Concepts",
        "### Guides",
        "### Optional (release notes and other background)",
    ]
    # Every index link points at a bundled file.
    for target in __import__("re").findall(r"\]\((references/[^)]+)\)", text):
        assert (repo / SKILL_DIR / target).is_file()


def test_check_and_stale_files(repo: Path) -> None:
    assert run(repo, "--check") == 1
    assert run(repo) == 0
    assert run(repo, "--check") == 0
    (repo / SKILL_DIR / "references" / "stale.md").write_text("old")
    assert run(repo, "--check") == 1
    assert run(repo) == 0
    assert not (repo / SKILL_DIR / "references" / "stale.md").exists()


def test_zip_is_deterministic_and_skill_rooted(repo: Path, tmp_path: Path) -> None:
    a, b = tmp_path / "a.zip", tmp_path / "b.zip"
    assert run(repo, "--zip", str(a)) == 0
    assert run(repo, "--zip", str(b)) == 0
    assert a.read_bytes() == b.read_bytes()
    names = zipfile.ZipFile(a).namelist()
    assert "building-data-platform-api/SKILL.md" in names
    assert all(n.startswith("building-data-platform-api/") for n in names)
    assert not any("plugin.json" in n for n in names)


def test_search_script(repo: Path) -> None:
    assert run(repo) == 0
    script = repo / SKILL_DIR / "scripts" / "search_docs.py"
    proc = subprocess.run(
        [sys.executable, str(script), "historical", "pagination"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    first = proc.stdout.splitlines()[0]
    assert first == "references/api/rest-api/historicalvalues.md  (Historical Values)"
    assert "pageSize" in proc.stdout
    none = subprocess.run(
        [sys.executable, str(script), "zzzz"], capture_output=True, text=True, check=False
    )
    assert none.returncode == 1


@pytest.mark.parametrize(
    "name", ["Bad_Name", "claude-docs", "my-anthropic-skill", "a--b", "-x", "x" * 65]
)
def test_rejects_invalid_names(repo: Path, name: str) -> None:
    cfg = repo / "tools" / "skill.yml"
    data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    data["skill"]["name"] = name
    cfg.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(skill.SkillError):
        skill.load_config(cfg)


def test_repo_skill_is_up_to_date() -> None:
    assert main(["skill", "--repo", str(REPO_ROOT), "--check"]) == 0
