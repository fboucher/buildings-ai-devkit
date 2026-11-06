# ADR-0005: Deterministic transform, 1:1 page mapping

- Status: Accepted
- Date: 2026-11-05

## Decision

- Each `nav` page becomes exactly one page in `content/api/`, at a mirrored path.
  Long pages are flagged in the export report and fixed upstream rather than split here.
- Every exported page gets front matter:
  - `title`: from the nav label
  - `description`: the source `description:` front matter if present, otherwise the first
    paragraph; shortened to whole sentences within 200 characters (word cut with an
    ellipsis only when the first sentence is too long). Fallbacks are listed in the report
  - `section`: the nav path
- No `source_url` for now: the only human docs site is internal, and links to it would
  expose an internal hostname and be unreachable for partners. The base URL is a config
  value; when empty, the field is omitted. Traceability comes from the export report and
  `_source.json`. Sanitization fails the export if the internal docs host appears anywhere
  in the output.
- Theme-only front matter (e.g. `hide_title`, `template`) is dropped; `tags` are kept.
- Pages tagged `deprecated` are **kept and labelled**: they get `status: deprecated` in
  front matter and a one-line notice at the top of the body, so agents can explain existing
  integrations but do not suggest deprecated features for new code.
- Relative links are rewritten to kit paths.
- Images: by default, image files are **not** copied; each image is replaced with its alt
  text (`*[Image: <alt text>]*`). Screenshots can contain sensitive data that text-based
  scanners cannot detect. Images listed in the exporter config `images.allow` (reviewed by
  a human) are copied to `content/api/img/` and linked. The export report lists every
  image as copied or dropped.
- The exporter is idempotent: no source change means no diff and no PR.
- `mkdocs.yml` is found at the source root or one level below it, so no internal folder
  name has to appear in this repo's config.
- Invocation: `uv run devkit export --source <internal docs repo>` writes `content/api/`,
  `_source.json` and `public/` (llms files) to the working copy, and the report to
  `.export-tmp/export-report.md` (not committed). `--out <dir>` writes elsewhere (dry run);
  `--blocklist <path>` overrides the default block list location.
  With `--pr`, it also creates branch `export/<date>-<source-sha>`, commits, pushes and
  opens a PR (`gh pr create`) with the export report as the body. It never pushes to
  `main`. P5 automation uses the same `--pr` path.
- Each export writes an export report (pages added/changed/removed, fallbacks used,
  unresolved syntax, sanitization findings) that becomes the PR description.
