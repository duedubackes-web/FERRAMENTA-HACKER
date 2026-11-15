#!/usr/bin/env python3
"""Index an explicit, clean Git checkout; never runs upstream project code."""
import argparse
import collections
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-id', required=True)
    p.add_argument('--checkout', required=True, type=Path)
    p.add_argument('--snapshot-directory', required=True, type=Path)
    a = p.parse_args()
    if not a.source_id or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in a.source_id):
        raise ValueError('source-id must use lowercase letters, digits and hyphens')
    checkout = a.checkout.resolve()
    git = ['git', '-C', str(checkout)]
    subprocess.run(git+['diff', '--no-ext-diff', '--quiet', 'HEAD', '--'], check=True)
    commit = subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip()
    url = subprocess.check_output(git+['remote', 'get-url', 'origin'], text=True).strip()
    if not url.startswith(('https://github.com/', 'https://gitlab.com/')):
        raise ValueError('Expected explicit public GitHub or GitLab remote')
    lock_path = ROOT/'sources.lock.json'
    lock = json.loads(lock_path.read_text())
    if any(s['id'] == a.source_id for s in lock['sources']):
        raise ValueError('Source ID already exists; review updates explicitly')
    rows = []
    extensions = collections.Counter()
    total = 0
    for entry in subprocess.check_output(git+['ls-files', '-s', '-z']).split(b'\0'):
        if not entry:
            continue
        meta, name = entry.split(b'\t', 1)
        mode, oid, stage = meta.decode().split()
        name = os.fsdecode(name)
        if stage != '0':
            raise ValueError('Unmerged index entry')
        if mode == '160000':
            rows.append({'path': name, 'mode': mode, 'git_object': oid, 'kind': 'submodule', 'sha256': None})
            continue
        file = checkout/name
        data = os.readlink(file).encode() if file.is_symlink() else file.read_bytes()
        rows.append({'path': name, 'mode': mode, 'git_object': oid, 'kind': 'symlink' if mode == '120000' else 'file', 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        total += len(data)
        extensions[Path(name).suffix.lower() or '[none]'] += 1
    a.snapshot_directory.mkdir(parents=True, exist_ok=True)
    archive = a.snapshot_directory/f'{a.source_id}-{commit[:12]}.zip'
    if archive.exists():
        raise ValueError('Snapshot already exists')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for row in rows:
            if row['kind'] == 'submodule':
                continue
            file = checkout/row['path']
            data = os.readlink(file).encode() if file.is_symlink() else file.read_bytes()
            if hashlib.sha256(data).hexdigest() != row['sha256']:
                raise ValueError('Checkout changed during indexing')
            info = zipfile.ZipInfo(row['path'])
            info.create_system = 3
            info.external_attr = int(row['mode'], 8) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
    with archive.open('rb') as stream:
        archive_digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    record = {'id': a.source_id, 'url': url, 'commit': commit, 'tracked_files': len(rows), 'archive': archive.name, 'archive_sha256': archive_digest, 'archive_bytes': archive.stat().st_size, 'collected_at': datetime.now(timezone.utc).isoformat(), 'scope': 'HEAD tracked tree; no history, no recursive submodules, no LFS hydration', 'snapshot_method': 'Git tracked working tree bytes; symlink text preserved; gitlinks omitted; no export transformations', 'unfetched_gitlinks': [r['path'] for r in rows if r['kind'] == 'submodule']}
    dest = ROOT/'research/inventories'/f'{a.source_id}.jsonl.gz'
    with dest.open('wb') as raw, gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as stream:
        for row in rows:
            stream.write((json.dumps(row, ensure_ascii=False)+'\n').encode())
    summary_path = ROOT/'research/corpus-summary.json'
    summary = json.loads(summary_path.read_text())
    summary[a.source_id] = {'files': len(rows), 'bytes': total, 'extensions': dict(extensions.most_common()), 'submodules_not_downloaded': record['unfetched_gitlinks']}
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
    lock['sources'].append(record)
    lock_path.write_text(json.dumps(lock, indent=2)+'\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
