---
name: toscanini-workflow
description: Orchestrate feature development, material bug fixes, refactors, and architecture changes through an approved execution contract, independent complete review rounds, executable QA, causal findings, and impact-based revalidation.
---

# Toscanini Workflow

Preserve the user's request and repository rules. Inspect before planning. Choose the active assurance and classify the change. Read [execution contracts](references/execution-contract.md) and [orchestration](references/orchestration.md).

Before implementation, create and approve the run's execution contract. Freeze its goal, scope, non-goals, acceptance criteria, architecture invariants, direct regression surfaces, complete QA scenario matrix, artifacts, and budgets. Specialists cannot expand that validation scope without explicit contract amendment. If Spec Kit is installed and specification is required, require approved specification, clarification, and plan artifacts or ask the user to explicitly waive the gate with a recorded reason. Do not silently skip it.

Use this order for behavioral work:

1. Contract, clarification, and Spec Kit gate when applicable.
2. Architecture plus independent Architecture Review when applicable.
3. One Worker implements production code and tests.
4. Run deterministic verification.
5. Run Code Review and Test Analyst against the same stable checkpoint; collect their complete finding sets.
6. After source-level blockers are resolved, run executable QA through the real UI or API.
7. Wait for every assigned specialist, consolidate findings, classify causes, and return one correction batch to the failed stage.
8. Revalidate affected gates against the remediation delta.
9. Run one final independent whole-scope review and the completion gate.

Context isolation removes bias, not accepted artifacts. Fresh reviewers receive the contract, specification, architecture, acceptance criteria, repository rules, raw scope, and inspection commands; they do not receive author conclusions or previous verdicts. Directed remediation verification receives finding IDs and is not presented as an independent review.

Require reviewers to inspect their entire assigned scope and report all material findings before returning. No reviewer may add a new blocking criterion outside the approved contract. Classify valuable adjacent improvements as follow-ups. A genuine spec or architecture gap amends and reapproves the contract before work continues.

Use the finding ledger and route `SPEC_GAP` to clarification, `ARCHITECTURE_GAP` to Architecture, `IMPLEMENTATION_DEVIATION` to the Worker, `TEST_GAP` to test implementation, `QA_GAP` to the QA plan, `NEW_REQUIREMENT` to the user, and `ENVIRONMENT_FAILURE` to environment repair or a blocker. Record the detecting role separately from the `failureStage` that should have prevented the problem.

After remediation, run canonical verification once, inspect the delta, and reopen only affected gates. Every reopened role performs directed verification of assigned findings and the smallest direct regression checks caused by the remediation. It must not restart a full audit or add unrelated blockers. Only the designated final review inspects the complete contracted result again from raw evidence.

Apply `fast` for one remediation round and 8 specialist starts, `standard` for two rounds and 15 specialist starts, and `critical` for two rounds and 18 specialist starts. Critical means deeper evidence, not unlimited repetition. Any exhausted limit or new blocker family found by the final review triggers stop-and-replan, never approval. Automatically escalate high-risk security, money, destructive, migration, concurrency, sensitive-data, and data-loss work to critical.

Finish with an execution report that makes efficiency deductions and failure attribution visible. Specialists may propose reusable learnings for project policies, adapters, agents, or workflow stages, but Toscanini never applies them automatically. Keep each proposal pending until the user explicitly accepts, rejects, or defers it; application is a separate change.

Record telemetry and require `toscanini_contract.py` before implementation. For behavioral completion, require `toscanini-gate.py --require-contract` plus architecture/design flags when applicable. For installation operations, read [installation](references/installation.md).
