# Atlas — Evidence & Build Studio / FERRAMENTA-HACKER

Projeto de duedubackes-web, sem vínculo com Kali, Wireshark, THC, REA ou Craft Anything.

Repositório: https://github.com/duedubackes-web/FERRAMENTA-HACKER

Base preparada a partir de fontes públicas para estudar composição de ferramentas,
análise de tráfego e arquitetura de módulos, e projetar um produto próprio com evidências rastreáveis.
Este repositório contém pesquisa, inventários verificáveis e uma ferramenta offline para importar relatórios Nmap/Trivy/ZAP, comparar observações e gerar uma fila de revisão explicável em JSON e HTML.
Não contém uma distribuição nova, um substituto do Wireshark ou uma implementação nova do Hydra.

## Abrir o aplicativo com chatbot

```sh
python scripts/app_server.py
```

Versão **0.1.1**. Use o botão **✓ Verificar workspace** ou `python scripts/app_server.py --check` para conferir arquivos, banco e modelo opcional.

Abra **http://127.0.0.1:8765** e selecione **Explorar demonstração**. Requer Python 3.11+; o aplicativo local padrão não precisa de chave de API ou instalação de ferramentas externas.

- Projetos persistentes em SQLite, importação Nmap/Trivy/ZAP e revisão com referências.
- Chat local sobre evidências, tecnologias e planos; IA generativa opcional via Ollama local.
- Decisões com justificativa e histórico, conferência de reprodução e exportação ZIP.
- Estúdio de código-fonte ZIP: mapa estático, plano de produto, backlog e protótipo próprio com quadro de tarefas e chat local.

[Guia do aplicativo](docs/APLICATIVO-ATLAS.md): instalação, uso, configuração do modelo, backup, exportação e limites. Esta é a versão **local para um usuário**. REA/Craft/Kali estão documentados como pesquisa; os adaptadores funcionais não embutem seus motores. O protótipo é gerado por template próprio, e a novidade comercial permanece hipótese a validar.

## Usar a ferramenta de revisão

```sh
mkdir -p work
python scripts/workbench.py review --before tests/fixtures/nmap-synthetic.xml --after tests/fixtures/nmap-synthetic-after.xml --trivy tests/fixtures/trivy-synthetic.json --zap tests/fixtures/zap-synthetic.json --output work/review.json --html work/review.html
```

Abra o HTML gerado para ver prioridades de revisão, motivos, próximas verificações e fontes. O exemplo usa somente dados sintéticos; para relatórios próprios, substitua os caminhos.
A inteligência desta versão usa regras versionadas e explicáveis. A prioridade de revisão é distinta da severidade declarada pelo produtor; não há associação automática entre IP e pacote nem execução de sugestões.
Detalhes em `docs/REVISAO-INTELIGENTE.md` e demonstração pronta em `examples/review-plan.html`.

## Começar

Requer Python 3.11+ e Git para recuperar as fontes. A CLI e a verificação não precisam de dependências externas nem de rede.

```sh
python scripts/workbench.py verify
python scripts/workbench.py summary
python scripts/workbench.py sources
python scripts/workbench.py catalog --query gemini
python scripts/workbench.py catalog --query "red team"
python scripts/workbench.py packages --query nmap
python scripts/workbench.py find wireshark epan/epan.c
python scripts/workbench.py import-nmap tests/fixtures/nmap-synthetic.xml
python scripts/workbench.py compare-nmap tests/fixtures/nmap-synthetic.xml tests/fixtures/nmap-synthetic-after.xml
python -m unittest discover -s tests -v
```

## O que foi extraído

- Árvores Git rastreadas de dezenove repositórios, fixadas por commit em `sources.lock.json`.
- Inventários de arquivos, tamanho, modo e SHA-256 em `research/inventories/`.
- Evidências seletivas com trecho, arquivo, linha e URL fixada em `research/findings.json`.
- Inventários reais pelo Craft Anything de Kali, Wireshark, Hydra, Nmap, sqlmap, John the Ripper e as novas fontes descritas no catálogo; a cobertura de arquivos internos é detalhada por rodada.
- Evidências reais REA dos scripts públicos recebidos dos sites Wireshark, Nmap e sqlmap e da inspeção do ZIP de fontes do John, com proveniência e limites de cobertura.
- Textos de licença preservados em `third_party/notices/`.

Os dezenove snapshots de fontes foram gerados separadamente em `/workspace/output/source-snapshots/` no ambiente de trabalho. O GitHub recebe o lock e os inventários; as fontes podem ser recuperadas pelo script abaixo.
Não adicione esses ZIPs ao Git: Wireshark e REA tornam o histórico pesado.
O inventário cobre arquivos rastreados no commit, não histórico, submódulos recursivos, conteúdo externo ou todos os pacotes Kali.
O material foi indexado integralmente nesse recorte; a revisão semântica foi seletiva.

## Documentos

