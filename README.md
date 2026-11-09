# Buildings AI Developer Kit

Documentation for the **Schneider Electric EcoStruxure™ Building Data Platform APIs**
(REST API, GraphQL API, Event Hubs), packaged so AI coding agents (Claude Code, Cursor,
GitHub Copilot and others) can read it and write working integration code.

> **Early access.** This kit is shared with selected partners while it is being built.
> Feedback is welcome.

## Use it with your AI agent

Point your agent at the index:

```text
https://schneiderelectricbuildings.github.io/buildings-ai-devkit/llms.txt
```

| Agent | How |
|---|---|
| Any agent | Start your prompt with: *"Read `<url>/llms.txt` and the pages it links to before writing code against the Building Data Platform APIs."* |
| Claude Code | Add that sentence to your project's `CLAUDE.md` |
| Cursor | Add the URL as a custom doc (`@Docs` → *Add new doc*), then mention it with `@` |
| GitHub Copilot | Add that sentence to `.github/copilot-instructions.md` |

Need everything in one file? Use `llms-full.txt` (all pages), or one section at a time
with `llms-full/<section>.txt` (for example `llms-full/rest-api.txt`) if your agent has a
small context window. `llms.txt` lists them all under **Full text**.

## Install the Agent Skill

The skill bundles every page plus a small search script, so your agent finds the right
page itself and works offline. It loads only when a task needs it.

**Claude Code** (one step, Claude Code 2.1.275 or later):

```text
/plugin install buildings-ai-devkit --marketplace SchneiderElectricBuildings/buildings-ai-devkit
```

Or in two steps: `/plugin marketplace add SchneiderElectricBuildings/buildings-ai-devkit`,
then `/plugin install buildings-ai-devkit@buildings-ai-devkit`. Get new docs by running
`claude plugin update buildings-ai-devkit`, or turn on auto-update for this marketplace
under `/plugin` → Marketplaces (it is off by default).

**GitHub Copilot, Cursor, OpenAI Codex**: download `building-data-platform-api.zip` from
the latest [release](../../releases/latest) and unzip it into `.agents/skills/` in your
project (or `~/.agents/skills/` for all projects).

**claude.ai**: upload the same zip as a skill in your settings.

## Good to know

- **Documentation only.** The kit contains no live data and no credentials. Calling the
  APIs requires authentication, described in the *Authentication* pages.
- **Test against UAT.** The API introduction pages document the UAT environment partners
  use for testing.
- **Examples use fictional identifiers.** Replace them with IDs from your own environment.
- **Deprecated features are labelled** `(deprecated)` so agents do not suggest them for
  new code.
- Live building data is only available through the authenticated APIs (or the separate,
  authenticated API MCP server), never through this kit.

## Formats

| Format | Status |
|---|---|
| `llms.txt` / `llms-full.txt` | First release in progress |
| Agent Skill (install once, loaded on demand) | First release in progress |
| Docs MCP server (search and fetch pages from your agent) | Planned |

All formats are generated from the same pages in [`docs/`](docs/).

## Repository layout

| Folder | What |
|---|---|
| [`docs/`](docs/) | The documentation, as agent-friendly markdown: `api/` (generated from the official product docs), `guides/` |
| [`public/`](public/) | Generated `llms.txt`, `llms-full.txt` and per-section files |
| [`plugins/`](plugins/) | Generated Agent Skill, packaged as a Claude Code plugin (marketplace in `.claude-plugin/`) |
| [`tools/`](tools/) | Tooling that validates `docs/` and generates `public/` |

## Contributing and license

See [CONTRIBUTING.md](CONTRIBUTING.md). Licensing is being finalised: the tooling and the
documentation will be licensed separately.
