# Adapters and extensions

Toscanini core is framework- and specification-tool agnostic. Adapters add context and artifacts for a particular ecosystem; they never replace the orchestrator, independent reviewers, or verification gate.

`toscanini analyze` loads only enabled adapter analyzers and consolidates their read-only results. Adapter definitions live under `templates/adapters/`, keeping Laravel and Spec Kit knowledge outside the generic command. This is the same extension point intended for future Flutter, Django, Rails, and other adapters.

Built-in adapters are opt-in:

- `laravel` detects framework and Boost metadata. `toscanini verify` reports both visibly and blocks when the project's Boost policy is `required` and Boost is absent. Configure it with `toscanini laravel boost optional|required`.
- `spec-kit` installs architecture, UX, verification, and scenario templates under `.specify/templates`, plus an adapter-specific discovery policy in the managed `AGENTS.md` block.
- `terminal-ui` enables the local ANSI command center exposed by `toscanini ui`.

The terminal UI reads privacy-safe lifecycle telemetry emitted by the installed workflow under `.toscanini/runtime`. Runtime data is ignored by Git. The UI never reads Codex transcripts, prompts, hidden reasoning, secrets, environment values, or raw tool output.

Use `--with-adapter auto` to opt into every adapter supported by evidence in the target repository. Detection alone never enables an adapter.

For a Spec Kit project, finish a run with `toscanini verify --run-id <run-id>`. Toscanini validates the exact execution contract before running tests, so a missing or unapproved specification, clarification, or plan blocks delivery instead of becoming a hidden warning.

## Community extensions

An extension is a directory containing `toscanini-extension.json` with a stable `name`. It may contain `agents/` and `skills/`; their contents are installed into the target project's `.codex/agents` and `.agents/skills` directories.

```text
my-extension/
├── toscanini-extension.json
├── agents/
│   └── security-reviewer.toml
└── skills/
    └── security-gate/
        └── SKILL.md
```

Install it with `--extension /path/to/my-extension`. Managed-file collision rules also apply to extensions.

## Spec Kit discovery policy

Run the existing specify → clarify → checklist → plan → tasks → analyze → implement flow with the project AGENTS.md loaded. The adapter policy overrides question quotas and optional-test defaults without replacing upstream commands. It requires concrete rule examples, material clarification without a fixed question or answer-length limit, and a scenario-to-test map. Keep `scenarios.md` beside the feature's spec.md using the installed `toscanini-scenarios.md` template. Clarification includes user confirmation and explicit deferrals; it does not promise exhaustive correctness.

Plan tests alongside requirements, and later attach test identifiers and execution evidence. No Gherkin dependency or additional mandatory specialist pass is introduced. The existing Test Analyst can optionally assist discovery; that verdict never replaces its implemented-test audit. Human answers do not consume specialist/remediation budgets. Laravel settings remain independent.

Apply to an existing installation with `toscanini update`; enable first with `toscanini adapter add spec-kit` when needed. These are agent instructions, not a Spec Kit CLI patch or a deterministic proof of semantic coverage. Integrations that do not load AGENTS.md must explicitly load its Spec Kit policy before invoking upstream commands. Disabling the adapter removes its managed policy/templates; feature scenarios and user-customized files remain protected by installer conflict checks.
