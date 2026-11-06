# Content conventions

All three outputs (`llms.txt`, the Agent Skill and the docs MCP server) are generated from
`content/`. These rules are enforced by `uv run devkit validate` and in CI.

## Layout

| Folder | Owner | Notes |
|---|---|---|
| `content/api/` | **Generated** by the exporter (ADR-0003) | Never edit by hand; changes are overwritten on the next export |
| `content/brick/` | Authored here | How our APIs use Brick (P4) |
| `content/guides/` | Authored here | Task-oriented walkthroughs |
| `content/examples/` | Authored here | Runnable samples, fictional data only |

Pages in `content/api/` mirror the source docs paths 1:1 (ADR-0005). They are written by
the exporter in the internal docs repo, which must produce pages that pass
`devkit validate`, plus `content/api/_source.json` (source commit, exporter version, page
order used by `llms.txt`).

## Front matter

Every page starts with a YAML front matter block. Only these keys are allowed:

| Key | Required | Rule |
|---|---|---|
| `title` | yes | Non-empty string |
| `description` | yes | One line, at most 200 characters. Used as the one-liner in `llms.txt` |
| `section` | yes in `content/api/` | Nav path, e.g. `REST API / Endpoints` |
| `tags` | no | List of non-empty strings |
| `status` | no | Only `deprecated` (ADR-0005) |

```yaml
---
title: Sites
description: List and retrieve sites.
section: REST API / Endpoints
---
```

## Body

- Links between pages are **relative** (`../endpoints/sites.md`) and must resolve inside
  `content/`. External links use `https://`.
- No HTML comments: they are invisible on rendered sites but fully visible to agents.
- Images: alt text by default; only allowlisted images are copied (ADR-0005).
- Examples use **fictional data only**: IDs like `00000000-0000-0000-0000-000000000001`,
  names like "Example Site". Never real customer, site or tenant names.
