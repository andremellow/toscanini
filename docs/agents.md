# Agent model

The primary Codex session is the orchestrator. It preserves requirements, chooses the smallest safe workflow, starts specialists with bounded context, and blocks completion while material findings remain.

- **Architect:** read-only; proposes boundaries, contracts, data and operational risks.
- **Specification reviewer:** read-only and independent; identifies ambiguity and validates required specification, clarification, plan, and explicit waiver evidence before architecture or implementation.
- **Architecture reviewer:** read-only and independent; challenges the plan and final alignment.
- **Design agent:** read-only for production code; maps the existing system and creates a UI contract.
- **Design reviewer:** read-only and independent; checks implementation with browser evidence when warranted.
- **Worker:** the built-in Codex worker; sole owner of production edits during implementation.
- **Test Analyst:** read-only and independent; audits whether automated tests prove the execution contract and genuinely detect regressions, including fixture, assertion, mocking, database, isolation, and failure-path quality.
- **QA:** does not review or edit code or automated tests; exercises the real product or API with representative temporary data in a proven safe environment.
- **Code reviewer:** read-only; reviews the actual diff and execution paths.

The Test Analyst and QA are deliberately separate. The Test Analyst can reject a green but ineffective test suite. QA can reject an implementation that passes automation but fails through the actual screen, control, request, or workflow. QA prepares a complete scenario matrix, creates only scoped disposable test data, observes runtime evidence, and cleans up what it created. It returns `BLOCKED` rather than touching an environment whose safety it cannot establish.

All specialists receive the approved execution contract and accepted artifacts without inheriting the implementation conversation. Reviewers report their complete material finding set at one stable checkpoint. Toscanini classifies and consolidates those findings before returning one correction batch to the responsible stage. Remediation verification is directed; final review is fresh and independent.

Use the Codex subagent interface to inspect activity. Add a specialist by creating a narrowly scoped `.codex/agents/<name>.toml` template, documenting its write boundary, and adding it to `templates/agent-index.json`.

## Configure installed agents

The initializer presents every available specialist in an interactive checklist. The same selector is available after installation:

```sh
toscanini agent list
toscanini agent select
```

The selector uses arrow keys to move, Space to toggle, `a` to toggle all agents, Enter to confirm, and `q` to cancel without changing the selection.

Non-interactive environments can manage one role at a time:

```sh
toscanini agent enable qa
toscanini agent disable design-reviewer
```
