"""Versioned, deterministic review rules. Produces suggestions, never actions."""
from collections import Counter
import hashlib
import json

VERSION = '2'
PRIORITIES = {'review-first': 'Revisar primeiro', 'review-next': 'Revisar depois', 'context': 'Contexto'}
RULES = {
    'ZAP-HIGH': {'priority': 'review-first', 'category': 'producer-web-alert', 'title': 'Validar um alerta web de risco alto do produtor',
        'reason': 'ZAP declara riskcode 3 com confiança conhecida, sem marcação False Positive. Isso não é confirmação independente.',
        'next_steps': ['Conferir o escopo, a evidência original e a aplicabilidade com o responsável pela aplicação antes de planejar correções.']},
    'ZAP-REVIEW': {'priority': 'review-next', 'category': 'producer-web-alert', 'title': 'Revisar um alerta web do produtor',
        'reason': 'O relatório declara um alerta e sua classificação precisa ser interpretada no contexto da aplicação.',
        'next_steps': ['Conferir risco, confiança e instâncias no relatório original. Registrar a decisão de revisão com o responsável pela aplicação.']},
    'ZAP-FALSE-POSITIVE': {'priority': 'context', 'category': 'producer-web-alert', 'title': 'Conferir uma marcação de falso positivo',
        'reason': 'O produtor declarou confidence 0 (False Positive); o registro permanece visível e isso não comprova segurança.',
        'next_steps': ['Verificar a justificativa dessa classificação e manter ou revisar a decisão com evidências, sem descartar automaticamente o alerta.']},
    'ZAP-INFORMATION': {'priority': 'context', 'category': 'producer-web-alert', 'title': 'Preservar um alerta informativo',
        'reason': 'O produtor declarou riskcode 0; a informação não equivale a um atestado de ausência de impacto.',
        'next_steps': ['Consultar o alerta no contexto da aplicação e registrar se exige acompanhamento.']},
    'ZAP-CLASSIFICATION': {'priority': 'review-next', 'category': 'evidence-quality', 'title': 'Conferir a classificação de um alerta web',
        'reason': 'Risco ou confiança estão ausentes ou não são reconhecidos pelo adaptador.',
        'next_steps': ['Consultar os códigos e a versão do produtor; manter como desconhecido o que não foi estabelecido.']},
    'ZAP-COVERAGE': {'priority': 'review-first', 'category': 'evidence-quality', 'title': 'Conferir o recorte do relatório web',
        'reason': 'Há registros/contagens incompletos ou sinais de diagnóstico não interpretados que exigem revisão de cobertura.',
        'next_steps': ['Conferir a geração do relatório, as instâncias e os diagnósticos na origem. Não concluir cobertura completa ou ausência de alertas com base em campos ausentes.']},
    'EVIDENCE-COMPLETION': {'priority': 'review-first', 'category': 'evidence-quality', 'title': 'Conferir a conclusão da coleta',
        'reason': 'Um relatório Nmap não declara conclusão bem-sucedida.',
        'next_steps': ['Conferir se o arquivo está completo e como a coleta terminou antes de interpretar seus resultados.']},
    'EVIDENCE-SCOPE': {'priority': 'review-first', 'category': 'evidence-quality', 'title': 'Conferir a comparabilidade das coletas',
        'reason': 'Os escopos ou métodos declarados diferem ou são desconhecidos.',
        'next_steps': ['Conferir protocolo, método, intervalos, ponto de observação e conclusão dos relatórios antes de interpretar ausências.']},
    'EVIDENCE-IDENTITY': {'priority': 'review-first', 'category': 'evidence-quality', 'title': 'Resolver uma lacuna de evidência',
        'reason': 'O comparador registrou identidade ambígua, ausência de identidade ou timeout.',
        'next_steps': ['Conferir o registro de origem e a identidade do ativo. Manter as observações sem pareamento até haver evidência suficiente.']},
    'NMAP-OPEN-STATE': {'priority': 'review-first', 'category': 'network-observation', 'title': 'Conferir a mudança para estado aberto',
        'reason': 'A mesma porta foi explicitamente registrada com outro estado conhecido antes e com estado open depois.',
        'next_steps': ['Confirmar se a mudança era esperada e qual serviço deveria estar exposto. Verificar configuração e contexto com o responsável pelo ativo.']},
    'NMAP-OBSERVATION': {'priority': 'review-next', 'category': 'network-observation', 'title': 'Revisar uma diferença de observação',
        'reason': 'Há mudança no registro de host, porta ou detecção de serviço, sem conclusão automática sobre risco.',
        'next_steps': ['Conferir as duas evidências e a cobertura. Diferenciar mudança no sistema de mudança na detecção ou na coleta.']},
    'NMAP-ABSENCE': {'priority': 'context', 'category': 'network-observation', 'title': 'Preservar uma observação ausente',
        'reason': 'Um host ou porta não tem correspondência explícita no relatório atual; isso não comprova remoção ou fechamento.',
        'next_steps': ['Verificar se o ativo e a porta estão no escopo atual antes de concluir que houve correção.']},
    'TRIVY-HIGH': {'priority': 'review-first', 'category': 'producer-vulnerability', 'title': 'Validar um registro de alta severidade do produtor',
        'reason': 'O relatório declara severidade HIGH ou CRITICAL; a fila não comprova explorabilidade ou risco do ambiente.',
        'next_steps': ['Confirmar pacote, versão, aplicabilidade e aviso do produtor. Revisar atualização ou mitigação com o responsável, sem aplicar mudanças automaticamente.']},
    'TRIVY-OTHER': {'priority': 'review-next', 'category': 'producer-vulnerability', 'title': 'Revisar um registro do produtor',
        'reason': 'O registro está no relatório e requer contexto; severidade baixa, desconhecida ou ausente não demonstra ausência de impacto.',
        'next_steps': ['Conferir a classificação e a aplicabilidade no contexto do artefato. Preservar como desconhecido o que o relatório não informa.']},
    'TRIVY-COVERAGE': {'priority': 'review-first', 'category': 'evidence-quality', 'title': 'Conferir o recorte do relatório de componentes',
        'reason': 'Não há resultados, ou um resultado não inclui um array explícito de vulnerabilidades.',
        'next_steps': ['Conferir a origem do JSON, as opções de geração e quais categorias foram examinadas. Não interpretar ausência de campo como resultado de uma verificação concluída.']},
}


