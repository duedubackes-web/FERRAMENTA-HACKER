from pathlib import Path
import gzip
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from catalog_john import declarations
from verify_snapshots import verify_source


class CatalogTests(unittest.TestCase):
    def test_ignores_comments_and_preserves_source_lines(self):
        source = '/* struct fmt_main fake = {}; */\n#define FORMAT_LABEL "demo" // comment\nstruct fmt_main fmt_demo = {};\n'
        result = declarations(source)
        self.assertEqual(result['format_structs'], [{'symbol': 'fmt_demo', 'line': 3}])
        self.assertEqual(result['literal_label_definitions'], [{'literal': 'demo', 'line': 2}])

    def test_nonliteral_or_concatenated_label_is_not_reported_as_a_complete_literal(self):
        self.assertEqual(declarations('#define FORMAT_LABEL "prefix" SUFFIX\n')['literal_label_definitions'], [])
        self.assertEqual(declarations('#define FORMAT_LABEL SOME_MACRO\n')['literal_label_definitions'], [])

    def test_conditional_declarations_are_retained_without_claiming_active_support(self):
        source = '#if PLATFORM\nstruct fmt_main fmt_one = {};\n#else\nstruct fmt_main fmt_two = {};\n#endif\n'
        self.assertEqual([r['symbol'] for r in declarations(source)['format_structs']], ['fmt_one', 'fmt_two'])


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        (self.root/'research/inventories').mkdir(parents=True)
        self.archive = self.root/'sample.zip'
        self.data = b'reference bytes'
        self.rows = [{'path': 'file.txt', 'kind': 'file', 'bytes': len(self.data), 'sha256': hashlib.sha256(self.data).hexdigest()}]
        with zipfile.ZipFile(self.archive, 'w') as z:
            z.writestr('file.txt', self.data)
        self.source = {'id': 'sample', 'commit': '0'*40, 'archive': 'sample.zip', 'archive_bytes': self.archive.stat().st_size, 'archive_sha256': hashlib.sha256(self.archive.read_bytes()).hexdigest(), 'tracked_files': 1}
        self.write_inventory()

    def write_inventory(self):
        with gzip.open(self.root/'research/inventories/sample.jsonl.gz', 'wt') as stream:
            for row in self.rows:
                stream.write(json.dumps(row)+'\n')

    def test_valid_snapshot_is_checked_without_extracting_files(self):
        result = verify_source(self.root, self.root, self.source)
        self.assertEqual(result['checked_files'], 1)
        self.assertTrue(result['per_entry_sha256_verified'])
        self.assertFalse((self.root/'file.txt').exists())

    def test_detects_archive_and_inventory_tampering(self):
        self.rows[0]['sha256'] = '0'*64
        self.write_inventory()
        with self.assertRaisesRegex(ValueError, 'content mismatch'):
            verify_source(self.root, self.root, self.source)
        data = bytearray(self.archive.read_bytes())
        data[0] ^= 1
        self.archive.write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'archive SHA-256 mismatch'):
            verify_source(self.root, self.root, self.source)

    def test_detects_unexpected_zip_membership(self):
        self.rows[0]['path'] = 'another-name.txt'
        self.write_inventory()
        with self.assertRaisesRegex(ValueError, 'membership differs'):
            verify_source(self.root, self.root, self.source)


if __name__ == '__main__':
    unittest.main()
