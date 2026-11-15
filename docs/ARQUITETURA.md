# Arquitetura: observações e proposta

## Modelos observados

Kali é uma camada de composição: metapacotes selecionam conjuntos de ferramentas e receitas live-build constroem imagens.
Wireshark separa aquisição (dumpcap), leitura de formatos (wiretap), dissecação (epan), interface gráfica (ui/qt) e CLI (tshark).
A análise de chamadas registrada liga TShark a EPAN; as demais camadas são um mapa orientado pelas fontes e ainda precisam de rastreamento completo.
Hydra tem um núcleo C que registra serviços e mantém retomada; a inspeção desta entrega não percorreu todos os módulos.
Os identificadores K01–H03 do ledger sustentam o recorte observado.

## Produto proposto: laboratório de evidências offline

Oportunidade hipotética: reunir proveniência, comparação de sessões e relatórios reproduzíveis numa experiência em português.
Começar com arquivos e capturas já existentes, com conectores opcionais e contratos explícitos.

```mermaid
flowchart LR
  A[Arquivos locais e capturas sintéticas] --> B[Importação e hash]
  B --> C[Inventário versionado]
  C --> D[Adaptadores isolados]
  D --> E[Normalização de evidências]
  E --> F[Comparação entre execuções]
  E --> G[Relatório e exportação]
  G --> H[CLI e futura interface]
```

O diagrama é uma proposta; consulta dos inventários, verificação dos artefatos, importação/comparação offline Nmap XML e exportação JSON/HTML estão implementadas nesta etapa.

## Contratos propostos

- Artifact: identificador, SHA-256, tamanho, formato e proveniência.
- AnalysisRun: ferramenta, versão, parâmetros, entradas, saídas, horários e estado.
- Finding: observação/inferência/hipótese, evidências, cobertura e perguntas abertas.
- Adapter: aceitar artefato local; produzir JSON validado; declarar dependências e efeitos.

## Decisões iniciais

- ADR-001: preservar fonte upstream separadamente; não misturar código copyleft em um núcleo próprio MIT.
- ADR-002: primeiro produto focado em análise offline; não construir uma distribuição Linux no MVP.
- ADR-003: resultados devem distinguir observação, derivação e hipótese; sem pontuações de confiança inventadas.
- ADR-004: primeiro conector de tráfego será um processo separado TShark; a fronteira de processo não decide sozinha as obrigações de licença.
- ADR-005: Hydra é referência de arquitetura nesta fase. Não há executor de autenticação ou credenciais no núcleo inicial.

As decisões são opções de projeto, não requisitos extraídos nem validação de vantagem competitiva.


## Adaptador offline implementado

`workbench.py import-nmap` recebe um arquivo local, chama `nmap_report.import_report` e retorna um JSON v1 ou cria um novo arquivo de saída.
O adaptador lê até 32 MiB, recusa construções XML não suportadas, calcula SHA-256, preserva campos selecionados e explicita cobertura e omissões.
A identidade da análise depende do hash e da versão do adaptador; não representa uma nova execução do Nmap.
Nmap e sqlmap continuam como referências externas; nenhum motor é empacotado ou chamado pelo adaptador.
Os detalhes observados das novas fontes e as escolhas de projeto estão separados em `NMAP-SQLMAP.md`.


## Comparação e relatório implementados

`compare-nmap` importa os dois XMLs com `nmap_report`, passa os registros à função pura `nmap_compare.compare_reports` e grava JSON e/ou a projeção `render_html`.
A lógica de pareamento e cobertura pertence ao comparador; o HTML apenas apresenta seu resultado e suas referências.
As correspondências usam IPs canônicos em relação única. Ambiguidades, versões, conclusão e cobertura acompanham as diferenças.
A ausência de um registro não vira um estado inferido; alterações em detecção de serviço não viram confirmação de atualização ou vulnerabilidade.
O identificador considera os hashes e versões de importação/comparação. Caminhos locais não participam da identidade por conteúdo.
A geração HTML não depende de JavaScript ou recursos externos; dados do XML são escapados e os links são internos ao relatório.


## John: referência de contratos e composição

A leitura seletiva do John identificou um contrato de formato versionado (`FMT_MAIN_VERSION`), registro em `formats.c`/`john.c` e persistência em `recovery.c`.
Esses pontos reforçam a separação entre contrato do adaptador, registro de módulos e estado de execução na arquitetura própria.
O catálogo lexical da pesquisa guarda declarações do fonte; um futuro catálogo de capacidades de runtime deverá registrar build, plataforma e evidências de observação separadamente.
Nenhum algoritmo do John, motor de processamento de senhas ou integração de execução foi incorporado nesta etapa. Os detalhes e fontes estão em `JOHN-THE-RIPPER.md`.
