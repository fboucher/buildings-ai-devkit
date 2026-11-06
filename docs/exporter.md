# Running the exporter

The exporter turns the source MkDocs docs into `content/api/` and regenerates `public/`
(`llms.txt`, `llms-full.txt`, `llms-full/<section>.txt`). It is a deterministic script:
no AI is involved, and the same source commit always produces the same files.

It runs inside the corporate network, against a local clone of the source docs repo.

## One-time setup in the source docs repo

Create `.devkit/blocklist.txt` at the **root** of the source repo (outside the MkDocs
docs folder, so the docs site never publishes it). The exporter refuses to run without it.

```text
# One rule per line. Lines starting with # are comments.
# Plain lines: case-insensitive substring.
internal-docs.example.com
# re: lines: case-insensitive regular expression.
re:-uat\.
```

Put in it anything that must never be published: internal hostnames (including the
internal docs site and non-production API hosts), customer and site names, codenames,
known-real ID patterns. Findings are reported by **rule line number only**, never by the
matched text, because the report becomes a public PR description.

## Commands

Dry run into a scratch folder (writes nothing in this repo):

```bash
uv run devkit export --source <path-to-source-repo> --out <scratch-dir>
```

Write into this repo and review with `git diff`:

```bash
uv run devkit export --source <path-to-source-repo>
```

Write, then create a branch, commit, push and open a PR with the report as its description
(needs a clean working tree and the `gh` CLI):

```bash
uv run devkit export --source <path-to-source-repo> --pr
```

The report is written to `.export-tmp/export-report.md` (not committed).

## What the export does

- Exports pages listed in `nav` that are not tagged `draft`. Everything else is excluded
  and listed in the report.
- Rewrites front matter to `title`, `description`, `section`, `tags`, `status`.
- Labels pages tagged `deprecated`.
- Replaces images with their alt text, unless listed in `export.yml` under `images.allow`.
- Removes HTML comments and links to pages that are not exported.
- Stops, writing nothing, on any block list or gitleaks finding or validation issue.

Settings are in [`export.yml`](../export.yml). Design decisions: ADR-0003 to ADR-0008.
