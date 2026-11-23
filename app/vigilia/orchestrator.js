const controlActions = {
  'content-security-policy': 'Defina uma política de segurança de conteúdo compatível com os recursos da aplicação.',
  'strict-transport-security': 'Confirme que o serviço usa HTTPS antes de avaliar a política HSTS.',
  'x-content-type-options': 'Confira os tipos MIME e avalie o uso de nosniff.',
  'referrer-policy': 'Defina quanto da URL de origem pode ser compartilhado.',
  'permissions-policy': 'Restrinja recursos do navegador que a aplicação dispensa.',
  'x-frame-options': 'Confira se o uso de iframe é necessário. Revise também frame-ancestors na política CSP.'
};

function runTriage(type, input) {
  const indicators = extractIndicators(input);
  const counts = Object.entries(indicators).map(([key, values]) => {
    const label = { urls: 'URLs', ipv4: 'endereços IPv4', hashes: 'hashes' }[key];
    return label + ': ' + values.length;
  });
  const headerAudit = type === 'http' ? reviewHeaders(input) : null;
  const missing = headerAudit
    ? Object.entries(headerAudit.cabecalhos).filter(([, status]) => status !== 'Presente').map(([name]) => name)
    : [];
  const diagnosis = headerAudit
    ? missing.length + ' de 6 cabeçalhos ausentes ou vazios na resposta salva. A relevância depende do contexto da aplicação.'
    : 'Os indicadores são pistas para correlação. A triagem não atribui malícia ou confirma um incidente.';
  const actions = headerAudit
    ? [...missing.map(name => controlActions[name]), 'Após uma correção, salve uma nova resposta do mesmo recurso e repita a triagem.']
    : ['Correlacione os indicadores com registros de ativos e eventos do mesmo período.', 'Preserve o arquivo original e registre origem, horário e contexto.'];
  const conclusion = headerAudit
    ? 'A revisão se limita à presença de cabeçalhos na amostra. Valide os valores e a aplicabilidade antes de encerrar o caso.'
    : 'A extração se limita a URLs HTTP(S), IPv4 e hashes no texto fornecido. Revise o contexto antes de classificar o caso.';
  return {
    tipo: type,
    gerado_em: new Date().toISOString(),
    indicadores: indicators,
    auditoria_http: headerAudit,
    etapas: [
      { titulo: 'Extração', detalhes: counts },
      { titulo: 'Organização', detalhes: ['Indicadores separados por tipo e sem duplicatas.', input.split(/\r?\n/).length + ' linhas na amostra.'] },
      {
        titulo: 'Auditoria',
        detalhes: headerAudit ? Object.entries(headerAudit.cabecalhos).map(([name, status]) => name + ' — ' + status)
          : ['Auditoria HTTP dispensada para evidência do tipo log.']
      },
      { titulo: 'Diagnóstico', detalhes: [diagnosis] },
      { titulo: 'Resposta e revalidação', detalhes: actions },
      { titulo: 'Conclusão', detalhes: [conclusion] }
    ]
  };
}

const triageForm = document.querySelector('#orchestrator-form');
const artifactType = document.querySelector('#artifact-type');
const artifactText = document.querySelector('#artifact-text');
const triageStatus = document.querySelector('#triage-status');
const triageSteps = document.querySelector('#triage-steps');
const exportTriage = document.querySelector('#export-triage');
let latestTriage = null;

function resetTriage() {
  latestTriage = null;
  triageSteps.replaceChildren();
  triageStatus.textContent = '';
  exportTriage.disabled = true;
}

artifactText.addEventListener('input', resetTriage);
artifactType.addEventListener('change', resetTriage);
document.querySelector('#artifact-example').addEventListener('click', () => {
  artifactText.value = examples[artifactType.value === 'http' ? 'headers' : 'ioc'];
  resetTriage();
  artifactText.focus();
});

triageForm.addEventListener('submit', event => {
  event.preventDefault();
  resetTriage();
  try {
    const input = artifactText.value.trim();
    if (!input) throw new Error('Cole uma evidência ou use o exemplo fictício.');
    latestTriage = runTriage(artifactType.value, input);
    for (const step of latestTriage.etapas) {
      const row = document.createElement('li');
      const heading = document.createElement('h3');
      const details = document.createElement('ul');
      heading.textContent = step.titulo;
      for (const item of step.detalhes) {
        const line = document.createElement('li');
        line.textContent = item;
        details.append(line);
      }
      row.append(heading, details);
      triageSteps.append(row);
    }
    triageStatus.textContent = 'Triagem concluída. Consulte as etapas abaixo ou pergunte sobre o caso no chat.';
    exportTriage.disabled = false;
  } catch (error) {
    resetTriage();
    triageStatus.textContent = error.message;
  }
});

exportTriage.addEventListener('click', () => {
  if (!latestTriage) return;
  downloadJson(latestTriage, 'vigilia-parecer.json');
});