- `docs/RELATORIO.md`: primeira rodada, evidências e limites.
- `docs/NMAP-SQLMAP.md`: expansão Nmap/sqlmap, resultados e decisões.
- `docs/IMPORTAR-NMAP.md`: usar a importação offline e entender seu contrato.
- `docs/IMPORTAR-ZAP.md`: importação web, confiança/risco, omissão de mensagens e regras v2.
- `docs/REVISAO-INTELIGENTE.md`: novo fluxo Nmap/Trivy, regras explicáveis, contrato e limites.
- `docs/CATALOGO-FERRAMENTAS.md`: 38 projetos, categorias, estados de evidência e 409 candidatos de pacotes Kali.
- `docs/GEMINI.md`: observação pública do app e fontes abertas relacionadas, com limites explícitos.
- `docs/JOHN-THE-RIPPER.md`: coleta, arquitetura, catálogo estático e corroboração de inventários.
- `docs/COMPARAR-NMAP.md`: comparar observações, entender lacunas e gerar relatórios HTML.
- `examples/nmap-comparison.html`: demonstração pronta com dados sintéticos.
- `docs/ARQUITETURA.md`: composição atual e proposta de produto.
- `docs/PRODUTO.md`: hipótese, MVP, critérios e diferenciação a validar.
- `docs/FERRAMENTAS.md`: aplicação efetiva de REA e Craft Anything.
- `docs/ROADMAP.md`: tarefas de implementação e validação pendentes.
- `docs/LICENCAS.md`: obrigações e decisões antes de incorporar código.
- `docs/CRIAR_REPOSITORIO.md`: publicação da base em um repositório vazio.

## Recuperar fontes

```sh
python scripts/fetch_sources.py --destination work/upstream
```

Faz fetch somente dos commits fixados e checkout local; não instala dependências nem executa software dos projetos.
Não modifica o lock. Para examinar os ZIPs originais, confira o SHA-256 registrado no lock antes de extrair.
Instalações de ferramentas e comandos executados nesta pesquisa estão documentados; não são pré-requisitos desta base.

## Estado

Pesquisa estática ampliada, importação Nmap XML/Trivy JSON/ZAP Traditional JSON, comparação e fila de revisão explicável em JSON/HTML disponíveis. O corpus atual tem 59.740 entradas rastreadas em dezenove repositórios. Engenharia reversa dinâmica,
decompilação nativa, revisão completa dos pacotes Kali, testes dos produtos originais e evolução do produto final são trabalho futuro.
Nenhum teste de intrusão, tentativa de autenticação ou captura de rede de terceiros foi realizado.

Código original desta base: MIT, conforme `LICENSE` já escolhido pelo proprietário. Material de terceiros mantém suas próprias licenças; consulte `docs/LICENCAS.md`.


## Pesquisa John the Ripper

A fonte `openwall/john` foi fixada por commit na variante `bleeding-jumbo`. Consulte `research/john-format-declarations.json` para declarações textuais com linha e origem; isso não é um catálogo de capacidades testadas.
Para consultar caminhos sem recuperar as fontes:

```sh
python scripts/workbench.py find john formats
```

Para conferir ZIPs já coletados, sem extrair nem executar conteúdo:

```sh
python scripts/verify_snapshots.py /caminho/para/source-snapshots --source john
```

O novo verificador também funciona com as demais fontes do lock. O detalhe das execuções reais de REA/Craft e a diferença entre arquivo, link simbólico e capacidade de runtime estão em `docs/JOHN-THE-RIPPER.md`.


## Catálogo ampliado e Gemini

A busca offline reúne 38 projetos por categoria, com metadados, estado da coleta, avisos de licença e proveniência. O índice Kali cobre 409 candidatos diretamente declarados em 29 perfis de ferramentas; não é uma relação de pacotes instalados ou dependências transitivas.
A pesquisa Gemini mantém separados o app hospedado, o Gemini CLI e o SDK Google Gen AI. Foram analisados estaticamente dois scripts iniciais públicos; o backend e os modelos não foram obtidos.
Os bundles proprietários e o HTML bruto do app não são republicados no Git; a observação original, hashes, URLs e limitações estão em `research/gemini-public-observation.json`.
Os dois projetos abertos relacionados têm snapshots e licenças próprios, sem implicar direitos sobre o serviço web.

Os catálogos derivados podem ser regenerados offline com `python scripts/build_tool_catalog.py`. Isso não atualiza metadados pela internet nem executa ferramentas.


## Alertas web integrados

`import-zap` lê campos selecionados de Traditional JSON/JSON Plus e `review --zap` incorpora esses alertas à fila. Risco e confiança do produtor ficam separados; falsos positivos permanecem visíveis em contexto.
Mensagens HTTP, payloads e conteúdo de diagnósticos não são exportados. URIs selecionadas omitem userinfo, query e fragmento; isso não é anonimização completa.
Os contratos foram estudados em referências oficiais fixadas por commit e validados com saídas esperadas, sem executar ZAP. Veja `research/zap-format-validation.json`.

### Conferir uma revisão recebida

O novo `replay-review` reconstrói a fila a partir de fontes locais explícitas e detecta diferenças nas fontes ou no conteúdo da revisão. Permite mover os arquivos sem confiar nos caminhos embutidos. Veja [reprodução verificável](docs/REPRODUZIR-REVISAO.md), incluindo estados, códigos de saída e limites de confiança.
