"""Reproduce a review using explicit local sources, without trusting embedded paths."""
import copy
import hashlib
import json
from pathlib import Path

from json_reports import decode_object
from nmap_report import parse_xml
from nmap_compare import compare_reports
from trivy_report import parse_json as parse_trivy
from zap_report import parse_json as parse_zap
from review_rules import build_review, VERSION, RULES

MAX_BYTES = 32 * 1024 * 1024
PARSERS = {'nmap-before': parse_xml, 'nmap-after': parse_xml, 'trivy': parse_trivy, 'zap': parse_zap}


def read_review(path):
    with Path(path).open('rb') as stream:
        return decode_object(stream.read(MAX_BYTES + 1), 'review JSON', MAX_BYTES)


def source_arguments(values):
    sources = {}
    for value in values:
        role, separator, path = value.partition('=')
        if not separator or not path or role not in PARSERS or role in sources:
            raise ValueError('Use --source ROLE=PATH, com papéis conhecidos e sem duplicatas')
        sources[role] = Path(path)
    return sources


def _portable(report):
    result = copy.deepcopy(report)
    # Only these declared location fields may differ after moving source files.
    for source in result['inputs'].values():
        source['artifact'].pop('path', None)
    return result


def replay_review(report, sources):
    if type(report.get('schema_version')) is not int or report['schema_version'] != 1:
        raise ValueError('Unsupported review schema')
    inputs = report.get('inputs')
    if not isinstance(inputs, dict) or not inputs or set(inputs) - PARSERS.keys():
        raise ValueError('Invalid review input roles')
    if ('nmap-before' in inputs) != ('nmap-after' in inputs):
        raise ValueError('Review requires both Nmap roles')
    if set(inputs) != set(sources):
        raise ValueError('Provide exactly the source roles declared in review.inputs')
    expected_rules = hashlib.sha256(json.dumps(RULES, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    rules = report.get('ruleset')
    if not isinstance(rules, dict) or rules.get('version') != VERSION or rules.get('sha256') != expected_rules:
        raise ValueError('Ruleset unavailable: replay requires the exact installed rules version and digest')
    checks, parsed = {}, {}
    for role in sorted(inputs):
        source = inputs[role]
        if not isinstance(source, dict) or not isinstance(source.get('artifact'), dict):
            raise ValueError('Invalid input artifact')
        expected = source['artifact'].get('sha256')
        if not isinstance(expected, str) or len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected):
            raise ValueError('Invalid input SHA-256')
        with Path(sources[role]).open('rb') as stream:
            data = stream.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError('Source exceeds 32 MiB limit')
        actual = hashlib.sha256(data).hexdigest()
        checks[role] = {'expected_sha256': expected, 'actual_sha256': actual, 'matches': actual == expected}
        if actual == expected:
            parsed[role] = PARSERS[role](data, str(Path(sources[role]).resolve()))
    result = {'schema_version': 1, 'method': 'offline-deterministic-replay-v1', 'status': 'source-mismatch',
              'sources': checks, 'different_sections': [], 'target_executed': False,
              'limitations': ['Reprodução confirma consistência com fontes e regras instaladas, não autenticidade, revisão humana ou segurança do alvo.',
                              'Somente inputs.*.artifact.path é ignorado para permitir mover arquivos. Nenhum caminho embutido é aberto.']}
    if not all(check['matches'] for check in checks.values()):
        return result
    comparison = compare_reports(parsed['nmap-before'], parsed['nmap-after']) if 'nmap-before' in parsed else None
    rebuilt = build_review(comparison, parsed.get('trivy'), parsed.get('zap'))
    original, reproduced = _portable(report), _portable(rebuilt)
    result['different_sections'] = sorted(k for k in original.keys() | reproduced.keys() if k not in original or k not in reproduced or original[k] != reproduced[k])
    result['status'] = 'matched' if not result['different_sections'] else 'review-mismatch'
    return result
