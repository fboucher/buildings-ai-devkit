# Contributing

## Ground rules

- **Do not edit `docs/api/`.** It is generated from the source docs by an exporter in the
  internal docs repo and overwritten on every export. Fix the source docs instead.
- Changes land through pull requests only; CI must pass.
- Fictional data only in examples. No real customer, site or tenant names, internal
  hostnames, or production IDs.

## Repository layout

| Folder | What |
|---|---|
| `docs/` | The documentation published by the kit: `api/` (generated), `guides/` (authored here) |
| `public/` | Generated `llms.txt` and `llms-full` files. Do not edit; regenerate |
| `plugins/` | Generated Agent Skill (Claude Code plugin). Do not edit; regenerate |
| `tools/` | Python tooling: validator and generators ([tools/README.md](tools/README.md)) |

## Content rules

Enforced by `devkit validate` and in CI.

Every page under `docs/` starts with a YAML front matter block, with only these keys:

| Key | Required | Rule |
|---|---|---|
| `title` | yes | Non-empty string |
| `description` | yes | One line, at most 200 characters. Used in `llms.txt` and the skill index |
| `section` | yes in `docs/api/` | Nav path, e.g. `REST API / Endpoints` |
| `tags` | no | List of non-empty strings |
| `status` | no | Only `deprecated` |

```yaml
---
title: Sites
description: List and retrieve sites.
section: REST API / Endpoints
---
```

In the body:

- Links between pages are **relative** (`../endpoints/sites.md`) and must resolve inside
  `docs/`. External links use `https://`.
- No HTML comments: they are invisible on rendered sites but fully visible to agents.
- Examples use **fictional data only**: IDs like `00000000-0000-0000-0000-000000000001`,
  names like "Example Site".

## Development

Requires [uv](https://docs.astral.sh/uv/). Run everything from the repository root:

```bash
uv run --project tools ruff check tools
uv run --project tools ruff format tools
uv run --project tools pytest tools
uv run --project tools devkit validate
```

After changing anything under `docs/`, regenerate the outputs (CI checks they are current):

```bash
uv run --project tools devkit llms
uv run --project tools devkit skill
```

On the corporate network, set `UV_SYSTEM_CERTS=1` so uv trusts the Windows certificate store.
