# Comparar observações e exportar evidências

O comando recebe dois XMLs locais, usa o importador existente e compara os registros selecionados. Não executa Nmap nem realiza conexões de rede.

```sh
mkdir -p work
python scripts/workbench.py compare-nmap tests/fixtures/nmap-synthetic.xml tests/fixtures/nmap-synthetic-after.xml --output work/comparison.json --html work/comparison.html
```

Abra `work/comparison.html` no navegador. JSON e HTML são independentes; sem `--output`, o JSON sai na saída padrão.
Os diretórios de destino precisam existir. Os dois destinos são conferidos antes da gravação, precisam ser distintos e arquivos existentes não são sobrescritos.

Uma demonstração pronta está em `examples/nmap-comparison.html`. Ela usa exclusivamente os dois XMLs sintéticos do repositório, com endereços reservados para documentação e nenhuma coleta de rede.

## O que a comparação explica

| Evidência nos XMLs | Resultado |
|---|---|
| Mesma porta explicitamente fechada antes e aberta depois | Mudança no estado registrado, com as duas referências |
| Porta presente em apenas um relatório | Observação em um só lado; não se afirma abertura ou fechamento |
| Porta ausente, mas coberta por uma contagem agregada `extraports` | Continua sem observação individual; não se atribui o estado agregado a uma porta específica |
| Método, confiança ou descrição de serviço diferentes | Mudança na detecção registrada; não comprova atualização do software |
| Estado ausente, desconhecido ou não reconhecido | Mudança de evidência; não é classificada como transição de estado conhecido |
| IPs que não permitem pareamento único entre hosts | Questão de identidade; não se força correspondência por hostname ou MAC |

O pareamento usa IPs IPv4/IPv6 canônicos compartilhados em uma relação única um-para-um.
DHCP, NAT e reutilização de endereços ainda podem associar registros de equipamentos diferentes: a regra identifica uma correspondência de IP, não identidade física permanente.
Portas repetidas dentro do mesmo host são registradas como ambíguas e excluídas da comparação daquele endpoint.
Para hosts sem correspondência, registra-se a observação de host; não se inventam transições de suas portas.

## Cobertura e interpretação

O campo `comparability.scope_relation` distingue escopos declarados iguais, diferentes e desconhecidos.
Intervalos de portas são normalizados sem expandir listas; protocolo e tipo de varredura também participam da comparação.
Igualdade de `scaninfo` não prova igualdade de opções, privilégios, ponto de observação ou conclusão real da coleta.
Uma porta vista em apenas um lado inclui `other_declared_scope`: `declared`, `not_declared` ou `unknown`, referindo-se à declaração do outro XML.
Avisos de conclusão ausente, saída sem sucesso, versões diferentes e timeout acompanham os resultados.

O resumo conta registros comparados e diferenças. Não é uma pontuação de risco nem uma confirmação de vulnerabilidade.
Nenhuma diferença nos campos examinados não comprova equivalência completa dos sistemas.

## Proveniência e contrato v1

O JSON inclui os hashes e metadados de cada artefato, versões dos adaptadores, cobertura, mudanças, referências e questões abertas.
Cada diferença aponta ao lado `before`/`after`, SHA-256 do XML e índices de host/porta na importação normalizada, começando em zero.
O identificador da comparação depende dos hashes de entrada e das versões do importador e comparador, sem depender do caminho dos arquivos.
Ele identifica uma análise por conteúdo e versão, não uma nova execução do scanner ou um horário de coleta.

O HTML é uma projeção legível do mesmo resultado: resumo, diferenças expansíveis, questões e proveniência.
Todos os valores de entrada são escapados; não há scripts, bibliotecas remotas ou URLs de entrada usadas como links.
O HTML pode ser lido sem servidor. Nesta verificação, a política do Chromium bloqueou URLs `file:`; o teste visual usou o conteúdo HTML diretamente, sem alterar essa política. A abertura por arquivo no ambiente do usuário depende das políticas do navegador dele.

## Validação desta etapa

Casos de teste cobrem mudanças explícitas, ausência de observações, estados desconhecidos, pareamento ambíguo, IPv6, portas duplicadas, escopos diferentes, escapes HTML e o fluxo CLI JSON + HTML.
O relatório foi renderizado em Chromium com larguras de 1.365 e 375 pixels. Abertura dos detalhes e navegação à proveniência passaram, com zero requisições de rede e sem transbordamento horizontal da página; a tabela tem rolagem própria em telas pequenas.
O registro de QA está em `research/comparison-browser-check.json`.

Ainda faltam correlação com PCAP/TShark, comparação de formatos de outros produtores e validação com usuários. Nenhuma vantagem competitiva ou novidade de mercado foi demonstrada por esses testes.
