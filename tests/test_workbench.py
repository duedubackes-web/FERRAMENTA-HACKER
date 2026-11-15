import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('workbench', ROOT/'scripts/workbench.py')
workbench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workbench)


class IntegrityTests(unittest.TestCase):
    def test_detects_tampering_and_missing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            item = root/'sample.txt'
            item.write_bytes(b'original')
            sha = hashlib.sha256(item.read_bytes()).hexdigest()
            (root/'ARTIFACTS.sha256').write_text(f'{sha}  sample.txt\n')
            self.assertEqual(workbench.verify(root), [])
            item.write_bytes(b'modified')
            self.assertIn('checksum mismatch: sample.txt', workbench.verify(root))
            item.unlink()
            self.assertIn('missing: sample.txt', workbench.verify(root))

    def test_rejects_parent_traversal(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'ARTIFACTS.sha256').write_text('0'*64+'  ../outside\n')
            self.assertTrue(any('unsafe path' in e for e in workbench.verify(root)))

    def test_rejects_empty_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'ARTIFACTS.sha256').write_text('')
            self.assertIn('empty integrity manifest', workbench.verify(root))

    def test_unknown_inventory_cannot_select_filesystem_path(self):
        with self.assertRaises(ValueError):
            list(workbench.inventory(ROOT, '../../outside'))

    def test_inventory_matches_locked_entry_count(self):
        import json
        data = json.loads((ROOT/'sources.lock.json').read_text())
        for source in data['sources']:
            rows = list(workbench.inventory(ROOT, source['id']))
            self.assertEqual(len(rows), source['tracked_files'])
            self.assertEqual(len({r['path'] for r in rows}), len(rows))


if __name__ == '__main__':
    unittest.main()
