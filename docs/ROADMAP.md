# Roadmap e backlog

## Entrega atual

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
- [ ] P03: normalizar e comparar relatórios; preservar campos desconhecidos e cobertura.
- [ ] P04: exportar JSON e relatório HTML com proveniência navegável.
- [ ] P05: verificar corpus sintético ponta a ponta e medir tarefas completas.
- [ ] P06: conduzir entrevistas e decidir continuidade pelo resultado observado.

## Antes de distribuir um produto

- [ ] Definir modelo de integração e revisar licença por arquivo e dependência.
- [x] Preservar a licença MIT e titularidade já declaradas no repositório do proprietário; material terceiro mantém as próprias licenças.
- [ ] Revisar nome e marcas; criar identidade visual original.
- [ ] Definir política de atualização e verificar versões e avisos de segurança reais.

Use `.github/ISSUE_TEMPLATE/work-item.yml` para converter cada item em uma tarefa com fonte, resultado esperado e validação.
