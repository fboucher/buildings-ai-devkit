import datetime as dt
import json
import shutil
from pathlib import Path

import pytest

from devkit import llms
from devkit.cli import main
from devkit.export import gitpr
from devkit.export.config import load_config
from devkit.export.exporter import build_export
from devkit.export.nav import find_mkdocs_config, load_site
from devkit.export.transform import DEPRECATED_NOTICE

REPO_ROOT = Path(__file__).resolve().parents[1]

MKDOCS = """\
site_name: Example
site_url: !ENV [SITE_URL, "https://docs.example.com"]
nav:
  - Concepts:
    - Overview: intro.md
    - Old Thing: old.md
  - API:
    - Sites: api/sites.md
    - Draft Page: api/draft.md
  - Release Notes:
    - '1.0': notes/v1.md
  - External: https://example.com/elsewhere
"""

PAGES = {
    "intro.md": (
        "# Intro\n\n"
        "![Architecture](img/arch.png)\n\n"
        "The **Example** platform models [sites](api/sites.md) and more.\n"
        "Second line of the same paragraph.\n\n"
        "<!-- internal TODO -->\n"
        "See the [draft](api/draft.md), the [orphan](orphan.md) and [web](https://example.com).\n"
        "![Screenshot](img/screen.png)\n"
    ),
    "old.md": "---\ntags:\n  - deprecated\n---\n# Old\n\nOld feature.\n",
    "api/sites.md": (
        "---\nhide_title: true\ndescription: List and get sites.\ntags:\n  - updated\n---\n"
        "# Sites\n\nBack to [intro](../intro.md#top).\n\n"
        "```md\n[not a link](missing.md) <!-- kept in code -->\n```\n"
    ),
    "api/draft.md": "---\ntags:\n  - draft\n---\n# Draft\n",
    "notes/v1.md": "# 1.0\n\nFirst release.\n",
    "orphan.md": "# Orphan\n",
}


@pytest.fixture
def source(tmp_path: Path) -> Path:
    root = tmp_path / "source"
    project = root / "site"
    (project / "docs" / "img").mkdir(parents=True)
    (project / "mkdocs.yml").write_text(MKDOCS, encoding="utf-8")
    for rel, text in PAGES.items():
        path = project / "docs" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    (project / "docs" / "img" / "arch.png").write_bytes(b"\x89PNG arch")
    (project / "docs" / "img" / "screen.png").write_bytes(b"\x89PNG screen")
    (root / ".devkit").mkdir()
    (root / ".devkit" / "blocklist.txt").write_text(
        "# comment\nsecret-host.example\nre:\\bcodename-\\d+\\b\n", encoding="utf-8"
    )
    return root


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "content" / "guides").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "export.yml", root / "export.yml")
    (root / "content" / "guides" / "start.md").write_text(
        "---\ntitle: Start\ndescription: A guide.\n---\n# Start\n", encoding="utf-8"
    )
    return root


def config(repo: Path, allow: list[str] | None = None, include: list[str] | None = None):
    text = (repo / "export.yml").read_text(encoding="utf-8")
    if allow is not None:
        text = text.replace("allow: []", f"allow: {json.dumps(allow)}")
    if include is not None:
        text = text.replace('include:\n  - "**"', f"include: {json.dumps(include)}")
    (repo / "export.yml").write_text(text, encoding="utf-8")
    return load_config(repo / "export.yml")


def text(result, path: str) -> str:
    return result.files[path].decode("utf-8")


def test_nav_order_sections_and_external_links(source: Path) -> None:
    site = load_site(find_mkdocs_config(source))
    assert [(p.src, p.section) for p in site.pages] == [
        ("intro.md", "Concepts"),
        ("old.md", "Concepts"),
        ("api/sites.md", "API"),
        ("api/draft.md", "API"),
        ("notes/v1.md", "Release Notes"),
    ]


def test_selection_excludes_drafts_and_orphans(source: Path, repo: Path) -> None:
    result = build_export(source, config(repo))
    assert result.pages == ["intro.md", "old.md", "api/sites.md", "notes/v1.md"]
    assert {(e.src, e.reason) for e in result.excluded} == {
        ("api/draft.md", "tagged draft"),
        ("orphan.md", "not in nav"),
    }
    assert result.errors == []


