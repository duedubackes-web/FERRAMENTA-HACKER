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
import zap_report
from review_rules import build_review
from review_html import render_html

FIXTURE = ROOT/'tests/fixtures/zap-synthetic.json'


class ZapImportTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(FIXTURE.read_text())

    def parse(self):
        return zap_report.parse_json(json.dumps(self.raw).encode(), 'fixture')

    def test_risk_confidence_and_provenance_are_separate(self):
        report = zap_report.import_report(FIXTURE)
        first = report['findings'][0]
        self.assertEqual(report['artifact']['sha256'], hashlib.sha256(FIXTURE.read_bytes()).hexdigest())
        self.assertEqual(first['risk_normalized'], 3)
        self.assertEqual(first['confidence_normalized'], 2)
        self.assertEqual(first['confidence_label'], 'Medium')
        self.assertEqual(first['json_pointer'], '/site/0/alerts/0')
        self.assertEqual(first['instances'][0]['json_pointer'], '/site/0/alerts/0/instances/0')
        self.assertFalse(report['analysis_run']['target_executed'])

    def test_http_content_and_structural_url_credentials_are_not_exported(self):
        site = self.raw['site'][0]
        site['@name'] = 'https://user:USERINFO-ONLY@example.test?token=QUERY-ONLY#FRAGMENT-ONLY'
        instance = site['alerts'][0]['instances'][0]
        instance.update({'uri': 'https://u:USERINFO-ONLY@example.test/a?x=QUERY-ONLY#FRAGMENT-ONLY', 'attack': 'ATTACK-ONLY', 'evidence': 'EVIDENCE-ONLY', 'request-header': 'REQUEST-ONLY', 'response-body': 'RESPONSE-ONLY'})
        report = self.parse()
        output = json.dumps(report)
        for value in ['USERINFO-ONLY', 'QUERY-ONLY', 'FRAGMENT-ONLY', 'ATTACK-ONLY', 'EVIDENCE-ONLY', 'REQUEST-ONLY', 'RESPONSE-ONLY']:
            self.assertNotIn(value, output)
        self.assertEqual(report['findings'][0]['instances'][0]['uri_display']['uri'], 'https://example.test/a')
        self.assertEqual(report['coverage']['sites'][0]['site_display']['uri'], 'https://example.test')

    def test_missing_null_and_empty_sites_are_retained(self):
        for value, expected in [('missing', 'missing'), (None, 'null'), ([], 'array')]:
            self.raw = {'@version': 'fixture'}
            if value != 'missing':
                self.raw['site'] = value
            report = self.parse()
            self.assertEqual(report['coverage']['sites_state'], expected)
            self.assertEqual(build_review(zap=report)['items'][0]['rule_id'], 'ZAP-COVERAGE')

    def test_unknown_codes_are_not_guessed_from_risk_description(self):
        self.raw['site'][0]['alerts'][0].update({'riskcode': 'future-code', 'confidence': 'future-confidence', 'riskdesc': 'High (Confirmed)'})
        report = self.parse()
        self.assertIsNone(report['findings'][0]['risk_normalized'])
        self.assertIsNone(report['findings'][0]['confidence_normalized'])
        self.assertIn('ZAP-CLASSIFICATION', [i['rule_id'] for i in build_review(zap=report)['items']])

    def test_numeric_codes_and_ipv6_uri_are_supported(self):
        self.raw['site'][0]['alerts'][0].update({'riskcode': 3, 'confidence': 4})
        self.raw['site'][0]['alerts'][0]['instances'][0]['uri'] = 'https://user:pass@[2001:db8::1]:8443/path?q=omitted'
        first = self.parse()['findings'][0]
        self.assertEqual(first['confidence_label'], 'Confirmed')
        self.assertEqual(first['instances'][0]['uri_display']['uri'], 'https://[2001:db8::1]:8443/path')

    def test_invalid_or_non_http_uri_is_omitted_with_warning(self):
        for uri in ['javascript:untrusted()', 'file:///local-data', 'https://[broken', 'https://example.test:99999/path', '/relative']:
            with self.subTest(uri=uri):
                self.raw['site'][0]['alerts'][0]['instances'][0]['uri'] = uri
                report = self.parse()
                self.assertIsNone(report['findings'][0]['instances'][0]['uri_display']['uri'])
                self.assertTrue(report['warnings'])

    def test_invalid_shapes_duplicates_constants_and_size_are_rejected(self):
        bad = [b'[]', b'{}', b'{"@version":true}', b'{"@version":"x","@version":"y"}', b'{"@version":"x","n":NaN}', b'{"@version":"x","site":{}}', b'{"@version":"x","site":[null]}', b'{"@version":"x","site":[{"alerts":{}}]}']
        for raw in bad:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                zap_report.parse_json(raw, 'fixture')
        self.raw['site'][0]['alerts'][0]['riskcode'] = True
        with self.assertRaises(ValueError):
            self.parse()
        with patch.object(zap_report, 'MAX_BYTES', 8), self.assertRaises(ValueError):
            zap_report.parse_json(FIXTURE.read_bytes(), 'fixture')

    def test_count_mismatch_and_omitted_instances_trigger_coverage_review(self):
        self.raw['site'][0]['alerts'][0]['count'] = '10'
        report = self.parse()
        self.assertFalse(report['findings'][0]['instance_count_matches'])
        self.assertIn('ZAP-COVERAGE', [i['rule_id'] for i in build_review(zap=report)['items']])
        del self.raw['site'][0]['alerts'][0]['instances']
        report = self.parse()
        self.assertEqual(report['findings'][0]['instances_state'], 'missing')
        self.assertIsNone(report['findings'][0]['instance_count_matches'])


