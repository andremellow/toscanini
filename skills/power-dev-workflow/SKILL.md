---
name: power-dev-workflow
description: Orchestrate feature development, material bug fixes, refactors, and architecture changes with independent planning, implementation, QA, and review. Also handles explicit architecture-only, QA-only, and review-only requests.
---

# Power Dev Workflow

Preserve the user's requirements and repository rules. Inspect before planning. Classify the change and state why any role is omitted.

- Small: worker, deterministic verification, then code review for behavioral changes.
- Medium: architect; design agent for UI; plan review when risky; worker; verification; QA; final architecture and code review.
- Large: specification clarification and analysis; architecture and UX artifacts; independent reviews; user approval for material decisions; worker; verification; QA; final reviews; resolve and repeat.

Never let an author review their own work. Spawn architecture review, QA, and code review in independent contexts and give them accepted artifacts plus repository evidence, not the author's persuasive summary. Only the active worker may edit production code. QA may edit tests but must report production defects.

Use stable acceptance identifiers such as `AC-01`. Verification must map each criterion to implementation evidence, automated evidence, and result. Do not claim completion while blocking findings remain.

For installation, update, doctor, or rollback work, read [installation](references/installation.md). For role inputs and outputs, read [orchestration](references/orchestration.md).
