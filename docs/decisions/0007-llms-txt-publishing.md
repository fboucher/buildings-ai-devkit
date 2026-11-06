# ADR-0007: `llms.txt` format and publishing

- Status: Accepted
- Date: 2026-11-05

## Decision

- Generated here by `devkit llms` from all of `content/`; settings in `llms.yml`.
- Format follows https://llmstxt.org: H1 title, blockquote summary, H2 sections of links.
- H2 sections mirror the top-level `nav` groups. Long reference material and release
  notes go under the spec's `## Optional` section.
- Deprecated pages are listed with a `(deprecated)` marker in their link description.
- Links point to the **raw markdown** pages of this kit, not a rendered HTML site.
- The summary states what the documented API MCP server is, that it requires
  authentication, and that this kit contains no live data.
- `llms-full.txt`: all pages concatenated in `nav` order, each preceded by a small
  `path` / `title` / `section` header. Per-section files (`llms-full/<section>.txt`) are
  always produced too (the first real export is ~115k tokens; sections are 30k or less),
  and `llms.txt` lists them under `## Full text`. The export report shows the token size.
- Published on GitHub Pages of the org repo
  (`https://schneiderelectricbuildings.github.io/buildings-ai-devkit/llms.txt`) and also
  committed under `public/` as a fallback. Page URLs are `<site>/content/<path>.md`.
  A custom domain may be added later.
- CI fails if `public/` is out of date with `content/` (`devkit llms --check`).
