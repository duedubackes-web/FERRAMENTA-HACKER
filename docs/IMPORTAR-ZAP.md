# Importar alertas ZAP e revisar com evidências

Esta etapa adiciona leitura offline dos campos selecionados dos formatos **Traditional JSON** e **Traditional JSON Plus** do add-on oficial de relatórios ZAP. Nenhum scanner ou site citado no arquivo é executado/acessado.

```sh
python scripts/workbench.py import-zap tests/fixtures/zap-synthetic.json
```

Para criar uma revisão somente com esse relatório:

```sh
mkdir -p work
python scripts/workbench.py review --zap tests/fixtures/zap-synthetic.json --output work/zap-review.json --html work/zap-review.html
```

O novo `--zap` também pode ser combinado com `--trivy` e o par Nmap `--before`/`--after`. Os arquivos permanecem fontes distintas; sites, pacotes e IPs não são associados automaticamente.
A demonstração `examples/review-plan.html` usa agora os três produtores com dados sintéticos: oito itens, sendo quatro em “Revisar primeiro”, três em “Revisar depois” e um em “Contexto”.

## Contrato selecionado

Entrada UTF-8, objeto JSON com `@version` não vazio e campos estruturais `site[]`, `alerts[]` e `instances[]` quando presentes. O orçamento é 32 MiB.
Outros formatos, como o JSON da API de alertas, SARIF e XML, não são tratados automaticamente como esse relatório. Campos ausentes, null e arrays vazios são distinguíveis; formas estruturais incompatíveis são recusadas.
Chaves duplicadas e constantes JSON não padronizadas são recusadas pelo leitor compartilhado com o Trivy.

Cada alerta mantém identificadores, nome, risco, confiança, descrição de risco e contagem declarados pelo produtor, além das instâncias selecionadas e referências ao documento original.
`riskcode` conhecido vai de 0 a 3 (Informational, Low, Medium, High); `confidence` conhecido vai de 0 a 4 (False Positive, Low, Medium, High, Confirmed).
Strings numéricas e inteiros conhecidos são aceitos. Valores futuros/desconhecidos são preservados sem classificação adivinhada a partir do texto de `riskdesc`.

## Minimização de dados

O adaptador não exporta payloads `attack`, `evidence`, cabeçalhos/corpos HTTP, descrições/soluções/referências HTML, screenshots ou conteúdo de diagnósticos.
Nas URIs HTTP(S) selecionadas, omite userinfo, query e fragmento. São exibidos esquema, host, porta explícita e caminho. URI relativa, inválida ou de outro esquema não é exportada e gera aviso quando é uma instância.
O nome de site é representado pelo mesmo tratamento de URI; atributos paralelos de host não são usados para reconstruir ou inferir identidade.

Isso **não é anonimização completa**: nomes de alertas, caminhos de URI, metadados do produtor e caminhos locais de arquivos ainda podem conter informações sensíveis. O JSON original deve ser preservado para conferência controlada; escolha onde exportar e compartilhar os derivados.

Seções como `stoppingInsight`, estatísticas, diagnósticos e mensagens de automação mantêm somente estado de presença e contagem quando aplicável, sem copiar seus conteúdos.
A conclusão da coleta não é estabelecida pelo adaptador. Falta de alertas ou de instâncias não comprova segurança ou cobertura completa.

## Regras de revisão v2

| Regra | Condição | Resultado |
|---|---|---|
| ZAP-HIGH | riskcode 3, confiança conhecida e diferente de 0 | Revisar primeiro |
| ZAP-REVIEW | risco baixo/médio com confiança conhecida | Revisar depois |
| ZAP-FALSE-POSITIVE | confidence 0 | Contexto; alerta continua visível |
| ZAP-INFORMATION | riskcode 0 com confiança conhecida, diferente de 0 | Contexto |
| ZAP-CLASSIFICATION | risco ou confiança desconhecidos, sem marcação explícita False Positive | Revisar depois |
| ZAP-COVERAGE | recorte sem sites ou sem array explícito de alertas, instâncias ausentes/contagem divergente, stoppingInsight presente ou erros de automação declarados | Conferir evidência primeiro |

Uma marcação `Confirmed` é declaração do produtor, não confirmação independente. `False Positive` não é um atestado de segurança e não apaga o registro da fila.
A versão das regras passou a 2; o esquema de saída permanece 1. Identidades/fingerprints de revisões mudam de acordo com essa versão, inclusive em revisões que só usem os adaptadores anteriores.
Os comandos Nmap/Trivy existentes continuam disponíveis; sua interpretação de risco não foi ampliada por associação com alertas ZAP.

## Conhecimento absorvido e validação

O contrato foi estudado no template e na ajuda do add-on oficial, com commit e hashes Git registrados em `research/zap-format-validation.json`.
A consulta direta à página de documentação retornou HTTP 403 neste ambiente; o conteúdo de referência foi lido no repositório oficial pelo GitHub.
Foram lidas, sem executar ZAP, duas saídas esperadas oficiais: `basic-traditional-json.json` e `basic-traditional-json-plus.json`. Cada uma importou um alerta com duas instâncias.
Os bytes das referências foram conferidos contra os objetos Git. Nenhum payload, mensagem HTTP ou conteúdo completo dessas fixtures foi adicionado ao repositório.

Os testes próprios cobrem risco/confiança, falsos positivos, desconhecidos, estrutura inválida, omissão de componentes de URI, contagens, diagnósticos, escapes HTML e o fluxo CLI conjunto dos três produtores.
O exemplo visual foi renderizado em desktop e celular, com navegação de evidências e zero requisições de rede. A leitura de fixtures e o QA do HTML não são testes do motor ZAP ou de eficácia da ordem de revisão.

Fontes:

- [Formato Traditional JSON](https://www.zaproxy.org/docs/desktop/addons/report-generation/report-traditional-json/)
- [Formato Traditional JSON Plus](https://www.zaproxy.org/docs/desktop/addons/report-generation/report-traditional-json-plus/)
- [Código do add-on de relatórios](https://github.com/zaproxy/zap-extensions/tree/main/addOns/reports)
