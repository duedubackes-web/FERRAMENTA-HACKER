const catalog = [
  ['Kali Linux', 'Ambiente', 'Distribuição para análise e auditoria.', 'Registre a versão do ambiente, a origem dos arquivos e o responsável pela coleta.', ['kali']],
  ['REA', 'Engenharia reversa', 'Registro de observações sobre software próprio ou autorizado.', 'Anote a versão, a evidência observada, sua interpretação e o grau de confiança.'],
  ['Craft Anything', 'Engenharia de software', 'Documentação de requisitos e comportamento observado.', 'Transforme observações autorizadas em requisitos e critérios de aceitação verificáveis.'],
  ['Nmap', 'Rede', 'Revisão de inventário de serviços já coletado.', 'Registre a data do inventário e confirme os serviços esperados com o responsável pelo ativo.'],
  ['Trivy', 'Dependências', 'Triagem de relatórios de imagens, pacotes e configuração.', 'Registre pacote, versão instalada, versão corrigida e decisão de priorização.'],
  ['OSINT', 'Fontes abertas', 'Registro e verificação de fontes públicas.', 'Documente a fonte, a data e o grau de confiança. Minimize dados pessoais.'],
  ['Pentest', 'Avaliação', 'Acompanhamento de achados de um teste autorizado.', 'Registre escopo, impacto, evidência redigida, responsável e estado da correção.'],
  ['Geradores de LLM', 'Documentação', 'Preparação de material para revisão de texto.', 'Remova segredos e dados pessoais antes de compartilhar. Confira cada afirmação gerada com a fonte.', ['llm', 'modelo de linguagem']],
  ['Amass', 'Inventário', 'Revisão de inventário de domínios já exportado.', 'Valide se cada domínio pertence ao escopo e registre a fonte do inventário.'],
  ['theHarvester', 'Fontes abertas', 'Revisão de resultados de fontes públicas.', 'Confirme a procedência dos dados e preserve somente os campos necessários.', ['theharvester', 'harvester']],
  ['Metasploit Framework', 'Avaliação', 'Registro defensivo de conclusões de uma avaliação.', 'Documente impacto, versão afetada e remediação com evidências redigidas.', ['metasploit']],
  ['SQLmap', 'Aplicações', 'Acompanhamento de achados relacionados a injeção SQL.', 'Registre o componente afetado e acompanhe a correção com consultas parametrizadas e revisão de código.', ['sql map']],
  ['Hashcat', 'Credenciais', 'Registro de métricas agregadas de uma auditoria de senhas.', 'Prefira totais e recomendações. Exclua senhas, hashes de credenciais e dados de identificação.'],
  ['John the Ripper', 'Credenciais', 'Documentação de resultados agregados de auditoria.', 'Registre a política avaliada e as ações corretivas. Preserve o sigilo das credenciais.', ['john']],
  ['Hydra', 'Credenciais', 'Triagem de registros de autenticação.', 'Verifique se os logs registram falhas repetidas, bloqueios e alertas. Use dados redigidos.', ['hidra', 'thc-hydra']],
  ['Medusa', 'Credenciais', 'Registro de controles de autenticação.', 'Documente a eficácia de limites de tentativa, alertas e autenticação multifator.'],
  ['Ghidra', 'Engenharia reversa', 'Documentação de análise estática autorizada.', 'Registre hash, versão e observações verificáveis de arquivos próprios ou autorizados.'],
  ['Cuckoo', 'Análise de arquivos', 'Triagem de relatório comportamental de sandbox.', 'Documente os comportamentos observados e a confiança em cada indicador.'],
  ['CAPE', 'Análise de arquivos', 'Revisão de relatórios de sandbox já produzidos.', 'Registre a origem da amostra, seu hash e os indicadores confirmados no relatório.', ['cape sandbox']],
  ['Wireshark', 'Rede', 'Revisão de resumos de captura de rede.', 'Anote horário, protocolo e origem da captura. Remova dados sensíveis antes de compartilhar.'],
  ['Aircrack-ng', 'Rede sem fio', 'Documentação do estado de segurança de redes próprias.', 'Registre versões, política de criptografia e ações de correção, preservando as credenciais.', ['aircrack', 'wi-fi']]
].map(([name, category, description, help, aliases = []]) => ({ name, category, description, help, aliases }));

const byId = id => document.getElementById(id);
const normalize = text => text.toLowerCase().normalize('NFD').replace(/\p{M}/gu, '');
const library = byId('tool-library');
const detail = byId('tool-detail');
const note = byId('tool-note');
const help = byId('tool-help');
const helpButton = byId('show-help');
const log = byId('chat-log');
let selected;

