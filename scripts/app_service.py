"""Application use cases built on the existing offline adapters."""
import base64
import binascii
import io
import json
from pathlib import Path
import tempfile
import zipfile

from app_chat import answer
from app_version import VERSION
from app_store import Store
from app_studio import inspect_archive, blueprint, MAX_ARCHIVE
from app_scaffold import scaffold
import app_ai
from review_replay import PARSERS, MAX_BYTES, replay_review
from review_rules import build_review
from nmap_compare import compare_reports
from review_html import render_html

ROOT = Path(__file__).resolve().parents[1]
STATES = {'open', 'in-review', 'follow-up', 'dismissed'}


def text(value, name, maximum, minimum=1):
    if not isinstance(value, str) or not minimum <= len(value.strip()) <= maximum or '\x00' in value:
        raise ValueError(f'{name}: informe entre {minimum} e {maximum} caracteres')
    return value.strip()


class Application:
    def __init__(self, database):
        self.store = Store(database)
        self.capabilities = json.loads((ROOT/'research/app-capabilities.json').read_text())
        self.catalog = json.loads((ROOT/'research/tool-catalog.json').read_text())

    def create_project(self, name):
        return self.store.create_project(text(name, 'Nome', 100))

    def import_source(self, project, payload):
        role = payload.get('role')
        if not isinstance(role, str) or role not in PARSERS:
            raise ValueError('Selecione um tipo de relatório válido')
        name = text(payload.get('name'), 'Nome do arquivo', 200)
        encoded = payload.get('content_base64')
        if not isinstance(encoded, str) or len(encoded) > (MAX_BYTES + 2)//3*4:
            raise ValueError('Arquivo ausente ou maior que 32 MiB')
        try:
            data = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as error:
            raise ValueError('Conteúdo base64 inválido') from error
        normalized = PARSERS[role](data, 'uploaded-local-report')
        return self.store.add_source(project, role, name, data, normalized)

    def review(self, project):
        sources = self.store.sources(project, contents=True)
        selected = {s['role']: s for s in sources}
        if ('nmap-before' in selected) != ('nmap-after' in selected):
            raise ValueError('Importe os dois relatórios Nmap, anterior e atual, antes de gerar a revisão')
        if not selected:
            raise ValueError('Importe ao menos um relatório Trivy/ZAP ou um par Nmap')
        parsed = {role: PARSERS[role](s['content'], 'stored:'+s['id']) for role, s in selected.items()}
        comparison = compare_reports(parsed['nmap-before'], parsed['nmap-after']) if 'nmap-before' in parsed else None
        document = build_review(comparison, parsed.get('trivy'), parsed.get('zap'))
        return self.store.add_review(project, document, {role: s['id'] for role, s in selected.items()})

    def snapshot(self, project):
        info = self.store.project(project)
        sources = self.store.sources(project)
        latest = self.store.latest_review(project)
        active = {s['role']: s['id'] for s in sources}
        return {'project': info, 'sources': sources, 'review': latest,
                'review_stale': bool(latest and latest['source_ids'] != active),
                'decisions': self.store.decisions(project), 'messages': self.store.messages(project), 'studio': self.store.studio(project)}

    def decision(self, project, payload):
        latest = self.store.latest_review(project)
        if not latest or payload.get('review_id') != latest['id']:
            raise ValueError('A revisão mudou. Atualize a tela antes de registrar uma decisão')
        item = payload.get('item_id')
        if item not in {i['id'] for i in latest['document']['items']}:
            raise ValueError('Item não encontrado nesta revisão')
        state = payload.get('state')
        if not isinstance(state, str) or state not in STATES:
            raise ValueError('Estado de decisão inválido')
        note = text(payload.get('note'), 'Justificativa', 2000)
        author = text(payload.get('author'), 'Responsável declarado', 100)
        return self.store.add_decision(project, latest['id'], item, state, note, author)

    def chat(self, project, question, use_model=False):
        question = text(question, 'Pergunta', 2000)
        latest = self.store.latest_review(project)
        sources = self.store.sources(project)
        if latest:
            ids = set(latest['source_ids'].values())
            sources = [s for s in sources if s['id'] in ids]
        response = answer(question, latest['document'] if latest else None, sources, self.catalog)
        from app_chat import tokens
        query = tokens(question)
        matched = [c for c in self.capabilities['capabilities'] if query & tokens(c['name']+' '+c['id'])]
        evidence_reply = any(c['kind'] in {'review-item', 'review', 'source'} for c in response['citations'])
        integration_question = bool(query & {'integrado', 'integrados', 'integrada', 'integradas', 'integracao', 'embutido', 'embutidas', 'runtime'})
        if matched and (integration_question or not evidence_reply):
            response['text'] = '\n\n'.join(c['name']+' · '+c['status']+'\n'+c['description'] for c in matched)
            response['citations'] = [{'kind': 'capability', 'tool_id': c['id'], 'source': c['source']} for c in matched]
        if not matched:
            records = self.store.studio(project)
            analyses = [r for r in records if r['kind'] == 'analysis']
            plans = [r for r in records if r['kind'] == 'blueprint']
            record = (analyses[-1] if analyses and query & {'estrutura', 'linguagens', 'manifestos', 'licencas', 'zip', 'codigo'} else
                      plans[-1] if plans and query & {'plano', 'produto', 'backlog', 'prototipo', 'brief'} else None)
            if record:
                doc = record['document']
                if record['kind'] == 'analysis':
                    response['text'] = str(doc['files'])+' arquivos mapeados. Linguagens: '+', '.join(doc['languages'])+'\nManifestos: '+', '.join(doc['manifests'])+'\n'+' '.join(doc['limitations'])
                else:
                    response['text'] = doc['name']+'\nBrief declarado: '+doc['brief']+'\n\n'+ '\n'.join(t['priority']+' · '+t['task'] for t in doc['backlog'])+'\n\nPlano baseado em template; requer validação.'
                response['citations'] = [{'kind': 'studio', 'record_id': record['id'], 'method': doc['method']}]
        if type(use_model) is not bool:
            raise ValueError('use_model deve ser booleano')
        if use_model:
            response = app_ai.generate(question, response, self.store.messages(project)[-3:])
        response['review_record_id'] = latest['id'] if latest else None
        self.store.add_message(project, question, response)
        return response

    def replay(self, project):
        return self._replay_review(project, self.store.latest_review(project))

    def _replay_review(self, project, latest):
        if not latest:
            raise ValueError('Gere uma revisão antes de conferir a reprodução')
        sources = {s['id']: s for s in self.store.sources(project, contents=True)}
        with tempfile.TemporaryDirectory() as directory:
            paths = {}
            for role, source_id in latest['source_ids'].items():
                path = Path(directory)/role
                path.write_bytes(sources[source_id]['content'])
                paths[role] = path
            return replay_review(latest['document'], paths)

    def export(self, project, include_sources=False):
        state = self.snapshot(project)
        state['messages'] = self.store.messages(project, limit=None)
        latest = state['review']
        if not latest:
            raise ValueError('Gere uma revisão antes de exportar')
        result = io.BytesIO()
        def encoded(value):
            return json.dumps(value, ensure_ascii=False, indent=2).encode('utf-8')
        with zipfile.ZipFile(result, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('review.json', encoded(latest['document']))
            archive.writestr('review.html', render_html(latest['document']))
            archive.writestr('project.json', encoded(state['project']))
            archive.writestr('decisions.json', encoded(state['decisions']))
            archive.writestr('chat.json', encoded(state['messages']))
            archive.writestr('studio.json', encoded(state['studio']))
            archive.writestr('sources.json', encoded(state['sources']))
            archive.writestr('replay.json', encoded(self._replay_review(project, latest)))
            if include_sources:
                source_rows = {s['id']: s for s in self.store.sources(project, contents=True)}
                for role, source_id in latest['source_ids'].items():
                    archive.writestr('originals/'+role+('.xml' if role.startswith('nmap-') else '.json'), source_rows[source_id]['content'])
            archive.writestr('README.txt', 'Exportação local Atlas / FERRAMENTA-HACKER. Decisões são declarações do usuário, sem autenticação de identidade.\nFontes originais: '+('incluídas; podem conter dados sensíveis.' if include_sources else 'não incluídas; preserve-as separadamente para reprodução.')+'\nReprodução confirma consistência, não autenticidade. Fontes e derivados podem conter dados sensíveis.\n')
        return result.getvalue()

    def demo(self):
        project = self.create_project('Laboratório demonstrativo')
        for role, name in [('nmap-before', 'nmap-synthetic.xml'), ('nmap-after', 'nmap-synthetic-after.xml'), ('trivy', 'trivy-synthetic.json'), ('zap', 'zap-synthetic.json')]:
            data = (ROOT/'tests/fixtures'/name).read_bytes()
            self.import_source(project['id'], {'role': role, 'name': name, 'content_base64': base64.b64encode(data).decode()})
        self.review(project['id'])
        return project

    def source_detail(self, project, source_id):
        for source in self.store.sources(project, contents=True):
            if source['id'] == source_id:
                return {'id': source_id, 'name': source['name'], 'role': source['role'], 'normalized': json.loads(source['normalized'])}
        raise ValueError('Fonte não encontrada neste projeto')

    def inspect_source(self, project, payload):
        encoded = payload.get('content_base64')
        if not isinstance(encoded, str) or len(encoded) > (MAX_ARCHIVE + 2)//3*4:
            raise ValueError('ZIP ausente ou maior que 16 MiB')
        try:
            data = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as error:
            raise ValueError('ZIP base64 inválido') from error
        return self.store.add_studio(project, 'analysis', inspect_archive(data))

    def plan(self, project, payload):
        name = text(payload.get('name'), 'Nome do produto', 100)
        brief = text(payload.get('brief'), 'Brief', 4000)
        analyses = [r['document'] for r in self.store.studio(project) if r['kind'] == 'analysis']
        return self.store.add_studio(project, 'blueprint', blueprint(name, brief, analyses[-1] if analyses else None))

    def export_studio(self, project):
        records = self.store.studio(project)
        plans = [r['document'] for r in records if r['kind'] == 'blueprint']
        if not plans:
            raise ValueError('Crie um plano de produto antes de exportar')
        plan = plans[-1]
        result = io.BytesIO()
        with zipfile.ZipFile(result, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path, content in scaffold(plan).items():
                archive.writestr(path, content)
            archive.writestr('product-plan.json', json.dumps(plan, ensure_ascii=False, indent=2))
            archive.writestr('source-analyses.json', json.dumps([r for r in records if r['kind'] == 'analysis'], ensure_ascii=False, indent=2))
            archive.writestr('README.md', '# '+plan['name']+'\n\n'+plan['brief']+'\n\nPlano original em rascunho. Não é código de um produto implementado.\n')
            archive.writestr('BACKLOG.md', '# Backlog de validação e construção\n\n'+'\n'.join('- [ ] '+t['priority']+' — '+t['task']+': '+t['done_when'] for t in plan['backlog']))
        return result.getvalue()

    def diagnostics(self):
        from workbench import verify
        errors = verify(ROOT)
        with self.store.connect() as db:
            database_ok = [row[0] for row in db.execute('PRAGMA quick_check')] == ['ok']
            foreign_keys_ok = db.execute('PRAGMA foreign_key_check').fetchone() is None
        model = app_ai.check_model()
        local_ok = not errors and database_ok and foreign_keys_ok
        return {'schema_version': 1, 'version': VERSION,
                'status': 'ok' if local_ok and model['status'] in {'ready', 'not-configured'} else 'attention',
                'integrity': {'status': 'ok' if not errors else 'failed', 'errors': errors},
                'database': {'status': 'ok' if database_ok and foreign_keys_ok else 'failed', 'schema_version': 1},
                'chat': {'local_retrieval': 'available', 'optional_model': model},
                'target_executed': False,
                'limitations': ['A integridade não estabelece autenticidade. quick_check não substitui backup e teste de restauração.',
                                'A lista de modelos não testa geração, qualidade de respostas ou capacidade do equipamento.']}
