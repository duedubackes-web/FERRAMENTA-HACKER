# Revisão explicável de evidências

O comando `review` transforma relatórios locais em uma fila de verificações sugeridas. A inteligência desta versão é um conjunto de regras determinísticas, identificadas e versionadas; não há modelo de linguagem, consulta de CVEs ou execução de scanners.

## Experimentar com dados sintéticos

```sh
mkdir -p work
python scripts/workbench.py review --before tests/fixtures/nmap-synthetic.xml --after tests/fixtures/nmap-synthetic-after.xml --trivy tests/fixtures/trivy-synthetic.json --output work/review.json --html work/review.html
```

Abra o HTML gerado. O exemplo pronto `examples/review-plan.html` contém os mesmos dados sintéticos e declara que não houve coleta de rede.
O exemplo tem seis itens: três em “Revisar primeiro” e três em “Revisar depois”. As duas entradas Trivy têm identificadores DEMO, que não correspondem a CVEs reais.

Para trabalhar com relatórios próprios, substitua os caminhos. É possível fornecer apenas `--trivy` ou somente o par `--before`/`--after`; um par Nmap incompleto é recusado.
Sem `--output`, o JSON é escrito na saída padrão. Os diretórios de destino precisam existir, os destinos JSON/HTML devem ser distintos e nenhum arquivo existente é sobrescrito.

## O que cada item explica

- A regra aplicada e sua prioridade de revisão.
- O motivo e a próxima verificação sugerida.
- Os fatos selecionados do relatório e os limites conhecidos.
- O hash do arquivo e sua referência de origem: índice Nmap na importação normalizada ou JSON Pointer direto no Trivy.

“Revisar primeiro”, “Revisar depois” e “Contexto” organizam o trabalho humano. Não são severidades, escores de risco, SLAs ou confirmação de vulnerabilidade.
A severidade Trivy permanece um campo separado, atribuído ao produtor. Valores desconhecidos continuam desconhecidos.

## Regras v1

| Regra | Condição | Prioridade |
|---|---|---|
| EVIDENCE-COMPLETION | Nmap não declara conclusão bem-sucedida | Revisar primeiro |
| EVIDENCE-SCOPE | Cobertura/método declarados diferem ou são desconhecidos | Revisar primeiro |
| EVIDENCE-IDENTITY | Comparador registrou ambiguidade, identidade ausente ou timeout | Revisar primeiro |
| NMAP-OPEN-STATE | Mesma porta registrada com outro estado conhecido antes e open depois | Revisar primeiro |
| NMAP-OBSERVATION | Outras diferenças de observação | Revisar depois |
| NMAP-ABSENCE | Host ou porta sem correspondência explícita no relatório atual | Contexto |
| TRIVY-HIGH | Produtor declara HIGH ou CRITICAL | Revisar primeiro |
| TRIVY-OTHER | Outros valores, desconhecidos ou ausentes | Revisar depois |
| TRIVY-COVERAGE | Sem resultados ou sem array explícito de vulnerabilidades em algum resultado | Revisar primeiro |

Questões de qualidade da evidência aparecem antes dos demais itens da mesma prioridade. Não se infere fechamento a partir de ausência, identidade física a partir de IP ou versão atualizada a partir de mudança de detecção.
O campo Trivy `Status` é preservado literalmente e não é usado para afirmar que um pacote foi corrigido. `FixedVersion` ausente significa informação não declarada, não inexistência de correção.

## Importação Trivy

```sh
python scripts/workbench.py import-trivy tests/fixtures/trivy-synthetic.json
```

Suporta o objeto JSON nativo Trivy com `SchemaVersion: 2`, em UTF-8, até 32 MiB. Não aceita CycloneDX, SPDX, SARIF ou outras versões como se fossem esse formato.
Chaves duplicadas, formas inválidas nos campos selecionados e constantes JSON não padronizadas são recusadas. Campos desconhecidos não viram instruções para a ferramenta.

São importados metadados do produtor/artefato e campos selecionados de `Results[].Vulnerabilities[]`: identificação, pacote, versões, status, severidade/fonte, título e URL declarada.
Ausência, null e array vazio são distinguíveis. O formato não permite estabelecer por si só a conclusão de uma coleta ou quais scanners foram habilitados.
Valores de `Secrets`, configurações, licenças e outras categorias não são exportados; categorias conhecidas registram apenas presença e contagem quando disponível. CVSS, dependências, contexto de execução e outros detalhes ficam fora desta versão.

## Proveniência e limites

Os hashes identificam os bytes recebidos, não autenticam o produtor nem atestam a veracidade de um relatório. Os JSONs originais devem ser preservados para conferência.
O ID da revisão considera hashes de entrada, versões dos importadores/comparador e a versão e fingerprint das regras. Os IDs dos itens também distinguem fatos diferentes sobre a mesma porta.
Nenhuma associação é feita entre IPs Nmap e artefatos/pacotes Trivy. A ferramenta não transforma coocorrência de relatórios em correlação entre ativos.

O HTML usa dados escapados, navegação interna e nenhum recurso remoto. As sugestões são texto e não são executadas. Os resultados podem conter nomes, caminhos e dados selecionados dos arquivos fornecidos; escolha onde salvá-los e compartilhá-los.
Uma fila vazia não comprova segurança. Esta é uma revisão de campos selecionados, não uma auditoria integral ou uma determinação de explorabilidade.

## Validação realizada

Além dos testes de contrato e do fluxo CLI, foram lidos 92 arquivos públicos esperados do Trivy fixado no lock: 83 JSONs nativos importados e nove arquivos de outros formatos recusados corretamente (sete CycloneDX e dois SPDX).
O registro por arquivo está em `research/trivy-fixture-validation.json`. A leitura desses arquivos não executou código, scanner ou suíte de testes do Trivy.
O HTML sintético foi renderizado em Chromium a 1.365×980 e 375×812, com detalhes e navegação de origem funcionando, sem requisições de rede e sem transbordamento horizontal. O registro está em `research/review-browser-check.json`.
O QA usou `setContent`, pois o ambiente restringe a navegação por URL file:. Isso não comprova abertura por arquivo em todas as políticas de navegador.

A utilidade da ordem sugerida em ambientes reais e sua comparação com o julgamento de analistas ainda precisam ser avaliadas com usuários.
