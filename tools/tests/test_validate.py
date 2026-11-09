from pathlib import Path

import pytest

from devkit.cli import main
from devkit.validate import validate_tree

REPO_ROOT = Path(__file__).resolve().parents[2]

GOOD_API_PAGE = """---
title: Sites
description: List sites.
section: API / Endpoints
---

# Sites

See [Other](other.md) and [anchor](other.md#top) and [web](https://example.com).
"""

OTHER_API_PAGE = """---
title: Other
description: Another page.
section: API / Endpoints
---
"""


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def messages(root: Path) -> list[str]:
    issues, _ = validate_tree(root)
    return [f"{i.path}:{i.line}: {i.message}" for i in issues]


def test_valid_tree_has_no_issues(tmp_path: Path) -> None:
    write(tmp_path, "api/sites.md", GOOD_API_PAGE)
    write(tmp_path, "api/other.md", OTHER_API_PAGE)
    assert messages(tmp_path) == []


def test_missing_front_matter(tmp_path: Path) -> None:
    write(tmp_path, "guides/a.md", "# No front matter\n")
    assert messages(tmp_path) == ["guides/a.md:1: missing front matter"]


def test_unclosed_front_matter(tmp_path: Path) -> None:
    write(tmp_path, "guides/a.md", "---\ntitle: A\n")
    assert "not closed" in messages(tmp_path)[0]


def test_section_required_only_in_api(tmp_path: Path) -> None:
    page = "---\ntitle: A\ndescription: B\n---\n"
    write(tmp_path, "api/a.md", page)
    write(tmp_path, "guides/a.md", page)
    assert messages(tmp_path) == ["api/a.md:1: missing required front matter key 'section'"]


def test_unknown_key_and_bad_status(tmp_path: Path) -> None:
    write(
        tmp_path,
        "guides/a.md",
        "---\ntitle: A\ndescription: B\nhide_title: true\nstatus: beta\n---\n",
    )
    assert messages(tmp_path) == [
        "guides/a.md:1: 'status' must be one of ['deprecated']",
        "guides/a.md:1: unknown front matter key 'hide_title'",
    ]


def test_description_too_long(tmp_path: Path) -> None:
    write(tmp_path, "guides/a.md", f"---\ntitle: A\ndescription: {'x' * 201}\n---\n")
    assert "longer than 200" in messages(tmp_path)[0]


def test_broken_absolute_and_escaping_links(tmp_path: Path) -> None:
    body = "[a](missing.md)\n[b](/abs.md)\n[c](../../outside.md)\n"
    write(tmp_path, "guides/a.md", f"---\ntitle: A\ndescription: B\n---\n{body}")
    assert messages(tmp_path) == [
        "guides/a.md:5: broken link 'missing.md'",
        "guides/a.md:6: absolute link '/abs.md' is not allowed; use a relative path",
        "guides/a.md:7: link '../../outside.md' points outside docs/",
    ]


def test_links_in_code_are_ignored(tmp_path: Path) -> None:
    body = "```md\n[a](missing.md)\n```\nUse `[b](missing.md)` syntax.\n"
    write(tmp_path, "guides/a.md", f"---\ntitle: A\ndescription: B\n---\n{body}")
    assert messages(tmp_path) == []


def test_html_comment_rejected(tmp_path: Path) -> None:
    write(tmp_path, "guides/a.md", "---\ntitle: A\ndescription: B\n---\n<!-- todo -->\n")
    assert messages(tmp_path) == [
        "guides/a.md:5: HTML comments are not allowed (they are invisible on sites but kept here)"
    ]


def test_repo_content_is_valid() -> None:
    issues, _ = validate_tree(REPO_ROOT / "docs")
    assert [str(i) for i in issues] == []


@pytest.mark.parametrize(("page", "code"), [(GOOD_API_PAGE, 0), ("# none\n", 1)])
def test_cli_exit_codes(tmp_path: Path, page: str, code: int) -> None:
    write(tmp_path, "api/sites.md", page)
    write(tmp_path, "api/other.md", OTHER_API_PAGE)
    assert main(["validate", "--root", str(tmp_path)]) == code


def test_cli_missing_root(tmp_path: Path) -> None:
    assert main(["validate", "--root", str(tmp_path / "nope")]) == 2
