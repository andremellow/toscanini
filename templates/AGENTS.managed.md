<!-- toscanini:start -->
## Toscanini

Toscanini is the default delivery policy for feature development, material bug fixes, refactors, and architecture changes in this repository, including work started through another tool. Optional adapters extend this policy but never replace its contracts or gates.

### Establish the execution contract

Before implementation, create `.toscanini/runtime/runs/<run-id>/execution-contract.json` from `.toscanini/templates/execution-contract.json`. Freeze the goal, in-scope and out-of-scope boundaries, stable `AC-*` acceptance criteria, `INV-*` invariants, direct regression surfaces, and the complete executable QA scenario matrix. Required specification and architecture artifacts, assurance, and budgets belong in the same contract. The contract and validation scope must be approved before the Worker starts. No specialist may grow the QA matrix or regression surface during implementation or review without returning to the user for contract amendment.

If the Spec Kit adapter is enabled, require an approved specification, clarification, and plan for large work and for medium work with unresolved product, domain, data, security, or cross-system decisions. For narrow mechanical work, record why specification is not required. When required Spec Kit artifacts are absent, ask whether the user wants to run the Spec Kit flow or explicitly waive it with a recorded reason. Never silently waive it. Validate the contract with:

`python3 .toscanini/bin/toscanini_contract.py --run-id <run-id>`

An architecture artifact must state boundaries, non-negotiable invariants, risks, test implications, and out-of-scope improvements. The Architect authors the implementation-ready artifact using `.toscanini/templates/architecture.md`; the product owner approves it and the execution contract directly, binding the decision to the artifact SHA-256 and scope ID. No second agent reviews the architecture document. Missing implementation tasks or operational dependencies are conditions, not architecture blockers. After approval, agents validate against the contract; they may not silently expand it. A newly discovered contract gap returns to specification or architecture for explicit amendment and reapproval.

Before architecture approval, require a per-repository frameworkAlignment assessment: actual framework/version, consulted framework and adapter guidance (including installed Laravel Boost guidance when applicable), intended use of references and material conflicts. References are not architectural authority. Unresolved conflicts require a specific product-owner decision; do not silently inherit a reference API’s internal layering into Laravel, Flutter or another target stack. Keep TDD strategy separate from architecture. Use the Architect’s framework suitability procedure; no additional reviewer is required.

### Execution readiness before Worker dispatch

During planning and task preparation, identify and resolve dependencies for implementation, build, automated tests and executable QA. Consult the installed Toscanini workflow's execution-readiness procedure. Check required runtime/tools, package installation, private registry credentials/licences, services/devices, test environments/data and pending permissions in the actual Worker environment. Complete already-authorized setup and collect remaining user actions before promising unattended execution. Record nonsecret probe evidence in the contract's `readiness` assessment; never store or request credential values in artifacts or chat. Required missing access or pending installation blocks Worker dispatch, even when architecture is approved. Architecture-only approval remains possible. Refresh affected checks after plan/environment changes; no additional reviewer is needed.

### Share contracts, not persuasive history

Only one Worker may edit production code or tests. Reviewers and QA start with no inherited conversation history (`fork_turns: none`), but context isolation must remove bias, not the contract. For architecture authoring, give the Architect the plan and draft contract; author readiness precedes product-owner approval. Give implementation and validation specialists the approved request/specification, acceptance criteria, architecture, execution contract, relevant repository rules, raw diff or artifact scope, and inspection commands. Do not include the Worker's conclusions, implementation defenses, suspected defects, expected findings, external review comments, or another reviewer's verdict.

Remediation verification is deliberately directed and is not an independent review. It receives the finding IDs and required outcomes it must recheck. The post-implementation Architect receives approved specification, architecture, contract and raw final implementation/tests. This is conformance to approved decisions, not a new design review.

### Execute complete review rounds

The default behavioral workflow is:

1. Specification and clarification when applicable.
2. Planning.
3. Architecture authoring when applicable.
4. Product-owner approval of the architecture and execution contract.
5. Task generation.
6. One Worker implements production code and tests.
7. Deterministic verification.
8. Code Review and Test Analyst review at the same stable checkpoint.
9. Executable QA.
10. If an architecture artifact exists, the Architect checks final implementation conformance once.
11. Completion gate.

Every reviewer must inspect its entire assigned frozen scope and return every material finding in one verdict, not stop after the first blocker. Record findings in `.toscanini/runtime/runs/<run-id>/finding-ledger.json` from the installed template. Each finding requires a stable ID, discovery round and phase, severity, evidence, required outcome, scope, classification, and blocking basis. Only three bases may block: an approved acceptance criterion, an approved invariant, or a direct regression caused by the current diff on a regression surface frozen before implementation. Pre-existing defects, general hardening, adjacent workflows, infrastructure improvements, and newly imagined edge cases are `follow-up` and non-blocking.

Toscanini waits for the whole review checkpoint, consolidates all in-contract findings into one correction batch, and routes each finding to the stage that failed. Do not dispatch remediation while any assigned specialist is still running, and never create one correction loop per finding. Specification gaps return to clarification; architecture gaps return to Architecture; implementation deviations return to the Worker; test gaps return to test implementation; new requirements return to the user. Contract changes require reapproval before implementation continues. Record who detected each finding separately from the `failureStage` that should have prevented it; a QA discovery can prove that QA worked while still exposing an upstream implementation, architecture, specification, or test failure.

