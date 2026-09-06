---
name: toscanini-architecture
description: Create or independently review architecture for software changes involving boundaries, data, authorization, tenancy, concurrency, integrations, or operational risk.
---

# Toscanini Architecture

Inspect existing architecture, the execution contract, specification, and acceptance criteria before proposing change. Prefer established project patterns and the simplest sufficient design. Cover boundaries, contracts, preserved behavior, data changes, authorization, tenancy, transactions, concurrency, operational risks, tradeoffs, migrations, rollback, required tests, non-negotiable `INV-*` invariants, and explicit non-goals.

When authoring, inspect the whole scope and produce one complete architecture artifact before concluding `APPROVED`, `APPROVED_WITH_CONDITIONS`, or `BLOCKED`. When reviewing, use an independent context with the accepted artifacts, inspect the whole raw scope, report every material finding in one verdict, and conclude with `APPROVE`, `REQUEST_CHANGES`, or `BLOCKED`. Do not silently add requirements outside the approved execution contract; return genuine gaps for contract amendment.