def build_review(comparison: dict | None = None, trivy: dict | None = None, zap: dict | None = None) -> dict:
    if comparison is None and trivy is None and zap is None:
        raise ValueError('Forneça uma comparação Nmap e/ou um relatório Trivy/ZAP')
    inputs, context, items, warnings = {}, {}, [], []

    def add(rule_id, facts, references):
        rule = RULES[rule_id]
        identity = json.dumps({'rule': rule_id, 'version': VERSION, 'references': references, 'facts': facts}, sort_keys=True, separators=(',', ':'))
        items.append({'id': 'review-item-'+hashlib.sha256(identity.encode()).hexdigest(), 'rule_id': rule_id, **rule,
                      'next_steps': list(rule['next_steps']), 'evidence_type': 'derived-review-suggestion', 'facts': facts, 'references': references})

    if comparison is not None:
        for side, source in comparison['sources'].items():
            inputs['nmap-'+side] = source
        context['nmap'] = {'comparison_id': comparison['comparison_id'], 'summary': comparison['summary'], 'comparability': comparison['comparability']}
        warnings.extend({'origin': 'nmap', **warning} for warning in comparison['warnings'])
        global_refs = [{'role': 'nmap-'+side, 'artifact_sha256': source['artifact']['sha256']} for side, source in comparison['sources'].items()]
        for side, source in comparison['sources'].items():
            finished = source['producer']['finished']
            if finished is None or finished.get('exit') != 'success':
                add('EVIDENCE-COMPLETION', {'finished': finished}, [{'role': 'nmap-'+side, 'artifact_sha256': source['artifact']['sha256']}])
        if comparison['comparability']['scope_relation'] != 'same_declared':
            add('EVIDENCE-SCOPE', comparison['comparability'], global_refs)
        for issue in comparison['issues']:
            refs = [dict(r, role='nmap-'+r['source']) for r in issue['references']]
            add('EVIDENCE-IDENTITY', {k: v for k, v in issue.items() if k != 'references'}, refs)
        for change in comparison['changes']:
            kind = change['kind']
            rule = ('NMAP-ABSENCE' if kind in ('not_observed_endpoint_after', 'not_observed_host_after') else
                    'NMAP-OPEN-STATE' if kind == 'state_changed' and change['after'] == 'open' else 'NMAP-OBSERVATION')
            refs = [dict(r, role='nmap-'+r['source']) for r in change['references']]
            add(rule, {k: v for k, v in change.items() if k not in ('references', 'evidence_type')}, refs)
    if trivy is not None:
        inputs['trivy'] = {k: trivy[k] for k in ('artifact', 'analysis_run', 'producer', 'coverage')}
        warnings.extend({'origin': 'trivy', **warning} for warning in trivy['warnings'])
        context['trivy'] = {'imported_records': len(trivy['findings']), 'uninterpreted_categories': [r['uninterpreted_categories'] for r in trivy['coverage']['results']]}
        sha = trivy['artifact']['sha256']
        incomplete = [r['result_index'] for r in trivy['coverage']['results'] if r['vulnerabilities_state'] != 'array']
        if not trivy['coverage']['results'] or incomplete:
            add('TRIVY-COVERAGE', {'results_state': trivy['coverage']['results_state'], 'results_without_explicit_vulnerability_array': incomplete}, [{'role': 'trivy', 'artifact_sha256': sha, 'json_pointer': ''}])
        for finding in trivy['findings']:
            rule = 'TRIVY-HIGH' if finding['severity_normalized'] in ('HIGH', 'CRITICAL') else 'TRIVY-OTHER'
            add(rule, finding, [{'role': 'trivy', 'artifact_sha256': sha, 'json_pointer': finding['json_pointer']}])
    if zap is not None:
        inputs['zap'] = {k: zap[k] for k in ('artifact', 'analysis_run', 'producer', 'coverage')}
        warnings.extend({'origin': 'zap', **warning} for warning in zap['warnings'])
        context['zap'] = {'imported_alerts': len(zap['findings']), 'scan_completion': zap['coverage']['scan_completion']}
        sha = zap['artifact']['sha256']
        incomplete_sites = [s['site_index'] for s in zap['coverage']['sites'] if s['alerts_state'] != 'array']
        incomplete_alerts = [a['json_pointer'] for a in zap['findings'] if a['instances_state'] != 'array' or a['instance_count_matches'] is False]
        extra = zap['coverage']['uninterpreted_sections']
        diagnostic_flags = {key: value for key, value in extra.items() if (key == 'stoppingInsight' and value['state'] == 'present') or (key == 'afPlanErrors' and (value['count'] or 0) > 0)}
        if not zap['coverage']['sites'] or incomplete_sites or incomplete_alerts or diagnostic_flags:
            add('ZAP-COVERAGE', {'sites_state': zap['coverage']['sites_state'], 'sites_without_alert_array': incomplete_sites, 'incomplete_alert_records': incomplete_alerts, 'uninterpreted_diagnostics': diagnostic_flags}, [{'role': 'zap', 'artifact_sha256': sha, 'json_pointer': ''}])
        for finding in zap['findings']:
            risk, confidence = finding['risk_normalized'], finding['confidence_normalized']
            rule = ('ZAP-FALSE-POSITIVE' if confidence == 0 else 'ZAP-CLASSIFICATION' if risk is None or confidence is None else
                    'ZAP-HIGH' if risk == 3 else 'ZAP-INFORMATION' if risk == 0 else 'ZAP-REVIEW')
            add(rule, finding, [{'role': 'zap', 'artifact_sha256': sha, 'json_pointer': finding['json_pointer']}])
    priority_order = {key: i for i, key in enumerate(PRIORITIES)}
    items.sort(key=lambda i: (priority_order[i['priority']], i['category'] != 'evidence-quality', i['rule_id'], i['id']))
    rule_digest = hashlib.sha256(json.dumps(RULES, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    identity = {'rules_version': VERSION, 'rules_sha256': rule_digest, 'inputs': {role: {'sha256': data['artifact']['sha256'], 'importer_version': data['analysis_run']['adapter_version']} for role, data in inputs.items()}, 'comparator_version': comparison['adapter_version'] if comparison else None}
    review_id = 'review-v1-'+hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'schema_version': 1, 'review_id': review_id, 'ruleset': {'id': 'evidence-review', 'version': VERSION, 'sha256': rule_digest, 'mechanism': 'deterministic-rules', 'model_calls': 0},
            'target_executed': False, 'inputs': inputs, 'context': context,
            'summary': {'items': len(items), 'by_priority': dict(Counter(i['priority'] for i in items)), 'by_category': dict(Counter(i['category'] for i in items))},
            'items': items, 'warnings': warnings,
            'limitations': ['Prioridade de revisão não é uma pontuação de risco, urgência operacional ou validação de vulnerabilidade.',
                            'A severidade Trivy e suas versões/status continuam declarações do produtor; correção ausente significa informação não declarada, não inexistência de correção.',
                            'Não há associação entre IPs Nmap e artefatos/pacotes Trivy. As evidências coexistem na fila sem correlação automática.',
                            'Risco e confiança ZAP permanecem declarações separadas do produtor. Os sites ZAP não são associados automaticamente a IPs ou pacotes.',
                            'A fila inclui diferenças e campos selecionados, não uma auditoria integral ou garantia de segurança.',
                            'Sugestões não são executadas. Não houve consulta externa de CVEs, uso de modelo de IA ou alteração dos sistemas.']}
