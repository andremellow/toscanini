<!-- toscanini:start -->
## Toscanini

Toscanini is the default delivery policy for feature development, material bug fixes, refactors, and architecture changes in this repository, including work started through another tool. Optional adapters extend this policy but never replace its contracts or gates.

### Establish the execution contract

Before implementation, create `.toscanini/runtime/runs/<run-id>/execution-contract.json` from `.toscanini/templates/execution-contract.json`. Freeze the goal, in-scope and out-of-scope boundaries, stable `AC-*` acceptance criteria, `INV-*` invariants, direct regression surfaces, and the complete executable QA scenario matrix. Required specification and architecture artifacts, assurance, and budgets belong in the same contract. The contract and validation scope must be approved before the Worker starts. No specialist may grow the QA matrix or regression surface during implementation or review without returning to the user for contract amendment.

If the Spec Kit adapter is enabled, require an approved specification, clarification, and plan for large work and for medium work with unresolved product, domain, data, security, or cross-system decisions. For narrow mechanical work, record why specification is not required. When required Spec Kit artifacts are absent, ask whether the user wants to run the Spec Kit flow or explicitly waive it with a recorded reason. Never silently waive it. Validate the contract with:

`python3 .toscanini/bin/toscanini_contract.py --run-id <run-id>`

An architecture artifact must state boundaries, non-negotiable invariants, risks, test implications, and out-of-scope improvements. An independent Architecture Reviewer challenges it before approval. After approval, agents validate against the contract; they may not silently expand it. A newly discovered contract gap returns to specification or architecture for explicit amendment and reapproval.

### Share contracts, not persuasive history

Only one Worker may edit production code or tests. Reviewers and QA start with no inherited conversation history (`fork_turns: none`), but context isolation must remove bias, not the contract. Give each specialist the approved request/specification, acceptance criteria, architecture, execution contract, relevant repository rules, raw diff or artifact scope, and inspection commands. Do not include the Worker's conclusions, implementation defenses, suspected defects, expected findings, external review comments, or another reviewer's verdict.

Remediation verification is deliberately directed and is not an independent review. It receives the finding IDs and required outcomes it must recheck. A final independent review receives the updated contract and raw final diff without remediation narrative.

### Execute complete review rounds

The normal behavioral flow is: contract and clarification; architecture approval when applicable; implementation; deterministic verification; Code Review and Test Analyst review at the same stable checkpoint; then executable QA; final architecture/design alignment when applicable; completion gate. Code Review happens before expensive runtime QA so source-level blockers are removed first.

Every reviewer must inspect its entire assigned frozen scope and return every material finding in one verdict, not stop after the first blocker. Record findings in `.toscanini/runtime/runs/<run-id>/finding-ledger.json` from the installed template. Each finding requires a stable ID, discovery round and phase, severity, evidence, required outcome, scope, classification, and blocking basis. Only three bases may block: an approved acceptance criterion, an approved invariant, or a direct regression caused by the current diff on a regression surface frozen before implementation. Pre-existing defects, general hardening, adjacent workflows, infrastructure improvements, and newly imagined edge cases are `follow-up` and non-blocking.

Toscanini waits for the whole review checkpoint, consolidates all in-contract findings into one correction batch, and routes each finding to the stage that failed. Do not dispatch remediation while any assigned specialist is still running, and never create one correction loop per finding. Specification gaps return to clarification; architecture gaps return to Architecture; implementation deviations return to the Worker; test gaps return to test implementation; new requirements return to the user. Contract changes require reapproval before implementation continues. Record who detected each finding separately from the `failureStage` that should have prevented it; a QA discovery can prove that QA worked while still exposing an upstream implementation, architecture, specification, or test failure.

The Test Analyst is read-only and audits whether automated tests prove the accepted behavior, execute changed branches with representative state, and protect relevant persistence and failure boundaries. QA does not review code or substitute automated tests: it exercises the real UI or API with safe representative data and observes rendered behavior, persistence, browser console, network failures, and application errors. UI QA must navigate to the affected screen and interact with changed controls. QA returns `BLOCKED` when it cannot prove the environment is safe or cannot execute the changed path.

