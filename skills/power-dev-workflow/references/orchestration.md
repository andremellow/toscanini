# Orchestration contracts

Give each specialist the accepted spec or requested review target, relevant artifacts, repository paths, and required output. Keep contexts independent.

Architect: `APPROVED`, `APPROVED_WITH_CONDITIONS`, or `BLOCKED`.
Architecture reviewer: `APPROVE` or `REQUEST_CHANGES` with evidence.
QA: verification matrix plus `PASS`, `PASS_WITH_NON_BLOCKING_FINDINGS`, or `FAIL`.
Code and design reviewers: `APPROVE` or `REQUEST_CHANGES` with evidence.

Emit observability events when the installed project enables the command center. Events contain timestamps, role and state metadata, artifact paths, and concise summaries. Never emit hidden reasoning, secrets, full prompts, or environment values.
