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


def execution_contract(run_id: str, assurance: str = "standard") -> dict:
    budgets = {"remediationRounds": 2, "specialistRuns": 15}
    if assurance == "fast":
        budgets = {"remediationRounds": 1, "specialistRuns": 8}
    if assurance == "critical":
        budgets = {"remediationRounds": 2, "specialistRuns": 18}
    return {
        "schemaVersion": 2,
        "runId": run_id,
        "assurance": assurance,
        "goal": "Deliver the accepted behavior",
        "task": {"size": "small", "decisionRisk": "low", "estimatedBaselineMinutes": 5, "specKitEnabled": False},
        "scope": {"in": ["Changed behavior"], "out": ["Unrelated redesign"], "changeBoundary": []},
        "invariants": [{"id": "INV-01", "statement": "Preserve existing contracts"}],
        "acceptanceCriteria": [{"id": "AC-01", "statement": "The changed behavior works"}],
        "validationScope": {
            "scopeId": "scope-1",
            "frozen": True,
            "regressionSurfaces": ["Changed behavior"],
            "qaScenarios": [{"id": "QA-01", "description": "Exercise the changed behavior", "acceptanceCriteria": ["AC-01"], "invariants": []}],
        },
        "implementationCheckpoint": {"id": "checkpoint-1", "recordedAfterImplementation": True},
        "specification": {"required": False, "status": "not-required", "artifact": None, "clarifyStatus": "not-required", "planStatus": "not-required", "waiverReason": None},
        "architecture": {"required": False, "status": "not-required", "artifact": None},
        "budgets": budgets,
        "approved": True,
    }


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

    def test_spec_discovery_policy_lifecycle_preserves_upstream_and_laravel(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            upstream = target / ".specify/templates/commands/clarify.md"
            upstream.parent.mkdir(parents=True)
            upstream.write_text("User-owned upstream command")
            scenarios = target / "specs/feature/scenarios.md"
            scenarios.parent.mkdir(parents=True)
            scenarios.write_text("User-approved behavior")
            self.assertEqual(run(INSTALL, target, "--laravel").returncode, 0)
            self.assertNotIn("### Spec Kit behavior and test discovery", (target / "AGENTS.md").read_text())
            self.assertEqual(run(INSTALL, target, "--laravel", "--spec-kit").returncode, 0)
            installed = target / ".specify/templates/toscanini-scenarios.md"
            self.assertTrue(installed.exists())
            self.assertIn("### Spec Kit behavior and test discovery", (target / "AGENTS.md").read_text())
            self.assertNotIn("{{SPEC_KIT_POLICY}}", (target / "AGENTS.md").read_text())
            first = (target / "AGENTS.md").read_bytes()
            self.assertEqual(run(ROOT / "scripts/update-project", target).returncode, 0)
            self.assertEqual(first, (target / "AGENTS.md").read_bytes())
            self.assertEqual(run(INSTALL, target, "--laravel").returncode, 0)
            self.assertFalse(installed.exists())
            self.assertNotIn("### Spec Kit behavior and test discovery", (target / "AGENTS.md").read_text())
            self.assertEqual(upstream.read_text(), "User-owned upstream command")
            self.assertEqual(scenarios.read_text(), "User-approved behavior")
            config = json.loads((target / ".toscanini/manifest.json").read_text())["configuration"]
            self.assertEqual(config["adapters"], ["laravel"])

    def test_spec_scenario_template_customization_is_protected(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target, "--spec-kit").returncode, 0)
            template = target / ".specify/templates/toscanini-scenarios.md"
            template.write_text("Custom scenario contract")
            result = run(ROOT / "scripts/update-project", target)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(template.read_text(), "Custom scenario contract")
            self.assertIn("toscanini-scenarios.md", result.stdout)

    def test_agents_can_be_disabled(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target, "--without-agent", "design-agent", "--without-agent", "design-reviewer").returncode, 0)
            self.assertFalse((target / ".codex" / "agents" / "design-agent.toml").exists())
            self.assertTrue((target / ".codex" / "agents" / "architect.toml").exists())
            self.assertTrue((target / ".codex" / "agents" / "test-analyst.toml").exists())
            self.assertTrue((target / ".toscanini" / "templates" / "execution-contract.json").exists())

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
            self.assertEqual(configuration["assurance"], "standard")

    def test_update_migrates_test_expert_to_test_analyst(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target).returncode, 0)
            manifest_path = target / ".toscanini" / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["configuration"]["agents"] = [
                "test-expert" if agent == "test-analyst" else agent
                for agent in manifest["configuration"]["agents"]
            ]
            manifest_path.write_text(json.dumps(manifest))
            result = subprocess.run([str(ROOT / "scripts" / "update-project"), "--target", str(target), "--dry-run"], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0)
            agents = json.loads(result.stdout)["configuration"]["agents"]
            self.assertIn("test-analyst", agents)
            self.assertNotIn("test-expert", agents)

    def test_assurance_is_rendered_and_retained_on_update(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target, "--assurance", "critical").returncode, 0)
            self.assertIn("Default assurance: critical", (target / "AGENTS.md").read_text())
            result = subprocess.run([str(ROOT / "scripts" / "update-project"), "--target", str(target), "--dry-run"], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["configuration"]["assurance"], "critical")

    def test_completion_gate_requires_current_run_approvals(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target).returncode, 0)
            reporter = target / ".toscanini" / "bin" / "toscanini-event.py"
            gate = target / ".toscanini" / "bin" / "toscanini-gate.py"
            missing = subprocess.run(["python3", str(gate), "--run-id", "run-current"], cwd=target, capture_output=True, text=True)
            self.assertEqual(missing.returncode, 1)
            for role, verdict in (("test-analyst", "approve"), ("qa", "pass"), ("code-reviewer", "approve")):
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
            for role, verdict, context in (("test-analyst", "approve", "fresh"), ("qa", "pass", "fresh"), ("code-reviewer", "approve", "inherited")):
                subprocess.run([
                    "python3", str(reporter), "--run-id", "run-contaminated", "--agent", role,
                    "--role", role, "--event", "completed", "--state", "completed",
                    "--verdict", verdict, "--context-mode", context, "--summary", f"{role} result",
                ], cwd=target, check=True)
            result = subprocess.run(["python3", str(gate), "--run-id", "run-contaminated"], cwd=target, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("non-independent gate: code-reviewer", result.stdout)

    def test_contract_gate_requires_approved_spec_kit_artifacts(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target).returncode, 0)
            run_id = "run-spec"
            run_root = target / ".toscanini" / "runtime" / "runs" / run_id
            run_root.mkdir(parents=True)
            contract = execution_contract(run_id)
            contract["specification"] = {
                "required": True, "status": "draft", "artifact": None,
                "clarifyStatus": "pending", "planStatus": "pending", "waiverReason": None,
            }
            (run_root / "execution-contract.json").write_text(json.dumps(contract))
            checker = target / ".toscanini" / "bin" / "toscanini_contract.py"
            rejected = subprocess.run(["python3", str(checker), "--run-id", run_id], cwd=target, capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 1)
            self.assertIn("required specification is not approved", rejected.stdout)
            contract["specification"] = {
                "required": True, "status": "approved", "artifact": "specs/feature/spec.md",
                "clarifyStatus": "approved", "planStatus": "approved", "waiverReason": None,
            }
            (run_root / "execution-contract.json").write_text(json.dumps(contract))
            approved = subprocess.run(["python3", str(checker), "--run-id", run_id], cwd=target, capture_output=True, text=True)
            self.assertEqual(approved.returncode, 0)

    def test_contract_gate_requires_frozen_validation_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target).returncode, 0)
            run_id = "run-unfrozen-qa"
            run_root = target / ".toscanini" / "runtime" / "runs" / run_id
            run_root.mkdir(parents=True)
            contract = execution_contract(run_id)
            contract["validationScope"]["frozen"] = False
            (run_root / "execution-contract.json").write_text(json.dumps(contract))
            checker = target / ".toscanini" / "bin" / "toscanini_contract.py"
            rejected = subprocess.run(["python3", str(checker), "--run-id", run_id], cwd=target, capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 1)
            self.assertIn("validation scope and QA matrix must be frozen", rejected.stdout)

    def test_contract_gate_prevents_silent_spec_kit_bypass(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target, "--spec-kit").returncode, 0)
            run_id = "run-spec-bypass"
            run_root = target / ".toscanini" / "runtime" / "runs" / run_id
            run_root.mkdir(parents=True)
            contract = execution_contract(run_id)
            contract["task"] = {"size": "large", "decisionRisk": "material", "estimatedBaselineMinutes": 30, "specKitEnabled": True}
            contract["architecture"] = {"required": True, "status": "approved", "artifact": "docs/architecture.md"}
            (run_root / "execution-contract.json").write_text(json.dumps(contract))
            checker = target / ".toscanini" / "bin" / "toscanini_contract.py"
            rejected = subprocess.run(["python3", str(checker), "--run-id", run_id], cwd=target, capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 1)
            self.assertIn("Spec Kit must be required for this task classification", rejected.stdout)

    def test_contract_completion_rejects_unresolved_blocking_findings(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target).returncode, 0)
            run_id = "run-findings"
            run_root = target / ".toscanini" / "runtime" / "runs" / run_id
            run_root.mkdir(parents=True)
            (run_root / "execution-contract.json").write_text(json.dumps(execution_contract(run_id)))
            ledger = {
                "schemaVersion": 1, "runId": run_id, "findings": [{
                    "id": "QA-01", "sourceRole": "qa", "severity": "blocking",
                    "classification": "IMPLEMENTATION_DEVIATION", "failureStage": "implementation", "scope": "in-contract",
                    "basis": "acceptance-criterion", "regressionSurface": None,
                    "discoveredRound": 1, "discoveredPhase": "qa",
                    "acceptanceCriteria": ["AC-01"], "summary": "Broken flow", "evidence": "Observed failure",
                    "requiredOutcome": "Flow succeeds", "status": "open",
                }],
            }
            (run_root / "finding-ledger.json").write_text(json.dumps(ledger))
            checker = target / ".toscanini" / "bin" / "toscanini_contract.py"
            rejected = subprocess.run(["python3", str(checker), "--run-id", run_id, "--completion"], cwd=target, capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 1)
            self.assertIn("unresolved blocking finding: QA-01", rejected.stdout)

    def test_finding_without_contractual_basis_cannot_block(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target).returncode, 0)
            run_id = "run-scope-creep"
            run_root = target / ".toscanini" / "runtime" / "runs" / run_id
            run_root.mkdir(parents=True)
            (run_root / "execution-contract.json").write_text(json.dumps(execution_contract(run_id)))
            ledger = {
                "schemaVersion": 1, "runId": run_id, "findings": [{
                    "id": "QA-99", "sourceRole": "qa", "severity": "blocking",
                    "classification": "NEW_REQUIREMENT", "failureStage": "specification", "scope": "in-contract", "basis": "new-idea",
                    "regressionSurface": None, "discoveredRound": 2, "discoveredPhase": "remediation",
                    "acceptanceCriteria": ["AC-01"], "summary": "Adjacent improvement",
                    "evidence": "Unrelated behavior", "requiredOutcome": "Expand the feature", "status": "open",
                }],
            }
            (run_root / "finding-ledger.json").write_text(json.dumps(ledger))
            checker = target / ".toscanini" / "bin" / "toscanini_contract.py"
            rejected = subprocess.run(["python3", str(checker), "--run-id", run_id], cwd=target, capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 1)
            self.assertIn("blocking finding lacks an approved blocking basis: QA-99", rejected.stdout)

    def test_learning_cannot_be_applied_without_user_acceptance(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target).returncode, 0)
            run_id = "run-learning"
            run_root = target / ".toscanini" / "runtime" / "runs" / run_id
            run_root.mkdir(parents=True)
            (run_root / "execution-contract.json").write_text(json.dumps(execution_contract(run_id)))
            ledger = {
                "schemaVersion": 1, "runId": run_id, "findings": [{
                    "id": "QA-01", "sourceRole": "qa", "failureStage": "implementation",
                    "severity": "blocking", "classification": "IMPLEMENTATION_DEVIATION",
                    "scope": "in-contract", "basis": "acceptance-criterion", "regressionSurface": None,
                    "discoveredRound": 1, "discoveredPhase": "qa", "acceptanceCriteria": ["AC-01"],
                    "summary": "Broken flow", "evidence": "Observed failure",
                    "requiredOutcome": "Flow succeeds", "status": "resolved",
                    "learning": {"proposal": "Exercise the authored state", "target": "project-policy", "decision": "pending", "applied": True},
                }],
            }
            (run_root / "finding-ledger.json").write_text(json.dumps(ledger))
            checker = target / ".toscanini" / "bin" / "toscanini_contract.py"
            rejected = subprocess.run(["python3", str(checker), "--run-id", run_id], cwd=target, capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 1)
            self.assertIn("applied learning without user acceptance", rejected.stdout)

    def test_execution_report_explains_efficiency_and_learning_attribution(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target).returncode, 0)
            run_id = "run-report"
            run_root = target / ".toscanini" / "runtime" / "runs" / run_id
            run_root.mkdir(parents=True)
            (run_root / "execution-contract.json").write_text(json.dumps(execution_contract(run_id)))
            (run_root / "finding-ledger.json").write_text(json.dumps({
                "schemaVersion": 1, "runId": run_id, "findings": [{
                    "id": "QA-01", "sourceRole": "qa", "failureStage": "implementation",
                    "severity": "blocking", "classification": "IMPLEMENTATION_DEVIATION",
                    "scope": "in-contract", "basis": "acceptance-criterion", "regressionSurface": None,
                    "discoveredRound": 1, "discoveredPhase": "qa", "acceptanceCriteria": ["AC-01"],
                    "summary": "Broken flow", "evidence": "Observed failure",
                    "requiredOutcome": "Flow succeeds", "status": "resolved",
                    "learning": {"proposal": "Exercise representative authored content", "target": "qa-policy", "decision": "pending", "applied": False},
                }],
            }))
            gate = target / ".toscanini" / "bin" / "toscanini-gate.py"
            subprocess.run(["python3", str(gate), "--run-id", run_id, "--require-contract"], cwd=target, capture_output=True, text=True)
            report = (run_root / "execution-report.md").read_text()
            self.assertIn("Score: **", report)
            self.assertIn("detected by qa; attributed to implementation", report)
            self.assertIn("Proposed learnings — user approval required", report)
            self.assertIn("decision: `pending`, applied: `false`", report)

    def test_completion_infers_required_architecture_gate_from_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target).returncode, 0)
            run_id = "run-architecture"
            run_root = target / ".toscanini" / "runtime" / "runs" / run_id
            run_root.mkdir(parents=True)
            contract = execution_contract(run_id)
            contract["architecture"] = {"required": True, "status": "approved", "artifact": "docs/architecture.md"}
            (run_root / "execution-contract.json").write_text(json.dumps(contract))
            gate = target / ".toscanini" / "bin" / "toscanini-gate.py"
            rejected = subprocess.run(["python3", str(gate), "--run-id", run_id, "--require-contract"], cwd=target, capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 1)
            self.assertIn("missing gate: architecture-reviewer", rejected.stdout)
            self.assertTrue((run_root / "execution-report.md").exists())

    def test_completion_infers_required_specification_reviewer_from_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target).returncode, 0)
            run_id = "run-specification-review"
            run_root = target / ".toscanini" / "runtime" / "runs" / run_id
            run_root.mkdir(parents=True)
            contract = execution_contract(run_id)
            contract["specification"] = {
                "required": True, "status": "approved", "artifact": "specs/feature/spec.md",
                "clarifyStatus": "approved", "planStatus": "approved", "waiverReason": None,
            }
            (run_root / "execution-contract.json").write_text(json.dumps(contract))
            gate = target / ".toscanini" / "bin" / "toscanini-gate.py"
            rejected = subprocess.run(["python3", str(gate), "--run-id", run_id, "--require-contract"], cwd=target, capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 1)
            self.assertIn("missing gate: specification-reviewer", rejected.stdout)

    def test_completion_gate_enforces_specialist_budget(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target).returncode, 0)
            run_id = "run-budget"
            run_root = target / ".toscanini" / "runtime" / "runs" / run_id
            run_root.mkdir(parents=True)
            (run_root / "execution-contract.json").write_text(json.dumps(execution_contract(run_id, "fast")))
            reporter = target / ".toscanini" / "bin" / "toscanini-event.py"
            gate = target / ".toscanini" / "bin" / "toscanini-gate.py"
            for index in range(5):
                subprocess.run([
                    "python3", str(reporter), "--run-id", run_id, "--agent", f"specialist-{index}",
                    "--role", f"specialist-{index}", "--event", "started", "--state", "active",
                    "--round", "1", "--phase", "review", "--summary", "Review started",
                ], cwd=target, check=True)
            for role in ("code-reviewer", "test-analyst"):
                subprocess.run([
                    "python3", str(reporter), "--run-id", run_id, "--agent", role,
                    "--role", role, "--event", "started", "--state", "active", "--round", "1",
                    "--phase", "review", "--summary", f"{role} started",
                ], cwd=target, check=True)
                subprocess.run([
                    "python3", str(reporter), "--run-id", run_id, "--agent", role,
                    "--role", role, "--event", "completed", "--state", "completed",
                    "--verdict", "approve", "--context-mode", "fresh", "--round", "1",
                    "--phase", "review", "--finding-count", "0", "--summary", f"{role} approved",
                ], cwd=target, check=True)
            subprocess.run([
                "python3", str(reporter), "--run-id", run_id, "--agent", "qa", "--role", "qa",
                "--event", "started", "--state", "active", "--round", "1", "--phase", "qa",
                "--summary", "QA started",
            ], cwd=target, check=True)
            subprocess.run([
                "python3", str(reporter), "--run-id", run_id, "--agent", "qa", "--role", "qa",
                "--event", "completed", "--state", "completed", "--verdict", "pass",
                "--context-mode", "fresh", "--round", "1", "--phase", "qa", "--finding-count", "0",
                "--coverage", "QA-01", "--summary", "QA passed",
            ], cwd=target, check=True)
            subprocess.run([
                "python3", str(reporter), "--run-id", run_id, "--agent", "code-reviewer-final",
                "--role", "code-reviewer", "--event", "started", "--state", "active", "--round", "1",
                "--phase", "final-review", "--summary", "Final review started",
            ], cwd=target, check=True)
            subprocess.run([
                "python3", str(reporter), "--run-id", run_id, "--agent", "code-reviewer-final",
                "--role", "code-reviewer", "--event", "completed", "--state", "completed",
                "--verdict", "approve", "--context-mode", "fresh", "--round", "1",
                "--phase", "final-review", "--finding-count", "0", "--summary", "Final review approved",
            ], cwd=target, check=True)
            result = subprocess.run(["python3", str(gate), "--run-id", run_id, "--require-contract"], cwd=target, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            gate_findings = json.loads(result.stdout)["findings"]
            self.assertEqual(gate_findings, ["specialist budget exceeded: 9/8; replan required"])

    def test_directed_qa_cannot_replace_blocked_independent_qa(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.assertEqual(run(INSTALL, target).returncode, 0)
            run_id = "run-partial-qa"
            run_root = target / ".toscanini" / "runtime" / "runs" / run_id
            run_root.mkdir(parents=True)
            (run_root / "execution-contract.json").write_text(json.dumps(execution_contract(run_id)))
            reporter = target / ".toscanini" / "bin" / "toscanini-event.py"
            gate = target / ".toscanini" / "bin" / "toscanini-gate.py"
            for role in ("code-reviewer", "test-analyst"):
                subprocess.run(["python3", str(reporter), "--run-id", run_id, "--agent", role, "--role", role, "--event", "started", "--state", "active", "--round", "1", "--phase", "review", "--summary", "Started"], cwd=target, check=True)
                subprocess.run(["python3", str(reporter), "--run-id", run_id, "--agent", role, "--role", role, "--event", "completed", "--state", "completed", "--verdict", "approve", "--context-mode", "fresh", "--round", "1", "--phase", "review", "--finding-count", "0", "--summary", "Approved"], cwd=target, check=True)
            subprocess.run(["python3", str(reporter), "--run-id", run_id, "--agent", "qa-full", "--role", "qa", "--event", "started", "--state", "active", "--round", "1", "--phase", "qa", "--summary", "Full QA started"], cwd=target, check=True)
            subprocess.run(["python3", str(reporter), "--run-id", run_id, "--agent", "qa-full", "--role", "qa", "--event", "blocked", "--state", "blocked", "--verdict", "blocked", "--context-mode", "fresh", "--round", "1", "--phase", "qa", "--finding-count", "1", "--summary", "Browser unavailable"], cwd=target, check=True)
            subprocess.run(["python3", str(reporter), "--run-id", run_id, "--agent", "qa-directed", "--role", "qa", "--event", "started", "--state", "active", "--review-mode", "directed", "--round", "2", "--phase", "qa", "--summary", "API replay"], cwd=target, check=True)
            subprocess.run(["python3", str(reporter), "--run-id", run_id, "--agent", "qa-directed", "--role", "qa", "--event", "completed", "--state", "completed", "--verdict", "pass", "--context-mode", "inherited", "--review-mode", "directed", "--coverage", "QA-01", "--round", "2", "--phase", "qa", "--finding-count", "0", "--summary", "API replay passed"], cwd=target, check=True)
            result = subprocess.run(["python3", str(gate), "--run-id", run_id, "--require-contract"], cwd=target, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("incomplete gate: qa (blocked)", result.stdout)


if __name__ == "__main__":
    unittest.main()
