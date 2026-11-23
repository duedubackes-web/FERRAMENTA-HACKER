function inspectMessage(text) {
  const normalized = text.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase();
  const rules = [
    [/\b(urgente|imediatamente|ultima chance|em ate \d+ horas)\b/, 'Pressão por urgência'],
    [/\b(senha|codigo de verificacao|codigo sms|token|otp)\b/, 'Menção a senha ou código de verificação'],
    [/\b(pix|deposito|transferencia|taxa antecipada)\b/, 'Menção a pagamento ou transferência'],
    [/\b(conta bloqueada|conta suspensa|bloquearemos|sera cancelad[oa])\b/, 'Ameaça de bloqueio ou cancelamento']
  ];
  const signals = rules.filter(([pattern]) => pattern.test(normalized)).map(([, label]) => label);
  const links = new Map();
  for (const raw of extractIndicators(text).urls) {
    const url = new URL(raw);
    const flags = [];
    if (url.protocol === 'http:') flags.push('HTTP sem criptografia');
    if (url.username || url.password) flags.push('Endereço inclui seção de credenciais');
    if (/(^|\.)xn--/.test(url.hostname)) flags.push('Domínio internacionalizado em punycode');
    if (/^\d+\.\d+\.\d+\.\d+$|^\[/.test(url.hostname)) flags.push('Endereço IP como destino');
    const key = url.protocol + '//' + url.host;
    const prior = links.get(key) ?? [];
    links.set(key, [...new Set([...prior, ...flags])]);
  }
  return {
    sinais_na_mensagem: signals,
    destinos_visiveis: [...links].map(([destino, sinais]) => ({ destino, sinais })),
    orientacao: 'Confirme a solicitação por um canal oficial já conhecido. Estes sinais servem para triagem e não determinam se a mensagem é legítima.'
  };
}

function inspectContact(type, text) {
  const value = text.trim();
  if (type === 'email') {
    const [local, domain, extra] = value.split('@');
    if (extra !== undefined || value.length > 254 || !local || local.length > 64 ||
        !/^[a-z0-9!#$%&'*+\/=?^_`{|}~.-]+$/i.test(local) ||
        local.startsWith('.') || local.endsWith('.') || local.includes('..') ||
        !domain || !/^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z](?:[a-z0-9-]{0,61}[a-z0-9])$/i.test(domain)) {
      throw new Error('Informe um e-mail no formato nome@dominio, com domínio ASCII.');
    }
    return { tipo: 'E-mail', dominio: domain.toLowerCase(), formato: 'Compatível com a verificação básica',
      alcance: 'A sintaxe não confirma existência, titularidade ou entrega.' };
  }
  if (!/^\+?[\d ().-]+$/.test(value)) throw new Error('Use dígitos e separadores comuns. Inclua + e o código do país para formato internacional.');
  const digits = value.replace(/\D/g, '');
  const international = value.startsWith('+');
  if (digits.length < 7 || digits.length > 15 || (international && digits.startsWith('0'))) {
    throw new Error('A quantidade de dígitos ou o prefixo é incompatível com a verificação básica.');
  }
  return {
    tipo: 'Telefone',
    numero_mascarado: (international ? '+' : '') + '•'.repeat(digits.length - 4) + digits.slice(-4),
    formato: international ? 'Internacional, com prefixo +' : 'Local, sem código de país confirmado',
    indicacao: international && digits.startsWith('55') ? 'Prefixo internacional +55 (Brasil)' : 'País não inferido',
    alcance: 'O formato não confirma atribuição, operadora ou titular.'
  };
}

const fraudText = document.querySelector('#fraud-text');
document.querySelector('#fraud-example').addEventListener('click', () => {
  fraudText.value = 'URGENTE: sua conta será cancelada. Confirme seu código de verificação em http://example.org/validar.';
  document.querySelector('#fraud-result').textContent = '';
  fraudText.focus();
});

document.querySelector('#fraud-form').addEventListener('submit', event => {
  event.preventDefault();
  const text = fraudText.value.trim();
  document.querySelector('#fraud-result').textContent = text
    ? JSON.stringify(inspectMessage(text), null, 2)
    : 'Cole o texto da mensagem para analisar.';
});

document.querySelector('#contact-form').addEventListener('submit', event => {
  event.preventDefault();
  const result = document.querySelector('#contact-result');
  try {
    result.textContent = JSON.stringify(inspectContact(
      document.querySelector('#contact-type').value,
      document.querySelector('#contact-text').value
    ), null, 2);
  } catch (error) {
    result.textContent = error.message;
  }
});
