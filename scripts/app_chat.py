"""Grounded local conversational retrieval, without a language model or commands."""
import json
import re
import unicodedata

STOP = set('a o as os de da do das dos e em um uma para por que qual quais como com me meu minha no na nos nas sobre este esta isso eu voce'.split())


def tokens(text):
    value = ''.join(c for c in unicodedata.normalize('NFKD', text.casefold()) if not unicodedata.combining(c))
    return set(re.findall(r'[a-z0-9][a-z0-9_-]+', value)) - STOP


def answer(question, review, sources, catalog):
    query = tokens(question)
    response = {'mode': 'local-evidence-retrieval', 'model_calls': 0, 'target_executed': False,
                'text': '', 'citations': [], 'suggestions': ['O que revisar primeiro?', 'Quais são as limitações?', 'Quais fontes foram importadas?']}
    if not query:
        response['text'] = 'Escreva uma pergunta sobre as fontes, a fila de revisão ou uma ferramenta do catálogo.'
        return response
    if query & {'limitacoes', 'limites', 'cobertura', 'confianca', 'completo', 'completa'}:
        response['text'] = '\n'.join(review['limitations'] if review else [
            'Ainda não há revisão neste projeto. Importe relatórios e gere a fila para examinar sua cobertura.',
            'Este assistente recupera trechos e aplica intenções locais; não usa um modelo generativo nem confirma vulnerabilidades.'])
        response['citations'] = [{'kind': 'review', 'review_id': review['review_id'], 'section': 'limitations'}] if review else []
    elif query & {'fontes', 'arquivos', 'hash', 'hashes', 'importados', 'importadas', 'origem'}:
        response['text'] = '\n'.join(f"{s['role']} · {s['name']} · SHA-256 {s['sha256']}" for s in sources) or 'Ainda não há relatórios importados neste projeto.'
        response['citations'] = [{'kind': 'source', 'source_id': s['id'], 'role': s['role'], 'artifact_sha256': s['sha256']} for s in sources]
    else:
        items = review['items'] if review else []
        summary = bool(query & {'primeiro', 'prioridade', 'prioridades', 'resumo', 'resumir', 'revisar', 'fila'})
        ranked = sorted(enumerate(items), key=lambda pair: (-len(query & tokens(json.dumps(pair[1], ensure_ascii=False))), pair[0]))
        selected = items[:3] if summary else [item for _, item in ranked if query & tokens(json.dumps(item, ensure_ascii=False))][:3]
        if selected:
            parts = []
            for index, item in enumerate(selected, 1):
                parts.append(f"[{index}] {item['title']}\n{item['reason']}\nPróxima verificação: {' '.join(item['next_steps'])}")
                response['citations'].append({'kind': 'review-item', 'item_id': item['id'], 'review_id': review['review_id'],
                                               'rule_id': item['rule_id'], 'references': item['references']})
            response['text'] = '\n\n'.join(parts)
        else:
            candidates = []
            for tool in catalog['tools']:
                score = len(query & tokens(json.dumps(tool, ensure_ascii=False)))
                # Require a tool's name/id/alias, avoiding accidental matches on generic prose.
                names = tokens(json.dumps([tool.get('id'), tool.get('name'), tool.get('aliases', [])], ensure_ascii=False))
                if score and query & names:
                    candidates.append((score, tool))
            candidates.sort(key=lambda pair: (-pair[0], str(pair[1].get('id'))))
            if candidates:
                selected_tools = [t for _, t in candidates[:3]]
                response['text'] = '\n\n'.join(f"{t.get('name', t['id'])}\n{t.get('purpose', t.get('description', 'Registro do catálogo local.'))}\nConsulte a ficha para conhecer o recorte e as limitações de integração." for t in selected_tools)
                response['citations'] = [{'kind': 'catalog', 'tool_id': t['id']} for t in selected_tools]
            else:
                response['text'] = ('Não encontrei uma resposta nas evidências e no catálogo local. ' +
                                    ('Tente um nome de alerta, regra, pacote ou ferramenta.' if review else 'Importe relatórios e gere uma revisão para consultar os achados.'))
    return response
