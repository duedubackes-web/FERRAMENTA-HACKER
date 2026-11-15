#!/usr/bin/env python3
"""Offline research catalogs, artifact integrity and local report workflows. Never executes collected engines."""
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
    nmap = commands.add_parser('import-nmap', help='Import an existing local Nmap XML report without running Nmap')
    nmap.add_argument('path', type=Path)
    nmap.add_argument('--output', type=Path, help='Write a new JSON file; refuses to overwrite')
    compare = commands.add_parser('compare-nmap', help='Compare two local XML reports; preserve missing/ambiguous evidence')
    compare.add_argument('before', type=Path)
    compare.add_argument('after', type=Path)
    compare.add_argument('--output', type=Path, help='Create a comparison JSON file')
    compare.add_argument('--html', type=Path, help='Create an offline HTML report')
    catalog = commands.add_parser('catalog', help='Search retained project metadata, categories and source-review status')
    catalog.add_argument('--query', default='')
    catalog.add_argument('--category')
    catalog.add_argument('--source-indexed', action='store_true')
    packages = commands.add_parser('packages', help='Search direct package candidates declared in Kali tools profiles')
    packages.add_argument('--query', default='')
    packages.add_argument('--profile')
    trivy = commands.add_parser('import-trivy', help='Import selected fields of an existing Trivy JSON v2 report')
    trivy.add_argument('path', type=Path)
    trivy.add_argument('--output', type=Path)
    review = commands.add_parser('review', help='Build an explainable review queue from local reports; never executes suggestions')
    review.add_argument('--before', type=Path, help='Baseline Nmap XML, requires --after')
    review.add_argument('--after', type=Path, help='Current Nmap XML, requires --before')
    review.add_argument('--trivy', type=Path, help='Trivy JSON v2 input')
    review.add_argument('--output', type=Path, help='Create review JSON')
    review.add_argument('--html', type=Path, help='Create offline review HTML')
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
        elif args.command == 'import-nmap':
            from nmap_report import import_report, save_report
            report = import_report(args.path)
            if args.output:
                save_report(report, args.output)
                print(f'Imported {len(report["hosts"])} hosts into {args.output}')
            else:
                print(json.dumps(report, ensure_ascii=False, indent=2))
        elif args.command == 'compare-nmap':
            from nmap_report import import_report, save_report
            from nmap_compare import compare_reports, render_html, validate_destinations
            validate_destinations([p for p in [args.output, args.html] if p is not None])
            report = compare_reports(import_report(args.before), import_report(args.after))
            if args.output:
                save_report(report, args.output)
            else:
                print(json.dumps(report, ensure_ascii=False, indent=2))
            if args.html:
                with args.html.open('x', encoding='utf-8') as stream:
                    stream.write(render_html(report))
            if args.output:
                print(f'Compared {report["summary"]["matched_hosts"]} host pairs; {report["summary"]["changes"]} recorded differences')
        elif args.command == 'catalog':
            from research_catalog import filter_tools
            data = json.loads((ROOT/'research/tool-catalog.json').read_text())
            print(json.dumps(filter_tools(data, args.query, args.category, args.source_indexed), ensure_ascii=False, indent=2))
        elif args.command == 'packages':
            from research_catalog import filter_packages
            data = json.loads((ROOT/'research/kali-tool-package-index.json').read_text())
            print(json.dumps(filter_packages(data, args.query, args.profile), ensure_ascii=False, indent=2))
        elif args.command == 'import-trivy':
            from trivy_report import import_report
            from nmap_report import save_report
            report = import_report(args.path)
            if args.output:
                save_report(report, args.output)
                print(f'Imported {len(report["findings"])} producer records into {args.output}')
            else:
                print(json.dumps(report, ensure_ascii=False, indent=2))
        elif args.command == 'review':
            from nmap_report import import_report as import_nmap, save_report
            from nmap_compare import compare_reports, validate_destinations
            from trivy_report import import_report as import_trivy
            from review_rules import build_review
            from review_html import render_html
            if bool(args.before) != bool(args.after):
                raise ValueError('Use --before e --after juntos')
            if not args.before and not args.trivy:
                raise ValueError('Forneça um par Nmap e/ou --trivy')
            validate_destinations([p for p in (args.output, args.html) if p is not None])
            comparison = compare_reports(import_nmap(args.before), import_nmap(args.after)) if args.before else None
            report = build_review(comparison, import_trivy(args.trivy) if args.trivy else None)
            if args.output:
                save_report(report, args.output)
            else:
                print(json.dumps(report, ensure_ascii=False, indent=2))
            if args.html:
                with args.html.open('x', encoding='utf-8') as stream:
                    stream.write(render_html(report))
            if args.output:
                print(f'Created {len(report["items"])} explained review items')
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
