# Buildings AI Developer Kit

> **Status: P0 (skeleton). Not ready for use.** Content in this repo is placeholder only.
> See the [delivery plan](docs/plan/phases.md).

A developer kit that gives AI coding agents accurate, current documentation for the
Buildings APIs, in three formats generated from one source (`content/`):

1. **`llms.txt` / `llms-full.txt`**: an index any agent can fetch *(P1)*
2. **Agent Skill**: a packaged skill agents load on demand *(P2)*
3. **Docs MCP server**: read-only search and retrieval over the docs *(P3)*

This kit contains documentation only, never live data. Access to live data goes through the
separate, authenticated API MCP server.

## Repository layout

```
content/          single source for all outputs
  api/            generated from the source docs (do not edit)
  guides/         authored here
public/           generated llms.txt, llms-full.txt, llms-full/<section>.txt
src/devkit/       Python tooling: content validator, llms generator
llms.yml          llms.txt settings
tests/
docs/             plan, decisions, conventions
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md).
