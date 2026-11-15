"""Original, inert reader for selected ZAP Traditional JSON/JSON Plus fields."""
import hashlib
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from json_reports import decode_object, optional_text

VERSION = '1'
MAX_BYTES = 32 * 1024 * 1024
RISK_LABELS = {0: 'Informational', 1: 'Low', 2: 'Medium', 3: 'High'}
CONFIDENCE_LABELS = {0: 'False Positive', 1: 'Low', 2: 'Medium', 3: 'High', 4: 'Confirmed'}


def _scalar(record, key, context):
    value = record.get(key)
    if value is not None and type(value) not in (str, int):
        raise ValueError(f'{context}.{key} must be a string, integer or null')
    return value


def _code(value, known):
    if type(value) is int:
        return value if value in known else None
    if isinstance(value, str) and value in {str(k) for k in known}:
        return int(value)
    return None


def _array(record, key, context):
    value = record.get(key)
    if value is not None and not isinstance(value, list):
        raise ValueError(f'{context}.{key} must be an array or null')
    return value, 'missing' if key not in record else ('null' if value is None else 'array')


def display_uri(value):
    if value is None:
        return {'uri': None, 'status': 'not-supplied'}
    try:
        parsed = urlsplit(value)
        if parsed.scheme.lower() not in ('http', 'https') or not parsed.hostname:
            return {'uri': None, 'status': 'unsupported-or-invalid'}
        host = parsed.hostname
        netloc = '['+host+']' if ':' in host else host
        if parsed.port is not None:
            netloc += ':'+str(parsed.port)
        omitted = bool(parsed.query or parsed.fragment or parsed.username is not None or parsed.password is not None)
        return {'uri': urlunsplit((parsed.scheme.lower(), netloc, parsed.path, '', '')),
                'status': 'userinfo-query-fragment-omitted' if omitted else 'no-omitted-components'}
    except ValueError:
        return {'uri': None, 'status': 'unsupported-or-invalid'}


def parse_json(data: bytes, path: str) -> dict:
    raw = decode_object(data, 'ZAP JSON', MAX_BYTES)
    version = optional_text(raw, '@version', 'report')
    if not version:
        raise ValueError('Expected ZAP Traditional JSON with a nonempty @version')
    producer = {key: optional_text(raw, key, 'report') for key in ('@programName', '@version', '@generated', 'created')}
    sites, sites_state = _array(raw, 'site', 'report')
    findings, coverage, warnings = [], [], []
    for i, site in enumerate(sites or []):
        if not isinstance(site, dict):
            raise ValueError(f'site[{i}] must be an object')
        display = display_uri(optional_text(site, '@name', f'site[{i}]'))
        alerts, alerts_state = _array(site, 'alerts', f'site[{i}]')
        coverage.append({'site_index': i, 'site_display': display, 'alerts_state': alerts_state, 'alert_records': len(alerts or [])})
        for j, alert in enumerate(alerts or []):
            pointer = f'/site/{i}/alerts/{j}'
            if not isinstance(alert, dict):
                raise ValueError(f'{pointer} must be an object')
            fields = {key: optional_text(alert, key, pointer) for key in ('alert', 'name', 'riskdesc')}
            fields.update({key: _scalar(alert, key, pointer) for key in ('pluginid', 'alertRef', 'riskcode', 'confidence', 'count', 'cweid', 'wascid', 'sourceid')})
            risk, confidence = _code(fields['riskcode'], RISK_LABELS), _code(fields['confidence'], CONFIDENCE_LABELS)
            instances, state = _array(alert, 'instances', pointer)
            selected = []
            for k, instance in enumerate(instances or []):
                if not isinstance(instance, dict):
                    raise ValueError(f'{pointer}/instances/{k} must be an object')
                uri = display_uri(optional_text(instance, 'uri', pointer+f'/instances/{k}'))
                selected.append({'instance_index': k, 'json_pointer': pointer+f'/instances/{k}', 'method': optional_text(instance, 'method', pointer+f'/instances/{k}'), 'uri_display': uri})
                if uri['status'] == 'unsupported-or-invalid':
                    warnings.append({'json_pointer': pointer+f'/instances/{k}/uri', 'message': 'URI não suportada/inválida omitida da exportação.'})
            if risk is None or confidence is None:
                warnings.append({'json_pointer': pointer, 'message': 'Risco ou confiança ausentes/não reconhecidos; classificação permanece desconhecida.'})
            count = fields['count']
            declared = count if type(count) is int and count >= 0 else (int(count) if isinstance(count, str) and count.isascii() and count.isdecimal() and len(count) <= 10 else None)
            if declared is not None and state == 'array' and declared != len(selected):
                warnings.append({'json_pointer': pointer, 'message': 'Contagem declarada difere do número de instâncias presentes.'})
            findings.append({'site_index': i, 'alert_index': j, 'json_pointer': pointer, 'site_display': display,
                             'producer_fields': fields, 'risk_normalized': risk, 'risk_label': RISK_LABELS.get(risk),
                             'confidence_normalized': confidence, 'confidence_label': CONFIDENCE_LABELS.get(confidence),
                             'instances_state': state, 'declared_count_normalized': declared,
                             'instance_count_matches': declared == len(selected) if declared is not None and state == 'array' else None,
                             'imported_instances': len(selected), 'instances': selected})
    extras = {key: {'state': 'null' if raw[key] is None else 'present', 'count': len(raw[key]) if isinstance(raw[key], list) else None}
              for key in ('insights', 'stoppingInsight', 'scriptDiagnostics', 'statistics', 'afPlanErrors', 'afPlanWarns') if key in raw}
    if extras:
        warnings.append({'json_pointer': '', 'message': 'Seções adicionais de diagnóstico/estatística presentes, sem interpretação: '+', '.join(extras)})
    digest = hashlib.sha256(data).hexdigest()
    return {'schema_version': 1, 'artifact': {'sha256': digest, 'bytes': len(data), 'format': 'zap-traditional-json', 'path': path},
            'analysis_run': {'id': 'zap-json-v1-'+digest, 'adapter': 'offline-zap-json', 'adapter_version': VERSION, 'target_executed': False},
            'producer': producer, 'coverage': {'status': 'selected-alert-fields', 'sites_state': sites_state, 'sites': coverage, 'imported_alerts': len(findings), 'scan_completion': 'not-established', 'uninterpreted_sections': extras},
            'findings': findings, 'warnings': warnings,
            'limitations': ['Risco e confiança são declarações independentes do produtor; Confirmed não é confirmação externa e False Positive não atesta segurança.',
                            'Não são exportados payloads, evidence, mensagens HTTP, descrições HTML, soluções, referências, screenshots ou diagnósticos; URIs omitem userinfo, query e fragmento.',
                            'Nomes de alertas e caminhos de URI continuam dados do relatório e podem conter informações sensíveis; a omissão estrutural não é anonimização completa.',
                            'Campos ausentes/arrays vazios não comprovam cobertura, conclusão ou ausência de vulnerabilidades.',
                            'Nenhum site foi acessado ou associado automaticamente a IPs Nmap ou pacotes Trivy.']}


def import_report(path: Path) -> dict:
    with path.open('rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    return parse_json(data, str(path.resolve()))
