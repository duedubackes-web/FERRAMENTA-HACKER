#!/usr/bin/env python3
"""Atlas local web application. Run: python scripts/app_server.py"""
import argparse
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import sqlite3
import sys
from urllib.parse import urlsplit, parse_qs

from app_service import Application, ROOT
from app_ai import model_name
from app_version import VERSION
from json_reports import decode_object

MAX_REQUEST = 44 * 1024 * 1024
STATIC = {'/': ('index.html', 'text/html; charset=utf-8'), '/app.css': ('app.css', 'text/css; charset=utf-8'), '/app.js': ('app.js', 'text/javascript; charset=utf-8')}
STATIC.update({
    f'/vigilia/{name}': (f'vigilia/{name}', mime)
    for name, mime in {
        'style.css': 'text/css; charset=utf-8',
        'identity.css': 'text/css; charset=utf-8',
        'lion-paw.png': 'image/png',
        'app.js': 'text/javascript; charset=utf-8',
        'orchestrator.js': 'text/javascript; charset=utf-8',
        'hub.js': 'text/javascript; charset=utf-8',
        'labs.js': 'text/javascript; charset=utf-8',
        'vigilia.jpg': 'image/jpeg',
    }.items()
})
STATIC['/vigilia/'] = ('vigilia/index.html', 'text/html; charset=utf-8')


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, application):
        if address[0] != '127.0.0.1':
            raise ValueError('This single-user server must bind to 127.0.0.1')
        super().__init__(address, Handler)
        self.application = application
        self.session = secrets.token_urlsafe(32)
        self.csrf = secrets.token_urlsafe(32)
        self.origin = f'http://127.0.0.1:{self.server_port}'


