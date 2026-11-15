import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from review_replay import replay_review, source_arguments, read_review
from review_rules import build_review
from nmap_report import import_report as nmap
from nmap_compare import compare_reports
from trivy_report import import_report as trivy
from zap_report import import_report as zap

FIX = ROOT/'tests/fixtures'


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.sources = {'nmap-before': FIX/'nmap-synthetic.xml', 'nmap-after': FIX/'nmap-synthetic-after.xml',
                        'trivy': FIX/'trivy-synthetic.json', 'zap': FIX/'zap-synthetic.json'}
        self.report = build_review(compare_reports(nmap(self.sources['nmap-before']), nmap(self.sources['nmap-after'])),
                                   trivy(self.sources['trivy']), zap(self.sources['zap']))

    def test_three_producers_reproduce_without_mutation(self):
        original = copy.deepcopy(self.report)
        result = replay_review(self.report, self.sources)
        self.assertEqual(result['status'], 'matched')
        self.assertEqual(self.report, original)
        self.assertFalse(result['target_executed'])

    def test_moved_files_and_untrusted_embedded_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            moved = {}
            for role, path in self.sources.items():
                moved[role] = Path(folder)/role
                moved[role].write_bytes(path.read_bytes())
                self.report['inputs'][role]['artifact']['path'] = '/untrusted/never-open-this'
            self.assertEqual(replay_review(self.report, moved)['status'], 'matched')

    def test_detects_modified_priority_facts_references_summary_and_extra_fields(self):
        for section in ('priority', 'facts', 'references', 'summary', 'extra', 'review_id'):
            report = copy.deepcopy(self.report)
            if section in ('priority', 'facts', 'references'):
                report['items'][0][section] = 'tampered'
            elif section == 'summary':
                report['summary']['items'] = 0
            else:
                report[section] = 'tampered'
            with self.subTest(section=section):
                result = replay_review(report, self.sources)
                self.assertEqual(result['status'], 'review-mismatch')
                self.assertTrue(result['different_sections'])

    def test_detects_source_changes_without_parsing_changed_content(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'source'
            path.write_text('not JSON')
            sources = dict(self.sources, zap=path)
            with patch('review_replay.PARSERS', dict(__import__('review_replay').PARSERS, zap=lambda *_: self.fail('changed source parsed'))):
                result = replay_review(self.report, sources)
            self.assertEqual(result['status'], 'source-mismatch')
            self.assertFalse(result['sources']['zap']['matches'])

    def test_rejects_missing_extra_roles_duplicates_and_unknown_rules(self):
        for values in [['zap=x','zap=y'], ['unknown=x'], ['zap='], ['zap']]:
            with self.assertRaises(ValueError):
                source_arguments(values)
        for sources in [{}, dict(self.sources, extra=Path('unused'))]:
            with self.assertRaises(ValueError):
                replay_review(self.report, sources)
        for field in ('version', 'sha256'):
            report = copy.deepcopy(self.report)
            report['ruleset'][field] = 'unavailable'
            with self.assertRaises(ValueError):
                replay_review(report, self.sources)

    def test_single_producer_empty_queue_replays(self):
        from trivy_report import parse_json
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'empty.json'
            path.write_bytes(b'{"SchemaVersion":2,"Results":[{"Vulnerabilities":[]}]}')
            report = build_review(trivy=parse_json(path.read_bytes(), str(path)))
            self.assertEqual(report['items'], [])
            self.assertEqual(replay_review(report, {'trivy': path})['status'], 'matched')

    def test_bounded_review_reader_rejects_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'review.json'
            path.write_text('{"inputs":{},"inputs":{}}')
            with self.assertRaises(ValueError):
                read_review(path)
            path.write_text('{}')
            with patch('review_replay.MAX_BYTES', 1), self.assertRaises(ValueError):
                read_review(path)

    def test_cli_exit_codes_output_protection_and_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path, output = Path(folder)/'review.json', Path(folder)/'replay.json'
            path.write_text(json.dumps(self.report))
            command = [sys.executable, str(ROOT/'scripts/workbench.py'), 'replay-review', str(path)]
            for role, source in self.sources.items():
                command += ['--source', role+'='+str(source)]
            result = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'matched')
            self.report['items'] = []
            path.write_text(json.dumps(self.report))
            result = subprocess.run(command+['--output', str(output)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(output.read_text())['status'], 'review-mismatch')
            original = output.read_bytes()
            result = subprocess.run(command+['--output', str(output)], capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(output.read_bytes(), original)
