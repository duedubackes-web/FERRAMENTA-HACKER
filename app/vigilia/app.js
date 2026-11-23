const tool = document.querySelector('#tool');
const file = document.querySelector('#file');
const evidence = document.querySelector('#evidence');
const result = document.querySelector('#result');
const save = document.querySelector('#save');
const placeholder = 'O resultado da análise aparece aqui.';
const examples = {
  ioc: '2026-11-20 INFO recurso=https://example.org/relatorio origem=192.0.2.25',
  headers: 'HTTP/1.1 200 OK\nContent-Type: text/html; charset=UTF-8\nX-Content-Type-Options: nosniff\nReferrer-Policy: strict-origin-when-cross-origin'
};
let revision = 0;
let report = null;

function reset() {
  revision += 1;
  report = null;
  save.disabled = true;
  result.textContent = placeholder;
}

function selectTool() {
  document.querySelector('#file-area').hidden = tool.value !== 'hash';
  document.querySelector('#text-area').hidden = tool.value === 'hash';
  document.querySelector('#text-label').textContent = tool.value === 'headers'
    ? 'Cabeçalhos da resposta HTTP' : 'Texto ou log da evidência';
  evidence.value = '';
  file.value = '';
  reset();
}

function extractIndicators(input) {
  const unique = items => [...new Set(items)];
  const urls = (input.match(/https?:\/\/[^\s<>"']+/gi) ?? [])
    .map(url => url.replace(/[),.;]+$/, ''))
    .filter(url => {
      try { return Boolean(new URL(url).hostname); } catch { return false; }
    });
  const ipv4 = (input.match(/(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.]\d|\w)/g) ?? [])
    .filter(ip => ip.split('.').every(part => Number(part) <= 255 && String(Number(part)) === part));
  const hashes = (input.match(/\b(?:[a-f0-9]{64}|[a-f0-9]{40}|[a-f0-9]{32})\b/gi) ?? [])
    .map(hash => hash.toLowerCase());
  return { urls: unique(urls), ipv4: unique(ipv4), hashes: unique(hashes) };
}

function reviewHeaders(input) {
  const headers = new Map();
  const [headerBlock] = input.split(/\r?\n\r?\n/, 1);
  for (const line of headerBlock.split(/\r?\n/)) {
    const match = line.match(/^([\w-]+):[ \t]*(.*)$/);
    if (!match) continue;
    const name = match[1].toLowerCase();
    const values = headers.get(name) ?? [];
    values.push(match[2].trim());
    headers.set(name, values);
  }
  if (!headers.size) throw new Error('Cole pelo menos um cabeçalho HTTP no formato Nome: valor.');
  const names = ['content-security-policy', 'strict-transport-security', 'x-content-type-options',
    'referrer-policy', 'permissions-policy', 'x-frame-options'];
  return {
    observacao: 'A presença de um cabeçalho não confirma que sua configuração seja adequada.',
    cabecalhos: Object.fromEntries(names.map(name => [name,
      headers.get(name)?.some(Boolean) ? 'Presente' : 'Ausente ou vazio']))
  };
}

document.querySelectorAll('[data-tool]').forEach(card => {
  card.addEventListener('click', () => {
    tool.value = card.dataset.tool;
    selectTool();
    location.hash = 'bancada';
    tool.focus({ preventScroll: true });
  });
});
tool.addEventListener('change', selectTool);
file.addEventListener('change', reset);
evidence.addEventListener('input', reset);
document.querySelector('#example').addEventListener('click', () => {
  evidence.value = examples[tool.value];
  reset();
  evidence.focus();
});

document.querySelector('#analysis').addEventListener('submit', async event => {
  event.preventDefault();
  reset();
  const request = revision;
  const selectedTool = tool.value;
  try {
    let data;
    if (selectedTool === 'hash') {
      const selected = file.files[0];
      if (!selected) throw new Error('Escolha um arquivo para calcular o hash.');
      if (selected.size > 128 * 1024 * 1024) throw new Error('O limite por arquivo é de 128 MB.');
      if (!globalThis.crypto?.subtle) throw new Error('Abra a bancada por HTTPS, localhost ou como arquivo local.');
      result.textContent = 'Calculando SHA-256…';
      const bytes = await crypto.subtle.digest('SHA-256', await selected.arrayBuffer());
      const sha256 = Array.from(new Uint8Array(bytes), byte => byte.toString(16).padStart(2, '0')).join('');
      data = { arquivo: selected.name, bytes: selected.size, sha256 };
    } else {
      const input = evidence.value.trim();
      if (!input) throw new Error('Cole a evidência ou carregue um exemplo.');
      data = selectedTool === 'ioc' ? extractIndicators(input) : reviewHeaders(input);
    }
    if (revision !== request) return;
    report = { ferramenta: selectedTool, analisado_em: new Date().toISOString(), resultado: data };
    result.textContent = JSON.stringify(report, null, 2);
    save.disabled = false;
  } catch (error) {
    if (revision === request) result.textContent = error.message;
  }
});

function downloadJson(data, filename) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
  const download = document.createElement('a');
  download.href = url;
  download.download = filename;
  download.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

save.addEventListener('click', () => {
  if (report) downloadJson(report, 'vigilia-' + report.ferramenta + '.json');
});
