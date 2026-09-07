# Document reports

Generate a readable, versioned report from a project's actual Markdown documents. Each project can supply different document names, titles and ordering. The report is a reading surface: it does not approve a specification or prove tests passed.

## Agent handoff

After producing documents, create a JSON manifest in the target project. Start from the installed `.toscanini/templates/document-report.json`, or use:

```json
{
  "schemaVersion": 1,
  "reportId": "copy-course",
  "project": "Learning platform",
  "title": "Copy a course into a draft",
  "version": 1,
  "documents": [
    {"id": "spec", "title": "Specification", "path": "specs/copy-course/spec.md"},
    {"id": "scenarios", "title": "Scenarios", "path": "specs/copy-course/scenarios.md"},
    {"id": "tests", "title": "Test plan", "path": "specs/copy-course/test-plan.md"}
  ]
}
```

Include only files deliberately selected for reading. Paths resolve from `--target`, not the manifest's directory; documents must be Markdown files inside that project. The manifest path may be absolute or target-relative. IDs are stable lowercase letters, numbers and hyphens. Document order is the manifest order. No particular document type is mandatory.

```sh
toscanini report --target /path/to/project --manifest report.json
```

The command prints the generated `.toscanini/reports/copy-course/index.html`. Open that file directly, or generate and serve with:

```sh
toscanini report --target /path/to/project --manifest report.json --serve
```

Keep the process alive while reading. It prints an available loopback URL; `--port 8080` selects a fixed port. This URL works on the same computer, not on another device. The server exposes only the reader, not the project directory. Ctrl-C stops it. Remote hosting is not performed by this command; the self-contained HTML can be separately deployed with the user's authorization.

## Versions and navigation

Use the same reportId and increment the integer version whenever documents change. Generation snapshots the selected Markdown and its SHA-256 hashes under `versions/`. Existing versions cannot be overwritten. The latest reader includes all snapshots, and its selector switches the document set, titles and contents together. Previously generated files remain historical copies. Keep stable document IDs to retain document selection across versions.

Links such as `index.html#version=2&document=scenarios` select a specific version and document. Unknown versions or documents fall back to the latest version or its first document. The reader supports headings, an in-document table of contents, tables, lists, checkboxes, blockquotes and fenced code. Native browser search works inside the document frame. Navigation labels are English; document text retains its original language.

## Boundaries

Raw Markdown HTML is shown as text; scripts do not execute. Document frames are sandboxed and network resources are disabled by CSP. Images display their alternative text rather than downloading remote resources. HTTP(S) and mail links remain links, but relative file links are rendered as text; choose included documents from the sidebar. There is no custom JavaScript, diagram execution, approval storage or test runner in this feature.

Limits: 100 documents, 2 MiB per Markdown file, 20 MiB per new document bundle and 40 MiB serialized history. Generation is serialized per report by a lock; if interrupted, inspect the output before removing a stale `.generation-lock` and retry with a new version if its snapshot was already written. Generated reports contain the selected source text; keep `.toscanini/reports/` out of public repositories unless intentionally sharing it.
