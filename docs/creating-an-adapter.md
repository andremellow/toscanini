# Creating an adapter

An adapter teaches Toscanini about an ecosystem. It does not replace the core workflow, lower a quality gate, or install an application framework.

Use an adapter when several repositories can benefit from the same detection and guidance. Use an [extension](adapters.md#community-extensions) when the behavior is specific to one organization or project.

## Adapter responsibilities

A focused adapter may provide:

- evidence-based project detection;
- ecosystem-specific agent instructions;
- templates or reusable skills;
- verification-command discovery;
- executable QA guidance;
- optional specialist roles.

It must not silently install dependencies, rewrite application code during setup, or report capabilities that were not detected.

## Example: Flutter

A Flutter adapter could detect a project from a `pubspec.yaml` containing the Flutter SDK:

```yaml
dependencies:
  flutter:
    sdk: flutter
```

Its inspection result might be:

```json
{
  "flutter": {
    "detected": true,
    "verification": "flutter test",
    "platforms": ["ios", "android", "web"]
  }
}
```

The adapter could then add guidance such as:

- preserve the repository's existing state-management approach;
- use widget tests for user-visible interaction;
- use integration tests for flows that cross screens or platform boundaries;
- run generated-code tooling only when the repository already uses it;
- exercise at least one supported runtime target during QA when practical.

The adapter should not choose Riverpod, Bloc, Provider, or another library on behalf of the project. It should discover and respect the existing architecture.

## Add a built-in adapter

Built-in adapters currently live in the Toscanini core rather than a dynamic plug-in registry. A contribution should:

1. add the stable adapter name to the CLI and installer registries;
2. add evidence-based detection to project inspection;
3. add only the templates or skills the adapter owns;
4. document what enabling the adapter does and does not do;
5. add installer, update, removal, and conflict tests;
6. verify behavior in both matching and non-matching repositories.

Relevant implementation areas:

```text
scripts/toscanini.mjs      CLI adapter registry and interactive setup
scripts/workflow.py        detection, configuration, and managed files
templates/                 adapter-owned instructions or artifacts
tests/                     installation and compatibility coverage
```

## Prototype as an extension

Before adding a built-in adapter, an ecosystem integration can be tested as an extension:

```text
flutter-extension/
├── toscanini-extension.json
├── agents/
│   └── flutter-reviewer.toml
└── skills/
    └── flutter-verification/
        └── SKILL.md
```

```json
{
  "name": "flutter-extension"
}
```

Install the prototype into a disposable repository:

```sh
./scripts/install-project \
  --target /tmp/flutter-adapter-test \
  --extension ./flutter-extension \
  --dry-run
```

Remove `--dry-run` only after reviewing the planned files.

## Contribution checklist

- The core still works without the adapter.
- Detection is based on repository evidence, not a guess.
- Setup does not install third-party dependencies silently.
- Existing project conventions win over adapter defaults.
- Managed files update and remove safely.
- Documentation uses real commands and states current limitations.
- Automated tests cover enabled, disabled, update, and conflict paths.
