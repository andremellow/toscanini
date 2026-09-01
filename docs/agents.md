# Agent model

The primary Codex session is the orchestrator. It preserves requirements, chooses the smallest safe workflow, starts specialists with bounded context, and blocks completion while material findings remain.

- **Architect:** read-only; proposes boundaries, contracts, data and operational risks.
- **Architecture reviewer:** read-only and independent; challenges the plan and final alignment.
- **Design agent:** read-only for production code; maps the existing system and creates a UI contract.
- **Design reviewer:** read-only and independent; checks implementation with browser evidence when warranted.
- **Worker:** the built-in Codex worker; sole owner of production edits during implementation.
- **QA:** may edit tests only; validates acceptance criteria without changing production behavior.
- **Code reviewer:** read-only; reviews the actual diff and execution paths.

Use the Codex subagent interface to inspect activity. Add a specialist by creating a narrowly scoped `.codex/agents/<name>.toml` template, documenting its write boundary, and adding it to `templates/agent-index.json`.
