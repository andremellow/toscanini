#!/usr/bin/env python3
"""Toscanini project inspection, installation, update, and verification."""

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
START = "<!-- toscanini:start -->"
END = "<!-- toscanini:end -->"
BUILT_IN_ADAPTERS = ("laravel", "spec-kit", "terminal-ui")
BUILT_IN_AGENTS = tuple(sorted(path.stem for path in (ROOT / "templates" / "agents").glob("*.toml")))


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


def rendered_agents(inspection: dict, adapters: list[str], agents: list[str], extensions: list[Path]) -> bytes:
    text = (ROOT / "templates" / "AGENTS.managed.md").read_text(encoding="utf-8")
    verify = inspection["verification"]["canonical"] or "Not configured; see .toscanini/gaps.md"
    design = inspection["designSystemCandidates"][0] if len(inspection["designSystemCandidates"]) == 1 else "Not configured; resolve with the project owner when UI work begins"
    adapter_text = ", ".join(adapters) if adapters else "none (core workflow only)"
    agent_text = ", ".join(agents)
    extension_text = ", ".join(path.name for path in extensions) if extensions else "none"
    return (text.replace("{{VERIFY_COMMAND}}", verify)
        .replace("{{DESIGN_SYSTEM_REFERENCE}}", design)
        .replace("{{ADAPTERS}}", adapter_text)
        .replace("{{AGENTS}}", agent_text)
        .replace("{{EXTENSIONS}}", extension_text)).encode()


def merge_agents(existing: bytes, managed: bytes) -> bytes:
    text = existing.decode("utf-8") if existing else ""
    block = managed.decode("utf-8").strip()
    if START in text and END in text:
        before, rest = text.split(START, 1)
        _, after = rest.split(END, 1)
        return (before.rstrip() + "\n\n" + block + after).strip().encode() + b"\n"
    return (text.rstrip() + ("\n\n" if text.strip() else "") + block + "\n").encode()


def extension_files(extension: Path, target: Path) -> dict[Path, bytes]:
    manifest_path = extension / "toscanini-extension.json"
    manifest = read_json(manifest_path)
    if not manifest or not manifest.get("name"):
        raise ValueError(f"invalid extension manifest: {manifest_path}")
    desired: dict[Path, bytes] = {}
    for source_dir, destination in (("agents", target / ".codex" / "agents"), ("skills", target / ".agents" / "skills")):
        root = extension / source_dir
        if root.exists():
            for source in root.rglob("*"):
                if source.is_file():
                    desired[destination / source.relative_to(root)] = source.read_bytes()
    return desired


def resolve_configuration(inspection: dict, requested: list[str], disabled_agents: list[str], extension_paths: list[str]) -> tuple[list[str], list[str], list[Path]]:
    adapters = list(dict.fromkeys(requested))
    if "auto" in adapters:
        adapters.remove("auto")
        if inspection["laravel"]["detected"]:
            adapters.append("laravel")
        if inspection["specKit"]:
            adapters.append("spec-kit")
    unknown = sorted(set(adapters) - set(BUILT_IN_ADAPTERS))
    if unknown:
        raise ValueError(f"unknown adapter(s): {', '.join(unknown)}")
    unknown_agents = sorted(set(disabled_agents) - set(BUILT_IN_AGENTS))
    if unknown_agents:
        raise ValueError(f"unknown agent(s): {', '.join(unknown_agents)}")
    agents = [agent for agent in BUILT_IN_AGENTS if agent not in disabled_agents]
    extensions = [Path(path).resolve() for path in extension_paths]
    return sorted(set(adapters)), agents, extensions


def desired_files(target: Path, inspection: dict, adapters: list[str], agents: list[str], extensions: list[Path]) -> dict[Path, bytes]:
    desired: dict[Path, bytes] = {}
    agents_path = target / "AGENTS.md"
    desired[agents_path] = merge_agents(agents_path.read_bytes() if agents_path.exists() else b"", rendered_agents(inspection, adapters, agents, extensions))
    for source in (ROOT / "templates" / "agents").glob("*.toml"):
        if source.stem in agents:
            desired[target / ".codex" / "agents" / source.name] = source.read_bytes()
    for skill in (ROOT / "skills").iterdir():
        if skill.is_dir():
            for source in skill.rglob("*"):
                if source.is_file():
                    desired[target / ".agents" / "skills" / skill.name / source.relative_to(skill)] = source.read_bytes()
    for runtime_tool in (ROOT / "templates" / "runtime").glob("*.py"):
        desired[target / ".toscanini" / "bin" / runtime_tool.name] = runtime_tool.read_bytes()
    desired[target / ".toscanini" / ".gitignore"] = b"runtime/\n"
    if "spec-kit" in adapters:
        for source in (ROOT / "templates" / "specs").glob("*.md"):
            desired[target / ".specify" / "templates" / source.name] = source.read_bytes()
    for extension in extensions:
        desired.update(extension_files(extension, target))
    return desired


