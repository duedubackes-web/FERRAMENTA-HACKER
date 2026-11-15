import base64
import copy
import json
import io
import zipfile
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from app_service import Application
from review_evolution import compare_reviews
from review_rules import build_review
from trivy_report import parse_json as trivy
from zap_report import parse_json as zap


def review(raw, producer='trivy'):
    parsed = (trivy if producer == 'trivy' else zap)(json.dumps(raw).encode(), 'fixture')
    return build_review(**{producer: parsed})


class EvolutionTests(unittest.TestCase):
    def setUp(self):
        self.trivy = json.loads((ROOT/'tests/fixtures/trivy-synthetic.json').read_bytes())
        self.zap = json.loads((ROOT/'tests/fixtures/zap-synthetic.json').read_bytes())

    def test_reordering_and_new_hash_preserve_declared_observations(self):
        before = review(self.trivy)
        self.trivy['Results'][0]['Vulnerabilities'].reverse()
        after = review(self.trivy)
        result = compare_reviews(before, after)
        self.assertEqual(result['summary']['unchanged'], 2)
        self.assertNotEqual(before['review_id'], after['review_id'])
        refs = result['observations'][0]
        self.assertNotEqual(refs['before'][0]['references'][0]['artifact_sha256'], refs['after'][0]['references'][0]['artifact_sha256'])

    def test_severity_change_is_a_changed_record_not_a_new_identity(self):
        before = review(self.trivy)
        self.trivy['Results'][0]['Vulnerabilities'][0]['Severity'] = 'LOW'
        result = compare_reviews(before, review(self.trivy))
        self.assertEqual(result['summary']['changed'], 1)
        changed = next(row for row in result['observations'] if row['status'] == 'changed')
        self.assertNotEqual(changed['before'][0]['rule_id'], changed['after'][0]['rule_id'])

    def test_absence_is_not_resolution_and_package_version_is_part_of_key(self):
        before = review(self.trivy)
        self.trivy['Results'][0]['Vulnerabilities'][0]['InstalledVersion'] = 'new-version'
        result = compare_reviews(before, review(self.trivy))
        self.assertEqual(result['summary']['introduced'], 1)
        self.assertEqual(result['summary']['not-observed'], 1)
        self.assertNotIn('resolved', result['summary'])

    def test_duplicate_keys_remain_ambiguous(self):
        before = review(self.trivy)
        vulnerabilities = self.trivy['Results'][0]['Vulnerabilities']
        vulnerabilities.append(copy.deepcopy(vulnerabilities[0]))
        result = compare_reviews(before, review(self.trivy))
        self.assertEqual(result['summary']['ambiguous'], 1)
        row = next(r for r in result['observations'] if r['status'] == 'ambiguous')
        self.assertEqual(len(row['after']), 2)

    def test_missing_identity_and_coverage_tasks_are_not_guessed(self):
        self.trivy['ArtifactName'] = None
        report = review(self.trivy)
        result = compare_reviews(report, report)
        self.assertEqual(result['summary']['unmatched'], 4)
        self.assertEqual(result['summary']['unchanged'], 0)
        report = review({'SchemaVersion': 2})
        self.assertEqual(compare_reviews(report, report)['summary']['unmatched'], 2)

    def test_zap_confidence_changes_and_instance_order(self):
        before = review(self.zap, 'zap')
        alert = self.zap['site'][0]['alerts'][0]
        alert['confidence'] = '0'
        result = compare_reviews(before, review(self.zap, 'zap'))
        self.assertEqual(result['summary']['changed'], 1)
        alert['instances'].append(copy.deepcopy(alert['instances'][0]))
        before = review(self.zap, 'zap')
        alert['instances'].reverse()
        self.assertEqual(compare_reviews(before, review(self.zap, 'zap'))['summary']['changed'], 0)

    def test_omitted_site_components_prevent_zap_pairing(self):
        self.zap['site'][0]['@name'] = 'https://example.test/?private=not-a-key'
        report = review(self.zap, 'zap')
        result = compare_reviews(report, report)
        self.assertEqual(result['summary']['unchanged'], 0)
        self.assertGreater(result['summary']['unmatched'], 0)

    def test_versions_block_comparison_without_inventing_absences(self):
        before = review(self.trivy)
        for part in ('rules', 'adapter'):
            after = copy.deepcopy(before)
            if part == 'rules': after['ruleset']['version'] = 'future'
            else: after['inputs']['trivy']['analysis_run']['adapter_version'] = 'future'
            result = compare_reviews(before, after)
            self.assertEqual(result['status'], 'blocked')
            self.assertEqual(result['observations'], [])

    def test_deterministic_without_mutation_and_reference_tampering_rejected(self):
        before, after = review(self.trivy), review(self.trivy)
        saved = copy.deepcopy(before)
        self.assertEqual(compare_reviews(before, after), compare_reviews(before, after))
        self.assertEqual(before, saved)
        after['items'][0]['references'][0]['artifact_sha256'] = '0'*64
        with self.assertRaises(ValueError): compare_reviews(before, after)
        after = copy.deepcopy(before)
        after['items'].append(copy.deepcopy(after['items'][0]))
        with self.assertRaises(ValueError): compare_reviews(before, after)

    def test_project_scoping_chat_and_export_history(self):
        with tempfile.TemporaryDirectory() as folder:
            app = Application(Path(folder)/'app.sqlite3')
            project = app.demo()['id']
            first = app.snapshot(project)['review']['id']
            second = app.review(project)['id']
            result = app.compare(project, first, second)
            self.assertEqual(result['comparison']['summary']['unchanged'], 4)
            self.assertEqual(len(app.snapshot(project)['reviews']), 2)
            self.assertEqual(app.chat(project, 'O que mudou na evolução?')['citations'][0]['kind'], 'review-comparison')
            other = app.demo()['id']
            with self.assertRaises(ValueError): app.compare(other, first, second)
            with self.assertRaises(ValueError): app.compare(project, first, first)
            self.assertEqual(Application(Path(folder)/'app.sqlite3').compare(project, first, second), result)
            with zipfile.ZipFile(io.BytesIO(app.export(project, True))) as archive:
                self.assertEqual(json.loads(archive.read('review-evolution.json')), result)
                self.assertIn('review-baseline.json', archive.namelist())
                self.assertIn('baseline-originals/trivy.json', archive.namelist())

    def test_malformed_metadata_and_instances_raise_controlled_errors(self):
        original = review(self.zap, 'zap')
        for kind in ('rules', 'producer', 'adapter', 'instances'):
            report = copy.deepcopy(original)
            if kind == 'rules': report['ruleset'] = {}
            elif kind == 'producer': report['inputs']['zap']['producer'] = None
            elif kind == 'adapter': report['inputs']['zap']['analysis_run']['adapter_version'] = None
            else: report['items'][0]['facts']['instances'] = [None]
            with self.subTest(kind=kind), self.assertRaises(ValueError): compare_reviews(original, report)

    def test_cli_output_overwrite_and_blocked_status(self):
        with tempfile.TemporaryDirectory() as folder:
            before, after, output = [Path(folder)/name for name in ('before.json','after.json','comparison.json')]
            report = review(self.trivy)
            before.write_text(json.dumps(report)); after.write_text(json.dumps(report))
            command = [sys.executable, str(ROOT/'scripts/workbench.py'),'compare-reviews',str(before),str(after),'--output',str(output)]
            result = subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(output.read_text())['summary']['unchanged'],2)
            original = output.read_bytes()
            self.assertEqual(subprocess.run(command,capture_output=True).returncode,2)
            self.assertEqual(output.read_bytes(), original)
            output.unlink();report['ruleset']['version']='future';after.write_text(json.dumps(report))
            self.assertEqual(subprocess.run(command,capture_output=True).returncode,1)