### Revalidate by impact

After a consolidated correction batch, run deterministic verification once and inspect the remediation delta. Reopen only affected gates. A reopened specialist performs directed verification of the assigned finding IDs and the smallest causal regression checks for that delta; it must not restart an open-ended audit or add unrelated blocking scenarios. A new remediation-round blocker is valid only when the remediation itself introduced it on a frozen regression surface. Otherwise it is a non-blocking follow-up. Retained approvals include a recorded reason. One fresh whole-scope Code Review remains at the designated final-review phase; that is not repeated after every correction.

If the final independent review discovers a new blocking problem family, stop and replan instead of beginning another correction cycle under the old plan. Critical assurance increases depth and evidence, not the number of repeated whole-scope reviews.

After implementation stabilizes, record one immutable implementation checkpoint ID in the contract. Every independent gate reports that checkpoint and the frozen scope ID. After the solution stabilizes, perform one final independent review of the complete contracted scope. Directed results can close findings but can never replace an independent gate. Partial QA cannot replace full QA: the independent QA terminal event must list every completed frozen `QA-*` scenario. Never convert a budget limit, unavailable gate, unresolved blocking finding, or missing evidence into approval.

### Assurance and convergence

Canonical verification: {{VERIFY_COMMAND}}
Design system reference: {{DESIGN_SYSTEM_REFERENCE}}
Enabled adapters: {{ADAPTERS}}
Enabled specialist agents: {{AGENTS}}
Installed extensions: {{EXTENSIONS}}
Default assurance: {{ASSURANCE}}
Laravel Boost policy: {{LARAVEL_BOOST_POLICY}}

Use the project assurance unless the current request explicitly overrides it. `fast` allows one consolidated remediation round and at most 8 specialist runs. `standard` allows two consolidated remediation rounds and at most 15 specialist runs. `critical` allows two consolidated remediation rounds and at most 18 specialist runs. Automatically escalate to `critical` for authentication, authorization, billing, destructive operations, irreversible migrations, concurrency, sensitive data, and credible data-loss risk, and tell the user. When a budget is exhausted, stop and replan with the user.

### Telemetry and completion

Create one run ID per user task. Use `.toscanini/bin/toscanini-event.py` for privacy-safe lifecycle events and pass `--round` and `--phase` when applicable. Every specialist emits `started` and a terminal `completed`, `blocked`, or `failed` event; terminal review events declare a verdict and `context-mode=fresh`. Emit only public-safe summaries and artifact paths, never prompts, hidden reasoning, secrets, environment values, raw tool output, or source contents.

Before declaring behavioral work complete, run:

`python3 .toscanini/bin/toscanini-gate.py --run-id <run-id> --require-contract [--require-architecture] [--require-design]`

Exit code zero is required. The gate rejects missing contracts, unresolved in-contract blockers, exceeded budgets, repeated whole-scope reviews, stale or contaminated reviews, and missing approvals. Telemetry write failure must be retried or reported; it must never be treated as approval.

The execution report includes a directional efficiency score with visible deductions, detected-by versus failure-stage attribution, and proposed learnings. A learning is a reusable rule for a project policy, adapter, agent, or workflow stage—not a copy of an implementation-specific fix. Never modify instructions from a finding automatically. Record a proposal as `pending`; only an explicit user decision may accept it, and applying it is a separate change. Rejected and deferred proposals remain visible for auditability.

Preserve existing project instructions and load installed Toscanini skills when their procedures apply.

Before declaring delivery complete, run `toscanini verify --run-id <run-id>`. This is the visible project exit gate: it validates required Spec Kit approvals, reports Laravel Boost status and policy, then runs the repository's canonical verification command. Do not bypass a failing preflight.
{{SPEC_KIT_POLICY}}
<!-- toscanini:end -->
