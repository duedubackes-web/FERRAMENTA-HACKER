import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from app_service import Application
from verify_tool_inventory import verify_tools


class TechnologyDossierTests(unittest.TestCase):
    def test_dossiers_reference_locked_files_and_findings(self):
        sources={s['id']:s for s in json.loads((ROOT/'sources.lock.json').read_text())['sources']}
        findings={f['id']:f for f in json.loads((ROOT/'research/findings.json').read_text())}
        dossiers=json.loads((ROOT/'research/technology-dossiers.json').read_text())['dossiers']
        for dossier in dossiers:
            source=sources[dossier['id']]
            self.assertEqual(dossier['commit'],source['commit'])
            with gzip.open(ROOT/'research/inventories'/f"{dossier['id']}.jsonl.gz",'rt') as stream:
                paths={r['path'] for r in map(json.loads,stream)}
            for fact in dossier['facts']:
                self.assertEqual(fact,findings[fact['id']])
                self.assertEqual(fact['commit'],source['commit'])
                self.assertIn(fact['path'],paths)
                self.assertIn('/blob/'+source['commit']+'/',fact['url'])
                self.assertGreater(fact['line'],0)

    def test_crosschecks_preserve_container_limits_and_available_hash_counts(self):
        records=json.loads((ROOT/'research/evidence/metasploit-set-crosschecks.json').read_text())['records']
        sources={s['id']:s for s in json.loads((ROOT/'sources.lock.json').read_text())['sources']}
        for record in records:
            source=sources[record['source_id']]
            self.assertEqual(record['root_files'],source['tracked_files']-len(source['unfetched_gitlinks']))
            self.assertEqual(record['craft']['all_root_hashes_matched'],record['root_files'])
            self.assertEqual(record['rea']['root_hashes_matched']+len(record['rea']['unhashed_root_entries']),record['root_files'])
            result=verify_tools(record['source_id'],ROOT/'research/evidence'/f"craft-{record['source_id']}-research.json.gz",ROOT/'research/evidence'/f"rea-{record['source_id']}-research.json.gz")
            self.assertEqual(result['craft_root_hashes_matched'],record['root_files'])
            self.assertEqual(result['rea_root_hashes_matched'],record['rea']['root_hashes_matched'])
            self.assertFalse(record['target_executed'])
            self.assertEqual(record['craft']['coverage']['status'],'partial')
            self.assertTrue(record['snapshot_verification']['per_entry_sha256_verified'])
            for tool in ('craft','rea'):
                with gzip.open(ROOT/'research/evidence'/f"{tool}-{record['source_id']}-research.json.gz",'rt') as stream:
                    evidence=json.load(stream)
                observed=evidence['subject']['sha256'] if tool=='craft' else evidence['subject']['digest']['sha256']
                self.assertEqual(observed,source['archive_sha256'])

    def test_chat_uses_source_facts_and_preserves_two_technology_citations(self):
        with tempfile.TemporaryDirectory() as folder:
            app=Application(Path(folder)/'test.sqlite3');project=app.create_project('Pesquisa')['id']
            response=app.chat(project,'Qual a arquitetura do Metasploit e SET?')
            self.assertEqual({c['tool_id'] for c in response['citations']},{'metasploit','set'})
            self.assertTrue(all(c['kind']=='source-research' for c in response['citations']))
            self.assertEqual(response['model_calls'],0)
            self.assertIn('pesquisa estática seletiva',response['text'])
            self.assertIn('não comprova',app.dossier('set')['facts'][0]['limit'])
            self.assertIn('MetasploitV5',app.chat(project,'Arquitetura do msfconsole')['text'])
            self.assertEqual(app.chat(project,'Como setoolkit está integrado?')['citations'][0]['kind'],'capability')

    def test_dossiers_are_explicit_and_unknown_ids_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            app=Application(Path(folder)/'test.sqlite3')
            for value in ('../sources.lock.json','unknown',None,[]):
                with self.assertRaises(ValueError):app.dossier(value)
            self.assertEqual(app.dossier('set')['kind'],'selected-static-source-research')

    def test_crosscheck_rejects_tampered_tool_hash(self):
        with gzip.open(ROOT/'research/evidence/craft-set-research.json.gz','rt') as stream:
            craft=json.load(stream)
        craft['result']['entries'][0]['sha256']='0'*64
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'tampered.json'
            path.write_text(json.dumps(craft))
            with self.assertRaisesRegex(ValueError,'Craft root hash mismatch'):
                verify_tools('set',path,ROOT/'research/evidence/rea-set-research.json.gz')
