# Contributing

## Ground rules

- **Do not edit `content/api/`.** It is generated from the source docs and overwritten on
  every export (ADR-0003). Fix the source docs or the exporter rules instead.
- Changes land through pull requests only; CI must pass.
- Fictional data only in examples. No real customer, site or tenant names, internal
  hostnames, or production IDs.

## Development

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run ruff check .
uv run ruff format .
uv run pytest
uv run devkit validate
```

Content rules are in [docs/content-conventions.md](docs/content-conventions.md).
Design decisions are in [docs/decisions/](docs/decisions/README.md).
