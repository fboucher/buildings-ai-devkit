# Delivery plan: phases

This kit is delivered in phases so that selected early-access partners can use each
piece as soon as it is ready. Each phase ends with something a partner can point an AI
agent at, except P0 and P5, which are internal plumbing.

See the [decision log](../decisions/README.md) for the reasoning behind each choice.

| Phase | Partner-visible outcome | Status |
|---|---|---|
| **P0** Skeleton | none (internal) | not started |
| **P1** Agent-optimised docs + `llms.txt` | "Point your agent at `llms.txt`" (public debut) | not started |
| **P2** Agent Skill + first eval | "Install this skill", before/after evidence | not started |
| **P3** Docs MCP server (local, stdio) | "Add this MCP server" (`uvx`) | not started |
| **P4** Brick guidance | Brick version mapping, class subset, worked examples, optional `brick_lookup` | not started |
| **P5** Automated sync | Freshness: internal CI runs the exporter on each docs release | not started |
| **P6** Hosted docs MCP + metrics | Remote MCP URL, rate limiting, anonymous usage metrics | not started |

## P0: Skeleton

Built in the personal development repo, using **placeholder content only**.

- `pyproject.toml` (uv workspace), `ruff`, `pytest`
- Repo layout: `content/`, `tools/export/`, `llms/`, `skill/`, `mcp-server/`, `.github/workflows/`
- Front matter conventions (see ADR-0005) and a content validator
- 3-5 placeholder pages so generators and CI can be developed end to end

## P1: Agent-optimised docs + `llms.txt` (public debut)

**Done when:**

1. `content/api/` is generated from the internal docs repo by the exporter (run locally),
   delivered as a PR with an export report, reviewed and merged.
   - Content: every page in the MkDocs `nav` that is not tagged `draft`.
   - The transform is a deterministic script. No AI is involved in producing the content.
2. `llms.txt` and `llms-full.txt` are generated in CI and published on GitHub Pages
   (also committed to the repo as a fallback).
3. CI checks: front matter present, internal links valid, secret scan clean,
   non-production host patterns absent.
4. README explains how to point Claude Code, Cursor and Copilot at the kit, and states
   clearly that the documented API MCP server is authenticated and separate from this kit.
5. Repo hygiene: legal-approved licenses (split code/content, ADR-0010), NOTICE,
   CONTRIBUTING, SECURITY.md, CODEOWNERS.
6. The repo is copied to `SchneiderElectricBuildings/buildings-ai-devkit` and made public.
   Work continues from a fork.

**Publication:** the source docs are labelled internal-only. Sharing them with
early-access partners through this kit is a decision owned by the project owner.

## P2: Agent Skill + first eval

- `SKILL.md` + sub-files packaged from `content/`, following the current Agent Skills spec (spike S-4).
- Release workflow publishing the skill as a GitHub release asset.
- First eval: ~5 realistic partner tasks, agent without vs. with the kit.

## P3: Docs MCP server (local)

- Python / FastMCP, stdio transport, distributed with `uvx`.
- `docs_search` (keyword first, spike S-3 later), `docs_get_page`, resources for key pages.
- Tool descriptions state that live data requires the separate authenticated API MCP server.

## P4: Brick guidance

- Brick version(s) targeted, class/relationship subset, conventions, worked examples.
- Link to official Brick definitions; attribution in NOTICE (spike S-5).

## P5: Automated sync

- The same exporter, triggered by internal CI on each docs release, opens a PR with a
  token scoped to the public repo only.

## P6: Hosted docs MCP + metrics

- Hosting and transport decision (spike S-2), rate limiting, monitoring, budget alerts.
- Anonymous metrics: top searches, zero-result searches.
