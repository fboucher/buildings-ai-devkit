# ADR-0006: Python tooling stack

- Status: Accepted
- Date: 2026-11-05

## Decision

All tooling (exporter, `llms.txt` generator, skill packaging, docs MCP server) is Python:
`uv` for environments and packaging, `pytest`, `ruff`. The docs MCP server uses the official
MCP Python SDK (FastMCP) and is distributed with `uvx`.

## Rationale

The source docs use MkDocs (Python). The exporter can load `mkdocs.yml` with MkDocs' own
config loader and reuse its Markdown extensions instead of re-implementing them.
