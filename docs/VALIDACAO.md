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
