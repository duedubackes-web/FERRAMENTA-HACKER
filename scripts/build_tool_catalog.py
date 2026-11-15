#!/usr/bin/env python3
"""Rebuild derived catalogs from retained research data; does not access the network."""
import json
from pathlib import Path

from research_catalog import build_package_index

ROOT = Path(__file__).resolve().parents[1]


def build(root: Path):
    curated = json.loads((root/'research/tool-curation.json').read_text())
    metadata = json.loads((root/'research/tool-repository-metadata.json').read_text())
    by_repo = {p['full_name'].casefold(): p for p in metadata['projects']}
    sources = {p['id']: p for p in json.loads((root/'sources.lock.json').read_text())['sources']}
    ids, tools = set(), []
    for seed in curated['tools']:
        if seed['id'] in ids:
            raise ValueError('Duplicate curated tool ID')
        ids.add(seed['id'])
        snapshots = []
        for ident in seed['source_ids']:
            source = sources[ident]
            snapshots.append({'id': ident, 'url': source['url'], 'commit': source['commit'], 'tracked_entries': source['tracked_files'], 'unfetched_gitlinks': source.get('unfetched_gitlinks', []), 'notices': [p.relative_to(root).as_posix() for p in sorted((root/'third_party/notices'/ident).rglob('*')) if p.is_file()]})
        meta = by_repo.get((seed['repository'] or '').casefold())
        if not meta and not snapshots and seed['id'] != 'gemini-app':
            raise ValueError(f'No verified metadata or source snapshot for {seed["id"]}')
        tool = {k: v for k, v in seed.items() if k != 'source_ids'}
        tool.update({'source_status': 'source-indexed' if snapshots else ('public-page-inspected' if seed['id'] == 'gemini-app' else 'cataloged-only'),
                     'source_snapshots': snapshots,
                     'runtime_evidence': 'static-inspection-cli-used' if seed['id'] in ('rea', 'craft-anything') else 'tool-not-executed',
                     'evidence_reference': 'research/tool-repository-metadata.json' if meta else ('research/gemini-public-observation.json' if seed['id'] == 'gemini-app' else 'sources.lock.json'),
                     'repository_metadata': meta,
                     'license_review': 'root-notices-preserved; component review incomplete' if snapshots else 'metadata-only; no integration license determination'})
        if seed['id'] == 'gemini-app':
            tool['website'] = 'https://gemini.google.com/app?hl=pt-BR'
        tools.append(tool)
    catalog = {'schema_version': 1, 'observed_date': metadata['retrieved_date'],
               'scope': 'Curated public-source research directory. Cataloged, source-indexed and runtime evidence are distinct; not an exhaustive ecosystem, recommendation ranking or executable toolkit.',
               'categories': curated['categories'], 'count': len(tools), 'tools': tools}
    index = build_package_index(json.loads((root/'research/kali-package-profiles.json').read_text()))
    (root/'research/tool-catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2)+'\n')
    (root/'research/kali-tool-package-index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'projects': len(tools), 'indexed_projects': sum(bool(t['source_snapshots']) for t in tools), 'declared_packages': index['count'], 'kali_tools_profiles': len(index['profiles'])}))


if __name__ == '__main__':
    build(ROOT)
