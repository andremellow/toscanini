<p align="center">
  <img src="brand/toscanini-maestro.png" alt="Toscanini conducting" width="260">
</p>

<h1 align="center">Toscanini</h1>

<p align="center">
  A disciplined multi-agent workflow for shipping software with independent architecture, testing, QA, and code review.
</p>

<p align="center">
  <a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-3f3d39"></a>
  <img alt="Status: early release" src="https://img.shields.io/badge/status-early%20release-b59b78">
</p>

> **Early release:** the installer and workflow are usable today. The command centers are still evolving, and live activity depends on tasks emitting Toscanini telemetry.

## The idea

AI coding agents are fast, but one agent should not design a change, implement it, write its tests, and approve its own work without independent checks.

Toscanini installs a persistent delivery policy into your repository. You keep speaking naturally to your coding agent; Toscanini decides which specialists are needed and makes every required gate produce evidence before the task can be called complete.

<p align="center">
  <img src="brand/toscanini-workflow.svg" alt="Toscanini conducts briefs, artifacts, findings, and corrections between independent specialists" width="1100">
</p>

Every specialist returns its artifact, evidence, or verdict to Toscanini. Review findings are consolidated and sent back to Implementation as one correction batch; affected gates then run again. Small changes take a smaller path, while risky changes earn more architecture, design, testing, QA, and independent review. Toscanini is the conductor, not another instrument: it coordinates the coding agents you already use.

```mermaid
flowchart LR
    T((Toscanini)) -->|work order| I[Implementation]
    I -->|change set| T
    T -->|independent checks| V[Validation]
    V -->|findings| T
    T -.->|consolidated corrections| I
    T -->|all gates approved| D[Verified delivery]
```

## Install

When the package is published, installation will be:

```sh
cd my-project
npx maestro-toscanini init
```

Until then, link the CLI from the local Toscanini source checkout:

```sh
git clone https://github.com/andremellow/toscanini.git
cd /path/to/toscanini
npm link

cd /path/to/my-project
toscanini init
```

The current directory is the default target. The interactive initializer inspects the repository, suggests compatible adapters, previews its changes, and asks before writing anything.

Start a new coding-agent session in the project after installation so the new repository instructions are loaded.

## Daily use

There is no separate `run` command and no Toscanini process to start. Ask your coding agent for work as usual:

```text
Implement customer invitations with expiring links.
```

```text
Fix the race condition in subscription renewal.
```

The installed `AGENTS.md` policy activates the workflow automatically. Commands from enabled tools enter the same workflow; for example, `/speckit.implement` remains governed by Toscanini when the Spec Kit adapter is enabled.

### Choose the assurance level

Every project starts with `standard` assurance. Change the project default at any time:

```sh
toscanini assurance fast
toscanini assurance standard
toscanini assurance critical
```

Use `toscanini assurance` to show the current default. You can also override it for one request in natural language, such as “implement this with critical assurance.”

| Level | Intended use | Convergence budget |
| --- | --- | --- |
| `fast` | Narrow, low-risk work | One correction round; 8 specialist starts |
| `standard` | Normal product development | Two correction rounds; 15 specialist starts |
| `critical` | Security, billing, concurrency, migrations, or data-loss risk | Deeper evidence; at most 2 consolidated remediation rounds and 18 specialist starts |

Review findings are consolidated before correction. Reaching the budget never converts an unresolved finding into an approval.

The validation boundary is frozen before implementation. QA and reviewers may block only for an approved criterion, invariant, or a direct regression caused by the diff. Adjacent defects and newly imagined edge cases become non-blocking follow-ups instead of silently enlarging the feature. After correction, specialists verify assigned findings rather than restarting open-ended audits.

Toscanini does **not**:

- replace Codex or another coding agent;
- require you to launch orchestration manually;
- install application frameworks;
- pretend that tests passed or that an agent is active;
- overwrite locally customized managed files during updates.

## Specialists and gates

| Role | Responsibility |
| --- | --- |
| Specification Reviewer | Finds ambiguity and missing decisions, and validates Spec Kit specification, clarification, and plan approval before implementation. |
| Architect | Defines boundaries, risks, data flow, and the implementation direction. |
| Worker | Implements the approved change. |
| Test Analyst | Audits whether automated tests prove the execution contract and cover changed behavior with effective assertions. |
| QA | Exercises the running UI or API with representative data. It does not review source code. |
| Code Reviewer | Independently reviews the production diff for correctness, security, and maintainability. |

Architecture and design reviewers join when the change requires them. Reviewers receive neutral context and start without the implementation conversation, reducing confirmation bias.

Before implementation, Toscanini freezes an **execution contract**: goal, scope, non-goals, acceptance criteria, architecture invariants, assurance, and budgets. Context isolation removes persuasive history, not this contract. Code Review and Test Analyst inspect one stable checkpoint before executable QA, return their complete findings, and Toscanini sends one consolidated correction batch to the responsible stage.

When Spec Kit is enabled, complex work requires approved specification, clarification, and plan artifacts. Toscanini asks before an explicit waiver; it never silently skips a required specification. Corrections reopen only affected gates, while a final independent review covers the complete contract.

Use the visible exit gate after implementing a task:

```sh
toscanini verify --run-id <run-id>
```

It first validates the exact execution contract and Spec Kit approvals, reports the detected Laravel and Laravel Boost state, enforces the project's Boost policy, and only then runs the repository's canonical verification command. The run ID is required when Spec Kit is enabled so an older feature cannot accidentally approve the current one.