def test_page_transform(source: Path, repo: Path) -> None:
    result = build_export(source, config(repo))
    intro = text(result, "intro.md")
    assert intro.startswith(
        "---\ntitle: Overview\n"
        "description: The Example platform models sites and more. "
        "Second line of the same paragraph.\n"
        "section: Concepts\n---\n\n# Intro\n"
    )
    assert "*[Image: Architecture]*" in intro
    assert "*[Image: Screenshot]*" in intro
    assert "[sites](api/sites.md)" in intro
    assert "the draft, the orphan and [web](https://example.com)" in intro
    assert "<!--" not in intro
    notes = result.notes["intro.md"]
    assert notes.description_fallback
    assert notes.comments_removed == 1
    assert notes.links_removed == ["api/draft.md", "orphan.md"]

    sites = text(result, "api/sites.md")
    assert "hide_title" not in sites
    assert "description: List and get sites.\n" in sites
    assert "tags:\n- updated\n" in sites
    assert "[intro](../intro.md#top)" in sites
    assert "[not a link](missing.md) <!-- kept in code -->" in sites
    assert not result.notes["api/sites.md"].description_fallback


def test_deprecated_pages_are_labelled(source: Path, repo: Path) -> None:
    result = build_export(source, config(repo))
    old = text(result, "old.md")
    assert "status: deprecated\n" in old
    assert f"---\n\n{DEPRECATED_NOTICE}\n\n# Old" in old
    assert result.deprecated == ["old.md"]


def test_allowlisted_image_is_copied(source: Path, repo: Path) -> None:
    result = build_export(source, config(repo, allow=["img/arch.png", "img/unused.png"]))
    assert "![Architecture](img/arch.png)" in text(result, "intro.md")
    assert result.files["img/arch.png"] == b"\x89PNG arch"
    assert "img/screen.png" not in result.files
    assert result.unused_allow == ["img/unused.png"]


def test_include_filter(source: Path, repo: Path) -> None:
    result = build_export(source, config(repo, include=["API/**"]))
    assert result.pages == ["api/sites.md"]
    # Links to pages outside the filter are removed, not left dangling.
    assert "Back to intro." in text(result, "api/sites.md")


def test_manifest_records_nav_order(source: Path, repo: Path) -> None:
    manifest = json.loads(text(build_export(source, config(repo)), "_source.json"))
    assert manifest["pages"] == ["intro.md", "old.md", "api/sites.md", "notes/v1.md"]
    assert manifest["source_commit"] is None  # fixture is not a git repo


def test_export_is_deterministic(source: Path, repo: Path) -> None:
    cfg = config(repo)
    assert build_export(source, cfg).files == build_export(source, cfg).files


def test_long_description_is_truncated(source: Path, repo: Path) -> None:
    page = source / "site" / "docs" / "notes" / "v1.md"
    page.write_text("# 1.0\n\n" + "word " * 80 + "\n", encoding="utf-8")
    result = build_export(source, config(repo))
    line = next(x for x in text(result, "notes/v1.md").splitlines() if x.startswith("descr"))
    assert len(line.removeprefix("description: ")) <= 200
    assert line.endswith("…")
    assert result.notes["notes/v1.md"].description_truncated


def test_long_description_keeps_whole_sentences(source: Path, repo: Path) -> None:
    first = "This release adds sites. " + "It also improves many things. " * 3
    page = source / "site" / "docs" / "notes" / "v1.md"
    page.write_text(f"# 1.0\n\n{first}" + "More detail here. " * 20 + "\n", encoding="utf-8")
    result = build_export(source, config(repo))
    line = next(x for x in text(result, "notes/v1.md").splitlines() if x.startswith("descr"))
    description = line.removeprefix("description: ")
    assert len(description) <= 200
    assert description.endswith(".")
    assert description.startswith("This release adds sites. It also improves many things.")


def run_export(repo: Path, source: Path, *extra: str) -> int:
    return main(["export", "--source", str(source), "--repo", str(repo), *extra])


