# FERRAMENTA-HACKER — base de pesquisa e desenvolvimento

Projeto de duedubackes-web, sem vínculo com Kali, Wireshark, THC, REA ou Craft Anything.

Repositório: https://github.com/duedubackes-web/FERRAMENTA-HACKER

Base preparada a partir de fontes públicas para estudar composição de ferramentas,
análise de tráfego e arquitetura de módulos, e projetar um produto próprio com evidências rastreáveis.
Este repositório contém pesquisa, inventário reproduzível e uma CLI offline de consulta.
Não contém uma distribuição nova, um substituto do Wireshark ou uma implementação nova do Hydra.

## Começar

Requer Python 3.11+ e Git para recuperar as fontes. A CLI e a verificação não precisam de dependências externas nem de rede.

```sh
python scripts/workbench.py verify
python scripts/workbench.py summary
python scripts/workbench.py sources
python scripts/workbench.py find wireshark epan/epan.c
python -m unittest discover -s tests -v
```

## O que foi extraído

- Árvores Git rastreadas de seis repositórios, fixadas por commit em `sources.lock.json`.
- Inventários de arquivos, tamanho, modo e SHA-256 em `research/inventories/`.
- Evidências seletivas com trecho, arquivo, linha e URL fixada em `research/findings.json`.
- Inventário real pelo Craft Anything dos quatro repositórios de produto/composição.
- Evidência real REA dos scripts inline recebidos do site Wireshark, com HTML e proveniência.
- Textos de licença preservados em `third_party/notices/`.

Os seis snapshots de fontes foram gerados separadamente em `/workspace/output/source-snapshots/` no ambiente de trabalho. O GitHub recebe o lock e os inventários; as fontes podem ser recuperadas pelo script abaixo.
Não adicione esses ZIPs ao Git: Wireshark e REA tornam o histórico pesado.
O inventário cobre arquivos rastreados no commit, não histórico, submódulos recursivos, conteúdo externo ou todos os pacotes Kali.
O material foi indexado integralmente nesse recorte; a revisão semântica foi seletiva.

## Documentos

- `docs/RELATORIO.md`: resultados, evidências e limites.
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

Pesquisa estática inicial e preparação de repositório concluídas. Engenharia reversa dinâmica,
decompilação nativa, revisão completa dos pacotes Kali, testes dos produtos originais e novo produto são trabalho futuro.
Nenhum teste de intrusão, tentativa de autenticação ou captura de rede de terceiros foi realizado.

Código original desta base: MIT, conforme `LICENSE` já escolhido pelo proprietário. Material de terceiros mantém suas próprias licenças; consulte `docs/LICENCAS.md`.