The Test Analyst is read-only and audits whether automated tests prove the accepted behavior, execute changed branches with representative state, and protect relevant persistence and failure boundaries. QA does not review code or substitute automated tests: it exercises the real UI or API with safe representative data and observes rendered behavior, persistence, browser console, network failures, and application errors. UI QA must navigate to the affected screen and interact with changed controls. QA returns `BLOCKED` when it cannot prove the environment is safe or cannot execute the changed path.

### Revalidate by impact

After a consolidated correction batch, run deterministic verification once and inspect the remediation delta. Reopen only affected gates. A reopened specialist performs directed verification of the assigned finding IDs and the smallest causal regression checks for that delta; it must not restart an open-ended audit or add unrelated blocking scenarios. A new remediation-round blocker is valid only when the remediation itself introduced it on a frozen regression surface. Otherwise it is a non-blocking follow-up. Retained approvals include a recorded reason. Do not repeat Code Review after QA by default. The Architect performs one architecture-conformance check when an architecture artifact exists; directed revalidation is permitted only for architecture-affecting corrections.

Conformance reports deviations from approved architecture sections or AC/INV IDs as implementation findings. Alternative architectures and unrelated improvements are non-blocking follow-ups. Critical assurance increases depth and evidence, not the number of repeated whole-scope reviews.

After implementation stabilizes, record one immutable implementation checkpoint ID in the contract. Every independent gate reports that checkpoint and the frozen scope ID. After executable QA at the stable final checkpoint, perform the architecture-conformance check when applicable. Directed results may close assigned findings; architecture revalidation must retain its earlier full-check evidence and record finding IDs and an impact reason. Partial QA cannot replace full QA: the independent QA terminal event must list every completed frozen `QA-*` scenario. Never convert a budget limit, unavailable gate, unresolved blocking finding, or missing evidence into approval.

### Assurance and convergence

Canonical verification: {{VERIFY_COMMAND}}
Design system reference: {{DESIGN_SYSTEM_REFERENCE}}
Enabled adapters: {{ADAPTERS}}
Enabled specialist agents: {{AGENTS}}
Installed extensions: {{EXTENSIONS}}
Default assurance: {{ASSURANCE}}
Laravel Boost policy: {{LARAVEL_BOOST_POLICY}}

Use the project assurance unless the current request explicitly overrides it. `fast` allows one consolidated remediation round and at most 7 specialist runs. `standard` allows two consolidated remediation rounds and at most 14 specialist runs. `critical` allows two consolidated remediation rounds and at most 17 specialist runs. Automatically escalate to `critical` for authentication, authorization, billing, destructive operations, irreversible migrations, concurrency, sensitive data, and credible data-loss risk, and tell the user. When a budget is exhausted, stop and replan with the user.

### Telemetry and completion

Create one run ID per user task. Use `.toscanini/bin/toscanini-event.py` for privacy-safe lifecycle events and pass `--round` and `--phase` when applicable. Every specialist emits `started` and a terminal `completed`, `blocked`, or `failed` event; independent Code Review/Test Analyst/QA events declare a verdict and `context-mode=fresh`. Architect authoring uses phase `architecture` with verdict `approved` or `approved-with-conditions`; final conformance uses phase `architecture-conformance` with `pass` or `pass-with-non-blocking-findings`, an evidence artifact, architecture hash and final checkpoint. Emit only public-safe summaries and artifact paths, never prompts, hidden reasoning, secrets, environment values, raw tool output, or source contents.

Before declaring behavioral work complete, run:

`python3 .toscanini/bin/toscanini-gate.py --run-id <run-id> --require-contract [--require-architecture] [--require-design]`

Exit code zero is required. The gate rejects missing contracts, unresolved in-contract blockers, exceeded budgets, repeated whole-scope reviews, stale or contaminated reviews, and missing approvals. Telemetry write failure must be retried or reported; it must never be treated as approval.

The execution report includes a directional efficiency score with visible deductions, detected-by versus failure-stage attribution, and proposed learnings. A learning is a reusable rule for a project policy, adapter, agent, or workflow stage—not a copy of an implementation-specific fix. Never modify instructions from a finding automatically. Record a proposal as `pending`; only an explicit user decision may accept it, and applying it is a separate change. Rejected and deferred proposals remain visible for auditability.

Preserve existing project instructions and load installed Toscanini skills when their procedures apply.

Before declaring delivery complete, run `toscanini verify --run-id <run-id>`. This is the visible project exit gate: it validates required Spec Kit approvals, reports Laravel Boost status and policy, then runs the repository's canonical verification command. Do not bypass a failing preflight.
### Document reading handoff

When the user requests a readable report of generated documents, use `.toscanini/templates/document-report.json` to list the actual Markdown files, titles and order for that feature. Paths are relative to the target project. Run `toscanini report --manifest <manifest> --target <project>`; use `--serve` for a local browser URL and retain the process while the user reads. Report the actual file or URL returned. Increment the version for changed documents and retain the report ID and stable document IDs. Do not claim a local URL is remotely published. Reading is not approval and test plans are not execution evidence.

{{SPEC_KIT_POLICY}}
<!-- toscanini:end -->