def test_cli_export_writes_content_and_llms(source: Path, repo: Path) -> None:
    assert run_export(repo, source) == 0
    api = repo / "content" / "api"
    assert sorted(p.relative_to(api).as_posix() for p in api.rglob("*") if p.is_file()) == [
        "_source.json",
        "api/sites.md",
        "intro.md",
        "notes/v1.md",
        "old.md",
    ]
    index = (repo / "public" / "llms.txt").read_text(encoding="utf-8")
    assert index.startswith("# Buildings AI Developer Kit\n\n> ")
    site = "https://schneiderelectricbuildings.github.io/buildings-ai-devkit"
    assert f"- [Overview]({site}/content/api/intro.md): The Example platform" in index
    assert f"- [Old Thing]({site}/content/api/old.md): (deprecated) Old feature." in index
    sections = [line for line in index.splitlines() if line.startswith("## ")]
    assert sections == ["## Concepts", "## API", "## Guides", "## Full text", "## Optional"]
    assert f"- [API]({site}/llms-full/api.txt): full text of this section" in index
    full = (repo / "public" / "llms-full.txt").read_text(encoding="utf-8")
    assert "---\npath: content/api/old.md\ntitle: Old Thing\nsection: Concepts\n" in full
    per_section = sorted(p.name for p in (repo / "public" / "llms-full").iterdir())
    assert per_section == ["api.txt", "concepts.txt", "guides.txt", "optional.txt"]
    api_full = (repo / "public" / "llms-full" / "api.txt").read_text(encoding="utf-8")
    assert "path: content/api/api/sites.md" in api_full
    assert "path: content/api/intro.md" not in api_full

    report = (repo / ".export-tmp" / "export-report.md").read_text(encoding="utf-8")
    assert "**Checks: passed.**" in report
    assert "`api/draft.md`: tagged draft" in report

    # Second run: nothing changes.
    before = {
        p: p.read_bytes() for p in repo.rglob("*") if p.is_file() and ".export-tmp" not in str(p)
    }
    assert run_export(repo, source) == 0
    after = {
        p: p.read_bytes() for p in repo.rglob("*") if p.is_file() and ".export-tmp" not in str(p)
    }
    assert before == after
    report = (repo / ".export-tmp" / "export-report.md").read_text(encoding="utf-8")
    assert "| 4 | 0 | 0 | 0 |" in report


def test_blocklist_hit_blocks_export_without_leaking_term(
    source: Path, repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    page = source / "site" / "docs" / "notes" / "v1.md"
    page.write_text("# 1.0\n\nCall https://SECRET-HOST.example/api and codename-42.\n")
    assert run_export(repo, source) == 1
    assert not (repo / "content" / "api").exists()
    assert not (repo / "public").exists()
    err = capsys.readouterr().err
    report = (repo / ".export-tmp" / "export-report.md").read_text(encoding="utf-8")
    for output in (err, report):
        assert "matches block list rule on line 2" in output
        assert "matches block list rule on line 3" in output
        assert "secret-host" not in output.lower()
        assert "codename-42" not in output
    assert "**Checks: FAILED.**" in report


def test_missing_blocklist_refuses_to_run(source: Path, repo: Path) -> None:
    (source / ".devkit" / "blocklist.txt").unlink()
    assert run_export(repo, source) == 2
    assert not (repo / "content" / "api").exists()


def test_out_writes_elsewhere(source: Path, repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "dry"
    assert run_export(repo, source, "--out", str(out)) == 0
    assert (out / "content" / "api" / "intro.md").is_file()
    assert (out / "public" / "llms.txt").is_file()
    assert not (repo / "content" / "api").exists()


def test_llms_check(repo: Path) -> None:
    assert main(["llms", "--repo", str(repo), "--check"]) == 1
    assert main(["llms", "--repo", str(repo)]) == 0
    assert main(["llms", "--repo", str(repo), "--check"]) == 0


def test_repo_llms_files_are_up_to_date() -> None:
    cfg = load_config(REPO_ROOT / "export.yml")
    files = llms.generate(REPO_ROOT / "content", cfg.llms)
    assert llms.stale(REPO_ROOT / "public", files) == []


def test_branch_name() -> None:
    assert gitpr.branch_name("abcdef123456", dt.date(2026, 11, 6)) == "export/2026-11-06-abcdef1"
