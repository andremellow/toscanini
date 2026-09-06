# Execution contracts and convergence

Every behavioral Toscanini run starts with a lightweight execution contract. The contract is not a second product specification: it is the stable evidence packet shared by Architecture, Implementation, Test Analysis, Code Review, and QA. Before implementation it also freezes direct regression surfaces and the complete executable QA scenario matrix.

Copy the installed template to:

```text
.toscanini/runtime/runs/<run-id>/execution-contract.json
```

It freezes the goal, explicit scope and non-goals, acceptance criteria, architecture invariants, artifact approvals, assurance, an estimated no-orchestration baseline, and finite budgets. Validate it before implementation:

```sh
python3 .toscanini/bin/toscanini_contract.py --run-id <run-id>
```

When Spec Kit is enabled, large work and ambiguous medium work require approved specification, clarification, and plan artifacts. A user can explicitly waive the requirement with a recorded reason; Toscanini may not waive it silently.

## Complete review checkpoints

Code Review and Test Analyst inspect the same stable implementation checkpoint before executable QA. Each role reviews its entire scope and returns all material findings. Toscanini waits for all assigned reviewers, records findings in the run's `finding-ledger.json`, removes duplicates, classifies their cause, shows the consolidated set, and sends one correction batch to the responsible stage. Detection and responsibility are separate: a finding detected by QA can be attributed to an implementation or architecture failure.

Findings remain inside the approved contract. Valid adjacent improvements become follow-ups. A real specification or architecture gap amends and reapproves the contract before implementation continues.

A finding may block only when it cites an approved acceptance criterion, an approved invariant, or demonstrates a direct regression caused by the current diff on a frozen regression surface. Pre-existing defects, general hardening, adjacent workflows, and scenarios invented during QA are non-blocking follow-ups. Adding them to the current delivery requires explicit contract amendment.

Independent approvals are bound to the frozen scope ID and the implementation checkpoint ID. Telemetry distinguishes `independent` review from `directed` remediation. A directed result may close its assigned finding, but it cannot replace an independent gate. Independent QA must report coverage for every frozen `QA-*` scenario, preventing a bounded API check from replacing incomplete browser QA.

## Remediation and final review

Remediation verification is directed: it knows which finding IDs must be closed and performs only the smallest causal checks for regressions introduced by the correction. It cannot become a new full audit. Final independent review happens once after stabilization and receives the contract and complete raw diff without the implementation narrative.

Only affected gates reopen after a correction. Unaffected approvals may be retained with an explicit impact reason. A new blocking problem family discovered by final review stops the run for replanning instead of starting another open-ended loop. The completion gate rejects unresolved blockers and exceeded finite budgets:

```sh
python3 .toscanini/bin/toscanini-gate.py --run-id <run-id> --require-contract
```

Fast assurance permits one remediation round and eight specialist starts. Standard permits two rounds and fifteen specialist starts. Critical permits two rounds and eighteen specialist starts; it increases evidence depth, not repetition. Exceeding a budget stops the run for replanning; it never approves incomplete work.

Every completion-gate attempt writes `.toscanini/runtime/runs/<run-id>/execution-report.md`, including an explainable efficiency score, agent starts, rounds, findings, follow-ups, elapsed/baseline ratio, detected-by versus failure-stage attribution, and the final gate result. A blocked or over-budget run still produces the report.

Material findings may include a reusable learning proposal and its intended policy, adapter, agent, or workflow target. Proposals start as `pending`. Toscanini reports them but never applies them automatically; acceptance and application require an explicit user decision and a separate change.
