# ADR-0008: Latest-only versioning with provenance

- Status: Accepted
- Date: 2026-11-05

## Decision

- P1 publishes the latest docs only.
- Each export writes `content/api/_source.json`: source commit SHA, export date, exporter
  version, and the API version if one is identifiable.
- Releases use CalVer tags (`YYYY.MM.DD`), because content follows docs releases.
- If multiple versions are needed later, they are added under `/vN/llms.txt` without
  changing the existing URLs.