See [Execution contracts and convergence](docs/execution-contract.md) for the contract, finding ledger, remediation, and budget model.

Each completion-gate attempt automatically creates `.toscanini/runtime/runs/<run-id>/execution-report.md` with quality, convergence, agent usage, findings, and efficiency signals—even when the run is blocked.

During `toscanini init`, use the interactive checklist to choose the specialists installed in the repository. You can review or change that selection later:

```sh
toscanini agent list
toscanini agent select
```

Use the arrow keys to move, <kbd>Space</kbd> to toggle an agent, and <kbd>Enter</kbd> to confirm. For scripts and CI, use `agent enable <name>` or `agent disable <name>` instead.

## Adapters

The core workflow knows nothing about Laravel, Flutter, Spec Kit, or any other ecosystem. An **adapter** adds ecosystem-specific detection, instructions, files, or verification conventions without changing the core quality model.

Run a read-only capability analysis at any time:

```sh
toscanini analyze
```

The core only consolidates results. Each enabled adapter owns its detection and checks. Disabled adapters do not inspect or recommend anything about their ecosystem. For example, the Laravel adapter reports framework, Boost, and Pint status; the Spec Kit adapter reports whether its installation and templates actually exist.

Built-in adapters:

| Adapter | What it adds |
| --- | --- |
| `laravel` | Laravel detection plus a visible Boost policy checked by `toscanini verify`. It does not install Laravel or Boost. |
| `spec-kit` | Toscanini architecture, UX, and verification templates inside an existing Spec Kit workspace. |
| `terminal-ui` | A local terminal view of configuration and emitted task activity. |

Manage adapters at any time:

```sh
toscanini adapter list
toscanini adapter add laravel
toscanini adapter add spec-kit
toscanini adapter add terminal-ui
toscanini adapter remove spec-kit
toscanini laravel boost optional
toscanini laravel boost required
```

Use `--dry-run` to preview a change.

### What would a Flutter adapter do?

A useful Flutter adapter could:

1. detect Flutter from `pubspec.yaml`;
2. teach agents to respect the project's widget, state-management, and localization conventions;
3. discover the repository-owned verification command, such as `flutter test`;
4. add a Flutter specialist or reusable testing skill when needed;
5. teach executable QA how to launch and inspect the supported target platform.

It should not install Flutter, choose a state-management library, or change application code during setup.

See [Creating an adapter](docs/creating-an-adapter.md) for a complete example and contribution checklist.

## Optional terminal UI

```sh
toscanini adapter add terminal-ui
toscanini ui
```

The UI observes privacy-safe events written by instrumented tasks. It does not launch the AI task, read hidden reasoning, or fabricate activity. If no task has emitted events, it displays configuration only.

## Commands

| Command | Purpose |
| --- | --- |
| `toscanini init` | Inspect and configure the current repository interactively. |
| `toscanini inspect` | Show detected stack and verification information without changing files. |
| `toscanini adapter list` | Show available and enabled adapters. |
| `toscanini adapter add <name>` | Add an adapter to an existing installation. |
| `toscanini adapter remove <name>` | Remove a managed adapter safely. |
| `toscanini agent enable <name>` | Enable a specialist role. |
| `toscanini agent disable <name>` | Disable an optional specialist role. |
| `toscanini agent list` | Show every available specialist and whether it is enabled. |
| `toscanini agent select` | Change enabled specialists with an interactive checklist. |
| `toscanini assurance [level]` | Show or change the project's default assurance. |
| `toscanini ui` | Open the optional terminal command center. |
| `toscanini update --dry-run` | Preview an update and report conflicts. |
| `toscanini update` | Update managed files while preserving local customizations. |
| `toscanini doctor` | Diagnose missing or modified managed files. |

Pass `--target /local/path` only when operating on a repository other than the current directory.

## Update safely

```sh
toscanini update --dry-run
toscanini update
toscanini doctor
```

Toscanini records hashes for the files it manages. An update replaces an unchanged managed file, but reports a conflict when you have customized it. Existing project instructions and user-owned files are preserved.

## Extend Toscanini

Organization-specific agents and skills can be distributed as an extension without forking the core:

```text
security-extension/
├── toscanini-extension.json
├── agents/
│   └── security-reviewer.toml
└── skills/
    └── security-gate/
        └── SKILL.md
```

```json
{
  "name": "security-extension"
}
```

```sh
./scripts/install-project --extension ../security-extension
```

## Project documentation

- [Creating an adapter](docs/creating-an-adapter.md)
- [Agent roles](docs/agents.md)
- [Adapters and extensions](docs/adapters.md)
- [Dashboard integration](dashboard/README.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Contributing](CONTRIBUTING.md)

## Open source

Toscanini is community software released under the [MIT License](LICENSE). Contributions for new ecosystems, stronger verification, specialist agents, documentation, and command-center interfaces are welcome.

## Distribution

The npm package is named `maestro-toscanini`; the installed executable remains `toscanini`:

```sh
npx maestro-toscanini init
```

After installing it in a project or globally, use the shorter executable:

```sh
npm install --save-dev maestro-toscanini
npx toscanini init
```

A Homebrew formula will follow versioned releases through the community tap:

```sh
brew install andremellow/tap/toscanini
```

## Readable document reports

Generate a versioned reader from a manifest of actual project Markdown files with `toscanini report --manifest report.json --serve`. Each version retains its documents and ordering. See [document reports](docs/document-reports.md) for the manifest and agent handoff.
