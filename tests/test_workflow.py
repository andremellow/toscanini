from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "scripts" / "install-project"
DOCTOR = ROOT / "scripts" / "doctor"


def run(script: Path, target: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(script), "--target", str(target), *args], text=True, capture_output=True, check=False)


class WorkflowTests(unittest.TestCase):
    def test_empty_repository_install_and_idempotency(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target).returncode, 0)
            first = (target / "AGENTS.md").read_text()
            self.assertEqual(run(INSTALL, target).returncode, 0)
            self.assertEqual((target / "AGENTS.md").read_text(), first)
            self.assertEqual(run(DOCTOR, target).returncode, 0)

    def test_existing_agents_content_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            (target / "AGENTS.md").write_text("# Existing rules\n\nKeep this.\n")
            self.assertEqual(run(INSTALL, target).returncode, 0)
            text = (target / "AGENTS.md").read_text()
            self.assertIn("Keep this.", text)
            self.assertIn("toscanini:start", text)

    def test_existing_codex_agent_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            path = target / ".codex" / "agents" / "architect.toml"
            path.parent.mkdir(parents=True)
            path.write_text("user-owned = true\n")
            result = run(INSTALL, target)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(path.read_text(), "user-owned = true\n")

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target, "--dry-run").returncode, 0)
            self.assertEqual(list(target.iterdir()), [])

    def test_laravel_boost_detection(self):
        for boost in (False, True):
            with self.subTest(boost=boost), tempfile.TemporaryDirectory() as folder:
                target = Path(folder)
                (target / "artisan").write_text("")
                require = {"laravel/framework": "^13.0"}
                if boost:
                    require["laravel/boost"] = "^1.0"
                (target / "composer.json").write_text(json.dumps({"require": require}))
                result = run(INSTALL, target, "--dry-run")
                data = json.loads(result.stdout)
                self.assertEqual(bool(data["inspection"]["laravel"]["boost"]), boost)

    def test_laravel_adapter_is_opt_in(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            (target / "artisan").write_text("")
            (target / "composer.json").write_text(json.dumps({"require": {"laravel/framework": "^13.0"}}))
            self.assertEqual(run(INSTALL, target).returncode, 0)
            self.assertNotIn("Optional Laravel Boost", (target / ".toscanini" / "gaps.md").read_text())
            other = target / "enabled"
            other.mkdir()
            (other / "artisan").write_text("")
            (other / "composer.json").write_text(json.dumps({"require": {"laravel/framework": "^13.0"}}))
            self.assertEqual(run(INSTALL, other, "--laravel").returncode, 0)
            self.assertIn("Optional Laravel Boost", (other / ".toscanini" / "gaps.md").read_text())

    def test_spec_kit_and_dirty_git_are_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            subprocess.run(["git", "init", "-q", str(target)], check=True)
            (target / ".specify").mkdir()
            (target / "untracked.txt").write_text("dirty")
            result = run(INSTALL, target, "--dry-run")
            data = json.loads(result.stdout)
            self.assertTrue(data["inspection"]["specKit"])
            self.assertTrue(data["inspection"]["git"]["dirty"])

    def test_spec_kit_adapter_is_opt_in(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            (target / ".specify").mkdir()
            self.assertEqual(run(INSTALL, target).returncode, 0)
            self.assertFalse((target / ".specify" / "templates" / "architecture.md").exists())
            self.assertEqual(run(INSTALL, target, "--spec-kit").returncode, 0)
            self.assertTrue((target / ".specify" / "templates" / "architecture.md").exists())

    def test_agents_can_be_disabled(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target, "--without-agent", "design-agent", "--without-agent", "design-reviewer").returncode, 0)
            self.assertFalse((target / ".codex" / "agents" / "design-agent.toml").exists())
            self.assertTrue((target / ".codex" / "agents" / "architect.toml").exists())
            self.assertTrue((target / ".codex" / "agents" / "test-expert.toml").exists())

    def test_reconfiguration_removes_only_unchanged_managed_agents(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target).returncode, 0)
            self.assertTrue((target / ".codex" / "agents" / "design-agent.toml").exists())
            self.assertEqual(run(INSTALL, target, "--without-agent", "design-agent").returncode, 0)
            self.assertFalse((target / ".codex" / "agents" / "design-agent.toml").exists())

    def test_extension_agents_and_skills_are_installed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / "target"
            extension = root / "extension"
            target.mkdir()
            (extension / "agents").mkdir(parents=True)
            (extension / "skills" / "security-gate").mkdir(parents=True)
            (extension / "toscanini-extension.json").write_text(json.dumps({"name": "security"}))
            (extension / "agents" / "security-reviewer.toml").write_text('name = "security_reviewer"\n')
            (extension / "skills" / "security-gate" / "SKILL.md").write_text("# Security gate\n")
            self.assertEqual(run(INSTALL, target, "--extension", str(extension)).returncode, 0)
            self.assertTrue((target / ".codex" / "agents" / "security-reviewer.toml").exists())
            self.assertTrue((target / ".agents" / "skills" / "security-gate" / "SKILL.md").exists())

    def test_non_laravel_repository_stays_supported(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            (target / "package.json").write_text(json.dumps({"scripts": {"test": "echo ok"}}))
            result = run(INSTALL, target)
            self.assertEqual(result.returncode, 0)
            self.assertIn("Canonical verification: npm test", (target / "AGENTS.md").read_text())

    def test_doctor_reports_partial_installation(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target).returncode, 0)
            (target / ".codex" / "agents" / "architect.toml").unlink()
            result = run(DOCTOR, target)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Missing managed file", result.stdout)

    def test_update_refuses_local_customization(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target).returncode, 0)
            agent = target / ".codex" / "agents" / "architect.toml"
            agent.write_text(agent.read_text() + "# local\n")
            result = subprocess.run([str(ROOT / "scripts" / "update-project"), "--target", str(target)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn(".codex/agents/architect.toml", result.stdout)

    def test_update_retains_installed_configuration(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            (target / ".specify").mkdir()
            self.assertEqual(run(INSTALL, target, "--spec-kit", "--without-agent", "design-agent").returncode, 0)
            result = subprocess.run([str(ROOT / "scripts" / "update-project"), "--target", str(target), "--dry-run"], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0)
            configuration = json.loads(result.stdout)["configuration"]
            self.assertEqual(configuration["adapters"], ["spec-kit"])
            self.assertNotIn("design-agent", configuration["agents"])

    def test_completion_gate_requires_current_run_approvals(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target).returncode, 0)
            reporter = target / ".toscanini" / "bin" / "toscanini-event.py"
            gate = target / ".toscanini" / "bin" / "toscanini-gate.py"
            missing = subprocess.run(["python3", str(gate), "--run-id", "run-current"], cwd=target, capture_output=True, text=True)
            self.assertEqual(missing.returncode, 1)
            for role, verdict in (("test-expert", "approve"), ("qa", "pass"), ("code-reviewer", "approve")):
                subprocess.run([
                    "python3", str(reporter), "--run-id", "run-current", "--agent", role,
                    "--role", role, "--event", "completed", "--state", "completed",
                    "--verdict", verdict, "--context-mode", "fresh", "--summary", f"{role} approved",
                ], cwd=target, check=True)
            approved = subprocess.run(["python3", str(gate), "--run-id", "run-current"], cwd=target, capture_output=True, text=True)
            self.assertEqual(approved.returncode, 0)
            stale = subprocess.run(["python3", str(gate), "--run-id", "another-run"], cwd=target, capture_output=True, text=True)
            self.assertEqual(stale.returncode, 1)

    def test_completion_gate_rejects_inherited_reviewer_context(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target).returncode, 0)
            reporter = target / ".toscanini" / "bin" / "toscanini-event.py"
            gate = target / ".toscanini" / "bin" / "toscanini-gate.py"
            for role, verdict, context in (("test-expert", "approve", "fresh"), ("qa", "pass", "fresh"), ("code-reviewer", "approve", "inherited")):
                subprocess.run([
                    "python3", str(reporter), "--run-id", "run-contaminated", "--agent", role,
                    "--role", role, "--event", "completed", "--state", "completed",
                    "--verdict", verdict, "--context-mode", context, "--summary", f"{role} result",
                ], cwd=target, check=True)
            result = subprocess.run(["python3", str(gate), "--run-id", "run-contaminated"], cwd=target, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("non-independent gate: code-reviewer", result.stdout)


if __name__ == "__main__":
    unittest.main()