class ZapReviewTests(unittest.TestCase):
    def setUp(self):
        self.report = zap_report.import_report(FIXTURE)

    def test_false_positive_is_visible_and_not_escalated_by_high_risk(self):
        first = self.report['findings'][0]
        first['confidence_normalized'] = 0
        review = build_review(zap=self.report)
        self.assertEqual(len(review['items']), 2)
        self.assertTrue(all(i['rule_id'] == 'ZAP-FALSE-POSITIVE' and i['priority'] == 'context' for i in review['items']))
        self.assertEqual(review['items'][0]['references'][0]['role'], 'zap')

    def test_information_and_medium_risk_keep_their_review_categories(self):
        self.report['findings'][0]['risk_normalized'] = 0
        review = build_review(zap=self.report)
        self.assertIn('ZAP-INFORMATION', [i['rule_id'] for i in review['items']])
        self.report['findings'][0]['risk_normalized'] = 2
        review = build_review(zap=self.report)
        self.assertIn('ZAP-REVIEW', [i['rule_id'] for i in review['items']])

    def test_extra_diagnostics_keep_presence_without_copying_contents(self):
        raw = json.loads(FIXTURE.read_text())
        raw['stoppingInsight'] = {'description': 'LOCAL-DIAGNOSTIC-ONLY'}
        raw['afPlanErrors'] = ['LOCAL-ERROR-ONLY']
        report = zap_report.parse_json(json.dumps(raw).encode(), 'fixture')
        review = build_review(zap=report)
        self.assertNotIn('LOCAL-DIAGNOSTIC-ONLY', json.dumps(review))
        self.assertNotIn('LOCAL-ERROR-ONLY', json.dumps(review))
        self.assertEqual(review['items'][0]['rule_id'], 'ZAP-COVERAGE')

    def test_empty_explicit_alerts_do_not_become_security_attestation(self):
        raw = b'{"@version":"fixture","site":[{"alerts":[]}]}'
        review = build_review(zap=zap_report.parse_json(raw, 'fixture'))
        self.assertEqual(review['items'], [])
        self.assertIn('não comprova segurança', render_html(review))

    def test_alert_text_remains_inert_in_html(self):
        self.report['findings'][0]['producer_fields']['name'] = '<img src="https://example.test/x" onerror="bad()">'
        page = render_html(build_review(zap=self.report))
        self.assertNotIn('<img', page)
        self.assertNotIn('<script', page)
        self.assertIn('&lt;img', page)

    def test_identity_and_fingerprint_are_versioned_and_inputs_unchanged(self):
        before = copy.deepcopy(self.report)
        first, second = build_review(zap=self.report), build_review(zap=self.report)
        self.assertEqual(first, second)
        self.assertEqual(before, self.report)
        self.assertEqual(first['ruleset']['version'], '2')
        self.report['analysis_run']['adapter_version'] = '2'
        self.assertNotEqual(first['review_id'], build_review(zap=self.report)['review_id'])

    def test_cli_import_and_review_produce_files_without_overwriting(self):
        command = [sys.executable, str(ROOT/'scripts/workbench.py')]
        imported = subprocess.run(command+['import-zap', str(FIXTURE)], capture_output=True, text=True)
        self.assertEqual(imported.returncode, 0, imported.stderr)
        self.assertEqual(json.loads(imported.stdout)['coverage']['imported_alerts'], 2)
        with tempfile.TemporaryDirectory() as folder:
            data, html = Path(folder)/'queue.json', Path(folder)/'queue.html'
            cmd = command+['review', '--zap', str(FIXTURE), '--output', str(data), '--html', str(html)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            review = json.loads(data.read_text())
            self.assertEqual(review['summary']['items'], 2)
            self.assertIn(review['review_id'], html.read_text())
            original = html.read_bytes()
            data.unlink()
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(data.exists())
            self.assertEqual(html.read_bytes(), original)

    def test_cli_combines_three_producers_with_references_to_distinct_inputs(self):
        cmd = [sys.executable, str(ROOT/'scripts/workbench.py'), 'review', '--before', str(ROOT/'tests/fixtures/nmap-synthetic.xml'), '--after', str(ROOT/'tests/fixtures/nmap-synthetic-after.xml'), '--trivy', str(ROOT/'tests/fixtures/trivy-synthetic.json'), '--zap', str(FIXTURE)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(set(report['inputs']), {'nmap-before', 'nmap-after', 'trivy', 'zap'})
        self.assertEqual(report['summary']['by_priority'], {'review-first': 4, 'review-next': 3, 'context': 1})
        self.assertEqual(report['summary']['items'], 8)
        for item in report['items']:
            for reference in item['references']:
                self.assertEqual(reference['artifact_sha256'], report['inputs'][reference['role']]['artifact']['sha256'])
        self.assertEqual(report['ruleset']['model_calls'], 0)
        self.assertFalse(report['target_executed'])


if __name__ == '__main__':
    unittest.main()
