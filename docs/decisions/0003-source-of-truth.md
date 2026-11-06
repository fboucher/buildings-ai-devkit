# ADR-0003: Internal docs repo is the source of truth

- Status: Accepted
- Date: 2026-11-05

## Context

API documentation is maintained as MkDocs markdown in a private internal repo that is not
reachable from outside the corporate network.

## Decision

- The internal docs repo stays the source of truth.
- `content/api/` in this repo is a **generated artifact**, fully overwritten on each export.
  It is never edited by hand.
- Content problems found during export are fixed upstream in the internal docs repo, or by
  improving the transform rules here.
- `content/brick/`, `content/guides/` and `content/examples/` are authored in this repo and
  never touched by the exporter.
- The exporter lives in this repo (`tools/export/`) and contains no internal URLs or
  hostnames. Sensitive configuration (e.g. block lists of names) lives in the internal repo.
- The exporter runs inside the network: locally against a clone (P1-P4), then in internal
  CI (P5).

## Consequences

- **No AI is involved in producing the content.** The export is a plain, deterministic
  script: the same source always produces the same output, so every diff can be reviewed
  and traced to a source change or a rule change.
