# ADR-0001: Repo hosting and visibility

- Status: Accepted
- Date: 2026-11-05

## Context

The kit is being built in a personal GitHub account. The canonical home is the
`SchneiderElectricBuildings` organization, and the kit must be public to give it visibility.

## Decision

- Development happens in the personal repo until P1 is ready, with placeholder content only.
- At P1, the repo is copied to `SchneiderElectricBuildings/buildings-ai-devkit` and made
  public. That repo becomes canonical; the personal repo is deleted and work continues
  from a fork.
- Partner-facing URLs are only ever the org URLs. Personal-account URLs are never shared.
- CI deploy and release steps run only in the org repo
  (`if: github.repository == 'SchneiderElectricBuildings/buildings-ai-devkit'`).
- The license must be approved by legal before the repo is public; code and content may
  use different licenses.

## Consequences

- A custom domain for `llms.txt` is optional and can be requested later.
- Content that is not cleared for public release must never be committed, because the
  history moves with the copy.
