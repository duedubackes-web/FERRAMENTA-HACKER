# Validação realizada

- Cinco testes locais passaram: alteração/ausência de arquivo, caminho com travessia, manifesto vazio, ID de fonte inválido e contagem/identidade única dos inventários.
- Verificação SHA-256 passou para todos os arquivos listados em ARTIFACTS.sha256 na árvore final.
- Os seis ZIPs tiveram checksums conferidos contra o lock e cada arquivo foi comparado ao inventário por SHA-256; research/snapshot-verification.json registra as contagens.
- Os cinco gitlinks de REA estão registrados, sem conteúdo de submódulo baixado.
- Os ZIPs preservam os bytes dos arquivos rastreados, sem omissões export-ignore ou substituições export-subst; links simbólicos preservam o texto de destino.
- Craft reportou cobertura completa do inventário de cada ZIP nos parâmetros registrados. Arquivos compactados internos não foram abertos.
- REA analisou 11 scripts inline, com zero falhas de parse reportadas. Isso não comprova execução ou análise da aplicação nativa.
- Nenhuma suíte dos projetos originais foi executada. A configuração de CI da base é entregue; seu estado no GitHub deve ser verificado após publicar o commit.
