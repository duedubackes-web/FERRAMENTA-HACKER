#!/usr/bin/env python3
"""Offline inventory and integrity CLI. Never executes collected software."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys

ROOT = Path(__file__).resolve().parents[1]


def verify(root: Path) -> list[str]:
    manifest = root / 'ARTIFACTS.sha256'
    if not manifest.is_file():
        return ['missing integrity manifest: ARTIFACTS.sha256']
    errors = []
    seen = set()
    for number, line in enumerate(manifest.read_text(encoding='utf-8').splitlines(), 1):
        try:
            expected, name = line.split('  ', 1)
            path = PurePosixPath(name)
            if len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected):
                raise ValueError('invalid SHA-256')
            if not name or path.is_absolute() or '..' in path.parts or '\\' in name:
                raise ValueError('unsafe path')
            target = root / name
            if not target.resolve().is_relative_to(root.resolve()):
                raise ValueError('path escapes project')
            if name in seen:
                raise ValueError('duplicate path')
            seen.add(name)
            if not target.is_file():
                errors.append(f'missing: {name}')
                continue
            with target.open('rb') as stream:
                actual = hashlib.file_digest(stream, 'sha256').hexdigest()
            if actual != expected:
                errors.append(f'checksum mismatch: {name}')
        except (ValueError, OSError) as error:
            errors.append(f'manifest line {number}: {error}')
    if not seen:
        errors.append('empty integrity manifest')
    return errors


def inventory(root: Path, source: str):
    # Source is an exact ID from the lock, not a free path.
    sources = json.loads((root / 'sources.lock.json').read_text())['sources']
    if source not in {s['id'] for s in sources}:
        raise ValueError(f'unknown source: {source}')
    with gzip.open(root / 'research/inventories' / f'{source}.jsonl.gz', 'rt', encoding='utf-8') as stream:
        for line in stream:
            yield json.loads(line)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('verify', help='Check files listed in the delivery integrity manifest')
    commands.add_parser('sources', help='List pinned upstream URLs and commits')
    commands.add_parser('summary', help='Show inventoried scope and explicit limitations')
    find = commands.add_parser('find', help='Search tracked paths in an offline inventory')
    find.add_argument('source')
    find.add_argument('query')
    args = parser.parse_args(argv)
    try:
        if args.command == 'verify':
            errors = verify(ROOT)
            for message in errors:
                print(message, file=sys.stderr)
            if errors:
                return 1
            print('OK: all listed delivery files match SHA-256; this is integrity, not authenticity.')
        elif args.command == 'sources':
            for source in json.loads((ROOT/'sources.lock.json').read_text())['sources']:
                print(f'{source["id"]}\t{source["commit"]}\t{source["url"]}')
        elif args.command == 'summary':
            data = json.loads((ROOT/'research/corpus-summary.json').read_text())
            for key, value in data.items():
                print(f'{key}: {value["files"]} tracked entries, {value["bytes"]} inventoried bytes')
            print('Scope: pinned tracked trees only. Semantic review selective; no full Kali package closure or runtime audit.')
        else:
            count = 0
            for row in inventory(ROOT, args.source):
                if args.query.casefold() in row['path'].casefold():
                    print(json.dumps(row, ensure_ascii=False))
                    count += 1
            print(f'{count} matching inventory entries', file=sys.stderr)
    except (OSError, ValueError, KeyError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
