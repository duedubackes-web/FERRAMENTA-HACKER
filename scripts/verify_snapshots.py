#!/usr/bin/env python3
"""Verify collected ZIP bytes and each inventoried file without extracting or running it."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def verify_source(root: Path, directory: Path, source: dict) -> dict:
    if Path(source['archive']).name != source['archive'] or Path(source['id']).name != source['id']:
        raise ValueError('Expected plain archive name and source ID')
    archive = directory/source['archive']
    if archive.stat().st_size != source['archive_bytes']:
        raise ValueError(f'{source["id"]}: archive size mismatch')
    with archive.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != source['archive_sha256']:
            raise ValueError(f'{source["id"]}: archive SHA-256 mismatch')
    with gzip.open(root/'research/inventories'/f'{source["id"]}.jsonl.gz', 'rt', encoding='utf-8') as stream:
        rows = [json.loads(line) for line in stream]
    if len(rows) != source['tracked_files'] or len({r['path'] for r in rows}) != len(rows):
        raise ValueError(f'{source["id"]}: inconsistent inventory entry count')
    expected = {r['path']: r for r in rows if r['kind'] != 'submodule'}
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError(f'{source["id"]}: ZIP membership differs from inventory')
        for name, row in expected.items():
            if z.getinfo(name).file_size != row['bytes']:
                raise ValueError(f'{source["id"]}: size mismatch for {name}')
            with z.open(name) as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() != row['sha256']:
                    raise ValueError(f'{source["id"]}: content mismatch for {name}')
    return {'source': source['id'], 'source_commit': source['commit'], 'checked_files': len(expected), 'unfetched_gitlinks': len(rows)-len(expected), 'archive_sha256_verified': True, 'per_entry_sha256_verified': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--source', help='Limit verification to one locked source ID')
    args = parser.parse_args()
    sources = json.loads((ROOT/'sources.lock.json').read_text())['sources']
    if args.source:
        sources = [s for s in sources if s['id'] == args.source]
        if not sources:
            raise ValueError('Unknown source ID')
    result = [verify_source(ROOT, args.directory, source) for source in sources]
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, zipfile.BadZipFile, KeyError) as error:
        raise SystemExit(str(error))
