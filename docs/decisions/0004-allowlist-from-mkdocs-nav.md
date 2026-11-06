# ADR-0004: Allowlist derived from MkDocs `nav`

- Status: Accepted
- Date: 2026-11-05

## Context

The epic proposes a separate `publish-allowlist.yml`. The source docs already define their
published set through the `nav:` section of `mkdocs.yml`. The source tree contains files
outside `nav` (drafts, templates, unlisted pages).

## Decision

- A page is exported only if **both** hold:
  1. it is listed in `nav` (files under `docs/` that are not in `nav` are never exported), and
  2. its front matter `tags` do not include `draft`.
  Excluded pages are listed in the export report with the reason.
- An `include:` filter on nav paths selects a subset (e.g. one section for P1), so the
  scope can grow with a config change, not a code change.
- A sanitization pass runs on every export: the block list (below) and gitleaks (when
  installed locally; CI always runs it). Any finding stops the export and nothing is written.
- HTML comments are removed by the transform (they are hidden on the site but would be
  visible to agents) and listed in the export report.
- The block list (internal hostnames, non-production hosts, customer/site names,
  codenames, known-real ID patterns) is sensitive, so it lives **in the internal docs
  repo** at `.devkit/blocklist.txt` (repo root, outside the MkDocs `docs_dir`, so it is
  never published by the docs site). The exporter reads it from the `--source` repo and
  **refuses to run if it is missing**. This repo only contains the generic rules and the
  loader, never the list's contents.

## Consequences

- One source of truth for "this page is published".
- `nav` defines what is *published on the source site*; it does not by itself establish
  that content is cleared for *public* release. That clearance is a separate gate.
