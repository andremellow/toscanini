# Adapters and extensions

Toscanini core is framework- and specification-tool agnostic. Adapters add context and artifacts for a particular ecosystem; they never replace the orchestrator, independent reviewers, or verification gate.

`toscanini analyze` loads only enabled adapter analyzers and consolidates their read-only results. Adapter definitions live under `templates/adapters/`, keeping Laravel and Spec Kit knowledge outside the generic command. This is the same extension point intended for future Flutter, Django, Rails, and other adapters.

Built-in adapters are opt-in:

- `laravel` detects framework and Boost metadata. `toscanini verify` reports both visibly and blocks when the project's Boost policy is `required` and Boost is absent. Configure it with `toscanini laravel boost optional|required`.
- `spec-kit` installs Toscanini architecture, UX, and verification templates under `.specify/templates`.
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
