<!-- toscanini:start -->
## Toscanini

Use Toscanini for feature development, material bug fixes, refactors, and architectural changes. Classify work as small, medium, or large and use independent specialist contexts. Only one worker may edit production code at a time. Architecture reviewers, design reviewers, test experts, and code reviewers are read-only. QA does not review or edit code; it may create temporary data only in a proven local, ephemeral, or explicitly designated test environment.

For changed behavior, run the deterministic verification command, then require an independent Test Expert to audit whether the automated tests can catch the regression, followed by independent QA against the executable product or API with representative data. For changed UI behavior, QA must navigate to the affected screen and interact with the changed control. A passing test command does not replace either gate. Test Expert `REQUEST_CHANGES` returns to the Worker for test repair and repeats verification plus a fresh test audit. QA `FAIL` returns to the Worker and repeats verification, test audit, and QA. Treat unavailable executable validation or an unverified data environment as `BLOCKED`, not passed. Do not claim completion while any gate is unapproved.

Spawn Test Expert, QA, Architecture Reviewer, Design Reviewer, and Code Reviewer with no inherited conversation history (`fork_turns: none`). Their briefing may contain only the accepted requirements/specification, repository rules, relevant artifact paths, base/head or diff scope, and commands needed to inspect evidence. Do not include prior agent conclusions, suspected defects, expected findings, implementation justifications, external review comments, or requests to confirm a particular fix. A reviewer must perform a complete review of its scope from raw evidence. If context contamination is discovered, discard that result and start a new reviewer with a neutral briefing.

Toscanini is the default development policy for this repository, including tasks started by commands from other tools. Optional adapters extend the workflow but never replace its orchestration and review guarantees.

Canonical verification: {{VERIFY_COMMAND}}
Design system reference: {{DESIGN_SYSTEM_REFERENCE}}
Enabled adapters: {{ADAPTERS}}
Enabled specialist agents: {{AGENTS}}
Installed extensions: {{EXTENSIONS}}

When `.toscanini/bin/toscanini-event.py` exists, create a unique `run-id` for each user task and record orchestration lifecycle events automatically. Pass the same run id to every specialist. The orchestrator records its own start, material progress, handoffs, blocked state, and completion. Every spawned specialist records start and terminal state. Terminal review events include a structured verdict. Use:

`python3 .toscanini/bin/toscanini-event.py --run-id <current-run-id> --agent <stable-id> --role <role> --event <started|progress|handoff|completed|blocked|failed> --state <active|waiting|completed|blocked|failed> --summary "<brief public-safe status>" [--verdict <approve|request-changes|pass|pass-with-non-blocking-findings|fail|blocked>] [--context-mode <fresh|inherited>] [--artifact <repository-relative-path>]`

Before declaring a behavioral task complete, run `python3 .toscanini/bin/toscanini-gate.py --run-id <current-run-id>`, adding `--require-architecture` and/or `--require-design` when those reviews apply. Exit code zero is required. A missing event, missing verdict, non-fresh review context, rejection, failure, or blocked gate must prevent completion and trigger the required specialist or repair loop. Never describe reviews as complete from memory; the completion gate is the source of truth.

Never include prompts, hidden reasoning, secrets, environment values, raw tool output, or source-code contents in telemetry. Telemetry failure must not block development work.

Treat repeated human review feedback as a candidate repository rule update. Preserve existing project instructions and load reusable procedures from repository skills on demand.
<!-- toscanini:end -->
