# Contributing

Toscanini welcomes focused contributions to the framework-agnostic core, optional adapters, specialist agents, reusable skills, documentation, tests, and command center.

## Design principles

- Keep the core independent of application frameworks and specification tools.
- Add ecosystem behavior through opt-in adapters or external extensions.
- Give every agent one bounded responsibility and an explicit write boundary.
- Keep authors and reviewers in independent contexts.
- Prefer repository-owned verification commands over invented command chains.
- Preserve user-owned files and make installation conflicts explicit.
- Keep all public code, prompts, documentation, and interface copy in English.

## Local development

```sh
python3 -m unittest discover -s tests -v
./scripts/install-project --target /tmp/toscanini-smoke-test --dry-run
```

For dashboard work, use Node.js 22.13 or newer:

```sh
cd dashboard
npm install
npm run lint
npm run build
```

## Proposing an adapter

An adapter must be optional, evidence-driven, and useful to more than one repository. Document what it detects, which files it installs, and what it deliberately does not do. Dependency installation and other material mutations must remain approval-gated.

## Proposing an agent

Agent definitions belong in `templates/agents`. Include a precise description, sandbox boundary, inputs, outputs, and terminal verdict. Read-only review agents must not repair the work they review.

## Proposing an extension

Use an external extension when a workflow is organization-specific, experimental, or independently maintained. An extension needs `toscanini-extension.json` and may provide `agents/` and `skills/`. Validate it against a temporary target before sharing it.

## Pull requests

Keep changes narrow, add or update tests for installer behavior, run the full verification suite, and explain compatibility implications. Never commit credentials, local paths, generated dependency directories, or private project context.
