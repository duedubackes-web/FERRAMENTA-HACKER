# Metasploit Framework e Social-Engineer Toolkit: pesquisa e integração

Em 16/11/2026 foram coletadas as árvores Git rastreadas dos dois projetos públicos. O objetivo é estudar arquitetura e contratos para uma implementação própria, preservando a diferença entre fonte observada, inspeção de artefato, proposta e execução real.

## Coleta verificável

| Projeto | Commit | Entradas rastreadas | Arquivos no ZIP | Gitlinks não coletados |
|---|---|---:|---:|---:|
| Metasploit Framework | `bea1fb069e79cb610fe3981f16b8697790369c63` | 15.152 | 15.151 | 1 |
| Social-Engineer Toolkit | `5e0fbb50ca8b156ac93532a0a4d138900c6e0827` | 232 | 232 | 0 |

O gitlink do Metasploit é `external/source/ReflectiveDLLInjection`: seu identificador está registrado, mas seu conteúdo não foi baixado. Histórico Git, submódulos recursivos, dependências externas e hidratação LFS ficam fora do recorte. As árvores originais permaneceram sem modificações.

Os snapshots ficam fora do repositório do Atlas, em `source-snapshots/` da área de entrega. `sources.lock.json` guarda commits, tamanho e SHA-256 de cada ZIP; `research/inventories/` guarda caminho, modo, tamanho, objeto Git e SHA-256 dos arquivos. Nenhum módulo ou binário dos projetos foi incorporado ao aplicativo.

## Aplicação efetiva de REA e Craft Anything

Foram reutilizados REA 6.9.0 e Craft Anything 0.6.1 já instalados. Conforme a skill REA, leitura de arquitetura usa ferramentas comuns sobre os fontes; REA foi aplicado aos ZIPs como artefatos.

- Craft: `--deep core-archive-show`, profundidade 0, até 20.000 entradas, orçamento de 1 GiB, offset 0 e página de 20.000.
- REA: `inspect-artifact CAMINHO_DO_ZIP --artifact-limits '{"expanded_bytes":1073741824}' --format json`.
- O verificador próprio conferiu SHA-256 do ZIP e de cada arquivo contra o inventário.

Os conjuntos de caminhos raiz coincidiram. Craft e REA conferiram os 15.151 hashes disponíveis do Metasploit e os 232 do SET. REA declarou inventário completo de entradas do contêiner; isso não é análise semântica de todo o código. Craft declarou **partial**, pois 29 arquivos compactados internos no Metasploit e três no SET não foram abertos na profundidade escolhida. Seus bytes externos foram conferidos, não o conteúdo interno.

Evidências completas, parâmetros, IDs e limitações:

- `research/evidence/metasploit-set-crosschecks.json`;
- `research/evidence/craft-metasploit-research.json.gz` e `rea-metasploit-research.json.gz`;
- `research/evidence/craft-set-research.json.gz` e `rea-set-research.json.gz`.

## Arquitetura estudada seletivamente

**Metasploit:** o ponto de entrada `msfconsole` delega à camada de comando; o contexto central compõe gerenciadores de módulos, eventos e plugins. `DBExport` declara exportação de workspace com raiz `MetasploitV5`. A leitura desse código não valida automaticamente um adaptador de importação para Atlas, nem comprova comportamento de uma versão instalada.

**SET:** `pyproject.toml` declara versão 8.1.3 e Python >=3.11,<3.14. O console usa helpers em `src/core`, preparando configurações e diretórios. O instalador legado contém instalação de dependências e escrita em caminhos do sistema. Nenhum deles foi importado ou executado durante a análise. Compatibilidade declarada não é teste de runtime.

As sete observações têm commit, caminho, linha, trecho curto e URL fixada em `research/findings.json` (MSF01–MSF03 e SET01–SET04). `research/technology-dossiers.json` organiza as observações e separa propostas de implementação própria.

## O que entrou no produto

A tela **Tecnologias** e o chat agora têm dossiês para ambos. Pergunte:

- **Qual a arquitetura do Metasploit?**
- **Quais fontes e licenças do SET foram estudadas?**
- **Qual a arquitetura do Metasploit e SET?**

Cada referência do chat abre o dossiê com commit, observações e origem. Também pode usar **Abrir dossiê com fontes** na ficha da tecnologia. O catálogo passa a 39 projetos, sendo 20 projetos com fontes indexadas em 21 snapshots, totalizando 75.124 entradas rastreadas. O índice Kali permanece em 409 candidatos diretamente declarados, sem resolução transitiva.

Os motores Metasploit e SET não estão embutidos: não há console operacional, RPC, execução de módulos, produção de payloads, campanhas ou coleta de credenciais. O incremento entrega pesquisa consultável e verificável, não um clone funcional desses motores.

## Aprendizados para desenvolvimento próprio

As propostas incluem manifestos de capacidades que separem contexto de execução; contratos de relatórios locais com minimização de dados; análise de fontes sem importação; e treinamento defensivo com dados sintéticos. São propostas, não comportamentos comprovados do Atlas. A identidade visual, os fluxos e o código futuro devem ser originais, sem alegação de endosso dos projetos estudados.

Os avisos de licença de raiz estão em `third_party/notices/metasploit/` e `third_party/notices/set/readme/LICENSE`. Metasploit contém componentes de terceiros com licenças variadas. A licença SET exige preservar avisos e restringe uso do nome para endosso. Não foi feita revisão completa das obrigações de cada componente para distribuição de motores.

## Reproduzir o recorte

```sh
python scripts/fetch_sources.py --destination work/novas-fontes
python scripts/workbench.py find metasploit lib/msf/core/
python scripts/workbench.py find set pyproject
python scripts/workbench.py catalog --query setoolkit
python scripts/verify_snapshots.py /caminho/source-snapshots --source metasploit
python scripts/verify_snapshots.py /caminho/source-snapshots --source set
python scripts/verify_tool_inventory.py metasploit --craft research/evidence/craft-metasploit-research.json.gz --rea research/evidence/rea-metasploit-research.json.gz
python scripts/verify_tool_inventory.py set --craft research/evidence/craft-set-research.json.gz --rea research/evidence/rea-set-research.json.gz
```

O script de coleta exige destino novo e obtém todos os commits fixados no lock. Não instala dependências nem inicia programas dos projetos. Valide novamente o snapshot e os orçamentos antes de repetir as CLIs de inspeção.
