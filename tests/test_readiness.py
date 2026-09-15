from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_workflow import ROOT, INSTALL, execution_contract, run


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'package.json').write_text(json.dumps({'scripts': {'verify': 'touch verified'}}))
        self.assertEqual(run(INSTALL, self.root).returncode, 0)
        self.path = self.root / '.toscanini/runtime/runs/ready/execution-contract.json'
        self.path.parent.mkdir(parents=True)
        self.contract = execution_contract('ready')

    def save(self):
        self.path.write_text(json.dumps(self.contract))

    def worker_start(self):
        self.save()
        return subprocess.run(['python3', str(self.root / '.toscanini/bin/toscanini-event.py'),
                               '--run-id', 'ready', '--agent', 'worker', '--event', 'started',
                               '--state', 'active', '--summary', 'Begin implementation'],
                              cwd=self.root, capture_output=True, text=True)

    def test_private_dependency_access_blocks_verification_and_worker_until_resolved(self):
        check = {'category': 'access', 'name': 'Licensed SDK registry', 'status': 'pending',
                 'evidence': 'Actual dependency resolution requires authentication'}
        self.contract['readiness']['checks'].append(check)
        self.save()
        self.assertNotEqual(run(ROOT / 'scripts/verify', self.root, '--run-id', 'ready').returncode, 0)
        self.assertFalse((self.root / 'verified').exists())
        self.assertNotEqual(self.worker_start().returncode, 0)
        self.assertFalse((self.root / '.toscanini/runtime/events.jsonl').exists())
        check.update(status='verified', evidence='Authenticated registry resolution succeeded in Worker environment')
        self.assertEqual(self.worker_start().returncode, 0)
        self.assertEqual(run(ROOT / 'scripts/verify', self.root, '--run-id', 'ready').returncode, 0)
        self.assertTrue((self.root / 'verified').exists())

    def test_readiness_requires_inventory_evidence_environment_and_current_scope(self):
        original = json.loads(json.dumps(self.contract))
        for kind in ['missing', 'category', 'evidence', 'environment', 'stale', 'permission', 'installation']:
            with self.subTest(kind=kind):
                self.contract = json.loads(json.dumps(original))
                assessment = self.contract['readiness']
                if kind == 'missing': del self.contract['readiness']
                if kind == 'category': assessment['checks'].pop()
                if kind == 'evidence': assessment['checks'][0]['evidence'] = ''
                if kind == 'environment': assessment['environment'] = ''
                if kind == 'stale': assessment['scopeId'] = 'previous-scope'
                if kind == 'permission': assessment['checks'][-1]['status'] = 'pending'
                if kind == 'installation': assessment['checks'][1]['status'] = 'blocked'
                self.assertNotEqual(self.worker_start().returncode, 0)

    def test_legacy_contract_remains_readable_without_invented_readiness(self):
        self.contract['schemaVersion'] = 2
        del self.contract['readiness']
        self.save()
        result = subprocess.run(['python3', str(self.root / '.toscanini/bin/toscanini_contract.py'),
                                 '--run-id', 'ready'], cwd=self.root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_feature_scope_rejects_unrelated_findings_even_with_a_valid_criterion(self):
        self.save()
        ledger_path = self.path.with_name('finding-ledger.json')
        for role in ['qa', 'code-reviewer', 'test-analyst']:
            item = {'id': 'F-01', 'sourceRole': role, 'failureStage': 'implementation',
                    'classification': 'IMPLEMENTATION_DEVIATION', 'scope': 'in-contract', 'severity': 'blocking',
                    'basis': 'acceptance-criterion', 'acceptanceCriteria': ['AC-01'], 'invariants': [],
                    'discoveredRound': 1, 'discoveredPhase': 'review', 'summary': 'Feature behavior fails',
                    'evidence': 'Observed failure', 'requiredOutcome': 'Accepted behavior', 'status': 'resolved',
                    'qaScenarios': ['QA-01'], 'changedPaths': ['src/feature.py'],
                    'changeEvidence': 'Changed feature handler drops the value required by AC-01'}
            for kind in ['valid', 'unrelated', 'no-cause', 'incidental']:
                with self.subTest(role=role, kind=kind):
                    finding = dict(item)
                    if kind == 'unrelated':
                        finding['qaScenarios' if role == 'qa' else 'changedPaths'] = ['unrelated-screen-or-file']
                    if kind == 'no-cause': finding['changeEvidence'] = ''
                    if kind == 'incidental':
                        finding.update(scope='follow-up', severity='non-blocking', status='deferred',
                                       changedPaths=['unrelated.py'], qaScenarios=['QA-UNRELATED'], changeEvidence='')
                    ledger_path.write_text(json.dumps({'runId': 'ready', 'findings': [finding]}))
                    result = subprocess.run(['python3', str(self.root / '.toscanini/bin/toscanini_contract.py'),
                                             '--run-id', 'ready'], cwd=self.root, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0 if kind in ['valid', 'incidental'] else 1, result.stdout + result.stderr)

    def test_review_scope_cannot_be_a_repository_wide_pattern(self):
        for paths in [[], ['**/*'], ['.'], ['/tmp/other.py'], ['../other.py']]:
            with self.subTest(paths=paths):
                self.contract['validationScope']['codeReviewPaths'] = paths
                self.save()
                result = subprocess.run(['python3', str(self.root / '.toscanini/bin/toscanini_contract.py'),
                                         '--run-id', 'ready'], cwd=self.root, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
