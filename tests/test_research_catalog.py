import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from research_catalog import build_package_index, filter_packages, filter_tools


class ToolCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = {'schema_version': 1, 'scope': 'public records only', 'categories': [{'id': 'network', 'label': 'Análise de tráfego', 'aliases': ['rede']}, {'id': 'emulation', 'label': 'Emulação', 'aliases': ['Red Team']}], 'tools': [
            {'id': 'a', 'name': 'Inspeção', 'purpose': 'Capturas', 'repository': 'example/a', 'categories': ['network'], 'source_snapshots': [{'id': 'a'}]},
            {'id': 'b', 'name': 'Simulador', 'purpose': 'Metadados', 'repository': 'example/b', 'categories': ['emulation'], 'source_snapshots': []}]}

    def test_query_handles_accents_category_aliases_and_indexed_filter(self):
        self.assertEqual(filter_tools(self.catalog, 'trafego')['count'], 1)
        self.assertEqual(filter_tools(self.catalog, 'RED TEAM')['tools'][0]['id'], 'b')
        self.assertEqual(filter_tools(self.catalog, indexed=True)['tools'][0]['id'], 'a')
        self.assertEqual(filter_tools(self.catalog, category='emulation', indexed=True)['count'], 0)

    def test_unknown_category_or_version_does_not_silently_return_empty(self):
        with self.assertRaises(ValueError):
            filter_tools(self.catalog, category='missing')
        self.catalog['schema_version'] = 2
        with self.assertRaises(ValueError):
            filter_tools(self.catalog)

    def test_retained_catalog_references_actual_locked_sources_and_existing_evidence(self):
        catalog = json.loads((ROOT/'research/tool-catalog.json').read_text())
        sources = {s['id']: s for s in json.loads((ROOT/'sources.lock.json').read_text())['sources']}
        self.assertEqual(len({t['id'] for t in catalog['tools']}), len(catalog['tools']))
        for tool in catalog['tools']:
            self.assertTrue((ROOT/tool['evidence_reference']).is_file())
            self.assertEqual(bool(tool['source_snapshots']), tool['source_status'] == 'source-indexed')
            for source in tool['source_snapshots']:
                self.assertEqual(source['commit'], sources[source['id']]['commit'])
                for notice in source['notices']:
                    self.assertTrue((ROOT/notice).is_file())


class PackageIndexTests(unittest.TestCase):
    def setUp(self):
        self.profiles = {'source_commit': 'a'*40, 'packages': [
            {'name': 'kali-tools-example', 'dependency_fields_raw': {'Depends': '${misc:Depends}, alpha:any (>= 1) [amd64] | beta, gamma', 'Recommends': 'alpha, delta <!nocheck>'}},
            {'name': 'kali-desktop-example', 'dependency_fields_raw': {'Depends': 'desktop-only'}}]}

    def test_retains_alternatives_constraints_and_unresolved_substitutions(self):
        index = build_package_index(self.profiles)
        self.assertEqual([p['name'] for p in index['packages']], ['alpha', 'beta', 'delta', 'gamma'])
        alpha = index['packages'][0]['declarations'][0]
        self.assertEqual(alpha['alternatives_in_clause'], 2)
        self.assertEqual(alpha['alternative'], 'alpha:any (>= 1) [amd64]')
        self.assertEqual(index['unresolved_declarations'][0]['alternative'], '${misc:Depends}')
        self.assertEqual(index['source']['commit'], self.profiles['source_commit'])

    def test_filters_keep_source_scope_and_reject_unknown_profile(self):
        index = build_package_index(self.profiles)
        result = filter_packages(index, query='ALP', profile='kali-tools-example')
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['scope'], index['scope'])
        with self.assertRaises(ValueError):
            filter_packages(index, profile='missing')

    def test_building_index_preserves_the_original_dependency_declarations(self):
        before = copy.deepcopy(self.profiles)
        build_package_index(self.profiles)
        self.assertEqual(self.profiles, before)


if __name__ == '__main__':
    unittest.main()
