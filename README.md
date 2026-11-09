# Buildings AI Developer Kit

Documentation for the **Schneider Electric EcoStruxure™ Building Data Platform APIs**
(REST API, GraphQL API, Event Hubs), packaged so AI coding agents (Claude Code, Cursor,
GitHub Copilot and others) can read it and write working integration code.

> **Early access.** This kit is shared with selected partners while it is being built.
> Content in this repository is currently placeholder; the real documentation is added
> with the first export. Feedback is welcome.

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
| Agent Skill (install once, loaded on demand) | Planned |
| Docs MCP server (search and fetch pages from your agent) | Planned |

All formats are generated from the same pages in [`docs/`](docs/).

## Repository layout

| Folder | What |
|---|---|
| [`docs/`](docs/) | The documentation, as agent-friendly markdown: `api/` (generated from the official product docs), `guides/` |
| [`public/`](public/) | Generated `llms.txt`, `llms-full.txt` and per-section files |
| [`tools/`](tools/) | Tooling that validates `docs/` and generates `public/` |
| [`.planning/`](.planning/) | Delivery plan and design decisions |

## Contributing and license

See [CONTRIBUTING.md](CONTRIBUTING.md). Licensing is being finalised: the tooling and the
documentation will be licensed separately.
