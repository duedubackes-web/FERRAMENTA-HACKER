import base64
import copy
import hashlib
from http.client import HTTPConnection
import io
import json
import os
import subprocess
import shutil
from pathlib import Path
import stat
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from app_service import Application
from app_server import LocalServer, MAX_REQUEST
from app_studio import inspect_archive
import app_ai


def payload(name='trivy-synthetic.json', role='trivy'):
    return {'role': role, 'name': name, 'content_base64': base64.b64encode((ROOT/'tests/fixtures'/name).read_bytes()).decode()}


def archive(entries):
    result = io.BytesIO()
    with zipfile.ZipFile(result, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, value in entries:
            z.writestr(name, value)
    return result.getvalue()


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database = Path(self.directory.name)/'atlas.sqlite3'
        self.app = Application(self.database)
        self.project = self.app.create_project('Investigação de teste')['id']

    def tearDown(self):
        self.directory.cleanup()

    def test_demo_integrates_three_producers_and_reproduces(self):
        project = self.app.demo()['id']
        snapshot = self.app.snapshot(project)
        self.assertEqual(len(snapshot['sources']), 4)
        self.assertEqual(snapshot['review']['document']['summary']['items'], 8)
        self.assertEqual(self.app.replay(project)['status'], 'matched')

    def test_chat_rule_question_returns_the_requested_evidence(self):
        project = self.app.demo()['id']
        reply = self.app.chat(project, 'Explique a regra ZAP-HIGH do ZAP')
        self.assertEqual([c.get('rule_id') for c in reply['citations']], ['ZAP-HIGH'])
        self.assertIn('riskcode 3', reply['text'])
        raw = json.loads((ROOT/'tests/fixtures/zap-synthetic.json').read_bytes())
        raw['site'][0]['alerts'] = [copy.deepcopy(raw['site'][0]['alerts'][0]) for _ in range(5)]
        self.app.import_source(project, {'role':'zap','name':'five-alerts.json','content_base64':base64.b64encode(json.dumps(raw).encode()).decode()})
        self.app.review(project)
        self.assertEqual(len(self.app.chat(project, 'Explique a regra ZAP-HIGH do ZAP')['citations']), 3)


    def test_chat_producer_priority_does_not_include_other_producers(self):
        project = self.app.demo()['id']
        reply = self.app.chat(project, 'O que revisar primeiro no ZAP?')
        self.assertTrue(reply['citations'])
        for citation in reply['citations']:
            self.assertEqual(citation['kind'], 'review-item')
            self.assertTrue(all(r['role'] == 'zap' for r in citation['references']))

    def test_chat_technology_name_does_not_hide_coverage_or_sources(self):
        project = self.app.demo()['id']
        for question, kind in [('Quais as limitações do ZAP?', 'review'), ('Quais fontes Trivy foram importadas?', 'source')]:
            with self.subTest(question=question):
                reply = self.app.chat(project, question)
                self.assertTrue(all(c['kind'] == kind for c in reply['citations']))

    def test_export_pins_replay_to_the_exported_review(self):
        self.app.import_source(self.project, payload())
        old = self.app.review(self.project)
        original_snapshot = self.app.snapshot
        def racing_snapshot(project):
            snapshot = original_snapshot(project)
            report = json.loads((ROOT/'tests/fixtures/trivy-synthetic.json').read_bytes())
            report['ArtifactName'] = 'new version during export'
            changed = payload()
            changed['content_base64'] = base64.b64encode(json.dumps(report).encode()).decode()
            self.app.import_source(project, changed)
            self.app.review(project)
            return snapshot
        with patch.object(self.app, 'snapshot', side_effect=racing_snapshot):
            data = self.app.export(self.project, True)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            exported = json.loads(z.read('review.json'))
            replay = json.loads(z.read('replay.json'))
            old_sha = old['document']['inputs']['trivy']['artifact']['sha256']
            self.assertEqual(exported['review_id'], old['document']['review_id'])
            self.assertEqual(replay['sources']['trivy']['expected_sha256'], old_sha)
            self.assertEqual(hashlib.sha256(z.read('originals/trivy.json')).hexdigest(), old_sha)

    def test_persists_sources_reviews_decisions_and_chat_after_restart(self):
        self.app.import_source(self.project, payload())
        review = self.app.review(self.project)
        item = review['document']['items'][0]
        self.app.decision(self.project, {'review_id': review['id'], 'item_id': item['id'], 'state': 'in-review', 'note': 'Aguardando conferência do pacote', 'author': 'Usuário de teste'})
        response = self.app.chat(self.project, 'O que revisar primeiro?')
        self.assertEqual(response['citations'][0]['references'][0]['artifact_sha256'], review['document']['inputs']['trivy']['artifact']['sha256'])
        restarted = Application(self.database).snapshot(self.project)
        self.assertEqual(len(restarted['decisions']), 1)
        self.assertEqual(len(restarted['messages']), 1)
        self.assertEqual(restarted['review']['id'], review['id'])

    def test_reimport_marks_stale_preserves_previous_review_sources(self):
        self.app.import_source(self.project, payload())
        before = self.app.review(self.project)
        self.app.import_source(self.project, payload())
        snapshot = self.app.snapshot(self.project)
        self.assertTrue(snapshot['review_stale'])
        self.assertEqual(snapshot['review']['id'], before['id'])
        self.assertEqual(self.app.replay(self.project)['status'], 'matched')
        response = self.app.chat(self.project, 'Quais fontes foram importadas?')
        self.assertEqual(len(response['citations']), 1)
        self.assertIn(response['citations'][0]['source_id'], before['source_ids'].values())
        self.app.review(self.project)
        self.assertFalse(self.app.snapshot(self.project)['review_stale'])

    def test_invalid_source_never_replaces_existing_source(self):
        self.app.import_source(self.project, payload())
        for data in [{'role': 'shell', 'name': 'test', 'content_base64': ''}, {'role': 'trivy', 'name': '../unused', 'content_base64': '!'}, {'role': 'trivy', 'name': 'bad', 'content_base64': base64.b64encode(b'not json').decode()}]:
            with self.assertRaises(ValueError):
                self.app.import_source(self.project, data)
        self.assertEqual(len(self.app.store.sources(self.project)), 1)

    def test_nmap_pair_is_required_and_empty_review_rejected(self):
        with self.assertRaises(ValueError):
            self.app.review(self.project)
        self.app.import_source(self.project, payload('nmap-synthetic.xml', 'nmap-before'))
        with self.assertRaises(ValueError):
            self.app.review(self.project)

    def test_decision_requires_current_review_existing_item_reason_author_and_state(self):
        self.app.import_source(self.project, payload())
        review = self.app.review(self.project)
        valid = {'review_id': review['id'], 'item_id': review['document']['items'][0]['id'], 'state': 'dismissed', 'note': 'Razão declarada', 'author': 'Autor declarado'}
        for key, value in [('review_id', 'unknown'), ('item_id', 'unknown'), ('state', 'confirmed-vulnerable'), ('note', ''), ('author', '')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.app.decision(self.project, {**valid, key: value})
        self.app.decision(self.project, valid)
        self.app.decision(self.project, {**valid, 'state': 'follow-up'})
        self.assertEqual(len(self.app.store.decisions(self.project)), 2)
        self.app.review(self.project)
        with self.assertRaises(ValueError):
            self.app.decision(self.project, valid)

    def test_projects_are_scoped_and_delete_cascades_all_records(self):
        self.app.import_source(self.project, payload())
        review = self.app.review(self.project)
        self.app.chat(self.project, 'fontes')
        other = self.app.create_project('Outro')['id']
        source = self.app.store.sources(self.project)[0]
        with self.assertRaises(ValueError):
            self.app.source_detail(other, source['id'])
        self.assertEqual(self.app.snapshot(other)['sources'], [])
        self.app.store.delete_project(self.project)
        with self.app.store.connect() as db:
            for table in ('sources', 'reviews', 'decisions', 'messages', 'studio'):
                self.assertEqual(db.execute('SELECT count(*) FROM '+table+' WHERE project=?', (self.project,)).fetchone()[0], 0)
        self.assertEqual(len(self.app.store.projects()), 1)

    def test_export_includes_replay_and_originals_only_when_explicit(self):
        self.app.import_source(self.project, payload())
        self.app.review(self.project)
        with zipfile.ZipFile(io.BytesIO(self.app.export(self.project))) as z:
            self.assertIsNone(z.testzip())
            self.assertFalse(any(name.startswith('originals/') for name in z.namelist()))
            self.assertEqual(json.loads(z.read('replay.json'))['status'], 'matched')
        with zipfile.ZipFile(io.BytesIO(self.app.export(self.project, True))) as z:
            self.assertEqual(z.read('originals/trivy.json'), (ROOT/'tests/fixtures/trivy-synthetic.json').read_bytes())

    def test_chat_capabilities_abstention_and_no_silent_ai_fallback(self):
        reply = self.app.chat(self.project, 'Como REA e Craft Anything estão integrados?')
        self.assertEqual(len(reply['citations']), 2)
        self.assertEqual(reply['model_calls'], 0)
        for alias in ('Metasploit Framework', 'MSF', 'msfconsole'):
            with self.subTest(alias=alias):
                cited = self.app.chat(self.project, 'Como '+alias+' está integrado?')
                self.assertEqual(cited['citations'][0]['tool_id'], 'metasploit')
                self.assertIn('sem runtime', cited['text'])
        self.assertIn('não está embutido', reply['text'])
        self.assertIn('Não encontrei', self.app.chat(self.project, 'xyzzy-unknown-question')['text'])
        with patch.dict(os.environ, {'ATLAS_OLLAMA_MODEL': ''}):
            with self.assertRaises(ValueError):
                self.app.chat(self.project, 'resumo', True)
        self.assertEqual(len(self.app.store.messages(self.project)), 5)

    def test_export_preserves_entire_chat_history_beyond_ui_window(self):
        self.app.import_source(self.project, payload())
        self.app.review(self.project)
        for index in range(51):
            self.app.store.add_message(self.project, 'Pergunta '+str(index), {'text': 'Resposta', 'citations': [], 'mode': 'local-evidence-retrieval'})
        self.assertEqual(len(self.app.snapshot(self.project)['messages']), 50)
        with zipfile.ZipFile(io.BytesIO(self.app.export(self.project))) as z:
            self.assertEqual(len(json.loads(z.read('chat.json'))), 51)

    def test_product_plan_and_source_analysis_persist_and_export(self):
        data = archive([('src/main.py', 'print("never executed")'), ('LICENSE', 'License text'), ('package.json', '{"dependencies":{"example":"1.0"}}')])
        analysis = self.app.inspect_source(self.project, {'content_base64': base64.b64encode(data).decode()})
        plan = self.app.plan(self.project, {'name': 'Produto próprio', 'brief': 'Organizar evidências para pequenas equipes'})
        self.assertEqual(plan['document']['analysis_sha256'], analysis['document']['artifact_sha256'])
        self.assertEqual(len(Application(self.database).snapshot(self.project)['studio']), 2)
        self.assertEqual(self.app.chat(self.project, 'Qual a estrutura do código?')['citations'][0]['record_id'], analysis['id'])
        self.assertEqual(self.app.chat(self.project, 'Qual o plano do produto?')['citations'][0]['record_id'], plan['id'])
        with zipfile.ZipFile(io.BytesIO(self.app.export_studio(self.project))) as z:
            self.assertIn('BACKLOG.md', z.namelist())
            self.assertIn('prototype/index.html', z.namelist())
            self.assertIn('prototype/app.js', z.namelist())
            self.assertEqual(json.loads(z.read('product-plan.json'))['status'], 'draft-requires-validation')


class ArchiveTests(unittest.TestCase):
    def test_static_inventory_hashes_and_declared_dependencies(self):
        data = archive([('src/main.py', 'raise RuntimeError("DO NOT RUN")'), ('package.json', '{"dependencies":{"demo":"^1"}}'), ('LICENSE', 'candidate')])
        result = inspect_archive(data)
        self.assertEqual(result['files'], 3)
        self.assertFalse(result['target_executed'])
        self.assertEqual(result['artifact_sha256'], hashlib.sha256(data).hexdigest())
        self.assertEqual(result['languages'], {'Python': 1})
        self.assertEqual(result['declared_dependencies'][0]['name'], 'demo')
        self.assertEqual(result['entrypoint_candidates'], ['src/main.py'])
        self.assertNotIn('DO NOT RUN', json.dumps(result))

    def test_rejects_unsafe_paths_symlinks_duplicates_invalid_and_bombs(self):
        for name in ['../escape', '/absolute', 'C:/drive', 'dir\\file']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                inspect_archive(archive([(name, 'x')]))
        info = zipfile.ZipInfo('symlink')
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        for data in [archive([(info, '../target')]), b'not zip', archive([('bomb', '0'*100000)])]:
            with self.assertRaises(ValueError):
                inspect_archive(data)
        with patch('app_studio.MAX_EXPANDED', 2), self.assertRaises(ValueError):
            inspect_archive(archive([('a', 'abcd')]))


class ScaffoldTests(unittest.TestCase):
    def test_generated_prototype_escapes_user_text_and_javascript_parses(self):
        from app_studio import blueprint
        from app_scaffold import scaffold
        plan = blueprint('<img src=x onerror=alert(1)>', 'Brief </script><script>alert(1)</script>')
        files = scaffold(plan)
        self.assertNotIn('<img src=x', files['prototype/index.html'])
        self.assertIn('&lt;img', files['prototype/index.html'])
        self.assertNotIn('innerHTML', files['prototype/app.js'])
        self.assertNotIn('fetch(', files['prototype/app.js'])
        if shutil.which('node'):
            with tempfile.TemporaryDirectory() as folder:
                script = Path(folder)/'app.js'
                script.write_text(files['prototype/app.js'])
                result = subprocess.run(['node', '--check', str(script)], capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_future_database_schema_is_not_silently_modified(self):
        import sqlite3
        from app_store import Store
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'future.sqlite3'
            with sqlite3.connect(path) as db:
                db.execute('PRAGMA user_version=99')
            with self.assertRaises(ValueError):
                Store(path)
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 99)


class ModelTests(unittest.TestCase):
    def test_diagnostics_without_model_does_not_connect(self):
        with patch.dict(os.environ, {'ATLAS_OLLAMA_MODEL': ''}), patch('app_ai.urllib.request.build_opener') as build:
            self.assertEqual(app_ai.check_model()['status'], 'not-configured')
        build.assert_not_called()

    def test_diagnostics_distinguishes_ready_missing_and_unavailable_models(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *_): return False
            def read(self, maximum): return b'{"models":[{"name":"installed:latest"}]}'
        for model, expected in [('installed', 'ready'), ('installed:latest', 'ready'), ('missing', 'model-missing')]:
            with patch.dict(os.environ, {'ATLAS_OLLAMA_MODEL': model}), patch('app_ai.urllib.request.build_opener') as build:
                build.return_value.open.return_value = Response()
                result = app_ai.check_model()
                self.assertEqual(result['status'], expected)
                self.assertFalse(result['generation_tested'])
                build.return_value.open.assert_called_once_with('http://127.0.0.1:11434/api/tags', timeout=3)
        with patch.dict(os.environ, {'ATLAS_OLLAMA_MODEL': 'installed'}), patch('app_ai.urllib.request.build_opener') as build:
            build.return_value.open.side_effect = OSError('offline')
            self.assertEqual(app_ai.check_model()['status'], 'unavailable')

    def test_ollama_request_is_fixed_local_bounded_and_has_no_tools(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *_): return False
            def read(self, maximum):
                self.maximum = maximum
                return b'{"message":{"role":"assistant","content":"Resposta local"}}'
        class Opener:
            def open(self, request, timeout):
                self.request, self.timeout = request, timeout
                return Response()
        opener = Opener()
        grounded = {'text': 'Contexto selecionado', 'citations': [{'kind': 'review'}], 'target_executed': False}
        with patch.dict(os.environ, {'ATLAS_OLLAMA_MODEL': 'installed-model'}), patch('app_ai.urllib.request.build_opener', return_value=opener):
            result = app_ai.generate('Pergunta', grounded)
        self.assertEqual(result['model_calls'], 1)
        self.assertEqual(result['text'], 'Resposta local')
        self.assertEqual(opener.request.full_url, 'http://127.0.0.1:11434/api/chat')
        body = json.loads(opener.request.data)
        self.assertFalse(body['stream'])
        self.assertNotIn('tools', body)
        self.assertIn('Contexto selecionado', body['messages'][1]['content'])
        self.assertEqual(result['citations'], grounded['citations'])

    def test_failed_model_is_not_reported_as_success(self):
        with patch.dict(os.environ, {'ATLAS_OLLAMA_MODEL': 'installed-model'}), patch('app_ai.urllib.request.build_opener') as build:
            build.return_value.open.side_effect = OSError('offline')
            with self.assertRaisesRegex(ValueError, 'nenhuma resposta foi simulada'):
                app_ai.generate('test', {})


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.application = Application(Path(self.directory.name)/'atlas.sqlite3')
        self.server = LocalServer(('127.0.0.1', 0), self.application)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_port
        self.headers = {}

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.directory.cleanup()

    def request(self, method, path, body=None, headers=None):
        connection = HTTPConnection('127.0.0.1', self.port, timeout=5)
        merged = dict(self.headers)
        if body is not None:
            body = json.dumps(body)
            merged['Content-Type'] = 'application/json'
        merged.update(headers or {})
        connection.request(method, path, body, merged)
        response = connection.getresponse()
        data = response.read()
        result = response.status, dict(response.getheaders()), data
        connection.close()
        return result

    def login(self):
        status, headers, data = self.request('GET', '/api/bootstrap')
        self.assertEqual(status, 200)
        self.headers = {'Cookie': headers['Set-Cookie'].split(';')[0], 'X-CSRF-Token': json.loads(data)['csrf']}

    def test_diagnostics_requires_session_and_reports_integrity_without_repair(self):
        self.assertEqual(self.request('POST', '/api/diagnostics', {})[0], 401)
        self.login()
        with patch('workbench.verify', return_value=['checksum mismatch: example']), patch('app_ai.check_model', return_value={'status':'not-configured','generation_tested':False}):
            status, _, data = self.request('POST', '/api/diagnostics', {})
        result = json.loads(data)
        self.assertEqual(status, 200)
        self.assertEqual(result['status'], 'attention')
        self.assertEqual(result['integrity']['status'], 'failed')
        self.assertEqual(result['database']['status'], 'ok')
        self.assertFalse(result['target_executed'])

    def test_http_full_flow_project_demo_chat_decision_replay_export_delete(self):
        self.login()
        status, _, data = self.request('POST', '/api/demo', {})
        self.assertEqual(status, 201)
        project = json.loads(data)['id']
        route = '/api/projects/'+project
        status, _, data = self.request('GET', route)
        self.assertEqual(status, 200)
        snapshot = json.loads(data)
        review = snapshot['review']
        status, _, data = self.request('POST', route+'/chat', {'question': 'O que revisar primeiro?'})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data)['model_calls'], 0)
        status, _, _ = self.request('POST', route+'/decisions', {'review_id': review['id'], 'item_id': review['document']['items'][0]['id'], 'state': 'in-review', 'note': 'Conferir escopo', 'author': 'Teste declarado'})
        self.assertEqual(status, 201)
        status, _, data = self.request('POST', route+'/replay', {})
        self.assertEqual(json.loads(data)['status'], 'matched')
        status, _, newer = self.request('POST', route+'/review', {})
        self.assertEqual(status, 201)
        status, _, comparison = self.request('POST', route+'/compare-reviews', {'before_id': review['id'], 'after_id': json.loads(newer)['id']})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(comparison)['comparison']['summary']['unchanged'], 4)
        status, headers, data = self.request('GET', route+'/export')
        self.assertEqual(status, 200)
        self.assertEqual(headers['Content-Type'], 'application/zip')
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            self.assertEqual(len(json.loads(z.read('decisions.json'))), 1)
        self.assertEqual(self.request('DELETE', route, {})[0], 200)
        self.assertEqual(self.request('GET', route)[0], 400)

    def test_sessions_host_origin_csrf_and_payload_limits(self):
        self.assertEqual(self.request('GET', '/api/projects')[0], 401)
        self.assertEqual(self.request('GET', '/api/bootstrap', headers={'Host': 'evil.test'})[0], 403)
        self.assertEqual(self.request('GET', '/api/bootstrap', headers={'Origin': 'https://evil.test'})[0], 403)
        self.assertEqual(self.request('GET', '/api/bootstrap', headers={'Sec-Fetch-Site': 'cross-site'})[0], 403)
        self.login()
        self.assertEqual(self.request('POST', '/api/projects', {'name': 'test'}, {'X-CSRF-Token': 'wrong'})[0], 403)
        self.assertEqual(self.request('POST', '/api/projects', {'name': 'test'}, {'Origin': 'null'})[0], 403)
        self.assertEqual(self.request('POST', '/api/projects', {'name': 'test'}, {'Content-Length': str(MAX_REQUEST+1)})[0], 413)
        self.assertEqual(self.request('POST', '/api/projects', {'name': 'test'}, {'Content-Type': 'text/plain'})[0], 415)

    def test_assets_csp_and_path_traversal(self):
        for path, mime in [('/', 'text/html'), ('/app.css', 'text/css'), ('/app.js', 'text/javascript')]:
            status, headers, data = self.request('GET', path)
            self.assertEqual(status, 200)
            self.assertTrue(headers['Content-Type'].startswith(mime))
            self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])
            self.assertIn('no-store', headers['Cache-Control'])
            self.assertTrue(data)
        self.login()
        self.assertEqual(self.request('GET', '/../../sources.lock.json')[0], 404)
        self.assertEqual(self.request('GET', '/scripts/app_server.py')[0], 404)


if __name__ == '__main__':
    unittest.main()
