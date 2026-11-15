"""Compare imported observations without inferring closure from missing evidence."""
from __future__ import annotations

from collections import Counter, defaultdict
from html import escape
import hashlib
import ipaddress
import json
from pathlib import Path
import re

VERSION = '1'
PORT_STATES = {'open', 'closed', 'filtered', 'unfiltered', 'open|filtered', 'closed|filtered'}
HOST_STATES = {'up', 'down'}
LABELS = {
    'state_changed': 'Estado registrado mudou',
    'state_evidence_changed': 'Evidência de estado mudou',
    'service_evidence_changed': 'Detecção de serviço mudou',
    'host_state_changed': 'Estado registrado do host mudou',
    'host_state_evidence_changed': 'Evidência de estado do host mudou',
    'first_observed_endpoint': 'Porta registrada apenas no relatório atual',
    'not_observed_endpoint_after': 'Porta sem registro explícito no relatório atual',
    'first_observed_host': 'Host registrado apenas no relatório atual',
    'not_observed_host_after': 'Host sem correspondência no relatório atual',
    'address_evidence_changed': 'Conjunto de endereços observado mudou',
}


def _ips(host: dict) -> set[str]:
    result = set()
    for address in host['addresses']:
        if address.get('addrtype') not in ('ipv4', 'ipv6'):
            continue
        try:
            ip = ipaddress.ip_address(address.get('addr', ''))
        except ValueError:
            continue
        if ip.version == (4 if address['addrtype'] == 'ipv4' else 6):
            result.add(str(ip))
    return result


def _scope(report: dict):
    """Normalize interval declarations without enumerating ports or expanding ranges."""
    rows = report['coverage']['scaninfo']
    normalized = []
    if not rows:
        return None
    for row in rows:
        protocol, method, services = row.get('protocol'), row.get('type'), row.get('services')
        if not protocol or not method or services is None:
            return None
        intervals = []
        for token in services.split(','):
            match = re.fullmatch(r'\s*([0-9]{1,5})(?:-([0-9]{1,5}))?\s*', token)
            if not match:
                return None
            low = int(match[1])
            high = int(match[2] or match[1])
            if not 0 <= low <= high <= 65535:
                return None
            intervals.append((low, high))
        merged = []
        for low, high in sorted(intervals):
            if merged and low <= merged[-1][1] + 1:
                merged[-1] = (merged[-1][0], max(high, merged[-1][1]))
            else:
                merged.append((low, high))
        normalized.append((protocol, method, tuple(merged)))
    return tuple(sorted(set(normalized)))


def _membership(scope, endpoint):
    if scope is None:
        return 'unknown'
    protocol, number = endpoint
    return 'declared' if any(p == protocol and any(lo <= number <= hi for lo, hi in ranges) for p, _, ranges in scope) else 'not_declared'


