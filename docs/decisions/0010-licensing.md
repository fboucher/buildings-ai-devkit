# ADR-0010: Split licensing for code and content

- Status: Proposed (pending legal approval)
- Date: 2026-11-06

## Context

The repo was created with an MIT `LICENSE` naming an individual as copyright holder. A
single MIT license would also cover the exported product documentation, making it freely
redistributable, which is not intended for company documentation.

## Decision (proposed, to be confirmed by legal)

| Part | Proposed license |
|---|---|
| Code (`tools/`, `llms/`, `skill/`, `mcp-server/`) | MIT or Apache-2.0, copyright Schneider Electric |
| Exported docs (`content/api/`) | Not open source: copyright Schneider Electric, all rights reserved, provided for use with Schneider Electric APIs |
| Authored guides and Brick pages (`content/guides/`, `content/brick/`) | Legal's choice (e.g. CC-BY-4.0); Brick excerpts follow Brick's license terms (spike S-5) |

- Root `LICENSE` covers code; `content/LICENSE` covers content; README states the split.
- `NOTICE` lists third-party attributions (incl. Brick).

## Consequences

- No real content is committed and the repo is not made public until legal confirms.
- The copyright holder changes to Schneider Electric when the repo moves to the org.
