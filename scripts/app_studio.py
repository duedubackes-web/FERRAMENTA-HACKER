"""Bounded, non-executing source-archive inspection and original product planning."""
from collections import Counter
import hashlib
import io
import json
from pathlib import PurePosixPath
import stat
import zipfile

MAX_ARCHIVE = 16 * 1024 * 1024
MAX_EXPANDED = 32 * 1024 * 1024
LANGUAGES = {'.py':'Python', '.ts':'TypeScript', '.tsx':'TypeScript / JSX', '.js':'JavaScript', '.jsx':'JavaScript / JSX', '.rs':'Rust', '.go':'Go', '.java':'Java', '.c':'C', '.h':'C headers', '.cpp':'C++', '.cs':'C#', '.php':'PHP', '.rb':'Ruby', '.html':'HTML', '.css':'CSS', '.sql':'SQL', '.sh':'Shell'}
MANIFESTS = {'package.json', 'pyproject.toml', 'requirements.txt', 'Cargo.toml', 'go.mod', 'pom.xml', 'composer.json', 'Gemfile'}
ENTRYPOINTS = {'main.py', '__main__.py', 'app.py', 'server.py', 'main.ts', 'main.js', 'index.html', 'main.go', 'main.rs', 'Dockerfile'}


def inspect_archive(data):
    if len(data) > MAX_ARCHIVE:
        raise ValueError('ZIP maior que 16 MiB')
    entries, names, languages, manifests, licenses, entrypoints, dependencies = [], set(), Counter(), [], [], [], []
    total = 0
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            records = archive.infolist()
            if len(records) > 2000:
                raise ValueError('ZIP excede 2.000 entradas')
            for info in records:
                name = info.filename
                if info.orig_filename != name:
                    raise ValueError('ZIP contém nome truncado ou inválido')
                path = PurePosixPath(name)
                if not name or path.is_absolute() or '..' in path.parts or '\\' in name or '\x00' in name or ':' in name or name.startswith('/'):
                    raise ValueError('ZIP contém caminho inseguro')
                normalized = path.as_posix()
                if normalized in names:
                    raise ValueError('ZIP contém caminhos duplicados')
                names.add(normalized)
                if stat.S_ISLNK(info.external_attr >> 16) or info.flag_bits & 1:
                    raise ValueError('Links simbólicos e arquivos criptografados não são suportados')
                if info.is_dir():
                    continue
                total += info.file_size
                if total > MAX_EXPANDED or info.file_size > 2 * 1024 * 1024:
                    raise ValueError('ZIP excede orçamento: 32 MiB descomprimidos, 2 MiB por arquivo')
                if info.file_size > max(info.compress_size, 1) * 200:
                    raise ValueError('Taxa de compressão excessiva')
                # Read bounded bytes and validate CRC. Never extract, import or execute archive contents.
                with archive.open(info) as stream:
                    content = stream.read(2 * 1024 * 1024 + 1)
                if len(content) != info.file_size:
                    raise ValueError('Tamanho de entrada ZIP inconsistente')
                language = LANGUAGES.get(path.suffix.lower())
                if language:
                    languages[language] += 1
                entries.append({'path': normalized, 'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest(), 'language': language})
                if path.name in MANIFESTS:
                    manifests.append(normalized)
                if path.name.lower().startswith(('license', 'licence', 'copying', 'notice')):
                    licenses.append(normalized)
                if path.name in ENTRYPOINTS:
                    entrypoints.append(normalized)
                if path.name == 'package.json' and len(content) <= 256 * 1024:
                    try:
                        package = json.loads(content)
                        if isinstance(package, dict):
                            for field in ('dependencies', 'devDependencies'):
                                values = package.get(field)
                                if isinstance(values, dict):
                                    dependencies.extend({'manifest': normalized, 'scope': field, 'name': key, 'declared_version': value} for key, value in values.items() if isinstance(value, str))
                    except (ValueError, UnicodeError, RecursionError):
                        pass
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, EOFError) as error:
        raise ValueError('ZIP inválido ou formato não suportado') from error
    return {'schema_version': 1, 'method': 'static-archive-map-v1', 'artifact_sha256': hashlib.sha256(data).hexdigest(),
            'files': len(entries), 'expanded_bytes': total, 'languages': dict(languages), 'manifests': manifests,
            'license_files': licenses, 'entrypoint_candidates': entrypoints, 'declared_dependencies': dependencies,
            'inventory': entries, 'target_executed': False,
            'limitations': ['Inventário estrutural, não análise semântica completa ou engenharia reversa de binários.',
                            'Arquivos de licença são candidatos encontrados pelo nome; direitos de reutilização não foram estabelecidos.',
                            'Dependências extraídas apenas de package.json; versões são declarações, sem instalação ou auditoria de vulnerabilidades.',
                            'Nomes de caminhos e manifestos podem conter dados sensíveis; conteúdo de fonte não é incorporado ao resultado.']}


def blueprint(name, brief, analysis=None):
    return {'schema_version': 1, 'method': 'original-product-blueprint-template-v1', 'name': name, 'brief': brief,
            'status': 'draft-requires-validation', 'analysis_sha256': analysis['artifact_sha256'] if analysis else None,
            'principles': ['Projetar uma implementação própria a partir de requisitos observáveis e autorizados.',
                           'Separar inspiração de produto, evidência técnica e hipóteses a validar.',
                           'Cada automação precisa de entradas explícitas, limites e resultados reproduzíveis.'],
            'modules': [{'id': 'workspace', 'name': 'Workspace e projetos', 'acceptance': 'Criar, selecionar, exportar e excluir os dados de um projeto.'},
                        {'id': 'evidence', 'name': 'Fontes e rastreabilidade', 'acceptance': 'Preservar hash, origem, recorte e avisos em cada importação.'},
                        {'id': 'chat', 'name': 'Chat contextual', 'acceptance': 'Distinguir recuperação de evidência e texto gerado; permitir abrir as fontes.'},
                        {'id': 'build', 'name': 'Planejamento de produção', 'acceptance': 'Converter requisitos em backlog revisável, sem alegar implementação não testada.'},
                        {'id': 'delivery', 'name': 'Entrega e operação', 'acceptance': 'Verificar testes, exportação, acesso, restauração e observabilidade antes de publicar.'}],
            'backlog': [{'priority': 'P0', 'task': 'Validar o problema com cinco usuários do público descrito', 'done_when': 'Registrar tarefas reais, dificuldades e critérios de utilidade.'},
                        {'priority': 'P0', 'task': 'Definir um único fluxo principal ponta a ponta', 'done_when': 'Entrada, saída e casos de erro têm critérios verificáveis.'},
                        {'priority': 'P1', 'task': 'Implementar interface e persistência do fluxo principal', 'done_when': 'Operação completa sobrevive a reinício e tem teste de integração.'},
                        {'priority': 'P1', 'task': 'Avaliar respostas do chatbot com um corpus de perguntas', 'done_when': 'Medir cobertura, referências corretas e respostas sem suporte.'},
                        {'priority': 'P1', 'task': 'Preparar autenticação e isolamento para eventual serviço multiusuário', 'done_when': 'Dados de usuários distintos não podem ser acessados entre si.'},
                        {'priority': 'P2', 'task': 'Definir distribuição, custos e cobrança após validação', 'done_when': 'Usuários validaram o fluxo e os custos foram medidos.'}],
            'research_tracks': [{'reference': 'Lovable / v0', 'opportunity': 'Brief conversacional, iteração de interface e prévia do resultado.', 'evidence_type': 'product-design-hypothesis'},
                                {'reference': 'Vercel', 'opportunity': 'Separar construção, verificação, prévia e publicação.', 'evidence_type': 'product-design-hypothesis'},
                                {'reference': 'REA / Craft Anything', 'opportunity': 'Conectar pesquisa de artefatos a documentação de decisões e produção própria.', 'evidence_type': 'integration-proposal'}],
            'limitations': ['Plano gerado por template explícito, não implementação automática nem equivalência com produtos citados.',
                            'A novidade de mercado e a utilidade precisam de validação; nenhum componente proprietário foi extraído.']}
