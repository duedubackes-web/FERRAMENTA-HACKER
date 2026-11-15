# Reprodução verificável de uma revisão

`replay-review` reconstrói a fila usando os relatórios locais indicados explicitamente e as regras instaladas. Detecta alterações nos bytes das fontes e divergências no conteúdo completo da revisão: prioridades, fatos, referências, justificativas, identificadores, resumos e campos adicionais.

Exemplo completo e reproduzível, a partir da raiz do projeto:

```sh
mkdir -p work
python scripts/workbench.py review \
  --before tests/fixtures/nmap-synthetic.xml \
  --after tests/fixtures/nmap-synthetic-after.xml \
  --trivy tests/fixtures/trivy-synthetic.json \
  --zap tests/fixtures/zap-synthetic.json \
  --output work/review.json
python scripts/workbench.py replay-review work/review.json \
  --source nmap-before=tests/fixtures/nmap-synthetic.xml \
  --source nmap-after=tests/fixtures/nmap-synthetic-after.xml \
  --source trivy=tests/fixtures/trivy-synthetic.json \
  --source zap=tests/fixtures/zap-synthetic.json \
  --output work/replay.json
```

Forneça exatamente os papéis declarados em `inputs` da revisão. Revisões somente Trivy ou ZAP precisam apenas daquela fonte. Caminhos podem conter espaços se o argumento inteiro `ROLE=PATH` estiver entre aspas.

## Resultados

| Estado | Significado | Código de saída |
|---|---|---|
| `matched` | Fontes coincidem e a revisão foi reproduzida integralmente, exceto localização dos arquivos | 0 |
| `source-mismatch` | Ao menos um SHA-256 difere; não foi concluída a comparação da revisão | 1 |
| `review-mismatch` | Fontes coincidem, mas há seções diferentes da reconstrução | 1 |
| Erro de entrada | Formato inválido, fonte inacessível, papéis incorretos ou regras indisponíveis | 2 |

O resultado informa hashes esperados/observados por papel e nomes das seções divergentes. Não copia os conteúdos divergentes. Arquivos de saída existentes são preservados.

A leitura de cada fonte tem limite de 32 MiB e usa os mesmos adaptadores offline do comando `review`. Uma fonte com hash divergente não é interpretada. A leitura da revisão rejeita chaves JSON duplicadas e constantes não padronizadas.

Somente `inputs.*.artifact.path` é ignorado na comparação, para permitir mover arquivos. Todos os outros campos são comparados. Nenhum caminho embutido no documento é aberto; os arquivos são fornecidos por `--source`. Nenhum conteúdo coletado, sugestão ou motor é executado.

A versão e o hash do conjunto de regras precisam coincidir com os instalados. Uma revisão histórica de outras regras exige o ambiente correspondente; este comando não migra revisões nem baixa código automaticamente. Divergências por versões de adaptadores/comparador aparecem na reconstrução e não são prova isolada de adulteração.

## Limites de confiança

Reprodução comprova consistência com os bytes fornecidos e o código instalado. Não autentica quem produziu os relatórios, não impede que alguém altere fontes e revisão em conjunto e não substitui assinatura ou preservação independente das fontes. Não atesta revisão humana, eficácia de priorização ou segurança dos sistemas.

Testes próprios cobrem os três produtores juntos, movimentação de arquivos, caminhos embutidos não confiáveis, fontes alteradas, alterações de conteúdo, filas vazias, regras indisponíveis, leitura limitada e códigos de saída da CLI.
