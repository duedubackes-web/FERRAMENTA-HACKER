# Validação realizada

- Cinco testes locais passaram: alteração/ausência de arquivo, caminho com travessia, manifesto vazio, ID de fonte inválido e contagem/identidade única dos inventários.
- Verificação SHA-256 passou para todos os arquivos listados em ARTIFACTS.sha256 na árvore final.
- Os seis ZIPs tiveram checksums conferidos contra o lock e cada arquivo foi comparado ao inventário por SHA-256; research/snapshot-verification.json registra as contagens.
- Os cinco gitlinks de REA estão registrados, sem conteúdo de submódulo baixado.
- Os ZIPs preservam os bytes dos arquivos rastreados, sem omissões export-ignore ou substituições export-subst; links simbólicos preservam o texto de destino.
- Craft reportou cobertura completa do inventário de cada ZIP nos parâmetros registrados. Arquivos compactados internos não foram abertos.
- REA analisou 11 scripts inline, com zero falhas de parse reportadas. Isso não comprova execução ou análise da aplicação nativa.
- Nenhuma suíte dos projetos originais foi executada. A configuração de CI da base é entregue; seu estado no GitHub deve ser verificado após publicar o commit.


## Continuação Nmap/sqlmap

- Os dois ZIPs novos tiveram seus checksums e cada entrada conferidos contra os inventários; o registro passa a abranger oito fontes.
- Doze testes da base, incluindo o fluxo CLI de importação e recusa de sobrescrita, foram executados localmente com sucesso.
- Foram lidos 19 fixtures XML públicos do Nmap: 16 importados, dois rejeitados por ISO-8859-1 e um por XML malformado. O relatório por arquivo está em `research/nmap-fixture-validation.json`.
- Craft declarou inventário completo após ampliar a profundidade: Nmap 2.631 entradas, sqlmap 899. As entradas extras são membros de arquivos internos.
- REA analisou dois scripts públicos de cada site sem falhas de parse reportadas; nenhum motor foi executado.
- Resultados históricos acima referem-se à primeira rodada; a CI do novo commit será verificada separadamente após publicação.


## Comparação de observações e relatório

- 27 testes da base passaram, incluindo comparação por IP, duplicidade, IPv6, cobertura, ausência de estado, versões de adaptadores, escapes de dados e o fluxo CLI com dois arquivos de saída.
- O HTML sintético foi renderizado em Chromium a 1.365×980 e 375×812, sem transbordamento da página; detalhes e links de proveniência funcionaram, com zero requisições de rede.
- A navegação por URL file: foi bloqueada pela política do navegador do ambiente. O QA de conteúdo/layout usou Playwright setContent, sem alterar políticas do navegador; não é uma comprovação de abertura por arquivo em todos os ambientes.
- O registro desta verificação está em research/comparison-browser-check.json. O exemplo pronto está em examples/nmap-comparison.html e usa somente dados sintéticos.
- Não houve execução de scanner, novos testes dos motores originais ou coleta de rede nesta etapa.


## Coleta John e ferramentas de pesquisa

- 33 testes da base passaram, incluindo seis novos casos para catálogo lexical e verificação de snapshots.
- O novo verificador conferiu os nove ZIPs, seus conjuntos de membros e hashes por entrada, sem extrair ou executar conteúdo. Resultados em `research/snapshot-verification.json`.
- Os 2.128 caminhos John coincidiram entre o inventário próprio, Craft e REA. Os hashes do Craft coincidiram para todas as entradas; REA conferiu 2.126 arquivos regulares e não atribuiu hashes aos dois links simbólicos.
- Catálogo do fonte: 380 arquivos com correspondências, 404 definições textuais de estruturas e 366 definições de labels literais; sem avaliação de pré-processador ou suporte real de builds.
- A revisão semântica foi seletiva. John não foi compilado ou executado, e não foram realizados benchmarks ou tentativas de quebra de senhas.


## Catálogo ampliado e Gemini

- 39 testes locais passaram, incluindo filtros por categoria/acentos/aliases, referências reais ao lock e preservação de alternativas e restrições dos pacotes Kali.
- As consultas CLI `catalog --query gemini`, `catalog --query "red team"` e `packages --query nmap` retornaram respectivamente 3, 2 e 2 registros no recorte atual.
- O verificador conferiu os 19 ZIPs locais e seus arquivos rastreados; 45 gitlinks não baixados permanecem explícitos. O total é 59.740 entradas, com 59.695 entradas de arquivo verificadas nos ZIPs.
- Craft/REA corroboraram caminhos raiz e todos os hashes disponíveis das oito novas árvores de segurança. Trivy manteve cobertura parcial de conteúdo aninhado; entradas sem hash no REA não foram tratadas como verificadas.
- No Gemini público: HTTP 200 sem autenticação, dois scripts iniciais inventariados e analisados como texto; alias expansion e grafo estático com lacunas explícitas.
- Os testes são da base própria. Nenhum teste dos novos motores de pentest, agente Gemini, chamada de modelo ou operação de intrusão foi executado.


## Importação Trivy e revisão explicável

- 54 testes da base passaram, incluindo 15 novos casos do importador e da fila de revisão.
- Foram exercitados formatos inválidos, chaves duplicadas, orçamento de entrada, severidade desconhecida, omissão de conteúdo de Secrets, referências, IDs e execução ponta a ponta do CLI.
- A leitura de 92 saídas públicas esperadas Trivy importou 83 JSONs nativos e recusou nove formatos fora do contrato: sete CycloneDX e dois SPDX. Não houve execução do Trivy.
- O HTML sintético foi conferido em Chromium em 1.365×980 e 375×812: detalhes, navegação de fontes, ausência de transbordamento e zero requisições de rede. QA por setContent, sujeito à restrição de file: já registrada no ambiente.
- O exemplo contém seis sugestões de revisão derivadas de dados sintéticos. Não é uma medição de risco ou comprovação de eficácia em sistemas reais.
