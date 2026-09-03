#!/usr/bin/env python3
"""One-off safe migration from the legacy installation name to Toscanini."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import workflow

LEGACY_START = "<!-- power-dev-workflow:start -->"
LEGACY_END = "<!-- power-dev-workflow:end -->"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def without_legacy_block(text: str) -> str:
    if LEGACY_START not in text or LEGACY_END not in text:
        return text
    before, rest = text.split(LEGACY_START, 1)
    _, after = rest.split(LEGACY_END, 1)
    merged = before.rstrip() + ("\n\n" if before.strip() and after.strip() else "") + after.lstrip()
    return merged.rstrip() + ("\n" if merged.strip() else "")


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate one legacy Power Dev installation to Toscanini.")
    parser.add_argument("--target", default=".", help="Project directory; defaults to the current directory")
    parser.add_argument("--dry-run", action="store_true", help="Show the migration plan without changing files")
    args = parser.parse_args()
    target = Path(args.target).resolve()
    legacy_root = target / ".power-dev-workflow"
    legacy_manifest_path = legacy_root / "manifest.json"
    if not legacy_manifest_path.is_file():
        parser.error(f"legacy manifest not found: {legacy_manifest_path}")

    legacy_manifest = json.loads(legacy_manifest_path.read_text(encoding="utf-8"))
    configuration = legacy_manifest.get("configuration", {})
    adapters = configuration.get("adapters", [])
    enabled_agents = set(configuration.get("agents", workflow.BUILT_IN_AGENTS))
    disabled_agents = [agent for agent in workflow.BUILT_IN_AGENTS if agent not in enabled_agents]
    extensions = configuration.get("extensions", [])
    if extensions:
        parser.error("legacy extensions require manual migration to toscanini-extension.json before this script can continue")

    removals: list[Path] = []
    conflicts: list[str] = []
    for relative, metadata in legacy_manifest.get("files", {}).items():
        path = target / relative
        if relative == "AGENTS.md" or not path.exists():
            continue
        if digest(path) == metadata.get("sha256"):
            removals.append(path)
        else:
            conflicts.append(relative)

    agents_path = target / "AGENTS.md"
    agents_before = agents_path.read_text(encoding="utf-8") if agents_path.exists() else ""
    agents_after = without_legacy_block(agents_before)
    if agents_before == agents_after:
        conflicts.append("AGENTS.md (legacy managed block not found)")

    plan = {
        "target": str(target),
        "dryRun": args.dry_run,
        "preservedConfiguration": {
            "adapters": adapters,
            "agents": sorted(enabled_agents),
            "extensions": extensions,
        },
        "remove": sorted(str(path.relative_to(target)) for path in removals),
        "replaceManagedAgentsBlock": agents_before != agents_after,
        "conflicts": sorted(set(conflicts)),
    }
    print(json.dumps(plan, indent=2))
    if conflicts:
        return 2
    if args.dry_run:
        return 0

    for path in removals:
        path.unlink()
    agents_path.write_text(agents_after, encoding="utf-8")
    legacy_manifest_path.unlink(missing_ok=True)

    result = workflow.install(target, False, adapters, disabled_agents, [], update=False)
    if result != 0:
        return result

    for directory in sorted(legacy_root.rglob("*"), reverse=True):
        if directory.is_dir():
            try:
                directory.rmdir()
            except OSError:
                pass
    try:
        legacy_root.rmdir()
    except OSError:
        print(f"Legacy runtime data remains at {legacy_root}; it is not used by Toscanini.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
