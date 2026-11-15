"""Conservative comparison of declared Trivy/ZAP observations across reviews."""
from collections import Counter, defaultdict
import hashlib
import json

VERSION = '1'
LABELS = {'introduced': 'Observado apenas depois', 'not-observed': 'Não observado depois',
          'unchanged': 'Mesmos campos selecionados', 'changed': 'Campos selecionados alterados',
          'ambiguous': 'Chave declarada duplicada', 'unmatched': 'Sem chave comparável'}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def validate(report):
    if not isinstance(report, dict) or type(report.get('schema_version')) is not int or report['schema_version'] != 1:
        raise ValueError('Expected review schema 1')
    if not isinstance(report.get('inputs'), dict) or not isinstance(report.get('ruleset'), dict) or not isinstance(report.get('items'), list):
        raise ValueError('Invalid review inputs, ruleset or items')
    if not isinstance(report.get('review_id'), str):
        raise ValueError('Missing review identity')
    rules = report['ruleset']
    if not all(isinstance(rules.get(k), str) and rules[k] for k in ('id', 'version', 'sha256')):
        raise ValueError('Missing ruleset identity')
    if len(rules['sha256']) != 64 or any(c not in '0123456789abcdef' for c in rules['sha256']):
        raise ValueError('Invalid ruleset digest')
    seen = set()
    for source in report['inputs'].values():
        if not isinstance(source, dict) or not isinstance(source.get('artifact'), dict) or not isinstance(source.get('analysis_run'), dict) or not isinstance(source.get('producer'), dict):
            raise ValueError('Invalid source metadata')
        version = source['analysis_run'].get('adapter_version')
        sha = source['artifact'].get('sha256')
        if not isinstance(version, str) or not version or not isinstance(sha, str) or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
            raise ValueError('Invalid source version or digest')
    for item in report['items']:
        if not isinstance(item, dict) or not all(isinstance(item.get(k), str) for k in ('id', 'rule_id', 'title', 'priority', 'category')):
            raise ValueError('Invalid review item')
        if item['id'] in seen:
            raise ValueError('Duplicate review item ID')
        seen.add(item['id'])
        if not isinstance(item.get('facts'), dict) or not isinstance(item.get('references'), list):
            raise ValueError('Invalid item facts or references')
        if 'instances' in item['facts'] and (not isinstance(item['facts']['instances'], list) or not all(isinstance(instance, dict) for instance in item['facts']['instances'])):
            raise ValueError('Invalid alert instances')
        for ref in item['references']:
            if not isinstance(ref, dict) or not isinstance(ref.get('role'), str) or ref['role'] not in report['inputs']:
                raise ValueError('Unknown evidence role')
            expected = report['inputs'][ref['role']]['artifact'].get('sha256')
            if not isinstance(expected, str) or len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected) or ref.get('artifact_sha256') != expected:
                raise ValueError('Evidence SHA-256 differs from declared input')


def text(value):
    return isinstance(value, str) and bool(value.strip())


def key_for(item, report):
    facts = item['facts']
    fields = facts.get('producer_fields')
    if not isinstance(fields, dict):
        return None
    if item['category'] == 'producer-vulnerability' and item['references'] and all(r['role'] == 'trivy' for r in item['references']):
        source = report['inputs'].get('trivy', {})
        producer = source.get('producer', {})
        required = [producer.get('artifact_name'), producer.get('artifact_type'), facts.get('target'),
                    fields.get('VulnerabilityID'), fields.get('PkgName'), fields.get('InstalledVersion')]
        if not all(text(value) for value in required):
            return None
        return ['trivy', *required, facts.get('class'), facts.get('type'), fields.get('PkgID'), fields.get('PkgPath')]
    if item['category'] == 'producer-web-alert' and item['references'] and all(r['role'] == 'zap' for r in item['references']):
        site = facts.get('site_display', {})
        plugin = fields.get('pluginid')
        if not isinstance(site, dict) or not text(site.get('uri')) or site.get('status') != 'no-omitted-components':
            return None
        if type(plugin) not in (int, str) or not str(plugin).strip():
            return None
        return ['zap', site['uri'], str(plugin), fields.get('alertRef')]
    return None


