from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_workflow import ROOT, INSTALL, execution_contract, run


class ArchitectureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.assertEqual(run(INSTALL, self.root).returncode, 0)
        self.run_root = self.root / '.toscanini/runtime/runs/arch'
        self.run_root.mkdir(parents=True)
        (self.root / 'architecture.md').write_text('# Approved architecture\nINV-01: preserve persistence boundaries.\n')
        (self.root / 'conformance.md').write_text('# Conformance\nINV-01 matches the implementation and tests.\n')
        self.sha = hashlib.sha256((self.root / 'architecture.md').read_bytes()).hexdigest()
        self.contract = execution_contract('arch')
        self.contract['architecture'] = {
            'required': True, 'status': 'approved', 'artifact': 'architecture.md', 'sha256': self.sha,
            'frameworkAlignment': [{'repository': '.', 'framework': 'test fixture runtime', 'version': '1',
                                    'guidance': ['Fixture project guidance'], 'referenceAssessment': 'No external reference supplied',
                                    'status': 'aligned', 'ownerDecision': None}],
            'ownerApproval': {'approvedBy': 'product-owner', 'decision': 'Owner approved architecture and contract',
                              'artifactSha256': self.sha, 'scopeId': 'scope-1'},
        }
        self.history = []
        self.pair('architect', 'architecture', 'approved-with-conditions', artifact='architecture.md')

    def pair(self, role, phase, verdict, **extra):
        base = {'runId': 'arch', 'role': role, 'agent': role, 'phase': phase, 'round': 1,
                'reviewMode': 'independent', 'contextMode': 'fresh', 'scopeId': 'scope-1',
                'checkpointId': self.contract['implementationCheckpoint']['id'], 'architectureSha256': self.sha,
                'findingCount': 0, **extra}
        self.history.extend([{**base, 'event': 'started', 'state': 'active'},
                             {**base, 'event': 'completed', 'state': 'completed', 'verdict': verdict}])

    def implemented(self):
        self.pair('worker', 'implementation', 'pass')
        self.pair('code-reviewer', 'review', 'approve')
        self.pair('test-analyst', 'review', 'approve')
        self.pair('qa', 'qa', 'pass', coverage=['QA-01'])
        self.pair('architect', 'architecture-conformance', 'pass', artifact='conformance.md')

    def check(self, program='toscanini-gate.py', *args):
        (self.run_root / 'execution-contract.json').write_text(json.dumps(self.contract))
        (self.root / '.toscanini/runtime/events.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in self.history))
        result = subprocess.run(['python3', str(self.root / '.toscanini/bin' / program), '--run-id', 'arch', *args],
                                cwd=self.root, text=True, capture_output=True)
        self.assertIn(result.returncode, [0, 1], result.stderr)
        return json.loads(result.stdout)

    def test_owner_approval_allows_tasks_and_worker_without_conformance(self):
        self.contract['implementationCheckpoint'] = {'id': None, 'recordedAfterImplementation': False}
        for program, args in [('toscanini_contract.py', ()), ('toscanini-gate.py', ('--require-architecture',))]:
            result = self.check(program, *args)
            self.assertTrue(result['approved'], result)

    def test_architecture_approval_does_not_require_operational_readiness(self):
        self.contract['implementationCheckpoint']['recordedAfterImplementation'] = False
        del self.contract['readiness']
        self.assertTrue(self.check('toscanini-gate.py', '--require-architecture')['approved'])
        self.assertFalse(self.check('toscanini_contract.py')['approved'])

    def test_completed_feature_needs_no_document_reviewer_or_second_code_review(self):
        self.implemented()
        result = self.check('toscanini-gate.py', '--require-architecture', '--require-contract')
        self.assertTrue(result['approved'], result)

    def test_artifact_alone_makes_conformance_applicable(self):
        self.implemented()
        self.contract['architecture']['required'] = False
        self.history = self.history[:-2]
        result = self.check()
        self.assertFalse(result['approved'])
        self.assertIn('missing architecture-conformance evidence', result['findings'])

    def test_missing_or_stale_approval_author_and_artifact_fail(self):
        self.contract['implementationCheckpoint']['recordedAfterImplementation'] = False
        original = copy.deepcopy(self.contract)
        author = copy.deepcopy(self.history)
        for kind in ['owner', 'decision', 'scope', 'hash', 'author', 'blocked', 'artifact']:
            with self.subTest(kind=kind):
                self.contract = copy.deepcopy(original)
                self.history = copy.deepcopy(author)
                if kind == 'owner': self.contract['architecture']['ownerApproval']['approvedBy'] = None
                if kind == 'decision': self.contract['architecture']['ownerApproval']['decision'] = None
                if kind == 'scope': self.contract['validationScope']['scopeId'] = 'changed'
                if kind == 'hash': self.contract['architecture']['sha256'] = 'changed'
                if kind == 'author': self.history = []
                if kind == 'blocked': self.history[-1]['verdict'] = 'blocked'
                if kind == 'artifact': self.contract['architecture']['artifact'] = '../missing.md'
                self.assertFalse(self.check('toscanini-gate.py', '--require-architecture')['approved'])
        self.contract, self.history = original, author
        (self.root / 'architecture.md').write_text('Unapproved change')
        self.assertFalse(self.check('toscanini-gate.py', '--require-architecture')['approved'])

    def test_conformance_rejects_stale_missing_or_premature_evidence(self):
        self.implemented()
        original = copy.deepcopy(self.history)
        for kind in ['checkpoint', 'hash', 'scope', 'missing-start', 'missing-file', 'failed', 'before-qa', 'second-full']:
            with self.subTest(kind=kind):
                self.history = copy.deepcopy(original)
                if kind == 'checkpoint': self.history[-1]['checkpointId'] = 'stale'
                if kind == 'hash': self.history[-1]['architectureSha256'] = 'stale'
                if kind == 'scope': self.history[-1]['scopeId'] = 'stale'
                if kind == 'missing-start': del self.history[-2]
                if kind == 'missing-file': self.history[-1]['artifact'] = 'missing.md'
                if kind == 'failed': self.history[-1]['verdict'] = 'fail'
                if kind == 'before-qa': self.history[-4:] = self.history[-2:] + self.history[-4:-2]
                if kind == 'second-full': self.pair('architect', 'architecture-conformance', 'pass', artifact='conformance.md')
                self.assertFalse(self.check()['approved'])

    def test_architecture_correction_uses_directed_revalidation(self):
        self.implemented()
        self.history[-1]['verdict'] = 'fail'
        self.contract['implementationCheckpoint']['id'] = 'checkpoint-2'
        delta = {'reviewMode': 'directed', 'contextMode': 'inherited', 'findingIds': ['ARCH-01'],
                 'revalidationReason': 'Correction to approved persistence boundary INV-01'}
        self.pair('worker', 'remediation', 'pass', **delta)
        self.pair('code-reviewer', 'remediation', 'approve', **delta)
        self.pair('test-analyst', 'remediation', 'approve', **delta)
        self.pair('qa', 'qa', 'pass', coverage=['QA-01'], **delta)
        self.pair('architect', 'architecture-conformance', 'pass', artifact='conformance.md', **delta)
        ledger = {'runId': 'arch', 'findings': [{
            'id': 'ARCH-01', 'sourceRole': 'architect', 'failureStage': 'implementation',
            'classification': 'IMPLEMENTATION_DEVIATION', 'scope': 'in-contract', 'severity': 'blocking',
            'basis': 'invariant', 'invariants': ['INV-01'], 'acceptanceCriteria': [],
            'discoveredRound': 1, 'discoveredPhase': 'architecture-conformance',
            'summary': 'Persistence boundary deviation', 'evidence': 'Query placed outside approved owner',
            'requiredOutcome': 'Use approved query owner', 'status': 'resolved',
        }]}
        (self.run_root / 'finding-ledger.json').write_text(json.dumps(ledger))
        result = self.check()
        self.assertTrue(result['approved'], result)
        self.history[-1]['findingIds'] = ['UNKNOWN']
        self.assertFalse(self.check()['approved'])
        self.history[-1]['findingIds'] = ['ARCH-01']
        del self.history[-1]['revalidationReason']
        self.assertFalse(self.check()['approved'])

    def test_failed_executed_qa_can_close_findings_without_another_full_pass(self):
        self.implemented()
        self.history = self.history[:-2]
        self.history[-1].update(verdict='fail', findingCount=1)
        self.contract['implementationCheckpoint']['id'] = 'checkpoint-2'
        delta = {'reviewMode': 'directed', 'contextMode': 'inherited', 'findingIds': ['QA-01'],
                 'revalidationReason': 'Correct persistence outcome required by AC-01'}
        self.pair('worker', 'remediation', 'pass', **delta)
        self.pair('code-reviewer', 'remediation', 'approve', **delta)
        self.pair('test-analyst', 'remediation', 'approve', **delta)
        self.pair('qa', 'qa', 'pass', coverage=['QA-01'], **delta)
        self.pair('architect', 'architecture-conformance', 'pass', artifact='conformance.md')
        ledger = {'runId': 'arch', 'findings': [{
            'id': 'QA-01', 'sourceRole': 'qa', 'failureStage': 'implementation',
            'classification': 'IMPLEMENTATION_DEVIATION', 'scope': 'in-contract', 'severity': 'blocking',
            'basis': 'acceptance-criterion', 'acceptanceCriteria': ['AC-01'], 'invariants': [],
            'discoveredRound': 1, 'discoveredPhase': 'qa', 'summary': 'Persistence outcome failed',
            'evidence': 'Executed QA scenario', 'requiredOutcome': 'Persist accepted behavior', 'status': 'resolved',
        }]}
        (self.run_root / 'finding-ledger.json').write_text(json.dumps(ledger))
        result = self.check()
        self.assertTrue(result['approved'], result)

    def test_new_reporter_rejects_retired_role_and_preserves_history(self):
        path = self.root / '.toscanini/runtime/events.jsonl'
        path.write_text(json.dumps({'runId': 'old', 'role': 'architecture-reviewer', 'event': 'completed'}) + '\n')
        before = path.read_bytes()
        result = subprocess.run(['python3', str(self.root / '.toscanini/bin/toscanini-event.py'),
                                 '--agent', 'architecture-reviewer', '--event', 'started', '--state', 'active',
                                 '--summary', 'Retired role'], cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(path.read_bytes(), before)
        self.implemented()
        self.history.insert(0, {'runId': 'arch', 'role': 'architecture-reviewer', 'event': 'completed'})
        self.assertTrue(self.check()['approved'])

    def test_framework_alignment_blocks_silent_reference_adoption(self):
        self.contract['implementationCheckpoint']['recordedAfterImplementation'] = False
        assessment = self.contract['architecture']['frameworkAlignment'][0]
        for change in [dict(status='unresolved'), dict(status='approved-deviation', ownerDecision=None),
                       dict(guidance=[]), dict(referenceAssessment=''), dict(version='')]:
            with self.subTest(change=change):
                self.contract['architecture']['frameworkAlignment'] = [{**assessment, **change}]
                result = self.check('toscanini-gate.py', '--require-architecture')
                self.assertFalse(result['approved'], result)
        self.contract['architecture']['frameworkAlignment'] = []
        self.assertFalse(self.check('toscanini-gate.py', '--require-architecture')['approved'])
        self.contract['architecture']['frameworkAlignment'] = [{**assessment, 'status': 'approved-deviation',
            'ownerDecision': 'Owner explicitly selected reference layering after comparing the framework-native option'}]
        self.assertTrue(self.check('toscanini-gate.py', '--require-architecture')['approved'])

    def test_each_target_framework_requires_a_resolved_assessment(self):
        self.implemented()
        assessment = self.contract['architecture']['frameworkAlignment'][0]
        self.contract['architecture']['frameworkAlignment'].append({**assessment, 'repository': 'mobile',
            'framework': 'Flutter', 'status': 'unresolved'})
        self.assertFalse(self.check()['approved'])

    def test_schema_two_budgets_remain_readable(self):
        self.implemented()
        self.contract['schemaVersion'] = 2
        del self.contract['architecture']['frameworkAlignment']
        self.contract['budgets']['specialistRuns'] = 15
        self.assertTrue(self.check()['approved'])

    def test_update_removes_retired_agent_and_archives_customization(self):
        for customized in [False, True]:
            with self.subTest(customized=customized), tempfile.TemporaryDirectory() as folder:
                target = Path(folder)
                self.assertEqual(run(INSTALL, target, '--laravel').returncode, 0)
                retired = target / '.codex/agents/architecture-reviewer.toml'
                retired.write_text('old managed reviewer')
                manifest_path = target / '.toscanini/manifest.json'
                manifest = json.loads(manifest_path.read_text())
                manifest['configuration']['agents'].append('architecture-reviewer')
                manifest['files'][str(retired.relative_to(target))] = {'sha256': hashlib.sha256(retired.read_bytes()).hexdigest()}
                manifest_path.write_text(json.dumps(manifest))
                if customized: retired.write_text('customized retired reviewer')
                policy = target / 'AGENTS.md'
                policy.write_text(policy.read_text().replace('Architect', 'Architecture Reviewer'))
                updated = run(ROOT / 'scripts/update-project', target)
                self.assertEqual(updated.returncode, 0, updated.stdout + updated.stderr)
                self.assertFalse(retired.exists())
                state = json.loads(manifest_path.read_text())
                self.assertNotIn('architecture-reviewer', state['configuration']['agents'])
                self.assertNotIn(str(retired.relative_to(target)), state['files'])
                self.assertIn('laravel', state['configuration']['adapters'])
                self.assertNotIn('Architecture Reviewer', policy.read_text())
                archives = list((target / '.toscanini/legacy').glob('*architecture-reviewer.toml'))
                self.assertEqual(len(archives), int(customized))
                if customized: self.assertEqual(archives[0].read_text(), 'customized retired reviewer')
                self.assertEqual(run(ROOT / 'scripts/update-project', target).returncode, 0)
