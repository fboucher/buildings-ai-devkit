# ADR-0008: Latest-only versioning with provenance

- Status: Accepted
- Date: 2026-11-05

## Decision

- P1 publishes the latest docs only.
- Each export writes `content/api/_source.json`: the last source commit that touched the
  docs project, the exporter version, and the page order. No export date: it would change
  the file on every run and break idempotency (the date is in the branch and commit).
- Releases use CalVer tags (`YYYY.MM.DD`), because content follows docs releases.
- If multiple versions are needed later, they are added under `/vN/llms.txt` without
  changing the existing URLs.
