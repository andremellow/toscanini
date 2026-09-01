# Power Dev Workflow

Power Dev Workflow is a reusable Codex plugin for spec-driven software delivery. It coordinates bounded specialist agents, keeps reviews independent, preserves repository conventions, and turns available build and test tooling into a deterministic verification gate.

## Use it

Install the plugin through a Codex marketplace or use the repository directly while developing it. Apply it to a target repository with:

```sh
./scripts/install-project --target /path/to/repository --dry-run
./scripts/install-project --target /path/to/repository
./scripts/doctor --target /path/to/repository
```

Then ask Codex:

```text
Use Power Dev Workflow to implement spec 024.
```

Partial workflows are supported:

```text
Use Power Dev Workflow for architecture and design only. Do not modify code.
```

```text
Review this branch with independent QA, architecture, and code-review agents.
```

## What gets installed

The installer merges a marked section into `AGENTS.md`, adds missing project-scoped agents under `.codex/agents`, installs repository skills under `.agents/skills`, and records managed-file hashes under `.power-dev-workflow/manifest.json`. Existing unmanaged files are never overwritten. A conflict is reported with a non-zero exit code.

The workflow classifies changes as small, medium, or large. Only one implementer owns production-code edits at a time. Architecture, design, QA, and code reviews use separate subagent contexts.

## Command center

`dashboard/` contains an optional local visual command center. It presents workflow phases, agent topology, handoffs, findings, and deterministic gates. Demo mode is clearly labeled. The integration contract supports Codex App Server thread and item events plus lifecycle hooks; it does not parse undocumented transcript formats.

Run it with Node.js 22.13 or newer:

```sh
cd dashboard
npm run dev
```

The dashboard is local by default. Publishing it is intentionally separate from installing the workflow.

## Laravel Boost

Laravel repositories remain fully usable without Boost. If Boost is absent, installation reports the optional commands but does not run them:

```sh
composer require laravel/boost --dev
php artisan boost:install
```

Run those only after reviewing the proposed dependency and generated configuration. Existing Boost installations are detected and preserved.

## Updating and rollback

Run `./scripts/update-project --target ... --dry-run` before applying an update. Managed files are updated only when their installed copy still matches the recorded baseline. Local changes become conflicts. Use Git to review or revert an installation; the installer does not delete user files.

See [agent roles](docs/agents.md), [stack adapters](docs/adapters.md), and [troubleshooting](docs/troubleshooting.md).
