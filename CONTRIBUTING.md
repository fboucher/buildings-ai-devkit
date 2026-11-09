# Contributing

## Ground rules

- **Do not edit `docs/api/`.** It is generated from the source docs and overwritten on
  every export (ADR-0003). Fix the source docs or the exporter rules instead.
- Changes land through pull requests only; CI must pass.
- Fictional data only in examples. No real customer, site or tenant names, internal
  hostnames, or production IDs.

## Repository layout

| Folder | What |
|---|---|
| `docs/` | The documentation published by the kit: `api/` (generated), `guides/` (authored here) |
| `public/` | Generated `llms.txt` and `llms-full` files. Do not edit; regenerate |
| `tools/` | Python tooling: validator and generators ([tools/README.md](tools/README.md)) |
| `.planning/` | Delivery plan, decision records (ADRs), content conventions |

## Development

Requires [uv](https://docs.astral.sh/uv/). Run everything from the repository root:

```bash
uv run --project tools ruff check tools
uv run --project tools ruff format tools
uv run --project tools pytest tools
uv run --project tools devkit validate
```

After changing anything under `docs/`, regenerate the llms files (CI checks they are current):

```bash
uv run --project tools devkit llms
```

On the corporate network, set `UV_SYSTEM_CERTS=1` so uv trusts the Windows certificate store.

- Content rules: [.planning/content-conventions.md](.planning/content-conventions.md)
- Plan: [.planning/plan/phases.md](.planning/plan/phases.md)
- Decisions: [.planning/decisions/](.planning/decisions/README.md)
- `docs/api/` is produced by the exporter maintained in the internal docs repo (ADR-0003).
