# Roadmap e backlog

## Primeira entrega

- [x] Coletar árvores públicas dos seis repositórios, fixar commits e preservar licenças.
- [x] Inventariar arquivos rastreados e gerar hashes.
- [x] Rodar REA em scripts públicos recebidos e Craft Anything nos ZIPs de fontes dos quatro alvos de composição/produto.
- [x] Criar ledger seletivo, proposta e CLI offline de pesquisa.
- [x] Preparar instruções para criar e publicar o repositório.

## Próxima iteração: confirmar comportamento

- [ ] Escolher plataforma e versões de release a comparar; commits de desenvolvimento não representam necessariamente versões lançadas.
- [ ] Construir Wireshark/TShark em ambiente separado e registrar versão, dependências e logs.
- [ ] Criar corpus PCAP/PCAPNG sintético e conferir cada resumo com saídas de referência.
- [ ] Aplicar REA aos binários obtidos, escolhendo provedor compatível e registrando hashes e limitações.
- [ ] Traçar um fluxo completo de leitura → dissecação → saída; registrar evidências por chamada.
- [ ] Resolver dependências transitivas dos metapacotes Kali por versão e arquitetura; importar fontes e licenças por pacote.
- [ ] Estudar interface de módulos e retomada do Hydra em laboratório próprio, sem ampliar protocolos ou capacidade de ataques nesta base.

## Implementação do MVP

- [ ] P01: contrato Artifact/AnalysisRun/Finding com validação de entrada e versões.
- [ ] P02: adaptador offline TShark, prazo máximo, saída limitada e erro de dependência ausente.
- [x] P03 (Nmap v1): normalizar e comparar relatórios; preservar campos desconhecidos e cobertura.
- [x] P04 (Nmap v1): exportar JSON e relatório HTML com proveniência navegável.
- [ ] P05: verificar corpus sintético ponta a ponta e medir tarefas completas.
- [ ] P06: conduzir entrevistas e decidir continuidade pelo resultado observado.
- [x] P07 (Nmap/Trivy v1): importar JSON Trivy local e produzir uma fila de revisão explicável, combinando evidências com a comparação Nmap, sem inferir correspondência entre IP e artefato.

## Antes de distribuir um produto

- [ ] Definir modelo de integração e revisar licença por arquivo e dependência.
- [x] Preservar a licença MIT e titularidade já declaradas no repositório do proprietário; material terceiro mantém as próprias licenças.
- [ ] Revisar nome e marcas; criar identidade visual original.
- [ ] Definir política de atualização e verificar versões e avisos de segurança reais.

Use `.github/ISSUE_TEMPLATE/work-item.yml` para converter cada item em uma tarefa com fonte, resultado esperado e validação.


## Expansão Nmap e sqlmap — 15/11/2026

- [x] Coletar as duas fontes oficiais e inventariar 3.507 entradas novas com hashes e licenças.
- [x] Ampliar inventários Craft para os arquivos compactados internos identificados; preservar cobertura e evidências.
- [x] Aplicar REA aos scripts públicos retidos dos dois sites, sem executar os motores.
- [x] Criar importador offline original XML Nmap → JSON v1, com Artifact/AnalysisRun, proveniência e limites.
- [x] Testar o fluxo CLI com XML sintético e comparar a compatibilidade de leitura com 19 fixtures públicas do upstream.
- [ ] Completar P01: contratos formais dos demais adaptadores e Finding; o importador atual cobre apenas seu recorte.
- [x] Comparar dois relatórios importados, distinguindo mudança observada de ausência de cobertura.
- [ ] Correlacionar inventário de ativos e capturas offline depois de implementar o adaptador TShark.
- [ ] Avaliar suporte a codificações legadas e corpus de releases Nmap atuais.
- [ ] Rever modelo de distribuição à luz de NPSL e dos termos próprios do sqlmap antes de incorporar motores.


## Comparação de evidências — 15/11/2026