def compare_reports(before: dict, after: dict) -> dict:
    reports = {'before': before, 'after': after}
    addresses = {side: [_ips(host) for host in report['hosts']] for side, report in reports.items()}
    indexes = {}
    for side in reports:
        index = defaultdict(set)
        for i, ips in enumerate(addresses[side]):
            for ip in ips:
                index[ip].add(i)
        indexes[side] = index
    candidates = {}
    for side, other in [('before', 'after'), ('after', 'before')]:
        candidates[side] = [set().union(*(indexes[other].get(ip, set()) for ip in ips)) if ips else set() for ips in addresses[side]]
    changes, issues, matches = [], [], []
    before_scope, after_scope = _scope(before), _scope(after)

    def ref(side, host, port=None):
        result = {'source': side, 'artifact_sha256': reports[side]['artifact']['sha256'], 'host_index': host}
        if port is not None:
            result['port_index'] = port
        return result

    def change(kind, host, old, new, refs, endpoint=None, **extra):
        item = {'id': f'change-{len(changes)+1}', 'kind': kind, 'evidence_type': 'derived-from-recorded-observations', 'host': host, 'before': old, 'after': new, 'references': refs}
        if endpoint:
            item['endpoint'] = {'protocol': endpoint[0], 'number': endpoint[1]}
        changes.append(item | extra)

    for side in reports:
        for i, ips in enumerate(addresses[side]):
            opposite = 'after' if side == 'before' else 'before'
            options = candidates[side][i]
            if not ips:
                issues.append({'kind': 'host_identity_unresolved', 'reason': 'No valid typed IP address; hostnames and MAC addresses are not identity keys', 'references': [ref(side, i)]})
            elif options and (len(options) != 1 or any(len(candidates[opposite][j]) != 1 for j in options)):
                issues.append({'kind': 'host_identity_ambiguous', 'reason': 'IP evidence does not establish a unique one-to-one pairing', 'references': [ref(side, i)]})
            elif not options:
                kind = 'not_observed_host_after' if side == 'before' else 'first_observed_host'
                change(kind, sorted(ips), {'recorded': True} if side == 'before' else None, {'recorded': True} if side == 'after' else None, [ref(side, i)])
            elif side == 'before':
                matches.append((i, next(iter(options))))
            if reports[side]['hosts'][i].get('timedout') in ('true', '1'):
                issues.append({'kind': 'producer_host_timeout', 'reason': 'Producer marked host processing as timed out', 'references': [ref(side, i)]})

    for left, right in matches:
        old_host, new_host = before['hosts'][left], after['hosts'][right]
        identity = sorted(addresses['before'][left] & addresses['after'][right])
        refs = [ref('before', left), ref('after', right)]
        if addresses['before'][left] != addresses['after'][right]:
            change('address_evidence_changed', identity, sorted(addresses['before'][left]), sorted(addresses['after'][right]), refs)
        old_state = (old_host['status'] or {}).get('state')
        new_state = (new_host['status'] or {}).get('state')
        if old_state != new_state:
            change('host_state_changed' if old_state in HOST_STATES and new_state in HOST_STATES else 'host_state_evidence_changed', identity, old_state, new_state, refs)
        ports = {}
        for side, host in [('before', old_host), ('after', new_host)]:
            grouped = defaultdict(list)
            for i, port in enumerate(host['ports']):
                grouped[(port['protocol'], port['port'])].append(i)
            ports[side] = grouped
        for key in sorted(set(ports['before']) | set(ports['after'])):
            old_indices, new_indices = ports['before'][key], ports['after'][key]
            if len(old_indices) > 1 or len(new_indices) > 1:
                issues.append({'kind': 'endpoint_identity_ambiguous', 'reason': 'Repeated protocol/number in a host; endpoint comparison omitted', 'endpoint': {'protocol': key[0], 'number': key[1]}, 'references': [ref('before', left, i) for i in old_indices] + [ref('after', right, i) for i in new_indices]})
                continue
            old = old_host['ports'][old_indices[0]] if old_indices else None
            new = new_host['ports'][new_indices[0]] if new_indices else None
            refs = ([ref('before', left, old_indices[0])] if old_indices else []) + ([ref('after', right, new_indices[0])] if new_indices else [])
            if old is None or new is None:
                change('first_observed_endpoint' if old is None else 'not_observed_endpoint_after', identity, old, new, refs, key, other_declared_scope=_membership(before_scope if old is None else after_scope, key))
                continue
            old_state, new_state = (old['state'] or {}).get('state'), (new['state'] or {}).get('state')
            if old_state != new_state:
                change('state_changed' if old_state in PORT_STATES and new_state in PORT_STATES else 'state_evidence_changed', identity, old_state, new_state, refs, key)
            if old['service'] != new['service']:
                change('service_evidence_changed', identity, old['service'], new['service'], refs, key)

    warnings = []
    for side, report in reports.items():
        warnings.extend({'source': side, 'message': w} for w in report['warnings'])
    relation = 'unknown' if before_scope is None or after_scope is None else ('same_declared' if before_scope == after_scope else 'different_declared')
    if relation != 'same_declared':
        warnings.append({'source': 'comparison', 'message': 'Declared scan coverage/method differs or is unknown; missing observations must not be treated as closure.'})
    if before['producer']['version'] != after['producer']['version']:
        warnings.append({'source': 'comparison', 'message': 'Producer versions differ; service detection changes may reflect tooling.'})
    identity = json.dumps({'comparison_version': VERSION, 'sources': {side: {'sha256': report['artifact']['sha256'], 'importer_version': report['analysis_run']['adapter_version']} for side, report in reports.items()}}, sort_keys=True, separators=(',', ':'))
    return {'schema_version': 1, 'comparison_id': 'nmap-diff-v1-'+hashlib.sha256(identity.encode()).hexdigest(),
            'adapter_version': VERSION, 'target_executed': False,
            'sources': {side: {'artifact': report['artifact'], 'analysis_run': report['analysis_run'], 'producer': report['producer'], 'coverage': report['coverage']} for side, report in reports.items()},
            'comparability': {'scope_relation': relation, 'identity_rule': 'Unique one-to-one shared canonical IP address; no hostname/MAC matching'},
            'summary': {'matched_hosts': len(matches), 'changes': len(changes), 'changes_by_kind': dict(sorted(Counter(c['kind'] for c in changes).items())), 'issues': len(issues)},
            'changes': changes, 'issues': issues, 'warnings': warnings,
            'limitations': ['All changes describe recorded observations, not current live state or confirmed vulnerabilities.', 'Absent hosts/ports are unobserved; no closure, removal or remediation is inferred.', 'An IP correspondence does not prove persistent device identity; DHCP, NAT and address reassignment may affect interpretation.', 'Matching scaninfo does not prove equal privileges, options, vantage point or complete capture.', 'Reference indices are zero-based positions in the normalized imports; original artifacts are identified by SHA-256.']}


