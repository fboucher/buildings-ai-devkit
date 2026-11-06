# ADR-0009: Review and branch protection

- Status: Accepted
- Date: 2026-11-05

## Context

There is a single maintainer for now.

## Decision

- `main` is protected: changes land through PRs only, and required CI checks must pass.
- 0 required approvals while there is a single maintainer (self-approval is not possible).
- CODEOWNERS is in place; adding a second reviewer and turning on required approval is a
  one-line change.
- Manual exports run whenever the source docs publish a release.