def load_manifest(target: Path) -> dict:
    return read_json(target / ".toscanini" / "manifest.json")


def plan(target: Path, adapters: list[str], agents: list[str], extensions: list[Path], update: bool = False) -> tuple[list[tuple[str, Path, bytes]], list[str], dict]:
    inspection = inspect(target)
    manifest = load_manifest(target)
    prior = manifest.get("files", {})
    actions: list[tuple[str, Path, bytes]] = []
    conflicts: list[str] = []
    desired = desired_files(target, inspection, adapters, agents, extensions)
    for path, content in desired.items():
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
    desired_relatives = {str(path.relative_to(target)) for path in desired}
    for relative, metadata in prior.items():
        if relative == ".toscanini/gaps.md" or relative in desired_relatives:
            continue
        path = target / relative
        if not path.exists():
            continue
        if digest(path.read_bytes()) == metadata.get("sha256"):
            actions.append(("remove", path, b""))
        else:
            conflicts.append(relative)
    return actions, conflicts, inspection


def gap_report(inspection: dict, adapters: list[str]) -> str:
    lines = ["# Verification gaps", ""]
    if inspection["verification"]["canonical"]:
        lines += [f"Canonical command: `{inspection['verification']['canonical']}`", ""]
    else:
        lines += ["No runnable canonical verification command was detected.", "", "Add a repository-owned command that composes the relevant formatter, linter, type checker, tests, static analysis, and build. Toscanini will not fabricate one.", ""]
    if "laravel" in adapters and inspection["laravel"]["detected"] and not inspection["laravel"]["boost"]:
        lines += ["## Optional Laravel Boost", "", "Laravel Boost is absent. After approval, install it with `composer require laravel/boost --dev` and run `php artisan boost:install`.", ""]
    return "\n".join(lines)


def install(target: Path, dry_run: bool, adapters: list[str], disabled_agents: list[str], extension_paths: list[str], update: bool = False) -> int:
    inspection = inspect(target)
    if update and not adapters and not disabled_agents and not extension_paths:
        previous = load_manifest(target).get("configuration", {})
        adapters = previous.get("adapters", [])
        enabled_agents = set(previous.get("agents", BUILT_IN_AGENTS))
        disabled_agents = [agent for agent in BUILT_IN_AGENTS if agent not in enabled_agents]
        extension_paths = previous.get("extensions", [])
    adapters, agents, extensions = resolve_configuration(inspection, adapters, disabled_agents, extension_paths)
    actions, conflicts, inspection = plan(target, adapters, agents, extensions, update)
    output = {
        "version": VERSION,
        "mode": "update" if update else "install",
        "dryRun": dry_run,
        "inspection": inspection,
        "configuration": {"adapters": adapters, "agents": agents, "extensions": [str(path) for path in extensions]},
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
        if action == "remove":
            path.unlink()
            continue
        if action != "unchanged":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        files[str(path.relative_to(target))] = {"sha256": digest(path.read_bytes())}
    state = target / ".toscanini"
    state.mkdir(exist_ok=True)
    gaps = gap_report(inspection, adapters).encode()
    (state / "gaps.md").write_bytes(gaps)
    files[".toscanini/gaps.md"] = {"sha256": digest(gaps)}
    manifest = {"version": VERSION, "configuration": output["configuration"], "files": files}
    (state / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0


def doctor(target: Path) -> int:
    manifest = load_manifest(target)
    findings = []
    if not manifest:
        findings.append("Toscanini is not installed.")
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
    parser.add_argument("--with-adapter", action="append", default=[], metavar="NAME", help="Enable an optional adapter: laravel, spec-kit, terminal-ui, or auto")
    parser.add_argument("--without-agent", action="append", default=[], metavar="NAME", help="Do not install a built-in specialist agent")
    parser.add_argument("--extension", action="append", default=[], metavar="PATH", help="Install an extension pack containing toscanini-extension.json")
    parser.add_argument("--laravel", action="store_true", help="Shortcut for --with-adapter laravel")
    parser.add_argument("--spec-kit", action="store_true", help="Shortcut for --with-adapter spec-kit")
    args = parser.parse_args()
    target = Path(args.target).resolve()
    if not target.is_dir():
        parser.error(f"target is not a directory: {target}")
    if args.operation == "inspect":
        print(json.dumps(inspect(target), indent=2))
        return 0
    if args.operation in ("install", "update"):
        adapters = args.with_adapter + (["laravel"] if args.laravel else []) + (["spec-kit"] if args.spec_kit else [])
        try:
            return install(target, args.dry_run, adapters, args.without_agent, args.extension, args.operation == "update")
        except ValueError as error:
            parser.error(str(error))
    if args.operation == "doctor":
        return doctor(target)
    return verify(target)


if __name__ == "__main__":
    raise SystemExit(main())
