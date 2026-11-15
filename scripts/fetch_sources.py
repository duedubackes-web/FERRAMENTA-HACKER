#!/usr/bin/env python3
"""Acquire the exact locked public Git trees. Does not install or run project code."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True, type=Path)
    args = parser.parse_args()
    base = args.destination.resolve()
    sources = json.loads((ROOT/'sources.lock.json').read_text())['sources']
    # Validate the complete plan before creating directories.
    for source in sources:
        if not source['url'].startswith(('https://github.com/', 'https://gitlab.com/')):
            raise ValueError('Unexpected source host in lock')
        if len(source['commit']) != 40 or any(c not in '0123456789abcdef' for c in source['commit']):
            raise ValueError('Expected a full Git SHA-1 commit identity')
        if Path(source['id']).name != source['id'] or source['id'] in ('.', '..'):
            raise ValueError('Invalid source ID')
        if (base/source['id']).exists():
            raise ValueError(f'Destination exists: {base/source["id"]}; choose a fresh directory')
    for source in sources:
        target = base/source['id']
        target.mkdir(parents=True)
        prefix = ['git', '-c', 'core.hooksPath=/dev/null', '-C', str(target)]
        for command in [
            ['init', '--quiet'],
            ['remote', 'add', 'origin', source['url']],
            ['fetch', '--depth=1', 'origin', source['commit']],
            ['-c', 'filter.lfs.smudge=', '-c', 'filter.lfs.required=false', 'checkout', '--detach', 'FETCH_HEAD'],
        ]:
            subprocess.run(prefix + command, check=True, timeout=300)
        actual = subprocess.check_output(prefix+['rev-parse', 'HEAD'], text=True).strip()
        if actual != source['commit']:
            raise RuntimeError(f'Commit mismatch: {source["id"]}')
        print(f'OK {source["id"]} {actual}', flush=True)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as error:
        raise SystemExit(str(error))
