import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('nmap_report', ROOT/'scripts/nmap_report.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
FIXTURE = ROOT/'tests/fixtures/nmap-synthetic.xml'


class NmapReportTests(unittest.TestCase):
    def test_import_preserves_identity_states_and_scope(self):
        report = adapter.import_report(FIXTURE)
        self.assertEqual(report['artifact']['sha256'], hashlib.sha256(FIXTURE.read_bytes()).hexdigest())
        self.assertFalse(report['analysis_run']['target_executed'])
        host = report['hosts'][0]
        self.assertEqual([p['state']['state'] for p in host['ports']], ['closed', 'open'])
        self.assertEqual(host['ports'][1]['service']['conf'], '3')
        self.assertIsNone(host['ports'][0]['service'])
        self.assertEqual(host['extraports'][0]['count'], '1')
        self.assertEqual(len(host['addresses']), 2)
        self.assertEqual(report['coverage']['status'], 'selected-fields')

    def test_missing_completion_and_script_output_remain_explicit(self):
        data = b'<nmaprun scanner="nmap"><host><ports><port protocol="udp" portid="53"><script id="example" output="not executed"/></port></ports></host></nmaprun>'
        report = adapter.parse_xml(data, 'fixture')
        self.assertIsNone(report['producer']['finished'])
        self.assertIsNone(report['hosts'][0]['ports'][0]['state'])
        self.assertEqual(report['coverage']['omitted_script_results'], 1)
        self.assertEqual(len(report['warnings']), 2)

    def test_rejects_malformed_xml_wrong_root_and_invalid_port(self):
        for data in [b'<nmaprun', b'<other/>', b'<nmaprun scanner="other"/>', b'<nmaprun scanner="nmap"><host><ports><port protocol="tcp" portid="99999"/></ports></host></nmaprun>']:
            with self.subTest(data=data), self.assertRaises(ValueError):
                adapter.parse_xml(data, 'fixture')

    def test_rejects_dtd_entities_and_non_utf8(self):
        for data in [b'<!DOCTYPE nmaprun SYSTEM "https://example.test/dtd"><nmaprun scanner="nmap"/>', b'<!DOCTYPE nmaprun [<!ENTITY a "text">]><nmaprun scanner="nmap"/>', '<nmaprun scanner="nmap"/>'.encode('utf-16')]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                adapter.parse_xml(data, 'fixture')

    def test_refuses_to_overwrite_an_existing_artifact(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)/'report.json'
            target.write_text('preserve')
            with self.assertRaises(FileExistsError):
                adapter.save_report({}, target)
            self.assertEqual(target.read_text(), 'preserve')

    def test_size_budget_is_enforced(self):
        from unittest.mock import patch
        with patch.object(adapter, 'MAX_REPORT_BYTES', 8), self.assertRaises(ValueError):
            adapter.parse_xml(b'<nmaprun scanner="nmap"/>', 'fixture')

    def test_cli_imports_to_a_new_file_and_refuses_overwrite(self):
        import json
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'report.json'
            command = [sys.executable, str(ROOT/'scripts/workbench.py'), 'import-nmap', str(FIXTURE), '--output', str(output)]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            original = output.read_bytes()
            report = json.loads(original)
            self.assertEqual(report['schema_version'], 1)
            self.assertEqual(report['coverage']['imported_hosts'], 1)
            self.assertEqual(report['artifact']['sha256'], hashlib.sha256(FIXTURE.read_bytes()).hexdigest())
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2)
            self.assertEqual(output.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
