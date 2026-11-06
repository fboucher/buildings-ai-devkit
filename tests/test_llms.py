import json
import shutil
from pathlib import Path

import pytest

from devkit import llms
from devkit.cli import main

REPO_ROOT = Path(__file__).resolve().parents[1]
SITE = "https://schneiderelectricbuildings.github.io/buildings-ai-devkit"


def page(title: str, description: str, section: str | None = None, extra: str = "") -> str:
    lines = ["---", f"title: {title}", f"description: {description}"]
    if section:
        lines.append(f"section: {section}")
    return "\n".join([*lines, *([extra] if extra else []), "---", "", f"# {title}", ""])


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    shutil.copy(REPO_ROOT / "llms.yml", root / "llms.yml")
    files = {
        "api/intro.md": page("Overview", "What it is.", "Concepts"),
        "api/old.md": page("Old Thing", "Old feature.", "Concepts", "status: deprecated"),
        "api/api/sites.md": page("Sites", "List sites.", "API / Endpoints"),
        "api/notes/v1.md": page("1.0", "First release.", "Release Notes"),
        "guides/start.md": page("Start", "A guide."),
    }
    for rel, text in files.items():
        path = root / "content" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    # Exporter manifest: nav order differs from alphabetical order.
    manifest = {"pages": ["intro.md", "old.md", "api/sites.md", "notes/v1.md"]}
    (root / "content" / "api" / "_source.json").write_text(json.dumps(manifest))
    return root


def test_index(repo: Path) -> None:
    assert main(["llms", "--repo", str(repo)]) == 0
    index = (repo / "public" / "llms.txt").read_text(encoding="utf-8")
    assert index.startswith("# Buildings AI Developer Kit\n\n> Agent-ready documentation")
    assert f"- [Overview]({SITE}/content/api/intro.md): What it is." in index
    assert f"- [Old Thing]({SITE}/content/api/old.md): (deprecated) Old feature." in index
    sections = [line for line in index.splitlines() if line.startswith("## ")]
    assert sections == ["## Concepts", "## API", "## Guides", "## Full text", "## Optional"]
    assert index.index("content/api/intro.md") < index.index("content/api/old.md")
    assert f"- [API]({SITE}/llms-full/api.txt): full text of this section" in index
    assert index.rstrip().endswith(f"- [1.0]({SITE}/content/api/notes/v1.md): First release.")


def test_full_and_per_section_files(repo: Path) -> None:
    assert main(["llms", "--repo", str(repo)]) == 0
    full = (repo / "public" / "llms-full.txt").read_text(encoding="utf-8")
    assert "---\npath: content/api/old.md\ntitle: Old Thing\nsection: Concepts\n" in full
    assert "status: deprecated\n---\n\n# Old Thing" in full
    per_section = sorted(p.name for p in (repo / "public" / "llms-full").iterdir())
    assert per_section == ["api.txt", "concepts.txt", "guides.txt", "optional.txt"]
    api_full = (repo / "public" / "llms-full" / "api.txt").read_text(encoding="utf-8")
    assert "path: content/api/api/sites.md" in api_full
    assert "path: content/api/intro.md" not in api_full


def test_check_detects_stale_and_extra_files(repo: Path) -> None:
    assert main(["llms", "--repo", str(repo), "--check"]) == 1
    assert main(["llms", "--repo", str(repo)]) == 0
    assert main(["llms", "--repo", str(repo), "--check"]) == 0
    (repo / "public" / "llms-full" / "gone.txt").write_text("old")
    assert main(["llms", "--repo", str(repo), "--check"]) == 1
    assert main(["llms", "--repo", str(repo)]) == 0
    assert not (repo / "public" / "llms-full" / "gone.txt").exists()


def test_missing_config(tmp_path: Path) -> None:
    assert main(["llms", "--repo", str(tmp_path)]) == 2


def test_repo_llms_files_are_up_to_date() -> None:
    cfg = llms.load_config(REPO_ROOT / "llms.yml")
    files = llms.generate(REPO_ROOT / "content", cfg)
    assert llms.stale(REPO_ROOT / "public", files) == []
