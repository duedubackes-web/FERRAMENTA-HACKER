# Nmap e sqlmap: expansão da pesquisa e implementação

## Resultado e cobertura

Foram adicionados dois repositórios oficiais ao corpus, com origem, commit, ZIP e SHA-256 fixados.
São 2.611 entradas Nmap e 896 sqlmap: 3.507 entradas novas e 22.867 no total dos oito repositórios.
O conteúdo dos ZIPs foi comparado arquivo por arquivo aos inventários. Histórico completo, dependências transitivas instaladas e revisão semântica de cada linha não fazem parte dessa contagem.

Os motores Nmap e sqlmap não foram executados contra os sites ou qualquer outro sistema. Os sites foram usados como fontes públicas de documentação e scripts entregues ao visitante.

## Evidências seletivas

- **N01** Nmap declara NPSL 0.95; não é uma licença MIT nem GPLv2 padrão. [Arquivo e linha](https://github.com/nmap/nmap/blob/68739db8e4ec139c3865a33073c76c6fd13fb96c/LICENSE#L1).

- **N02** A entrada principal do núcleo nativo está em nmap_main. [Arquivo e linha](https://github.com/nmap/nmap/blob/68739db8e4ec139c3865a33073c76c6fd13fb96c/nmap.cc#L1862).

- **N03** O motor de varredura tem uma interface ultra_scan independente das rotinas de serialização de saída. [Arquivo e linha](https://github.com/nmap/nmap/blob/68739db8e4ec139c3865a33073c76c6fd13fb96c/scan_engine.cc#L2735).

- **N04** A serialização XML expõe metadados de cobertura em scaninfo. [Arquivo e linha](https://github.com/nmap/nmap/blob/68739db8e4ec139c3865a33073c76c6fd13fb96c/output.cc#L1207).

- **N05** Há um contrato documentado para o XML de saída; o importador próprio lê um subconjunto sem carregar DTDs. [Arquivo e linha](https://github.com/nmap/nmap/blob/68739db8e4ec139c3865a33073c76c6fd13fb96c/docs/nmap.dtd#L3).

- **N06** A licença discute resultados fornecidos pelo usuário e práticas que podem não exigir direitos concedidos pela licença; não é uma autorização genérica para redistribuir o motor. [Arquivo e linha](https://github.com/nmap/nmap/blob/68739db8e4ec139c3865a33073c76c6fd13fb96c/LICENSE#L158).

- **S01** O ponto de entrada Python inicializa ambiente e opções antes de encaminhar o trabalho ao controlador. [Arquivo e linha](https://github.com/sqlmapproject/sqlmap/blob/8b78b676c1376ae28feccd957b03bbecea05eff1/sqlmap.py#L175).

- **S02** A configuração é compartilhada em um objeto conf. [Arquivo e linha](https://github.com/sqlmapproject/sqlmap/blob/8b78b676c1376ae28feccd957b03bbecea05eff1/lib/core/data.py#L22).

- **S03** O estado de resultados é compartilhado em kb; isto orienta o estudo de contratos de sessão, não demonstra um defeito. [Arquivo e linha](https://github.com/sqlmapproject/sqlmap/blob/8b78b676c1376ae28feccd957b03bbecea05eff1/lib/core/data.py#L25).

- **S04** O entrypoint importa start do controlador para despachar o fluxo. [Arquivo e linha](https://github.com/sqlmapproject/sqlmap/blob/8b78b676c1376ae28feccd957b03bbecea05eff1/sqlmap.py#L235).

- **S05** sqlmap declara GPLv2-ou-posterior com esclarecimentos e exceções próprias. [Arquivo e linha](https://github.com/sqlmapproject/sqlmap/blob/8b78b676c1376ae28feccd957b03bbecea05eff1/LICENSE#L8).

- **S06** A licença inclui execução com interpretação de resultados entre seus exemplos de obra derivada; integração comercial precisa considerar esse texto. [Arquivo e linha](https://github.com/sqlmapproject/sqlmap/blob/8b78b676c1376ae28feccd957b03bbecea05eff1/LICENSE#L21).

## Aplicação real de Craft Anything

A CLI 0.6.1 foi executada em modo Deep, operação `core-archive-show`, nos ZIPs de fonte fixados.
Na primeira chamada, `max_depth=0` inventariou todos os arquivos externos, mas reportou cobertura parcial: um arquivo DOCX no Nmap e três arquivos ZIP de dados no sqlmap não foram abertos.
A segunda chamada usou `max_depth=1`, mantendo `max_entries=20000`, `limit=20000` e `max_total_bytes=1000000000`.
Ela reportou cobertura completa do inventário: Nmap 2.631/2.631 entradas e sqlmap 899/899, contando os membros internos desses arquivos.
Os dois resultados, parcial e expandido, foram preservados em `research/evidence/craft-nmap*.json.gz` e `craft-sqlmap*.json.gz`.
Isso é inventário e leitura estática, não reconstrução funcional, análise integral de binários ou prova de equivalência.

## Aplicação real de REA

Foi reutilizada a CLI REA 6.9.0, com `analyze-javascript-application` sobre os scripts públicos retidos de cada página.
Nmap: dois arquivos e 2.612 bytes; sqlmap: dois arquivos e 3.970 bytes. Não houve falha de parse reportada.
São fatos sobre os scripts dos sites, não sobre o funcionamento dos motores de varredura ou injeção.
O resultado reporta zero findings no Nmap e uma no sqlmap; essas contagens não significam ausência ou presença de vulnerabilidades.
`research/web/*-script-provenance.json` registra a extração de texto inline e a coleta de scripts públicos do mesmo domínio. Scripts de outras origens não foram buscados.
As evidências completas e sínteses estão em `research/evidence/rea-nmap-*` e `rea-sqlmap-*`.
O guia REA recomenda ferramentas normais para arquitetura de repositório quando o fonte já está disponível; por isso o ledger do núcleo vem de leitura estática comum.

## O que foi construído

Uma capacidade original da base: importar XML local do Nmap e produzir JSON versionado com hash do artefato, identidade do adaptador, hosts, endereços, portas, estados, serviços e cobertura declarada.
Não interpreta uma porta ausente como fechada; preserva confiança e método declarados pelo produtor e alerta quando não há registro de conclusão.
Resultados de scripts, fingerprint de SO e outros campos não são interpretados; a limitação e a contagem de scripts omitidos acompanham a saída.
Não executa Nmap, sqlmap, scripts importados ou requisições de rede.

## Verificação e limites

O fluxo CLI foi testado com um XML sintético original usando endereços de documentação. Foram exercitados hash, estados, campos desconhecidos, entrada inválida, orçamento de tamanho e recusa de sobrescrita.
Também foram lidos 19 XMLs públicos de teste do upstream Nmap, sem executar seu código: 16 importados; dois rejeitados por declararem ISO-8859-1 e um rejeitado por XML malformado.
Esses resultados estão em `research/nmap-fixture-validation.json`; não comprovam compatibilidade com todo XML produzido por versões atuais ou históricas.
O adaptador aceita UTF-8/US-ASCII, no máximo 32 MiB, e o DOCTYPE simples do Nmap. DTDs externas/internas e entidades customizadas são recusadas.

## Decisões para o produto

- Priorizar ingestão, proveniência e comparação de artefatos, em vez de incorporar motores nesta iteração.
- Preservar a MIT do código original da base e os termos específicos das fontes de pesquisa.
- Nmap declara NPSL 0.95. O texto distingue redistribuição/incorporação de certas práticas de leitura de resultados fornecidos pelo usuário; não presumir autorização geral para empacotar o motor.
- sqlmap declara GPLv2-ou-posterior com esclarecimentos próprios, incluindo execução e interpretação de resultados entre exemplos de derivação. Esta entrega não executa nem implementa um adaptador sqlmap.
- Oportunidade a validar: correlacionar resultados de inventário de ativos com evidências de tráfego offline e rastrear mudanças entre execuções. Ainda não houve estudo de mercado ou comprovação de inovação.

## Pendências

Análise dinâmica em laboratório próprio, binários fixados por versão, compatibilidade de formatos adicionais, comparação entre relatórios e o conector TShark continuam no roadmap.
Não há vulnerabilidade confirmada ou atualização dos motores originais nesta entrega.
