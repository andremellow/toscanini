---
name: power-verification
description: Validate an implementation against stable acceptance criteria using repository evidence, deterministic gates, tests, and an independent QA matrix.
---

# Power Verification

Start from the accepted requirements, not the implementer's explanation. Run the canonical verification command if one exists. Validate happy paths, negative paths, permissions, tenant isolation, validation, failures, regression risks, responsive behavior, browser console errors, and network failures when applicable.

Map every acceptance criterion to implementation evidence, automated evidence, and a result. QA may improve tests but must not change production behavior. Conclude with `PASS`, `PASS_WITH_NON_BLOCKING_FINDINGS`, or `FAIL`.
