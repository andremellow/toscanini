#!/usr/bin/env python3
"""Power Dev Workflow project inspection, installation, update, and verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
START = "<!-- power-dev-workflow:start -->"
END = "<!-- power-dev-workflow:end -->"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def git_dirty(target: Path) -> bool | None:
    result = subprocess.run(
        ["git", "-C", str(target), "status", "--porcelain"],
        text=True,
        capture_output=True,
        check=False,
    )
    return bool(result.stdout.strip()) if result.returncode == 0 else None


def package_scripts(target: Path) -> dict:
    return read_json(target / "package.json").get("scripts", {})


def detect_verify(target: Path) -> tuple[str | None, list[str]]:
    candidates: list[tuple[str, bool]] = [
        ("composer verify", "verify" in read_json(target / "composer.json").get("scripts", {})),
        ("make verify", (target / "Makefile").exists() and "verify:" in (target / "Makefile").read_text(encoding="utf-8", errors="ignore")),
        ("npm run verify", "verify" in package_scripts(target)),
        ("npm test", "test" in package_scripts(target)),
        ("cargo test", (target / "Cargo.toml").exists()),
        ("go test ./...", (target / "go.mod").exists()),
        ("pytest", (target / "pytest.ini").exists() or (target / "pyproject.toml").exists()),
    ]
    available = [command for command, present in candidates if present]
    return (available[0] if available else None, available)


def inspect(target: Path) -> dict:
    composer = read_json(target / "composer.json")
    require = {**composer.get("require", {}), **composer.get("require-dev", {})}
    verify, candidates = detect_verify(target)
    codex_files = sorted(str(path.relative_to(target)) for path in (target / ".codex").rglob("*") if path.is_file()) if (target / ".codex").exists() else []
    design_candidates = [
        name for name in ("DESIGN.md", "docs/design-system.md", "docs/design.md", "storybook")
        if (target / name).exists()
    ]
    return {
        "target": str(target),
        "git": {"repository": (target / ".git").exists(), "dirty": git_dirty(target)},
        "agentsMd": (target / "AGENTS.md").exists(),
        "codexFiles": codex_files,
        "specKit": (target / ".specify").exists(),
        "ci": (target / ".github" / "workflows").exists(),
        "laravel": {
            "detected": (target / "artisan").exists() and "laravel/framework" in require,
            "framework": require.get("laravel/framework"),
            "boost": require.get("laravel/boost"),
        },
        "packageManagers": [name for name, marker in (("composer", "composer.json"), ("npm", "package.json"), ("cargo", "Cargo.toml"), ("go", "go.mod"), ("python", "pyproject.toml")) if (target / marker).exists()],
        "designSystemCandidates": design_candidates,
        "verification": {"canonical": verify, "candidates": candidates},
    }


def rendered_agents(inspection: dict) -> bytes:
    text = (ROOT / "templates" / "AGENTS.managed.md").read_text(encoding="utf-8")
    verify = inspection["verification"]["canonical"] or "Not configured; see .power-dev-workflow/gaps.md"
    design = inspection["designSystemCandidates"][0] if len(inspection["designSystemCandidates"]) == 1 else "Not configured; resolve with the project owner when UI work begins"
    return text.replace("{{VERIFY_COMMAND}}", verify).replace("{{DESIGN_SYSTEM_REFERENCE}}", design).encode()


def merge_agents(existing: bytes, managed: bytes) -> bytes:
    text = existing.decode("utf-8") if existing else ""
    block = managed.decode("utf-8").strip()
    if START in text and END in text:
        before, rest = text.split(START, 1)
        _, after = rest.split(END, 1)
        return (before.rstrip() + "\n\n" + block + after).strip().encode() + b"\n"
    return (text.rstrip() + ("\n\n" if text.strip() else "") + block + "\n").encode()


def desired_files(target: Path, inspection: dict) -> dict[Path, bytes]:
    desired: dict[Path, bytes] = {}
    agents_path = target / "AGENTS.md"
    desired[agents_path] = merge_agents(agents_path.read_bytes() if agents_path.exists() else b"", rendered_agents(inspection))
    for source in (ROOT / "templates" / "agents").glob("*.toml"):
        desired[target / ".codex" / "agents" / source.name] = source.read_bytes()
    for skill in (ROOT / "skills").iterdir():
        if skill.is_dir():
            for source in skill.rglob("*"):
                if source.is_file():
                    desired[target / ".agents" / "skills" / skill.name / source.relative_to(skill)] = source.read_bytes()
    if inspection["specKit"]:
        for source in (ROOT / "templates" / "specs").glob("*.md"):
            desired[target / ".specify" / "templates" / source.name] = source.read_bytes()
    return desired


def load_manifest(target: Path) -> dict:
    return read_json(target / ".power-dev-workflow" / "manifest.json")


def plan(target: Path, update: bool = False) -> tuple[list[tuple[str, Path, bytes]], list[str], dict]:
    inspection = inspect(target)
    manifest = load_manifest(target)
    prior = manifest.get("files", {})
    actions: list[tuple[str, Path, bytes]] = []
    conflicts: list[str] = []
    for path, content in desired_files(target, inspection).items():
        relative = str(path.relative_to(target))
        if not path.exists():
            actions.append(("create", path, content))
        elif path.read_bytes() == content:
            actions.append(("unchanged", path, content))
        elif path.name == "AGENTS.md":
            actions.append(("merge", path, content))
        elif prior.get(relative, {}).get("sha256") == digest(path.read_bytes()):
            actions.append(("update", path, content))
        else:
            conflicts.append(relative)
    return actions, conflicts, inspection


def gap_report(inspection: dict) -> str:
    lines = ["# Verification gaps", ""]
    if inspection["verification"]["canonical"]:
        lines += [f"Canonical command: `{inspection['verification']['canonical']}`", ""]
    else:
        lines += ["No runnable canonical verification command was detected.", "", "Add a repository-owned command that composes the relevant formatter, linter, type checker, tests, static analysis, and build. Power Dev Workflow will not fabricate one.", ""]
    if inspection["laravel"]["detected"] and not inspection["laravel"]["boost"]:
        lines += ["## Optional Laravel Boost", "", "Laravel Boost is absent. After approval, install it with `composer require laravel/boost --dev` and run `php artisan boost:install`.", ""]
    return "\n".join(lines)


def install(target: Path, dry_run: bool, update: bool = False) -> int:
    actions, conflicts, inspection = plan(target, update)
    output = {
        "version": VERSION,
        "mode": "update" if update else "install",
        "dryRun": dry_run,
        "inspection": inspection,
        "actions": [{"action": action, "path": str(path.relative_to(target))} for action, path, _ in actions],
        "conflicts": conflicts,
    }
    print(json.dumps(output, indent=2))
    if conflicts:
        return 2
    if dry_run:
        return 0
    files = {}
    for action, path, content in actions:
        if action != "unchanged":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        files[str(path.relative_to(target))] = {"sha256": digest(path.read_bytes())}
    state = target / ".power-dev-workflow"
    state.mkdir(exist_ok=True)
    gaps = gap_report(inspection).encode()
    (state / "gaps.md").write_bytes(gaps)
    files[".power-dev-workflow/gaps.md"] = {"sha256": digest(gaps)}
    manifest = {"version": VERSION, "files": files}
    (state / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0


def doctor(target: Path) -> int:
    manifest = load_manifest(target)
    findings = []
    if not manifest:
        findings.append("Power Dev Workflow is not installed.")
    for relative, metadata in manifest.get("files", {}).items():
        path = target / relative
        if not path.exists():
            findings.append(f"Missing managed file: {relative}")
        elif digest(path.read_bytes()) != metadata.get("sha256"):
            findings.append(f"Locally modified managed file: {relative}")
    print(json.dumps({"version": manifest.get("version"), "healthy": not findings, "findings": findings, "inspection": inspect(target)}, indent=2))
    return 1 if findings else 0


def verify(target: Path) -> int:
    command, _ = detect_verify(target)
    if not command:
        print("No canonical verification command detected.", file=sys.stderr)
        return 2
    print(f"Running: {command}")
    return subprocess.run(command, cwd=target, shell=True, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("inspect", "install", "update", "doctor", "verify"))
    parser.add_argument("--target", default=".")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    target = Path(args.target).resolve()
    if not target.is_dir():
        parser.error(f"target is not a directory: {target}")
    if args.operation == "inspect":
        print(json.dumps(inspect(target), indent=2))
        return 0
    if args.operation in ("install", "update"):
        return install(target, args.dry_run, args.operation == "update")
    if args.operation == "doctor":
        return doctor(target)
    return verify(target)


if __name__ == "__main__":
    raise SystemExit(main())