- [x] Parear hosts por IP canônico em correspondência única, sem forçar identidades ambíguas.
- [x] Comparar estados explícitos e detecção de serviços; preservar desconhecidos e ausências.
- [x] Considerar protocolo, método e intervalos declarados ao explicar diferenças de cobertura.
- [x] Exportar comparação JSON v1 e relatório HTML offline com referências a hashes e índices dos registros.
- [x] Verificar CLI, escapes HTML, recusas de sobrescrita e comportamento responsivo do exemplo sintético.
- [ ] Validar tarefas de investigação com usuários e artefatos sanitizados reais.
- [ ] Implementar conector TShark offline e correlação entre inventário e tráfego, preservando proveniência e limites de identidade.


## John the Ripper — 15/11/2026

- [x] Coletar `openwall/john` em `bleeding-jumbo`, fixar commit e indexar 2.128 entradas rastreadas.
- [x] Executar Craft Anything e REA no snapshot e registrar a lacuna de hashes de dois links simbólicos no REA.
- [x] Conferir caminhos e todos os hashes disponíveis entre ferramentas e inventário próprio.
- [x] Catalogar definições textuais de formatos com linha, hash e URL, sem inferir formatos ativos no runtime.
- [x] Preservar licenças, responsabilidades de arquitetura e decisões de integração.
- [x] Disponibilizar verificador reutilizável de snapshots e testar detecção de alterações e divergências.
- [ ] Comparar uma release core com a variante jumbo e identificar diferenças por componente.
- [ ] Registrar capacidades observadas de builds específicos em laboratório próprio, separadas das declarações estáticas.
- [ ] Definir contrato de importação de resultados agregados/sanitizados de auditoria, com proveniência e minimização dos dados necessários.
- [ ] Medir custo, utilidade e compatibilidade de uma eventual integração após definir escopo, plataforma e modelo de distribuição.


## Catálogo amplo e Google Gemini — 15/11/2026

- [x] Verificar endereços e reter metadados de 29 repositórios adicionais para o diretório de pesquisa; preservar fontes já fixadas.
- [x] Organizar 38 projetos em categorias e distinguir registro de catálogo, fonte indexada e evidência de execução limitada.
- [x] Coletar oito árvores adicionais de segurança e dois projetos abertos relacionados ao Gemini, sem executar os motores.
- [x] Aplicar REA/Craft aos snapshots e aos dois scripts iniciais públicos do app Gemini, preservando cobertura parcial e lacunas.
- [x] Gerar índice de 409 candidatos diretamente declarados em 29 perfis kali-tools-*, sem resolver ou instalar dependências.
- [x] Adicionar busca offline por categoria/aliases e consultas ao índice de pacotes, com testes.
- [x] Separar Gemini web, CLI e SDK; publicar observações e hashes sem republicar bundles proprietários ou bootstrap de sessão.
- [ ] Revisar componentes e dependências dos projetos selecionados antes de qualquer incorporação ou distribuição de motores.
- [x] Implementar primeiro adaptador de vulnerabilidades Trivy JSON v2, mantendo campos selecionados e cobertura explícita.
- [ ] Priorizar formatos adicionais de ZAP e outros produtores e ampliar o contrato de achados.
- [ ] Validar com usuários o valor de busca fundamentada e comparação de evidências; uma interface conversacional permanece proposta, sem integração de modelos.
- [ ] Definir corpus de tarefas e critérios antes de avaliar funcionalidades interativas de assistentes de IA.


## Revisão explicável — 15/11/2026

- [x] Importar Trivy JSON v2 com identidade do artefato, campos do produtor e desconhecidos preservados.
- [x] Criar regras versionadas e fingerprint para ordenar uma fila de verificações, separada da severidade do produtor.
- [x] Integrar comparação Nmap e Trivy sem inferir correlação IP/pacote; preservar ambiguidades e lacunas.
- [x] Exportar JSON e HTML offline com motivo, sugestão e referências por item.
- [x] Testar o fluxo CLI, proteção de saídas, texto inerte, exemplos públicos e layout responsivo.
- [ ] Avaliar com analistas tarefas completas e a utilidade da ordem de revisão sugerida.
- [ ] Definir mapeamento explícito e verificável de ativos antes de qualquer correlação entre diferentes produtores.
- [ ] Ampliar formatos/categorias selecionados mantendo as limitações e minimização de dados necessárias.
