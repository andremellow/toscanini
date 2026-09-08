---
name: toscanini-workflow
description: Orchestrate feature development, material bug fixes, refactors, and architecture changes through an approved execution contract, independent complete review rounds, executable QA, causal findings, and impact-based revalidation.
---

# Toscanini Workflow

Preserve the user's request and repository rules. Inspect before planning. Choose the active assurance and classify the change. Read [execution contracts](references/execution-contract.md) and [orchestration](references/orchestration.md).

Before implementation, create and approve the run's execution contract. Freeze its goal, scope, non-goals, acceptance criteria, architecture invariants, direct regression surfaces, complete QA scenario matrix, artifacts, and budgets. Specialists cannot expand that validation scope without explicit contract amendment. If Spec Kit is installed and specification is required, require approved specification, clarification, and plan artifacts or ask the user to explicitly waive the gate with a recorded reason. Do not silently skip it.

Use this order for behavioral work:

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

Context isolation removes bias, not accepted artifacts. Fresh reviewers receive the contract, specification, architecture, acceptance criteria, repository rules, raw scope, and inspection commands; they do not receive author conclusions or previous verdicts. Directed remediation verification receives finding IDs and is not presented as an independent review.

Require reviewers to inspect their entire assigned scope and report all material findings before returning. No reviewer may add a new blocking criterion outside the approved contract. Classify valuable adjacent improvements as follow-ups. A genuine spec or architecture gap amends and reapproves the contract before work continues.

Use the finding ledger and route `SPEC_GAP` to clarification, `ARCHITECTURE_GAP` to Architecture, `IMPLEMENTATION_DEVIATION` to the Worker, `TEST_GAP` to test implementation, `QA_GAP` to the QA plan, `NEW_REQUIREMENT` to the user, and `ENVIRONMENT_FAILURE` to environment repair or a blocker. Record the detecting role separately from the `failureStage` that should have prevented the problem.

After remediation, run canonical verification once, inspect the delta, and reopen only affected gates. Every reopened role performs directed verification of assigned findings and the smallest direct regression checks caused by the remediation. It must not restart a full audit or add unrelated blockers. The Architect performs one final architecture-conformance check after QA, and only directed revalidation when a later correction affects architecture. No second whole-scope Code Review is required.

Apply `fast` for one remediation round and 7 specialist starts, `standard` for two rounds and 14 specialist starts, and `critical` for two rounds and 17 specialist starts. Critical means deeper evidence, not unlimited repetition. Any exhausted limit triggers stop-and-replan, never approval. Automatically escalate high-risk security, money, destructive, migration, concurrency, sensitive-data, and data-loss work to critical.

Finish with an execution report that makes efficiency deductions and failure attribution visible. Specialists may propose reusable learnings for project policies, adapters, agents, or workflow stages, but Toscanini never applies them automatically. Keep each proposal pending until the user explicitly accepts, rejects, or defers it; application is a separate change.

Record telemetry and require `toscanini_contract.py` before implementation. For behavioral completion, require `toscanini-gate.py --require-contract` plus architecture/design flags when applicable. For installation operations, read [installation](references/installation.md).