class Handler(BaseHTTPRequestHandler):
    server_version = 'AtlasLocal/1'
    def log_message(self, *_):
        pass

    def respond(self, status, data, content_type='application/json; charset=utf-8', extra=None):
        if not isinstance(data, bytes):
            data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def session_valid(self):
        try:
            jar = cookies.SimpleCookie(self.headers.get('Cookie', ''))
            value = jar['atlas_session'].value if 'atlas_session' in jar else ''
            return secrets.compare_digest(value, self.server.session)
        except cookies.CookieError:
            return False

    def dispatch(self, method):
        if self.headers.get('Host') != urlsplit(self.server.origin).netloc:
            return self.respond(403, {'error': 'Host não permitido. Use '+self.server.origin})
        origin = self.headers.get('Origin')
        if origin is not None and origin != self.server.origin:
            return self.respond(403, {'error': 'Origem não permitida'})
        if self.headers.get('Sec-Fetch-Site') == 'cross-site':
            return self.respond(403, {'error': 'Requisição entre sites não permitida'})
        url = urlsplit(self.path)
        path = url.path
        app = self.server.application
        if method == 'GET' and path in STATIC:
            name, mime = STATIC[path]
            return self.respond(200, (ROOT/'app'/name).read_bytes(), mime)
        if method == 'GET' and path == '/api/bootstrap':
            return self.respond(200, {'csrf': self.server.csrf, 'mode': 'local-single-user', 'chat_mode': 'local-evidence-retrieval', 'version': VERSION, 'model_configured': bool(model_name()), 'model': model_name()}, extra={'Set-Cookie': 'atlas_session='+self.server.session+'; HttpOnly; SameSite=Strict; Path=/'})
        if not self.session_valid():
            return self.respond(401, {'error': 'Abra o aplicativo para iniciar a sessão local'})
        payload = {}
        if method in ('POST', 'DELETE'):
            if not secrets.compare_digest(self.headers.get('X-CSRF-Token', ''), self.server.csrf):
                return self.respond(403, {'error': 'Sessão inválida. Recarregue a página'})
            if self.headers.get('Transfer-Encoding'):
                return self.respond(400, {'error': 'Transfer-Encoding não suportado'})
            length = self.headers.get('Content-Length', '')
            if not length.isascii() or not length.isdecimal() or not 0 < int(length) <= MAX_REQUEST:
                return self.respond(413, {'error': 'Corpo ausente ou maior que o limite'})
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                return self.respond(415, {'error': 'Use application/json'})
            self.connection.settimeout(30)
            payload = decode_object(self.rfile.read(int(length)), 'API request', MAX_REQUEST)
        parts = path.strip('/').split('/')
        if path == '/api/projects':
            if method == 'GET':
                return self.respond(200, app.store.projects())
            if method == 'POST':
                return self.respond(201, app.create_project(payload.get('name')))
        if path == '/api/diagnostics' and method == 'POST':
            return self.respond(200, app.diagnostics())
        if path == '/api/demo' and method == 'POST':
            return self.respond(201, app.demo())
        if path == '/api/capabilities' and method == 'GET':
            return self.respond(200, app.capabilities)
        if path == '/api/catalog' and method == 'GET':
            return self.respond(200, app.catalog)
        if len(parts) >= 3 and parts[:2] == ['api', 'projects']:
            project = parts[2]
            if len(parts) == 3:
                if method == 'GET':
                    return self.respond(200, app.snapshot(project))
                if method == 'DELETE':
                    app.store.delete_project(project)
                    return self.respond(200, {'deleted': True})
            if len(parts) == 5 and parts[3] == 'sources' and method == 'GET':
                return self.respond(200, app.source_detail(project, parts[4]))
            if len(parts) == 4:
                action = parts[3]
                if method == 'POST' and action == 'sources':
                    return self.respond(201, app.import_source(project, payload))
                if method == 'POST' and action == 'review':
                    return self.respond(201, app.review(project))
                if method == 'POST' and action == 'decisions':
                    return self.respond(201, app.decision(project, payload))
                if method == 'POST' and action == 'chat':
                    return self.respond(200, app.chat(project, payload.get('question'), payload.get('use_model', False)))
                if method == 'POST' and action == 'inspect-source':
                    return self.respond(201, app.inspect_source(project, payload))
                if method == 'POST' and action == 'blueprint':
                    return self.respond(201, app.plan(project, payload))
                if method == 'GET' and action == 'export-studio':
                    return self.respond(200, app.export_studio(project), 'application/zip', {'Content-Disposition': 'attachment; filename="atlas-product-plan.zip"'})
                if method == 'POST' and action == 'compare-reviews':
                    return self.respond(200, app.compare(project, payload.get('before_id'), payload.get('after_id')))
                if method == 'POST' and action == 'replay':
                    return self.respond(200, app.replay(project))
                if method == 'GET' and action == 'export':
                    originals = parse_qs(url.query).get('originals') == ['1']
                    return self.respond(200, app.export(project, originals), 'application/zip', {'Content-Disposition': 'attachment; filename="atlas-project.zip"'})
        self.respond(404, {'error': 'Rota não encontrada'})

    def handle_request(self, method):
        try:
            self.dispatch(method)
        except (ValueError, KeyError, TypeError, UnicodeError) as error:
            self.respond(400, {'error': str(error)})
        except (OSError, sqlite3.Error):
            self.respond(500, {'error': 'Não foi possível acessar o armazenamento local'})

    def do_GET(self):
        self.handle_request('GET')

    def do_POST(self):
        self.handle_request('POST')

    def do_DELETE(self):
        self.handle_request('DELETE')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--database', type=Path, default=ROOT/'work/atlas.sqlite3')
    parser.add_argument('--check', action='store_true', help='Check integrity, SQLite and optional local model; exit without serving')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('Port must be between 1 and 65535')
    try:
        application = Application(args.database)
        if args.check:
            result = application.diagnostics()
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result['status'] == 'ok' else 1
        server = LocalServer(('127.0.0.1', args.port), application)
    except (OSError, sqlite3.Error, ValueError) as error:
        print(f'Cannot start Atlas: {error}', file=sys.stderr)
        return 2
    print('Atlas disponível em '+server.origin+' — Ctrl+C para encerrar.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