def validate_destinations(destinations: list[Path]) -> None:
    resolved = [p.resolve() for p in destinations]
    if len(set(resolved)) != len(resolved):
        raise ValueError('JSON and HTML destinations must differ')
    for path in destinations:
        if path.exists() or path.is_symlink():
            raise FileExistsError(f'Refusing to overwrite: {path}')
        if not path.parent.is_dir():
            raise ValueError(f'Output directory does not exist: {path.parent}')


def render_html(report: dict, demo: bool = False) -> str:
    """Render inert, escaped data. No script, external asset or input-derived URL."""
    def pre(value):
        return '<pre>'+escape(json.dumps(value, ensure_ascii=False, indent=2))+'</pre>'

    cards = ''.join(f'<article><strong>{value}</strong><span>{label}</span></article>' for label, value in [('Hosts pareados por IP', report['summary']['matched_hosts']), ('Diferenças registradas', report['summary']['changes']), ('Questões de evidência', report['summary']['issues'])])
    rows = []
    for item in report['changes']:
        endpoint = item.get('endpoint')
        target = ', '.join(item['host']) + (f' · {endpoint["protocol"]}/{endpoint["number"]}' if endpoint else '')
        details = {'before': item['before'], 'after': item['after'], 'references': item['references']}
        if 'other_declared_scope' in item:
            details['other_declared_scope'] = item['other_declared_scope']
        rows.append('<tr id="'+escape(item['id'], quote=True)+'"><td>'+escape(target)+'</td><td>'+escape(LABELS[item['kind']])+'</td><td><details><summary>Ver antes, depois e origem</summary>'+pre(details)+'<a href="#sources">Conferir arquivos e hashes</a></details></td></tr>')
    table = '<div class="table-wrap"><table><caption>Diferenças entre observações</caption><thead><tr><th scope="col">Ativo / porta</th><th scope="col">Diferença</th><th scope="col">Evidência</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>' if rows else '<p class="notice">Nenhuma diferença nos campos comparados. Isso não comprova ausência de riscos ou equivalência dos sistemas.</p>'
    warning_labels = {
        'No finished record: scan completion is unknown': 'Não há registro de conclusão; a conclusão da coleta é desconhecida.',
        'The producer did not report a successful scan exit': 'O produtor não registrou conclusão bem-sucedida da coleta.',
        'Declared scan coverage/method differs or is unknown; missing observations must not be treated as closure.': 'Cobertura ou método declarados diferem ou são desconhecidos. A ausência de observações não indica fechamento.',
        'Producer versions differ; service detection changes may reflect tooling.': 'As versões do produtor diferem; mudanças na detecção de serviços podem refletir a ferramenta.',
    }
    source_labels = {'before': 'Anterior', 'after': 'Atual', 'comparison': 'Comparação'}
    warnings = ''.join('<li>'+escape(source_labels[x['source']]+': '+warning_labels.get(x['message'], x['message']))+'</li>' for x in report['warnings'])
    sources = ''.join('<details open><summary>'+escape(label)+'</summary>'+pre(report['sources'][side])+'</details>' for side, label in [('before', 'Relatório anterior'), ('after', 'Relatório atual')])
    limitation_labels = {
        'All changes describe recorded observations, not current live state or confirmed vulnerabilities.': 'As diferenças descrevem registros históricos, não o estado atual da rede ou vulnerabilidades confirmadas.',
        'Absent hosts/ports are unobserved; no closure, removal or remediation is inferred.': 'Hosts e portas ausentes ficam como não observados; não se infere fechamento, remoção ou correção.',
        'An IP correspondence does not prove persistent device identity; DHCP, NAT and address reassignment may affect interpretation.': 'Um IP em comum não comprova identidade permanente do equipamento: DHCP, NAT e reutilização de endereços afetam a interpretação.',
        'Matching scaninfo does not prove equal privileges, options, vantage point or complete capture.': 'Escopos declarados iguais não comprovam igualdade de privilégios, opções, ponto de coleta ou completude.',
        'Reference indices are zero-based positions in the normalized imports; original artifacts are identified by SHA-256.': 'Os índices de referência começam em zero e apontam para as importações normalizadas; os hashes identificam os XMLs originais.',
    }
    limitations = ''.join('<li>'+escape(limitation_labels.get(x, x))+'</li>' for x in report['limitations'])
    demo_notice = '<p class="notice">Demonstração com XMLs sintéticos do repositório. Nenhuma coleta de rede foi realizada.</p>' if demo else ''
    scope_label = {'same_declared': 'escopo declarado igual', 'different_declared': 'escopos declarados diferentes', 'unknown': 'escopo desconhecido'}[report['comparability']['scope_relation']]
    return '''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>FERRAMENTA-HACKER · comparação de evidências</title>
<style>
:root{color-scheme:dark;--bg:#0c1422;--panel:#152238;--line:#34465f;--text:#edf4ff;--muted:#b6c8df;--accent:#72e2cf}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.6 system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:36px 24px}header{border-bottom:1px solid var(--line);padding-bottom:24px}.eyebrow{color:var(--accent);letter-spacing:.12em;font-size:.8rem}h1{font-size:clamp(1.8rem,5vw,3rem);line-height:1.15;margin:.6em 0}h2{margin-top:2em}p,li{max-width:90ch}.muted{color:var(--muted)}nav{display:flex;gap:20px;flex-wrap:wrap;margin-top:24px}a{color:var(--accent)}a:focus-visible,summary:focus-visible{outline:3px solid var(--accent);outline-offset:4px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin:28px 0}article,details,.notice{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px}article strong{display:block;font-size:2.2rem;color:var(--accent)}article span{color:var(--muted)}details{margin:12px 0;min-width:0}summary{cursor:pointer;font-weight:600}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:.8rem;color:var(--muted);max-height:32rem;overflow:auto}table{border-collapse:collapse;width:100%;min-width:620px}caption{text-align:left;padding:12px 0;font-weight:600}th,td{text-align:left;vertical-align:top;padding:14px;border-bottom:1px solid var(--line);overflow-wrap:anywhere}td:first-child{min-width:160px}th{color:var(--muted)}td details{margin:0;max-width:540px}.table-wrap{overflow-x:auto}.scope{border-left:4px solid var(--accent);padding:12px 18px;background:var(--panel)}footer{overflow-wrap:anywhere;margin-top:40px;border-top:1px solid var(--line);padding-top:18px;font-size:.85rem;color:var(--muted)}@media print{body{background:white;color:black}main{padding:0}details,article,.scope{background:white}pre,.muted,article span,footer,th{color:#333}a{color:#005c50}.table-wrap{overflow:visible}table{min-width:0}pre{max-height:none}}
</style></head><body><main>
<header><div class="eyebrow">FERRAMENTA-HACKER / EVIDÊNCIAS OFFLINE</div><h1>O que mudou nos registros?</h1>
<p class="muted">Compare o que foi observado, confira a cobertura e siga cada diferença até seus arquivos de origem.</p>'''+demo_notice+'''
<nav aria-label="Seções do relatório"><a href="#overview">Visão geral</a><a href="#changes">Diferenças</a><a href="#questions">Questões abertas</a><a href="#sources">Proveniência</a></nav></header>
<section id="overview"><h2>Visão geral</h2>'''+ '<div class="cards">'+cards+'</div><p class="scope">Comparação da cobertura: <strong>'+escape(scope_label)+'</strong>. Ausência de registro não significa porta fechada ou ativo removido.</p>' + ('<ul>'+warnings+'</ul>' if warnings else '') + '''</section>
<section id="changes"><h2>Diferenças observadas</h2>'''+table+'''</section>
<section id="questions"><h2>Questões de evidência</h2>'''+(pre(report['issues']) if report['issues'] else '<p>Nenhuma ambiguidade de pareamento ou timeout foi identificada nos campos examinados.</p>')+'''</section>
<section id="sources"><h2>Proveniência e cobertura</h2><p>Os índices de referência começam em zero e apontam para os registros das importações normalizadas. Os hashes identificam os XMLs originais.</p>'''+sources+'''<h2>Limites da interpretação</h2><ul>'''+limitations+'''</ul></section><footer>Relatório local, sem requisições externas ou execução de scanner. Comparação '''+escape(report['comparison_id'])+'</footer></main></body></html>'
