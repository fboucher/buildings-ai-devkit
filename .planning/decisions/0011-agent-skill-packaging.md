# ADR-0011: Agent Skill packaging and distribution

- Status: Accepted
- Date: 2026-11-09

## Context

P2 delivers the docs as an Agent Skill. The Agent Skills format is an open standard
(https://agentskills.io): a folder with a `SKILL.md` (front matter `name`, `description`)
plus files loaded on demand. Claude Code, GitHub Copilot, VS Code, Cursor and OpenAI Codex
read it; Claude Code also installs skills through plugin marketplaces hosted on GitHub.

## Decision

- **One generated skill**, `building-data-platform-api`, built by `devkit skill` from all of
  `docs/` (settings in `tools/skill.yml`). CI fails if it is out of date (`--check`).
  - `SKILL.md`: hand-written guidance (`tools/src/devkit/skill_assets/SKILL.template.md`:
    find the page first, use documented names only, authenticate, test against UAT, avoid
    deprecated features) followed by a generated index of every page with its description,
    grouped like `llms.txt`. Kept under 500 lines / ~5k tokens.
  - `references/`: every page of `docs/`, byte-for-byte, at the same relative paths.
  - `scripts/search_docs.py`: BM25 keyword search over the references, standard library only,
    so the agent can find the right page without reading ~115k tokens.
  - Front matter uses only spec fields (`name`, `description`, `license`), so the same
    folder is accepted by claude.ai uploads. The name avoids the reserved words "claude"
    and "anthropic".
- **Two install paths at launch:**
  - **Claude Code plugin**: the skill sits in `plugins/buildings-ai-devkit/skills/`, and the
    repo root `.claude-plugin/marketplace.json` makes this repo the marketplace.
    `plugin.json` has no `version`, so installs track the latest commit and receive each
    export through `claude plugin update`.
  - **Zip** of the skill folder (skill name at the zip root), attached to each CalVer GitHub
    release by `release.yml`, for Copilot / Cursor / Codex (`.agents/skills/`) and claude.ai.
    The zip is deterministic (fixed timestamps).
- Releases, like Pages, run only in the org repo (ADR-0001).

## Consequences

- The exporter (internal docs repo) regenerates the skill after each export, alongside the
  llms files, so an export PR contains `docs/api/`, `public/` and `plugins/`.
- The skill duplicates `docs/` inside the repo (~0.5 MB). Acceptable for one source of
  truth that is always regenerated, never edited.
- Revisit `version` pinning if partners need reproducible installs.
