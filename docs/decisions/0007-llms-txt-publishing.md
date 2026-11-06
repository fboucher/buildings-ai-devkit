# ADR-0007: `llms.txt` format and publishing

- Status: Accepted
- Date: 2026-11-05

## Decision

- Format follows https://llmstxt.org: H1 title, blockquote summary, H2 sections of links.
- H2 sections mirror the top-level `nav` groups. Long reference material and release
  notes go under the spec's `## Optional` section.
- Deprecated pages are listed with a `(deprecated)` marker in their link description.
- Links point to the **raw markdown** pages of this kit, not a rendered HTML site.
- The summary states what the documented API MCP server is, that it requires
  authentication, and that this kit contains no live data.
- `llms-full.txt`: all pages concatenated in `nav` order, each preceded by its kit path and title. If it exceeds ~100k tokens, per-section full files are also produced.
  CI reports the token size on each PR.
- Published on GitHub Pages of the org repo
  (`https://schneiderelectricbuildings.github.io/buildings-ai-devkit/llms.txt`) and also
  committed to the repo as a fallback. A custom domain may be added later.
