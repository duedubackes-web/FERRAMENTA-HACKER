"""Original deterministic starter generator. Inputs remain text, never code."""
from html import escape
import hashlib
import json


def scaffold(plan):
    title, brief = escape(plan['name']), escape(plan['brief'])
    seed = [{'id': str(index), 'title': row['task'], 'done': False} for index, row in enumerate(plan['backlog'])]
    key = 'atlas-starter-'+hashlib.sha256((plan['name']+'\n'+plan['brief']).encode()).hexdigest()[:16]
    html = '''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'"><title>'''+title+'''</title><link rel="stylesheet" href="app.css"><script src="app.js" defer></script></head><body><main><header><span class="eyebrow">PROTÓTIPO ORIGINAL · ATLAS STUDIO</span><h1>'''+title+'''</h1><p>'''+brief+'''</p></header><section class="metrics"><article><strong id="total">0</strong><span>tarefas do produto</span></article><article><strong id="done">0</strong><span>concluídas neste navegador</span></article></section><div class="columns"><section><h2>Da ideia à execução</h2><form id="add"><label for="task">Nova tarefa</label><div class="row"><input id="task" maxlength="300" required placeholder="Qual é o próximo passo?"><button>Adicionar</button></div></form><ul id="tasks"></ul><button id="reset" type="button" class="secondary">Restaurar backlog inicial</button></section><section class="assistant"><span class="eyebrow">ASSISTENTE DO PROTÓTIPO</span><h2>Converse com o plano</h2><p>Este chat consulta o brief e as tarefas locais. Não usa IA generativa.</p><div id="messages" aria-live="polite"></div><form id="chat"><label for="question">Pergunta sobre o produto</label><div class="row"><input id="question" required maxlength="1000" placeholder="Qual é o objetivo? ou O que falta?"><button>Enviar</button></div></form></section></div><footer>Protótipo baseado em template próprio. Dados locais neste navegador, sem autenticação ou sincronização. Não é uma implementação dos produtos usados como inspiração.</footer></main></body></html>'''
    css = '''*{box-sizing:border-box}body{margin:0;background:#f5f7f2;color:#213c30;font:15px/1.6 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:45px 25px}h1{font-size:clamp(32px,6vw,55px);line-height:1.1;letter-spacing:-2px;margin:18px 0}h2{font-size:22px}p{color:#6c7d6a;white-space:pre-wrap}.eyebrow{font-size:10px;letter-spacing:2px}.metrics{display:flex;gap:18px;margin:35px 0}.metrics article{background:#203e31;color:white;padding:22px;border-radius:13px;flex:1}.metrics strong{display:block;font-size:38px}.metrics span{font-size:12px;color:#cbe2b6}.columns{display:grid;grid-template-columns:1.1fr 1fr;gap:28px}.columns>section{background:white;padding:25px;border:1px solid #dee5d7;border-radius:13px}.row{display:flex;gap:8px}input{min-width:0;flex:1}input,button{padding:12px;border:1px solid #d4e1c9;border-radius:7px;font:inherit}button{background:#234e37;color:white;cursor:pointer;font-size:12px}button.secondary{background:white;color:#516f44}input:focus-visible,button:focus-visible{outline:3px solid #b0d979;outline-offset:2px}label{display:block;font-size:12px;margin-bottom:8px}ul{padding:0;list-style:none}li{display:flex;gap:10px;align-items:start;border-bottom:1px solid #e5ebdf;padding:15px 0;font-size:13px}li input{flex:0;margin-top:6px}li button{margin-left:auto;padding:3px 9px;background:#f1f5ec;color:#64785a}li.completed span{text-decoration:line-through;color:#94a18a}.message{padding:12px;border-radius:8px;background:#f3f6ee;margin:10px 0;white-space:pre-wrap;font-size:12px}.user{background:#e1edcf;margin-left:25px}#messages{max-height:330px;overflow:auto;margin:22px 0}footer{font-size:11px;color:#7c8b73;border-top:1px solid #dce5d3;margin-top:35px;padding-top:20px}@media(max-width:700px){.columns{grid-template-columns:1fr}main{padding:25px 18px}.row{flex-wrap:wrap}.row input{width:100%}}'''
    javascript = "'use strict';\nconst initial="+json.dumps(seed, ensure_ascii=True)+";\nconst brief="+json.dumps(plan['brief'], ensure_ascii=True)+";\nconst storageKey="+json.dumps(key)+";\n"+'''
const $ = selector => document.querySelector(selector);
let tasks;
try { tasks = JSON.parse(localStorage.getItem(storageKey)); } catch { tasks = null; }
if (!Array.isArray(tasks) || !tasks.every(t => t && typeof t.id === 'string' && typeof t.title === 'string' && typeof t.done === 'boolean')) tasks = structuredClone(initial);
function render() {
  $('#tasks').replaceChildren();
  for (const task of tasks) {
    const row = document.createElement('li'); row.className = task.done ? 'completed' : '';
    const check = document.createElement('input'); check.type = 'checkbox'; check.checked = task.done; check.setAttribute('aria-label', 'Concluir '+task.title);
    check.addEventListener('change', () => { task.done = check.checked; save(); });
    const text = document.createElement('span'); text.textContent = task.title;
    const remove = document.createElement('button'); remove.textContent = '×'; remove.setAttribute('aria-label', 'Remover '+task.title);
    remove.addEventListener('click', () => { tasks = tasks.filter(t => t.id !== task.id); save(); });
    row.append(check, text, remove); $('#tasks').append(row);
  }
  $('#total').textContent = tasks.length; $('#done').textContent = tasks.filter(t => t.done).length;
}
function save() { try { localStorage.setItem(storageKey, JSON.stringify(tasks)); } catch { /* Task state still works during this session. */ } render(); }
$('#add').addEventListener('submit', event => { event.preventDefault(); const title = $('#task').value.trim(); if (!title) return; tasks.push({id:crypto.randomUUID(),title,done:false}); $('#task').value = ''; save(); });
$('#reset').addEventListener('click', () => { if (confirm('Restaurar o backlog e remover alterações locais?')) { tasks = structuredClone(initial); save(); } });
function message(text, user) { const div = document.createElement('div'); div.className = 'message'+(user?' user':''); div.textContent = text; $('#messages').append(div); div.scrollIntoView({block:'nearest'}); }
$('#chat').addEventListener('submit', event => { event.preventDefault(); const question = $('#question').value.trim(); if (!question) return; message(question,true); const query = question.toLocaleLowerCase(); let reply;
  if (/objetivo|brief|publico|público|problema/.test(query)) reply = 'Brief declarado: '+brief;
  else if (/falta|pendente|tarefa|proximo|próximo|backlog/.test(query)) reply = tasks.filter(t => !t.done).map(t => '• '+t.title).join('\\n') || 'Não há tarefas pendentes neste quadro. Isso não comprova que o produto esteja completo.';
  else if (/concluid|concluíd|feito/.test(query)) reply = tasks.filter(t => t.done).length+' de '+tasks.length+' tarefas marcadas como concluídas neste navegador.';
  else reply = 'Posso consultar o objetivo do produto, as tarefas pendentes e as tarefas marcadas como concluídas. Esta resposta é uma consulta local, sem IA generativa.';
  message(reply,false); $('#question').value = '';
});
render();
'''
    return {'prototype/index.html': html, 'prototype/app.css': css, 'prototype/app.js': javascript,
            'prototype/README.md': '# Protótipo gerado pelo Atlas\n\nExecute `python -m http.server 8787 --bind 127.0.0.1` nesta pasta e abra http://127.0.0.1:8787.\n\nQuadro de tarefas com persistência no navegador e chat local sobre o brief/backlog. Template próprio, não geração livre por IA. Nenhuma dependência de frontend ou serviço externo. Não use para dados compartilhados sem implementar autenticação e armazenamento adequado.\n'}
