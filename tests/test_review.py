import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import trivy_report
from nmap_report import import_report as import_nmap
from nmap_compare import compare_reports
from review_rules import build_review
from review_html import render_html

TRIVY = ROOT/'tests/fixtures/trivy-synthetic.json'
BEFORE = ROOT/'tests/fixtures/nmap-synthetic.xml'
AFTER = ROOT/'tests/fixtures/nmap-synthetic-after.xml'


class TrivyImportTests(unittest.TestCase):
    def test_import_preserves_producer_fields_provenance_and_undeclared_fix(self):
        report = trivy_report.import_report(TRIVY)
        self.assertEqual(report['artifact']['sha256'], hashlib.sha256(TRIVY.read_bytes()).hexdigest())
        self.assertEqual(report['findings'][0]['json_pointer'], '/Results/0/Vulnerabilities/0')
        self.assertEqual(report['findings'][0]['producer_fields']['FixedVersion'], '1.1')
        self.assertIsNone(report['findings'][1]['producer_fields']['FixedVersion'])
        self.assertEqual(report['findings'][1]['severity_normalized'], 'UNKNOWN')
        self.assertFalse(report['analysis_run']['target_executed'])

    def test_missing_null_and_empty_results_remain_distinct(self):
        for raw, expected in [({'SchemaVersion': 2}, 'missing'), ({'SchemaVersion': 2, 'Results': None}, 'null'), ({'SchemaVersion': 2, 'Results': []}, 'array')]:
            report = trivy_report.parse_json(json.dumps(raw).encode(), 'fixture')
            self.assertEqual(report['coverage']['results_state'], expected)
            self.assertEqual(report['coverage']['scan_completion'], 'not-established')
            self.assertEqual(build_review(trivy=report)['items'][0]['rule_id'], 'TRIVY-COVERAGE')

    def test_secrets_and_other_categories_are_counted_without_exporting_contents(self):
        raw = {'SchemaVersion': 2, 'Results': [{'Secrets': [{'Match': 'SYNTHETIC-LOCAL-ONLY-CONTENT'}], 'Misconfigurations': [{'private': 'SYNTHETIC-LOCAL-ONLY-CONTENT'}]}]}
        report = trivy_report.parse_json(json.dumps(raw).encode(), 'fixture')
        self.assertNotIn('SYNTHETIC-LOCAL-ONLY-CONTENT', json.dumps(report))
        self.assertEqual(report['coverage']['results'][0]['uninterpreted_categories']['Secrets']['count'], 1)
        self.assertEqual(report['coverage']['results'][0]['vulnerabilities_state'], 'missing')

    def test_rejects_wrong_shapes_versions_duplicates_and_nonstandard_constants(self):
        invalid = [b'[]', b'{', b'{"SchemaVersion":3}', b'{"SchemaVersion":true}', b'{"SchemaVersion":2,"SchemaVersion":2}',
                   b'{"SchemaVersion":2,"unused":NaN}', b'{"SchemaVersion":2,"Trivy":[]}', b'{"SchemaVersion":2,"Results":{}}',
                   b'{"SchemaVersion":2,"Results":[null]}', b'{"SchemaVersion":2,"Results":[{"Vulnerabilities":{}}]}',
                   b'{"SchemaVersion":2,"Results":[{"Vulnerabilities":[{"Severity":8}]}]}']
        for data in invalid:
            with self.subTest(data=data), self.assertRaises(ValueError):
                trivy_report.parse_json(data, 'fixture')

    def test_unknown_severity_is_preserved_with_warning(self):
        raw = {'SchemaVersion': 2, 'Results': [{'Vulnerabilities': [{'Severity': 'new-producer-value'}]}]}
        report = trivy_report.parse_json(json.dumps(raw).encode(), 'fixture')
        self.assertIsNone(report['findings'][0]['severity_normalized'])
        self.assertEqual(report['findings'][0]['producer_fields']['Severity'], 'new-producer-value')
        self.assertEqual(len(report['warnings']), 1)

    def test_input_budget_is_enforced(self):
        with patch.object(trivy_report, 'MAX_BYTES', 8), self.assertRaises(ValueError):
            trivy_report.parse_json(b'{"SchemaVersion":2}', 'fixture')


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.comparison = compare_reports(import_nmap(BEFORE), import_nmap(AFTER))
        self.trivy = trivy_report.import_report(TRIVY)

    def test_combined_review_explains_priorities_and_preserves_severity(self):
        report = build_review(self.comparison, self.trivy)
        rules = [i['rule_id'] for i in report['items']]
        self.assertEqual(report['summary']['items'], 6)
        self.assertEqual(rules[0], 'EVIDENCE-SCOPE')
        high = next(i for i in report['items'] if i['rule_id'] == 'TRIVY-HIGH')
        self.assertEqual(high['priority'], 'review-first')
        self.assertEqual(high['facts']['producer_fields']['Severity'], 'HIGH')
        self.assertEqual(high['references'][0]['json_pointer'], '/Results/0/Vulnerabilities/0')
        self.assertNotIn('host', high['facts'])
        self.assertEqual(report['ruleset']['model_calls'], 0)
        self.assertFalse(report['target_executed'])

    def test_missing_port_is_context_and_unknown_state_does_not_trigger_open_rule(self):
        after = import_nmap(BEFORE)
        after['hosts'][0]['ports'].pop()
        comparison = compare_reports(import_nmap(BEFORE), after)
        report = build_review(comparison)
        self.assertEqual(report['items'][0]['rule_id'], 'NMAP-ABSENCE')
        self.assertEqual(report['items'][0]['priority'], 'context')
        self.assertIsNone(report['items'][0]['facts']['after'])
        comparison['changes'][0]['kind'] = 'state_evidence_changed'
        comparison['changes'][0]['after'] = 'open'
        self.assertNotIn('NMAP-OPEN-STATE', [i['rule_id'] for i in build_review(comparison)['items']])

    def test_identity_ambiguity_and_missing_completion_create_evidence_tasks(self):
        before, after = import_nmap(BEFORE), import_nmap(AFTER)
        before['hosts'].append(copy.deepcopy(before['hosts'][0]))
        after['producer']['finished'] = None
        result = build_review(compare_reports(before, after))
        self.assertIn('EVIDENCE-IDENTITY', [i['rule_id'] for i in result['items']])
        self.assertIn('EVIDENCE-COMPLETION', [i['rule_id'] for i in result['items']])
        self.assertNotIn('NMAP-OPEN-STATE', [i['rule_id'] for i in result['items']])

    def test_two_observations_of_same_endpoint_keep_distinct_item_ids(self):
        self.comparison['changes'][0]['kind'] = 'state_evidence_changed'
        self.comparison['changes'][1]['kind'] = 'service_evidence_changed'
        self.comparison['changes'][1]['references'] = self.comparison['changes'][0]['references']
        report = build_review(self.comparison)
        self.assertEqual(len({i['id'] for i in report['items']}), len(report['items']))

    def test_review_is_deterministic_does_not_mutate_inputs_or_share_rule_steps(self):
        original = copy.deepcopy(self.trivy)
        first = build_review(trivy=self.trivy)
        second = build_review(trivy=self.trivy)
        self.assertEqual(first, second)
        self.assertEqual(self.trivy, original)
        first['items'][0]['next_steps'].append('LOCAL EDIT')
        self.assertNotIn('LOCAL EDIT', build_review(trivy=self.trivy)['items'][0]['next_steps'])
        self.trivy['analysis_run']['adapter_version'] = '2'
        self.assertNotEqual(build_review(trivy=self.trivy)['review_id'], second['review_id'])

    def test_empty_explicit_vulnerability_array_is_not_a_security_attestation(self):
        raw = b'{"SchemaVersion":2,"Results":[{"Vulnerabilities":[]}]}'
        report = build_review(trivy=trivy_report.parse_json(raw, 'fixture'))
        self.assertEqual(report['items'], [])
        self.assertIn('não comprova segurança', render_html(report))

    def test_html_escapes_producer_text_and_does_not_make_input_urls_clickable(self):
        attack = '<img src="https://example.test/x" onerror="alert(1)">'
        self.trivy['findings'][0]['producer_fields']['Title'] = attack
        self.trivy['findings'][0]['producer_fields']['PrimaryURL'] = 'javascript:alert(1)'
        page = render_html(build_review(trivy=self.trivy))
        self.assertNotIn('<img', page)
        self.assertNotIn('<script', page)
        self.assertNotIn('href="javascript:', page)
        self.assertIn('&lt;img', page)

    def test_cli_creates_outputs_and_refuses_existing_file_before_partial_creation(self):
        with tempfile.TemporaryDirectory() as folder:
            data, html = Path(folder)/'review.json', Path(folder)/'review.html'
            cmd = [sys.executable, str(ROOT/'scripts/workbench.py'), 'review', '--before', str(BEFORE), '--after', str(AFTER), '--trivy', str(TRIVY), '--output', str(data), '--html', str(html)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(data.read_text())
            self.assertEqual(report['summary']['items'], 6)
            self.assertIn(report['review_id'], html.read_text())
            original = html.read_bytes()
            data.unlink()
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(data.exists())
            self.assertEqual(html.read_bytes(), original)

    def test_cli_rejects_unpaired_or_missing_inputs_and_imports_trivy(self):
        command = [sys.executable, str(ROOT/'scripts/workbench.py')]
        for args in [['review'], ['review', '--before', str(BEFORE)]]:
            result = subprocess.run(command+args, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
        imported = subprocess.run(command+['import-trivy', str(TRIVY)], capture_output=True, text=True)
        self.assertEqual(imported.returncode, 0, imported.stderr)
        self.assertEqual(json.loads(imported.stdout)['coverage']['imported_records'], 2)


if __name__ == '__main__':
    unittest.main()
