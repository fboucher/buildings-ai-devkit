# ADR-0006: Python tooling stack

- Status: Accepted
- Date: 2026-11-05

## Decision

All tooling (the exporter in the source repo; the `llms.txt` generator, skill packaging and
docs MCP server here) is Python:
`uv` for environments and packaging, `pytest`, `ruff`. The docs MCP server uses the official
MCP Python SDK (FastMCP) and is distributed with `uvx`.

## Rationale

The source docs use MkDocs (Python), so the whole toolchain stays in one ecosystem.

## Note (P1)

The source uses a custom theme with no Material-style syntax (no admonitions, tabs or
snippets), so the exporter reads `mkdocs.yml` with a tolerant YAML loader instead of
depending on MkDocs itself. Revisit if the source adopts Markdown extensions that need
MkDocs to resolve.
