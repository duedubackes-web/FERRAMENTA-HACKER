#!/usr/bin/env python3
"""Regenerate delivery checksums after an intentional, reviewed change."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {'.git', '__pycache__', '.venv', 'node_modules', 'work', 'source-snapshots', '.pytest_cache'}


def main():
    records = []
    for file in sorted(ROOT.rglob('*')):
        relative = file.relative_to(ROOT)
        if not file.is_file() or any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if file.name == 'ARTIFACTS.sha256' or file.name == '.env' or file.name.startswith('.env.') or file.suffix == '.pyc':
            continue
        with file.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        records.append(f'{digest}  {relative.as_posix()}')
    (ROOT/'ARTIFACTS.sha256').write_text('\n'.join(records)+'\n', encoding='utf-8')
    print(f'Wrote {len(records)} checksums. Review the diff before committing.')


if __name__ == '__main__':
    main()