def selected_fields(item):
    # Remove only known positional provenance fields; preserve all producer values.
    facts = {k: v for k, v in item['facts'].items() if k not in {'json_pointer', 'result_index', 'vulnerability_index', 'site_index', 'alert_index'}}
    if isinstance(facts.get('instances'), list):
        facts['instances'] = sorted([{k: v for k, v in instance.items() if k not in {'json_pointer', 'instance_index'}} for instance in facts['instances']], key=canonical)
    return {'rule_id': item['rule_id'], 'priority': item['priority'], 'category': item['category'], 'title': item['title'], 'facts': facts}


def compare_reviews(before, after):
    validate(before)
    validate(after)
    same_rules = before['ruleset'] == after['ruleset']
    shared = before['inputs'].keys() & after['inputs'].keys()
    adapters_changed = sorted(role for role in shared if before['inputs'][role]['analysis_run'].get('adapter_version') != after['inputs'][role]['analysis_run'].get('adapter_version'))
    result = {'schema_version': 1, 'method': 'declared-observation-evolution-v1', 'adapter_version': VERSION,
              'comparison_id': 'review-evolution-v1-'+digest({'before': before, 'after': after, 'version': VERSION}),
              'before': {'review_id': before['review_id'], 'document_fingerprint': digest(before)},
              'after': {'review_id': after['review_id'], 'document_fingerprint': digest(after)},
              'status': 'compared' if same_rules and not adapters_changed else 'blocked',
              'comparability': {'same_ruleset': same_rules, 'changed_adapters': adapters_changed,
                               'roles_only_before': sorted(before['inputs'].keys()-after['inputs'].keys()),
                               'roles_only_after': sorted(after['inputs'].keys()-before['inputs'].keys()),
                               'producer_metadata_changed': sorted(role for role in shared if before['inputs'][role].get('producer') != after['inputs'][role].get('producer')),
                               'coverage_changed': sorted(role for role in shared if before['inputs'][role].get('coverage') != after['inputs'][role].get('coverage'))},
              'summary': {code: 0 for code in LABELS}, 'observations': [], 'target_executed': False,
              'limitations': ['Correspondência usa chaves declaradas, não identidade verificada do ativo, cobertura equivalente ou validação de vulnerabilidade.',
                              'Não observado depois não significa corrigido. Observado apenas depois não significa introduzido no sistema.',
                              'Nmap e tarefas de cobertura não são pareados nesta versão. Chaves incompletas ou duplicadas permanecem explícitas.',
                              'Versões de pacote distintas são observações distintas. A comparação não transfere decisões humanas.',
                              'ZAP compara site e identificador de alerta; não estabelece identidade de cada URI/instância, cujos componentes podem ter sido omitidos.',
                              'A comparação não autentica revisões. Use reprodução e preservação independente das fontes quando necessário.']}
    if result['status'] == 'blocked':
        return result
    groups = [defaultdict(list), defaultdict(list)]
    for side, report in enumerate((before, after)):
        for item in report['items']:
            key = key_for(item, report)
            if key is None:
                result['observations'].append({'status': 'unmatched', 'key': None, 'before': [item] if side == 0 else [], 'after': [item] if side == 1 else []})
            else:
                groups[side][canonical(key)].append(item)
    for key in sorted(groups[0].keys() | groups[1].keys()):
        left, right = groups[0].get(key, []), groups[1].get(key, [])
        status = ('ambiguous' if len(left) > 1 or len(right) > 1 else 'introduced' if not left else 'not-observed' if not right else
                  'unchanged' if selected_fields(left[0]) == selected_fields(right[0]) else 'changed')
        result['observations'].append({'status': status, 'key': json.loads(key), 'before': left, 'after': right})
    result['summary'].update(Counter(row['status'] for row in result['observations']))
    return result
