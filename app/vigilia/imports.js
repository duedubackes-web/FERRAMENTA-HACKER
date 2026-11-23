function analyzeTrivy(input) {
  const report = JSON.parse(input);
  if (!Array.isArray(report?.Results) && !(report?.SchemaVersion && report?.Results == null)) {
    throw new Error('Selecione um relatório JSON do Trivy com o campo Results.');
  }
  const findings = [];
  const severities = {};
  for (const entry of report.Results ?? []) {
    if (!entry || typeof entry.Target !== 'string') throw new Error('O relatório contém um alvo inválido.');
    if (entry.Vulnerabilities != null && !Array.isArray(entry.Vulnerabilities)) {
      throw new Error('A lista Vulnerabilities está em formato inválido.');
    }
    for (const item of entry.Vulnerabilities ?? []) {
      if (!item || typeof item.VulnerabilityID !== 'string') throw new Error('Um registro não possui VulnerabilityID.');
      const severity = String(item.Severity ?? 'UNKNOWN').toUpperCase();
      const key = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].includes(severity) ? severity : 'UNKNOWN';
      severities[key] = (severities[key] ?? 0) + 1;
      findings.push({ alvo: entry.Target, id: item.VulnerabilityID, pacote: item.PkgName ?? null,
        instalada: item.InstalledVersion ?? null, corrigida: item.FixedVersion || null, severidade: key });
    }
  }
  return { alvos: (report.Results ?? []).length, por_severidade: severities, vulnerabilidades: findings };
}

function analyzeNmap(input) {
  if (/<!ENTITY\b|<!DOCTYPE[^>]*(?:\[|\bSYSTEM\b|\bPUBLIC\b)/i.test(input)) {
    throw new Error('Use um XML do Nmap com declaração de tipo simples.');
  }
  const xml = new DOMParser().parseFromString(input, 'application/xml');
  if (xml.documentElement.localName !== 'nmaprun' || xml.querySelector('parsererror')) {
    throw new Error('Selecione um relatório XML válido do Nmap.');
  }
  return {
    dispositivos: [...xml.documentElement.children].filter(node => node.localName === 'host').map(host => ({
      estado: host.querySelector('status')?.getAttribute('state') ?? null,
      enderecos: [...host.querySelectorAll('address[addrtype="ipv4"], address[addrtype="ipv6"]')].map(node => node.getAttribute('addr')),
      portas: [...host.querySelectorAll('ports > port')].map(port => ({
        porta: port.getAttribute('portid'), protocolo: port.getAttribute('protocol'),
        estado: port.querySelector('state')?.getAttribute('state') ?? null,
        servico: port.querySelector('service')?.getAttribute('name') ?? null
      }))
    }))
  };
}

function parseWiresharkCsv(input) {
  const rows = [];
  let row = [], field = '', quoted = false, closed = false;
  for (let index = 0; index < input.length; index++) {
    const char = input[index];
    if (quoted) {
      if (char === '"' && input[index + 1] === '"') { field += '"'; index++; }
      else if (char === '"') { quoted = false; closed = true; }
      else field += char;
    } else if (char === ',' || char === '\n' || char === '\r') {
      row.push(field);
      field = '';
      closed = false;
      if (char !== ',') {
        if (char === '\r' && input[index + 1] === '\n') index++;
        if (row.some(Boolean)) rows.push(row);
        row = [];
      }
    } else if (!closed && char === '"' && !field) quoted = true;
    else if (closed || char === '"') throw new Error('O CSV contém aspas em posição inválida.');
    else field += char;
  }
  if (quoted) throw new Error('O CSV contém um campo entre aspas sem fechamento.');
  row.push(field);
  if (row.some(Boolean)) rows.push(row);
  return rows;
}

function analyzeWireshark(input) {
  const [header, ...rows] = parseWiresharkCsv(input);
  const fields = header?.map(field => field.trim().toLowerCase()) ?? [];
  const protocol = fields.indexOf('protocol');
  const length = fields.indexOf('length');
  if (protocol < 0 || length < 0) throw new Error('Exporte a lista de pacotes em CSV com as colunas Protocol e Length.');
  const counts = new Map();
  let bytes = 0;
  for (const row of rows) {
    const size = Number(row[length]);
    if (row.length !== fields.length || !/^\d+$/.test(row[length]?.trim()) || !Number.isSafeInteger(size)) {
      throw new Error('O CSV possui uma linha com colunas ou comprimento inválidos.');
    }
    const name = row[protocol].trim() || 'Indefinido';
    counts.set(name, (counts.get(name) ?? 0) + 1);
    bytes += size;
  }
  return { pacotes: rows.length, bytes, por_protocolo: Object.fromEntries(counts) };
}

function analyzeAndroidManifest(input) {
  if (/<!DOCTYPE|<!ENTITY/i.test(input)) throw new Error('O manifesto não deve declarar um DTD.');
  const xml = new DOMParser().parseFromString(input, 'application/xml');
  const manifest = xml.documentElement;
  if (manifest.localName !== 'manifest' || xml.querySelector('parsererror')) {
    throw new Error('Selecione um AndroidManifest.xml em texto, extraído do projeto Android.');
  }
  const android = 'http://schemas.android.com/apk/res/android';
  const attr = (node, field) => node?.getAttributeNS(android, field) ?? null;
  const children = [...manifest.children];
  const app = children.find(node => node.localName === 'application');
  const permissions = children.filter(node => ['uses-permission', 'uses-permission-sdk-23'].includes(node.localName))
    .map(node => ({ nome: attr(node, 'name'), max_sdk: attr(node, 'maxSdkVersion') })).filter(item => item.nome);
  const sensitive = new Set(['CAMERA', 'RECORD_AUDIO', 'READ_CONTACTS', 'ACCESS_FINE_LOCATION',
    'ACCESS_COARSE_LOCATION', 'ACCESS_BACKGROUND_LOCATION', 'READ_SMS', 'RECEIVE_SMS', 'SEND_SMS']);
  const components = [...(app?.children ?? [])]
    .filter(node => ['activity', 'activity-alias', 'receiver', 'service', 'provider'].includes(node.localName))
    .filter(node => attr(node, 'exported') === 'true')
    .map(node => ({ tipo: node.localName, nome: attr(node, 'name'), permissao: attr(node, 'permission') }));
  return {
    pacote: manifest.getAttribute('package'),
    permissoes_declaradas: permissions,
    permissoes_para_revisar: permissions.filter(item =>
      item.nome.startsWith('android.permission.') && sensitive.has(item.nome.slice('android.permission.'.length))),
    componentes_com_exportacao_explicita: components,
    configuracao_declarada: {
      depuracao: attr(app, 'debuggable'),
      backup: attr(app, 'allowBackup'),
      trafego_em_texto_claro: attr(app, 'usesCleartextTraffic')
    },
    alcance: 'Auditoria estática do XML. Valores ausentes dependem da compilação e da versão Android. A análise não identifica malware nem verifica permissões concedidas.'
  };
}

const reportAnalyzers = {
  "Auditoria Android": { accept: ".xml", label: "AndroidManifest.xml em texto", run: analyzeAndroidManifest },
  Nmap: { accept: '.xml', label: 'XML exportado pelo Nmap', run: analyzeNmap },
  Trivy: { accept: '.json', label: 'JSON exportado pelo Trivy', run: analyzeTrivy },
  Wireshark: { accept: '.csv', label: 'CSV da lista de pacotes do Wireshark', run: analyzeWireshark }
};
