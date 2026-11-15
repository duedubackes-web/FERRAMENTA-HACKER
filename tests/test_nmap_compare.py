from pathlib import Path
import copy
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from nmap_report import import_report
from nmap_compare import compare_reports, render_html

BEFORE = ROOT/'tests/fixtures/nmap-synthetic.xml'
AFTER = ROOT/'tests/fixtures/nmap-synthetic-after.xml'


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.before = import_report(BEFORE)
        self.after = import_report(AFTER)

    def test_explicit_state_service_and_first_observation_have_source_references(self):
        result = compare_reports(self.before, self.after)
        self.assertEqual(result['summary']['matched_hosts'], 1)
        self.assertEqual(result['summary']['changes_by_kind'], {'first_observed_endpoint': 1, 'service_evidence_changed': 1, 'state_changed': 1})
        state = next(c for c in result['changes'] if c['kind'] == 'state_changed')
        self.assertEqual((state['before'], state['after']), ('closed', 'open'))
        self.assertEqual(state['references'][0]['artifact_sha256'], self.before['artifact']['sha256'])
        self.assertEqual(state['references'][1]['port_index'], 0)
        first = next(c for c in result['changes'] if c['kind'] == 'first_observed_endpoint')
        self.assertEqual(first['endpoint']['number'], 8443)
        self.assertEqual(first['other_declared_scope'], 'not_declared')
        self.assertEqual(result['comparability']['scope_relation'], 'different_declared')

    def test_missing_port_is_not_reported_as_closed_even_with_aggregated_extraports(self):
        after = copy.deepcopy(self.before)
        after['hosts'][0]['ports'].pop()
        after['hosts'][0]['extraports'] = [{'state': 'closed', 'count': '1'}]
        result = compare_reports(self.before, after)
        self.assertEqual(len(result['changes']), 1)
        item = result['changes'][0]
        self.assertEqual(item['kind'], 'not_observed_endpoint_after')
        self.assertIsNone(item['after'])
        self.assertEqual(item['other_declared_scope'], 'declared')

    def test_missing_state_is_an_evidence_change_not_a_transition(self):
        self.after['hosts'][0]['ports'][0]['state'] = None
        result = compare_reports(self.before, self.after)
        states = [c for c in result['changes'] if c['endpoint']['number'] == 22]
        self.assertEqual(states[0]['kind'], 'state_evidence_changed')
        self.assertIsNone(states[0]['after'])

    def test_unknown_or_unrecognized_states_remain_evidence_changes(self):
        for state in ['unknown', '', 'future-state']:
            with self.subTest(state=state):
                self.after['hosts'][0]['ports'][0]['state'] = {'state': state}
                self.after['hosts'][0]['status'] = {'state': 'unknown'}
                result = compare_reports(self.before, self.after)
                self.assertNotIn('state_changed', result['summary']['changes_by_kind'])
                self.assertIn('state_evidence_changed', result['summary']['changes_by_kind'])
                self.assertIn('host_state_evidence_changed', result['summary']['changes_by_kind'])

    def test_duplicate_ip_records_are_unresolved_instead_of_new_or_removed(self):
        self.before['hosts'].append(copy.deepcopy(self.before['hosts'][0]))
        result = compare_reports(self.before, self.after)
        self.assertEqual(result['summary']['matched_hosts'], 0)
        self.assertEqual(result['changes'], [])
        self.assertEqual([i['kind'] for i in result['issues']], ['host_identity_ambiguous']*3)

    def test_split_aliases_do_not_produce_a_false_host_pair(self):
        first, second = copy.deepcopy(self.after['hosts'][0]), copy.deepcopy(self.after['hosts'][0])
        first['addresses'] = first['addresses'][:1]
        second['addresses'] = second['addresses'][1:]
        self.after['hosts'] = [first, second]
        result = compare_reports(self.before, self.after)
        self.assertEqual(result['summary']['matched_hosts'], 0)
        self.assertEqual(result['changes'], [])
        self.assertEqual(result['summary']['issues'], 3)

    def test_canonical_ipv6_matches_without_using_hostnames(self):
        self.before['hosts'][0]['addresses'] = [{'addrtype': 'ipv6', 'addr': '2001:0db8:0:0:0:0:0:10'}]
        self.after['hosts'][0]['addresses'] = [{'addrtype': 'ipv6', 'addr': '2001:db8::10'}]
        result = compare_reports(self.before, self.after)
        self.assertEqual(result['summary']['matched_hosts'], 1)
        self.assertNotIn('address_evidence_changed', result['summary']['changes_by_kind'])

    def test_hostname_only_is_not_an_identity_key(self):
        self.before['hosts'][0]['addresses'] = []
        self.after['hosts'][0]['addresses'] = []
        result = compare_reports(self.before, self.after)
        self.assertEqual(result['summary']['matched_hosts'], 0)
        self.assertEqual(result['changes'], [])
        self.assertEqual(result['summary']['issues'], 2)

    def test_duplicate_endpoint_records_are_not_silently_overwritten(self):
        self.before['hosts'][0]['ports'].append(copy.deepcopy(self.before['hosts'][0]['ports'][0]))
        result = compare_reports(self.before, self.after)
        self.assertTrue(any(i['kind'] == 'endpoint_identity_ambiguous' for i in result['issues']))
        self.assertFalse(any(c.get('endpoint', {}).get('number') == 22 for c in result['changes']))

    def test_missing_completion_version_and_timeout_warnings_are_retained(self):
        self.after['warnings'] = ['No finished record: scan completion is unknown']
        self.after['producer']['finished'] = None
        self.after['producer']['version'] = 'another-fixture'
        self.after['hosts'][0]['timedout'] = 'true'
        result = compare_reports(self.before, self.after)
        self.assertTrue(any(w['source'] == 'after' for w in result['warnings']))
        self.assertTrue(any('versions differ' in w['message'] for w in result['warnings']))
        self.assertTrue(any(i['kind'] == 'producer_host_timeout' for i in result['issues']))

    def test_reordered_intervals_are_equivalent_and_invalid_scope_stays_unknown(self):
        after = copy.deepcopy(self.before)
        after['coverage']['scaninfo'][0]['services'] = '8080,22,443'
        self.assertEqual(compare_reports(self.before, after)['comparability']['scope_relation'], 'same_declared')
        after['coverage']['scaninfo'][0]['services'] = '1-999999'
        self.assertEqual(compare_reports(self.before, after)['comparability']['scope_relation'], 'unknown')

    def test_identical_input_has_no_changes_and_deterministic_identity(self):
        first = compare_reports(self.before, self.before)
        second = compare_reports(self.before, self.before)
        self.assertEqual(first, second)
        self.assertEqual(first['changes'], [])
        self.assertFalse(first['target_executed'])

    def test_identity_tracks_importer_version_but_not_artifact_location(self):
        original = compare_reports(self.before, self.after)['comparison_id']
        self.after['artifact']['path'] = 'another-copy.xml'
        self.assertEqual(compare_reports(self.before, self.after)['comparison_id'], original)
        self.after['analysis_run']['adapter_version'] = '2'
        self.assertNotEqual(compare_reports(self.before, self.after)['comparison_id'], original)

    def test_html_escapes_artifact_paths_and_service_data(self):
        attack = '<img src="https://example.test/x" onerror="alert(1)">'
        self.after['hosts'][0]['ports'][1]['service']['product'] = attack
        self.after['artifact']['path'] = attack
        page = render_html(compare_reports(self.before, self.after))
        self.assertNotIn('<img', page)
        self.assertNotIn('<script', page)
        self.assertIn('&lt;img', page)
        self.assertIn('Content-Security-Policy', page)
        self.assertIn('href="#sources"', page)

    def test_cli_produces_json_and_html_and_preflights_existing_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            data, html = base/'comparison.json', base/'comparison.html'
            command = [sys.executable, str(ROOT/'scripts/workbench.py'), 'compare-nmap', str(BEFORE), str(AFTER), '--output', str(data), '--html', str(html)]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            report = json.loads(data.read_text())
            self.assertEqual(report['summary']['changes'], 3)
            self.assertIn(report['comparison_id'], html.read_text())
            original = html.read_bytes()
            data.unlink()
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2)
            self.assertFalse(data.exists())
            self.assertEqual(html.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
