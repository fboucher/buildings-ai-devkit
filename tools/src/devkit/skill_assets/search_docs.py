#!/usr/bin/env python3
"""Search the documentation pages bundled with this skill.

Usage: python scripts/search_docs.py "search terms" [--limit 5]

Prints the best-matching pages (path, title) and the lines that matched, so an agent can
open the right page instead of reading every page. Standard library only.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

REFERENCES = Path(__file__).resolve().parent.parent / "references"
WORD = re.compile(r"[a-z0-9_]+")


def stem(word: str) -> str:
    """Tiny plural folding so "mutation" matches "mutations" and "values" matches "value"."""
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def tokens(text: str) -> list[str]:
    return [stem(w) for w in WORD.findall(text.lower())]


def title_of(text: str, path: Path) -> str:
    match = re.search(r"^title:\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip().strip("'\"") if match else path.stem


def best_lines(text: str, terms: list[str], keep: int = 3) -> list[tuple[int, str]]:
    """Body lines (front matter and headings skipped) matching the most terms."""
    lines = text.splitlines()
    start = 0
    if lines and lines[0].strip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), 0)
        start = end + 1
    scored = []
    for n in range(start, len(lines)):
        line = lines[n].strip()
        if not line or line.startswith("#"):
            continue
        hits = len(set(tokens(line)) & set(terms))
        if hits:
            scored.append((-hits, n + 1, line))
    best = sorted(scored)[:keep]
    return [(n, line) for _, n, line in sorted(best, key=lambda s: s[1])]


def search(query: str, limit: int) -> list[tuple[float, Path, str, list[tuple[int, str]]]]:
    """Rank pages with BM25 (rare words count more; long pages are not favoured),
    plus a boost for words that appear in the page title or file name."""
    terms = sorted(set(tokens(query)))
    if not terms:
        return []
    pages = []
    for path in sorted(REFERENCES.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        words = tokens(text)
        if words:
            pages.append((path, text, title_of(text, path), words))
    if not pages:
        return []

    avg_len = sum(len(w) for *_, w in pages) / len(pages)
    doc_freq = {t: sum(1 for *_, w in pages if t in set(w)) for t in terms}
    idf = {t: math.log(1 + (len(pages) - doc_freq[t] + 0.5) / (doc_freq[t] + 0.5)) for t in terms}
    k1, b = 1.2, 0.75

    results = []
    for path, text, title, words in pages:
        counts = {t: words.count(t) for t in terms}
        matched = [t for t in terms if counts[t]]
        if not matched:
            continue
        norm = k1 * (1 - b + b * len(words) / avg_len)
        score = sum(idf[t] * counts[t] * (k1 + 1) / (counts[t] + norm) for t in matched)
        title_words = set(tokens(title)) | set(tokens(path.stem.replace("-", " ")))
        score += sum(1.5 * idf[t] for t in terms if t in title_words)
        results.append((score, path, title, best_lines(text, matched)))
    results.sort(key=lambda r: (-r[0], str(r[1])))
    return results[:limit]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("query", nargs="+", help="search terms")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    results = search(" ".join(args.query), args.limit)
    if not results:
        print("No matching pages. Try other terms, or browse the index in SKILL.md.")
        return 1
    for _score, path, title, lines in results:
        rel = path.relative_to(REFERENCES.parent).as_posix()
        print(f"{rel}  ({title})")
        for n, line in lines:
            print(f"    {n}: {line[:160]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
