"""Local SQLite persistence. Collected content is data, never executable code."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def stamp():
    return datetime.now(timezone.utc).isoformat()


def identifier():
    return uuid4().hex


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            if db.execute('PRAGMA user_version').fetchone()[0] not in (0, 1):
                raise ValueError('Versão de banco não suportada; o arquivo não foi migrado')
            db.executescript('''
            CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, name TEXT NOT NULL, created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY, project TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
              role TEXT NOT NULL, name TEXT NOT NULL, sha256 TEXT NOT NULL, content BLOB NOT NULL, normalized TEXT NOT NULL, created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS reviews(id TEXT PRIMARY KEY, project TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
              document TEXT NOT NULL, source_ids TEXT NOT NULL, created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS decisions(id INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
              review TEXT NOT NULL REFERENCES reviews(id) ON DELETE CASCADE, item TEXT NOT NULL, state TEXT NOT NULL, note TEXT NOT NULL, author TEXT NOT NULL, created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
              question TEXT NOT NULL, response TEXT NOT NULL, created TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS sources_project ON sources(project,created);
            CREATE INDEX IF NOT EXISTS reviews_project ON reviews(project,created);
            CREATE INDEX IF NOT EXISTS decisions_project ON decisions(project,id);
            CREATE TABLE IF NOT EXISTS studio(id TEXT PRIMARY KEY, project TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
              kind TEXT NOT NULL, document TEXT NOT NULL, created TEXT NOT NULL);
            PRAGMA user_version=1;
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    def project(self, project):
        with self.connect() as db:
            row = db.execute('SELECT * FROM projects WHERE id=?', (project,)).fetchone()
        if not row:
            raise ValueError('Projeto não encontrado')
        return dict(row)

    def projects(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM projects ORDER BY created DESC')]

    def create_project(self, name):
        project = {'id': identifier(), 'name': name, 'created': stamp()}
        with self.connect() as db:
            db.execute('INSERT INTO projects VALUES (:id,:name,:created)', project)
        return project

    def delete_project(self, project):
        self.project(project)
        with self.connect() as db:
            db.execute('DELETE FROM projects WHERE id=?', (project,))

    def add_source(self, project, role, name, data, normalized):
        self.project(project)
        source = {'id': identifier(), 'project': project, 'role': role, 'name': name,
                  'sha256': normalized['artifact']['sha256'], 'created': stamp()}
        with self.connect() as db:
            db.execute('INSERT INTO sources VALUES (?,?,?,?,?,?,?,?)',
                       (source['id'], project, role, name, source['sha256'], data, json.dumps(normalized, ensure_ascii=False), source['created']))
        return source

    def sources(self, project, contents=False):
        self.project(project)
        fields = '*' if contents else 'id,project,role,name,sha256,created'
        with self.connect() as db:
            return [dict(r) for r in db.execute(f'SELECT {fields} FROM sources WHERE project=? ORDER BY created,id', (project,))]

    def add_review(self, project, document, source_ids):
        row = {'id': identifier(), 'project': project, 'created': stamp(), 'document': document, 'source_ids': source_ids}
        with self.connect() as db:
            db.execute('INSERT INTO reviews VALUES (?,?,?,?,?)', (row['id'], project, json.dumps(document, ensure_ascii=False), json.dumps(source_ids), row['created']))
        return row

    def latest_review(self, project):
        self.project(project)
        with self.connect() as db:
            row = db.execute('SELECT * FROM reviews WHERE project=? ORDER BY created DESC,id DESC LIMIT 1', (project,)).fetchone()
        if not row:
            return None
        result = dict(row)
        for key in ('document', 'source_ids'):
            result[key] = json.loads(result[key])
        return result

    def decisions(self, project):
        self.project(project)
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM decisions WHERE project=? ORDER BY id', (project,))]

    def add_decision(self, project, review, item, state, note, author):
        with self.connect() as db:
            cursor = db.execute('INSERT INTO decisions(project,review,item,state,note,author,created) VALUES(?,?,?,?,?,?,?)',
                                (project, review, item, state, note, author, stamp()))
            return dict(db.execute('SELECT * FROM decisions WHERE id=?', (cursor.lastrowid,)).fetchone())

    def messages(self, project, limit=50):
        self.project(project)
        with self.connect() as db:
            query = 'SELECT * FROM messages WHERE project=? ORDER BY id DESC'
            rows = list(db.execute(query, (project,))) if limit is None else list(db.execute(query+' LIMIT ?', (project, limit)))
        return [{**dict(r), 'response': json.loads(r['response'])} for r in reversed(rows)]

    def add_message(self, project, question, response):
        self.project(project)
        with self.connect() as db:
            db.execute('INSERT INTO messages(project,question,response,created) VALUES(?,?,?,?)',
                       (project, question, json.dumps(response, ensure_ascii=False), stamp()))

    def studio(self, project):
        self.project(project)
        with self.connect() as db:
            rows = db.execute('SELECT * FROM studio WHERE project=? ORDER BY created,id', (project,)).fetchall()
        return [{**dict(r), 'document': json.loads(r['document'])} for r in rows]

    def add_studio(self, project, kind, document):
        self.project(project)
        result = {'id': identifier(), 'project': project, 'kind': kind, 'document': document, 'created': stamp()}
        with self.connect() as db:
            db.execute('INSERT INTO studio VALUES (?,?,?,?,?)', (result['id'], project, kind, json.dumps(document, ensure_ascii=False), result['created']))
        return result
