# Architecture authoring, owner approval and conformance

The default flow is specification/clarification when applicable → planning → applicable architecture authoring → product-owner approval of architecture and execution contract → tasks → one Worker for code and tests → deterministic verification → Code Review and Test Analyst together → executable QA → one Architect conformance check when an architecture artifact exists → completion gate. There is no second architecture-document reviewer or mandatory second Code Review after QA.

The Architect owns its implementation-ready artifact using `.toscanini/templates/architecture.md` (also available to Spec Kit as `.specify/templates/architecture.md`). It defines evidenced conventions, architectural style, directories, responsibilities/non-use, invocation/naming, query placement, dependency direction, cross-cutting ownership, concrete flows and test seams. Only unresolved decisions materially changing architecture block authoring readiness; tasks, operational dependencies and spikes remain classified conditions. APPROVED_WITH_CONDITIONS is compatible with owner approval when those conditions do not leave a material architecture decision unresolved.

## Approval evidence

New runs use schemaVersion 3. Compute the architecture's SHA-256 after authoring. Record:

```json
{
  "architecture": {
    "required": true,
    "status": "approved",
    "artifact": "specs/feature/architecture.md",
    "sha256": "<SHA-256 of the approved artifact>",
    "ownerApproval": {
      "approvedBy": "product-owner",
      "decision": "Reference to the owner's explicit approval message",
      "artifactSha256": "<same SHA-256>",
      "scopeId": "<frozen scope ID>"
    }
  },
  "approved": true,
  "approvedBy": "product-owner"
}
```

The Architect emits started and terminal events under role `architect`, phase `architecture`. Its terminal event uses verdict `approved` or `approved-with-conditions`, `--artifact`, `--architecture-sha256` and the frozen scope. A readiness verdict never creates an owner decision. The orchestrator records only an approval actually given by the product owner. Approval metadata is an audit record, not a cryptographic identity verification.

Run `toscanini_contract.py --run-id <id>` before task generation/Worker start. It validates author evidence and owner approval without requiring conformance or finished implementation. The full artifact must exist inside the project, and its hash must still match the approved value. Changing the approved artifact or scope requires another explicit owner decision.

## Completion evidence

After final implementation/tests and QA, the same Architect responsibility writes a separate conformance artifact citing architecture sections or AC/INV IDs, observed implementation/test evidence, deviations and non-blocking follow-ups. It does not reassess the desirability of the design. Telemetry uses phase `architecture-conformance`, architecture hash, frozen scope, final checkpoint, finding count, evidence artifact and verdict `pass`, `pass-with-non-blocking-findings`, `fail` or `blocked`.

The first full conformance check uses `--review-mode independent` to distinguish it from corrections, not to create a new role or require independence from architecture authorship. It runs once after completed Worker and QA events. Corrections affecting architecture use `--review-mode directed`, `--finding-id` and `--revalidation-reason`, retain the earlier full-check evidence and inspect only assigned findings and causal regressions. A completed full review or executed QA pass that found defects can be closed through directed correction; an incomplete or blocked independent run cannot. Directed completion must cite resolved IDs from the run’s finding ledger. Code Review, Test Analyst and QA may similarly carry their earlier independent approval to a corrected checkpoint with a directed closure, recorded impact reason and resolved finding IDs.

`toscanini-gate.py --require-contract --require-architecture --run-id <id>` requires the architecture artifact, Architect author verdict, owner approval and final conformance. Architecture is also inferred when the contract contains an architecture artifact or requires one. For an architecture-only task before implementation, `--require-architecture` alone validates authoring and approval without implementation gates; normal behavioral delivery still uses `--require-contract`. Merely omitting the flag does not bypass architecture requirements of an existing contract.

## Compatibility and budgets

Version 0.9.0 introduces schema v3 and specialist ceilings of 7 (fast), 14 (standard), and 17 (critical), reflecting one fewer activation: the conformance check replaces the document reviewer, and the redundant final Code Review is removed. Remediation ceilings remain one/two/two. Architect authoring and conformance are distinct starts, not accidental repeated authoring; product-owner interaction does not consume specialist starts.

Updates remove the retired `architecture-reviewer` registration and unchanged managed agent file. A customized retired agent file is archived under `.toscanini/legacy/` outside the active agent directory; managed policy/skill references are refreshed automatically. Old configuration references map to `architect`. Other user customizations keep the existing conflict protection.

Historical events and reports are not rewritten. Schema v2 contracts retain their recorded legacy budget ceilings for auditability; old Architecture Reviewer events appear as legacy evidence in reports and the historical dashboard. No new event may be emitted under that retired role, and no gate consumes its verdict. Revalidating an old architecture-required run does not manufacture missing owner approval: it needs the new author/owner/conformance evidence. Historical readability is preserved, not automatic certification under a changed workflow.

## Framework suitability before owner approval

The Architect compares each target's installed framework/version, actual project conventions, official guidance and applicable adapter guidance with the intended purpose of external references. Laravel Boost installation is not proof that its guidance was read. Use available Boost documentation tools and installed guidance, or record the unavailable tool and official version-appropriate documentation fallback. Flutter and other stacks receive their own assessment. A reference API can define behavior and integration contracts without dictating the application's internal architecture.

Schema v3 requires `architecture.frameworkAlignment`, an array with one entry per affected repository:

```json
{
  "repository": "mobile-app",
  "framework": "Flutter",
  "version": "<installed version>",
  "guidance": ["<actual official documentation or project guidance consulted>"],
  "referenceAssessment": "API reference supplies contracts; its internal layering is not adopted",
  "status": "aligned",
  "ownerDecision": null
}
```

`unresolved` blocks approval. A material conflict requires the Architect to explain framework-native and reference/target alternatives and ask the owner; choosing a deviation uses `approved-deviation` and a specific `ownerDecision` reference. Previously explicit decisions remain valid without repeated questions. The gate checks recorded evidence and decision completeness, not the semantic truth of a claimed framework recommendation. The owner sees that assessment in the architecture artifact before approval. Schema v2 history remains readable without retroactively inventing this assessment.

TDD is recorded separately as a development/testing strategy. Follow explicit preferences and ask only when that choice is material and unresolved. This does not add another reviewer or require a new round after implementation.
