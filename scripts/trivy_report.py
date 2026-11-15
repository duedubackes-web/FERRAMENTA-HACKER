"""Original offline reader for the selected vulnerability fields of Trivy JSON v2."""
import hashlib
from pathlib import Path

from json_reports import decode_object, optional_text as _text

VERSION = '1'
MAX_BYTES = 32 * 1024 * 1024
KNOWN_SEVERITIES = {'UNKNOWN', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'}
FIELDS = ('VulnerabilityID', 'PkgID', 'PkgName', 'PkgPath', 'InstalledVersion', 'FixedVersion', 'Status', 'Severity', 'SeveritySource', 'Title', 'PrimaryURL')


def parse_json(data: bytes, path: str) -> dict:
    raw = decode_object(data, 'Trivy JSON', MAX_BYTES)
    if not isinstance(raw, dict) or type(raw.get('SchemaVersion')) is not int or raw['SchemaVersion'] != 2:
        raise ValueError('Expected a Trivy JSON object with SchemaVersion 2')
    producer = raw.get('Trivy')
    if producer is None:
        producer = {}
    if not isinstance(producer, dict):
        raise ValueError('Trivy metadata must be an object')
    for field in ('ArtifactName', 'ArtifactType', 'CreatedAt'):
        _text(raw, field, 'report')
    results = raw.get('Results')
    if results is not None and not isinstance(results, list):
        raise ValueError('Results must be an array or null')
    findings, coverage, warnings = [], [], []
    for i, result in enumerate(results or []):
        if not isinstance(result, dict):
            raise ValueError(f'Results[{i}] must be an object')
        context = f'Results[{i}]'
        target, group, kind = [_text(result, key, context) for key in ('Target', 'Class', 'Type')]
        vulnerabilities = result.get('Vulnerabilities')
        if vulnerabilities is not None and not isinstance(vulnerabilities, list):
            raise ValueError(f'{context}.Vulnerabilities must be an array or null')
        omitted = {key: {'present': key in result, 'count': len(result[key]) if isinstance(result.get(key), list) else None}
                   for key in ('Misconfigurations', 'Secrets', 'Licenses', 'CryptoAssets', 'CustomResources') if key in result}
        coverage.append({'result_index': i, 'target': target, 'class': group, 'type': kind,
                         'vulnerabilities_state': 'missing' if 'Vulnerabilities' not in result else ('null' if vulnerabilities is None else 'array'),
                         'vulnerability_records': len(vulnerabilities or []), 'uninterpreted_categories': omitted})
        for j, vulnerability in enumerate(vulnerabilities or []):
            if not isinstance(vulnerability, dict):
                raise ValueError(f'{context}.Vulnerabilities[{j}] must be an object')
            fields = {key: _text(vulnerability, key, context+f'.Vulnerabilities[{j}]') for key in FIELDS}
            severity = (fields['Severity'] or '').upper()
            normalized = severity if severity in KNOWN_SEVERITIES else None
            if normalized is None:
                warnings.append({'json_pointer': f'/Results/{i}/Vulnerabilities/{j}', 'message': 'Severidade ausente ou não reconhecida; classificação permanece desconhecida.'})
            findings.append({'result_index': i, 'vulnerability_index': j, 'json_pointer': f'/Results/{i}/Vulnerabilities/{j}',
                             'target': target, 'class': group, 'type': kind, 'producer_fields': fields, 'severity_normalized': normalized})
    digest = hashlib.sha256(data).hexdigest()
    return {'schema_version': 1, 'artifact': {'sha256': digest, 'bytes': len(data), 'format': 'trivy-json-v2', 'path': path},
            'analysis_run': {'id': 'trivy-json-v1-'+digest, 'adapter': 'offline-trivy-json', 'adapter_version': VERSION, 'target_executed': False},
            'producer': {'version': _text(producer, 'Version', 'Trivy'), 'created_at': raw.get('CreatedAt'), 'artifact_name': raw.get('ArtifactName'), 'artifact_type': raw.get('ArtifactType')},
            'coverage': {'status': 'selected-vulnerability-fields', 'results_state': 'missing' if 'Results' not in raw else ('null' if results is None else 'array'), 'results': coverage, 'imported_records': len(findings), 'scan_completion': 'not-established'},
            'findings': findings, 'warnings': warnings,
            'limitations': ['Severidade, status e correções são declarações do produtor, sem validação externa ou análise de explorabilidade.',
                            'Results/Vulnerabilities ausentes ou vazios não comprovam ambiente seguro nem quais scanners foram usados.',
                            'Campos de segredos, configuração, licenças, criptografia, contexto da imagem e demais detalhes não são exportados; categorias conhecidas têm apenas presença/contagem.',
                            'Não houve consulta de CVEs, execução do Trivy, alteração de pacotes ou associação a IPs.']}


def import_report(path: Path) -> dict:
    with path.open('rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    return parse_json(data, str(path.resolve()))
