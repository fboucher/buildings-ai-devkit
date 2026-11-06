# ADR-0002: Phased delivery for early-access partners

- Status: Accepted
- Date: 2026-11-05

## Context

The epic's milestone order (foundations, static outputs, sync, MCP, launch) puts internal
plumbing ahead of partner-visible value. Selected partners will try early versions.

## Decision

Reorder into phases that each end with a partner-usable outcome:
P0 skeleton, P1 docs + `llms.txt`, P2 skill + eval, P3 local docs MCP, P4 Brick,
P5 automated sync, P6 hosted MCP + metrics. See [phases.md](../plan/phases.md).

Until P5, the exporter is run manually.

## Consequences

- Partners get real content from P1 onwards, so P1 content must be cleared for public release.
