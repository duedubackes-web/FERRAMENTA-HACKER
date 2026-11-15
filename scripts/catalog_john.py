#!/usr/bin/env python3
"""Catalog inert format-declaration metadata, without compiling or running John."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TOKENS = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/')


def declarations(text: str) -> dict:
    def strip_comment(match):
        value = match.group()
        return ''.join('\n' if c == '\n' else ' ' for c in value) if value.startswith(('/', '/*')) else value
    text = TOKENS.sub(strip_comment, text)
    structs = [{'symbol': m[1], 'line': text.count('\n', 0, m.start())+1}
               for m in re.finditer(r'^[ \t]*(?:static[ \t]+)?struct[ \t]+fmt_main[ \t]+([A-Za-z_]\w*)\s*=', text, re.MULTILINE)]
    labels = [{'literal': m[1], 'line': text.count('\n', 0, m.start())+1}
              for m in re.finditer(r'^[ \t]*#[ \t]*define[ \t]+FORMAT_LABEL[ \t]+"([^"\\\r\n]*)"[ \t]*$', text, re.MULTILINE)]
    return {'format_structs': structs, 'literal_label_definitions': labels}


def catalog(checkout: Path, source: dict) -> dict:
    git = ['git', '-C', str(checkout)]
    commit = subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip()
    if commit != source['commit']:
        raise ValueError('Checkout commit differs from sources.lock.json')
    subprocess.run(git+['diff', '--no-ext-diff', '--quiet', 'HEAD', '--'], check=True)
    files = []
    tracked = subprocess.check_output(git+['ls-files', '-z']).decode().split('\0')
    for name in sorted(p for p in tracked if Path(p).parent == Path('src') and Path(p).suffix == '.c'):
        file = checkout/name
        data = file.read_bytes()
        result = declarations(data.decode('utf-8', errors='replace'))
        if not result['format_structs'] and not result['literal_label_definitions']:
            continue
        path = file.relative_to(checkout).as_posix()
        files.append({'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'url': source['url'].removesuffix('.git')+'/blob/'+commit+'/'+path, **result})
    return {'schema_version': 1, 'source_id': source['id'], 'source_commit': commit,
            'method': 'Comment-aware lexical matching in tracked top-level src/*.c; no preprocessor, compiler or target execution',
            'counts': {'files_with_matches': len(files), 'format_struct_definitions': sum(len(f['format_structs']) for f in files), 'literal_label_definitions': sum(len(f['literal_label_definitions']) for f in files)},
            'files': files,
            'limitations': ['Conditional compilation is not evaluated; declarations do not establish runtime support.', 'Macro-generated declarations, included headers, nested source directories and nonliteral label expressions are outside this catalog.', 'File-level label declarations are not automatically associated with individual format structures.', 'No test hashes, passwords, candidate lists, format algorithms or performance measurements are extracted.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    source = next(s for s in json.loads((ROOT/'sources.lock.json').read_text())['sources'] if s['id'] == 'john')
    result = catalog(args.checkout, source)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result['counts']))
