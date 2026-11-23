const labCases = [
  {
    title: 'Ruído no gateway',
    category: 'Análise de logs',
    description: 'Separe a origem dos eventos bloqueados dos acessos bem-sucedidos.',
    type: 'log',
    evidence: '08:12Z gateway ALLOW origem=192.0.2.10\n08:14Z gateway BLOCK origem=198.51.100.44\n08:16Z gateway BLOCK origem=198.51.100.44',
    question: 'Qual IPv4 aparece nos eventos bloqueados?',
    answer: '198.51.100.44',
    hint: 'Localize o campo origem nos eventos BLOCK. Repetições contam como um único indicador.',
    explanation: 'Os dois eventos BLOCK têm a mesma origem. O log mostra o bloqueio do gateway. A classificação do endereço depende de correlação com outras evidências.'
  },
  {
    title: 'Cabeçalho no lugar errado',
    category: 'Auditoria HTTP',
    description: 'Diferencie os controles presentes no cabeçalho de texto no corpo.',
    type: 'http',
    evidence: 'HTTP/1.1 200 OK\nContent-Type: text/plain\nReferrer-Policy: no-referrer\n\nContent-Security-Policy: default-src \'self\'',
    question: 'Qual controle aparece somente no corpo da resposta? Digite o nome do cabeçalho.',
    answer: 'Content-Security-Policy',
    hint: 'A linha em branco marca o fim do bloco de cabeçalhos.',
    explanation: 'Content-Security-Policy aparece depois da linha em branco. O navegador só recebe essa linha como parte do corpo desta resposta.'
  },
  {
    title: 'Revalidação de uma correção',
    category: 'Resposta defensiva',
    description: 'Compare duas respostas salvas antes de encerrar um achado.',
    type: 'http',
    context: 'Resposta anterior',
    baseline: 'HTTP/1.1 200 OK\nContent-Type: text/plain',
    evidence: 'HTTP/1.1 200 OK\nContent-Type: text/plain\nX-Content-Type-Options: nosniff',
    question: 'Qual cabeçalho foi adicionado na nova coleta?',
    answer: 'X-Content-Type-Options',
    hint: 'Compare os dois blocos e desconsidere os campos que aparecem nas duas respostas.',
    explanation: 'A nova coleta contém X-Content-Type-Options com o valor nosniff. Registre a comparação e valide a aplicação do controle nos recursos relevantes.'
  }
];

const labPanel = byId('lab-panel');
const labResponse = byId('lab-response');
const labFeedback = byId('lab-feedback');
const labHint = byId('lab-hint');
const labHintToggle = byId('lab-hint-toggle');
let activeLab;

function openLab(lab) {
  activeLab = lab;
  byId('lab-title').textContent = lab.title;
  byId('lab-brief').textContent = lab.description;
  byId('lab-evidence').textContent = lab.baseline
    ? lab.context + '\n' + lab.baseline + '\n\nNova coleta\n' + lab.evidence
    : lab.evidence;
  byId('lab-question').textContent = lab.question;
  labHint.textContent = lab.hint;
  labHint.hidden = true;
  labHintToggle.setAttribute('aria-expanded', 'false');
  labHintToggle.textContent = 'Mostrar pista';
  labFeedback.textContent = '';
  labResponse.value = '';
  labPanel.hidden = false;
  labResponse.focus();
}

for (const lab of labCases) {
  const card = document.createElement('button');
  card.type = 'button';
  card.className = 'card';
  const category = document.createElement('span');
  category.className = 'eyebrow';
  category.textContent = lab.category;
  const title = document.createElement('strong');
  title.textContent = lab.title;
  const description = document.createElement('span');
  description.textContent = lab.description;
  card.append(category, title, description);
  card.addEventListener('click', () => openLab(lab));
  byId('lab-list').append(card);
}

labHintToggle.addEventListener('click', () => {
  labHint.hidden = !labHint.hidden;
  labHintToggle.setAttribute('aria-expanded', String(!labHint.hidden));
  labHintToggle.textContent = labHint.hidden ? 'Mostrar pista' : 'Ocultar pista';
});

byId('lab-triage').addEventListener('click', () => {
  if (!activeLab) return;
  artifactType.value = activeLab.type;
  artifactText.value = activeLab.evidence;
  resetTriage();
  location.hash = 'orquestrador';
  artifactText.focus({ preventScroll: true });
});

byId('lab-answer').addEventListener('submit', event => {
  event.preventDefault();
  if (!activeLab) return;
  const correct = labResponse.value.trim().toLowerCase() === activeLab.answer.toLowerCase();
  labFeedback.textContent = correct ? 'Correto. ' + activeLab.explanation
    : 'A resposta ainda não corresponde à evidência. Consulte a pista e tente de novo.';
});
