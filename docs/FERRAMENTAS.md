# Execuções de REA e Craft Anything

## Procedimento aplicado

1. REA: ler `.agents/skills/reverse-engineer-anything/SKILL.md` do commit fixado. O guia recomenda não usar REA para análise ordinária de código-fonte completo. Por isso, a arquitetura dos repositórios foi estudada com leitura de fontes e buscas, enquanto REA foi aplicado ao JavaScript efetivamente entregue por um site.
2. Craft Anything: seguir a sequência Study → Build → Check → Ready como organização do trabalho. Nesta entrega foi executada a etapa de inventário da investigação (Study). Build/Check do produto-alvo ainda não ocorreram; a CLI própria de pesquisa foi criada e verificada separadamente.
3. Preservar evidências completas e limitações; não converter um inventário em alegação de reconstrução ou auditoria.

## Instalação local realizada

REA 6.9.0 obtido do npm com `--ignore-scripts`, sem instalação global nem registro MCP. O runtime existente foi Node.js 24.22.1. `research/tooling-npm-lock.json` preserva as versões resolvidas e integridades de pacotes, não implica uma auditoria das dependências.
Craft Anything 0.6.1 obtido do tarball oficial linux-x86_64. SHA-256 do tarball: `83ec0730c9117f399122b315c63ed4c3a8d31ac55bddd74cb8b33cd2f76ef704`, conferido contra SHA256SUMS.txt da mesma release.
Isso verifica integridade contra o canal recebido; não foi feita validação independente de assinatura ou identidade de publicação.

URL: https://github.com/storytold/craft-anything/releases/download/v0.6.1/craft-anything-0.6.1-linux-x86_64.tar.gz

As versões dos executáveis (6.9.0 e 0.6.1) são distintas dos commits de desenvolvimento coletados. Os snapshots não devem ser apresentados como builds idênticos a essas releases.
Nenhum dos dois foi registrado no perfil global do usuário. Não foram iniciados agentes externos para reconstruir os alvos.

## Chamadas efetivas

Para REA, foi usado o entrypoint `node /workspace/work/tooling/node_modules/rea-agents/scripts/rea.mjs` com os argumentos:

```text
analyze-javascript-application /workspace/work/web/wireshark-scripts --format json
```

Os 11 scripts inline vieram de um GET público a https://www.wireshark.org/. A relação entre índice no HTML e arquivo está em `research/web/script-provenance.json`.
Foram lidos 19.765 bytes de texto e analisados 11 arquivos JavaScript, sem falhas sintáticas reportadas. As 6 findings reportadas pelo analisador não são 6 vulnerabilidades confirmadas.
O JSON completo está em `research/evidence/rea-wireshark-scripts.json.gz`, e a síntese em `rea-summary.json`.

Para Craft Anything, foi usado `/workspace/work/craft-runtime/craft-anything-cli` com:

```text
--deep core-archive-show --json PARAMETROS_JSON
```

Os parâmetros por ZIP foram: `path` absoluto do snapshot, `max_depth: 0`, `max_entries: 20000`, `max_total_bytes: 1000000000`, `offset: 0` (padrão) e `limit: 20000`.
Os diretórios de dados/configuração foram redirecionados para `/workspace/work/runtime-state` usando XDG_DATA_HOME e XDG_CONFIG_HOME.
Deep permite ler arquivos; **não é um procedimento clean room independente**. Os alvos coletados não foram executados.

## Resultados do inventário Craft

| Fonte | Itens no ZIP examinados/total | Evidência |
|---|---:|---|
| hydra | 134/134 | `ev_47d85b80d597eced56f765c0a130f62f0d41b3c3bcf0ecbac33b342ca8c6c55a` |
| kali-live-build | 56/56 | `ev_adb12879b80c63c80899d2a883e8078af5f3e01b2abcd40c68a29002acca8b89` |
| kali-meta | 13/13 | `ev_f0c68af450c46f4f5c66938fad8be4e59b5e985bcff20b5b491f4d65dbddc567` |
| wireshark | 9461/9461 | `ev_460145a8b51d482ea0a3aedb93e5978d2bc4ac9d77e773fdc1c5b114da8bb149` |

Os ZIPs finais contêm os arquivos rastreados sem entradas extras de diretório. Os cinco gitlinks REA permanecem registrados apenas no inventário da fonte. Profundidade 0 não analisa arquivos compactados aninhados.
`research/evidence/craft-*.json.gz` preserva os resultados integrais e `craft-summary.json` os limites de cobertura.

## O que não foi executado

`craft-anything-cli rebuild`, decompilação REA de binários nativos, Ghidra/Hopper/IDA, automação de navegador, compilação dos produtos originais, Hydra e captura de tráfego.
Nenhuma chave de provedor de IA foi exigida. O fluxo futuro de reconstrução depende da instalação e autenticação de um agente compatível e da definição do produto a reconstruir.

Para repetir esta pesquisa, recupere os snapshots fixados, instale as versões indicadas das ferramentas em um diretório de trabalho e consulte `--help` dessas versões.
Guarde um novo resultado em arquivo distinto: horários e caminhos podem mudar; compare hashes de entrada, versão, parâmetros e conteúdo normalizado antes de afirmar equivalência.
