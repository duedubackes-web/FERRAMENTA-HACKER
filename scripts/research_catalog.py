"""Offline discovery of research records; never installs or executes cataloged tools."""
import re
import unicodedata


def _search_text(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', text.casefold()) if not unicodedata.combining(c))


def filter_tools(catalog: dict, query: str = '', category: str | None = None, indexed: bool = False) -> dict:
    if catalog.get('schema_version') != 1:
        raise ValueError('Unsupported tool catalog schema')
    if category and category not in {c['id'] for c in catalog['categories']}:
        raise ValueError('Unknown category; consult research/tool-curation.json')
    needle = _search_text(query)
    categories = {c['id']: c for c in catalog['categories']}
    tools = []
    for tool in catalog['tools']:
        if category and category not in tool['categories']:
            continue
        if indexed and not tool['source_snapshots']:
            continue
        tags = [value for ident in tool['categories'] for value in [categories[ident]['label'], *categories[ident].get('aliases', [])]]
        text = _search_text(' '.join([tool['id'], tool['name'], tool['purpose'], tool.get('repository') or '', *tool['categories'], *tool.get('aliases', []), *tags]))
        if needle in text:
            tools.append(tool)
    return {'schema_version': 1, 'scope': catalog['scope'], 'count': len(tools), 'tools': tools}


def build_package_index(profiles: dict) -> dict:
    packages, unresolved, selected = {}, [], []
    for profile in profiles['packages']:
        name = profile['name']
        if not name.startswith('kali-tools-'):
            continue
        selected.append(name)
        for field, raw in profile['dependency_fields_raw'].items():
            if field not in ('Depends', 'Recommends', 'Suggests'):
                continue
            for clause in raw.split(','):
                if not clause.strip():
                    continue
                alternatives = clause.split('|')
                for alternative in alternatives:
                    match = re.match(r'^\s*([a-z0-9][a-z0-9+.-]*)(?::[a-z0-9-]+)?(?=\s|\(|$)', alternative)
                    record = {'profile': name, 'field': field, 'clause': clause.strip(), 'alternative': alternative.strip(), 'alternatives_in_clause': len(alternatives)}
                    if match:
                        packages.setdefault(match[1], []).append(record)
                    else:
                        unresolved.append(record)
    return {'schema_version': 1, 'source': {'source_id': 'kali-meta', 'commit': profiles['source_commit'], 'path': 'debian/control'},
            'scope': 'Direct dependency candidates declared in kali-tools-* profiles; alternatives and constraints are retained. No APT resolution, installation or transitive dependency closure.',
            'profiles': sorted(selected), 'count': len(packages),
            'packages': [{'name': name, 'declarations': declarations} for name, declarations in sorted(packages.items())],
            'unresolved_declarations': unresolved}


def filter_packages(index: dict, query: str = '', profile: str | None = None) -> dict:
    if index.get('schema_version') != 1:
        raise ValueError('Unsupported package index schema')
    if profile and profile not in index['profiles']:
        raise ValueError('Unknown Kali tools profile')
    packages = []
    for record in index['packages']:
        if query.casefold() not in record['name'].casefold():
            continue
        declarations = [d for d in record['declarations'] if profile is None or d['profile'] == profile]
        if declarations:
            packages.append({'name': record['name'], 'declarations': declarations})
    return {'schema_version': 1, 'source': index['source'], 'scope': index['scope'], 'count': len(packages), 'packages': packages}
