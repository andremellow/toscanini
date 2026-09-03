# Adapters and extensions

Toscanini core is framework- and specification-tool agnostic. Adapters add context and artifacts for a particular ecosystem; they never replace the orchestrator, independent reviewers, or verification gate.

Built-in adapters are opt-in:

- `laravel` detects framework and Boost metadata and reports optional Laravel-specific setup.
- `spec-kit` installs Toscanini architecture, UX, and verification templates under `.specify/templates`.
- `terminal-ui` enables the local ANSI command center exposed by `toscanini ui`.

The terminal UI reads privacy-safe lifecycle telemetry emitted by the installed workflow under `.toscanini/runtime`. Runtime data is ignored by Git. The UI never reads Codex transcripts, prompts, hidden reasoning, secrets, environment values, or raw tool output.

Use `--with-adapter auto` to opt into every adapter supported by evidence in the target repository. Detection alone never enables an adapter.

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