function renderLibrary() {
  const query = normalize(byId('tool-search').value.trim());
  const exact = catalog.filter(tool => [tool.name, ...tool.aliases].some(name => normalize(name) === query));
  const matches = exact.length ? exact : catalog.filter(tool =>
    normalize([tool.name, tool.category, ...tool.aliases].join(' ')).includes(query));
  library.replaceChildren();
  byId('tool-empty').hidden = matches.length > 0;
  for (const tool of matches) {
    const card = document.createElement('article');
    card.className = 'card';
    const category = document.createElement('p');
    category.className = 'eyebrow';
    category.textContent = tool.category;
    const name = document.createElement('strong');
    name.textContent = tool.name;
    const description = document.createElement('p');
    description.textContent = tool.description;
    const button = document.createElement('button');
    button.className = 'outline';
    button.type = 'button';
    button.textContent = 'Abrir ficha';
    button.setAttribute('aria-label', 'Abrir ficha de ' + tool.name);
    button.addEventListener('click', () => {
      selected = tool;
      byId('detail-title').textContent = tool.name;
      byId('detail-category').textContent = tool.category;
      byId('detail-description').textContent = tool.description;
      help.textContent = tool.help;
      help.hidden = true;
      helpButton.setAttribute('aria-expanded', 'false');
      note.value = '';
      detail.showModal();
    });
    card.append(category, name, description, button);
    library.append(card);
  }
}

function reply(question) {
  const normalized = normalize(question);
  const topics = { 'diagnostico': 'Diagnóstico', 'acoes': 'Resposta e revalidação', 'conclusao': 'Conclusão' };
  const topic = normalized.match(/\b(diagnostico|acoes|conclusao) do caso\b/)?.[1];
  if (topic) {
    const step = latestTriage?.etapas.find(item => item.titulo === topics[topic]);
    return step ? step.detalhes.join('\n') : 'Execute uma triagem no Orquestrador para consultar o caso nesta sessão.';
  }
  const words = normalized.match(/[\p{L}\d]+/gu) ?? [];
  const matches = catalog.filter(tool => [tool.name, ...tool.aliases].some(name => {
    const term = normalize(name);
    return term.includes(' ') || term.includes('-') ? normalized.includes(term) : words.includes(term);
  }));
  if (matches.length) return matches.map(tool => tool.name + ' — ' + tool.description + ' ' + tool.help).join('\n\n');
  if (normalized.includes('export')) return 'Abra uma ficha, cole um trecho redigido do relatório e use Baixar registro JSON. O download inclui a ferramenta e a data do registro.';
  if (normalized.includes('escopo')) return 'Documente os ativos autorizados, a janela da avaliação, o responsável e os limites antes de registrar os achados.';
  if (normalized.includes('evidencia')) return 'Registre a origem, data e contexto da evidência. Use a bancada para calcular SHA-256 do arquivo original.';
  return 'Posso orientar sobre as ferramentas do catálogo, evidências, escopo e exportação de relatórios. Cite o nome da ferramenta para ver sua orientação.';
}

function appendMessage(author, message) {
  const item = document.createElement('li');
  const label = document.createElement('strong');
  label.textContent = author;
  const body = document.createElement('span');
  body.style.whiteSpace = 'pre-wrap';
  body.textContent = message;
  item.append(label, body);
  log.append(item);
  log.scrollTop = log.scrollHeight;
}

function ask(question) {
  appendMessage('Você', question);
  appendMessage('Vigília', reply(question));
}

helpButton.addEventListener('click', () => {
  help.hidden = !help.hidden;
  helpButton.setAttribute('aria-expanded', String(!help.hidden));
});
byId('tool-report').addEventListener('submit', event => {
  event.preventDefault();
  if (!note.value.trim()) {
    note.focus();
    return;
  }
  const report = { ferramenta: selected.name, registrado_em: new Date().toISOString(), evidencia: note.value.trim() };
  downloadJson(report, 'vigilia-registro.json');
});
byId('ask-about-tool').addEventListener('click', () => {
  detail.close();
  ask('Como documentar evidências de ' + selected.name + '?');
  location.hash = 'chat';
  byId('chat-message').focus({ preventScroll: true });
});
byId('chat-form').addEventListener('submit', event => {
  event.preventDefault();
  const input = byId('chat-message');
  if (!input.value.trim()) return;
  ask(input.value.trim());
  input.value = '';
  input.focus();
});
byId('tool-search').addEventListener('input', renderLibrary);
renderLibrary();
