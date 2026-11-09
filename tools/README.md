# tools

Python tooling that checks `docs/` and builds the kit's outputs from it.

| Command | What it does |
|---|---|
| `devkit validate` | Checks front matter and links of every page under `docs/` |
| `devkit llms` | Generates `public/llms.txt`, `public/llms-full.txt` and `public/llms-full/<section>.txt` (settings: `tools/llms.yml`) |
| `devkit llms --check` | Fails if `public/` is out of date (used in CI) |

Run from the **repository root**:

```bash
uv run --project tools devkit validate
uv run --project tools devkit llms
uv run --project tools pytest tools
uv run --project tools ruff check tools
```

`docs/api/` is not produced here: it is written by the exporter maintained in the internal
docs repo, which calls `devkit validate` and `devkit llms` in a local clone of this repo.
Later phases add the Agent Skill packaging (P2) and the docs MCP server (P3) here.
