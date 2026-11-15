# Evolução das revisões — Atlas v0.2

Compare dois registros salvos de um mesmo projeto para acompanhar o que mudou nos campos selecionados de Trivy e ZAP. A comparação usa declarações dos relatórios, sem estabelecer identidade verificada de ativos ou transferir decisões humanas.

## Usar na interface e no chat

1. Importe relatórios e gere uma revisão.
2. Importe os relatórios seguintes e gere outra revisão; ambas permanecem salvas.
3. Na fila, selecione **Comparar revisões salvas** e escolha os registros anterior/posterior.
4. Abra cada resultado para conferir os itens e suas referências originais, ou baixe a comparação JSON.
5. Pergunte ao chat **O que mudou entre as revisões?**. A resposta compara as duas mais recentes e inclui uma referência que abre o resultado completo.

As seleções da interface definem a direção da comparação. Escolher os registros na ordem inversa inverte a perspectiva. A lista mostra data, número de itens e identificador do registro; comparações entre projetos distintos são recusadas.

## Interpretar os resultados

| Estado | O que estabelece |
|---|---|
| Observado apenas depois | A chave declarada só está na revisão posterior; não comprova introdução no sistema |
| Não observado depois | A chave não aparece no recorte posterior; não comprova correção |
| Mesmos campos selecionados | Uma chave única em cada lado tem a mesma projeção selecionada |
| Campos selecionados alterados | Uma chave única em cada lado tem diferença nos campos comparados |
| Chave declarada duplicada | Há mais de um registro com a chave em ao menos um lado; não há pareamento individual |
| Sem chave comparável | Faltam identificadores necessários ou a categoria ainda não é suportada |

Contagens referem-se às linhas da comparação: uma linha ambígua pode conter vários registros, enquanto itens sem chave aparecem individualmente por lado. Mudanças de regras ou de versão dos adaptadores compartilhados bloqueiam o pareamento e não geram supostas adições/remoções.

## Chaves e comparabilidade

**Trivy:** nome/tipo do artefato, alvo declarado, identificador da vulnerabilidade, pacote e versão instalada precisam estar presentes. Classe, tipo, PkgID e PkgPath também compõem a chave quando disponíveis. Uma mudança de versão instalada cria outra observação; não presume atualização corretiva ou equivalência entre artefatos. Severidade, versão de correção e outros campos selecionados podem mudar sem trocar a chave.

**ZAP:** site declarado sem componentes omitidos e pluginid identificam o grupo de alerta, acrescido de alertRef quando presente. Site ausente ou com userinfo/query/fragmento omitidos não é pareado. A chave não comprova identidade de cada instância: caminhos podem conter dados sensíveis e as URIs de instância já passaram pela minimização do importador. Mudanças de confiança e risco são comparadas separadamente; falso positivo continua como declaração do produtor.

Reordenação de vulnerabilidades ou instâncias não conta como alteração por si só. Somente índices/pointers de posição conhecidos são excluídos da projeção; os registros originais, hashes e referências permanecem na saída. As regras de revisão, prioridade, categoria, título e fatos selecionados são comparados. O comparador não tenta parear observações Nmap nem tarefas de cobertura nesta versão: ambas permanecem como sem chave comparável. Para mudanças de rede, use o comparador Nmap já existente.

Diferenças de cobertura, metadados dos produtores e presença de papéis são explicitadas. Correspondência por chave não comprova cobertura equivalente, mesma máquina ou mesma aplicação. A comparação não consulta avisos externos, não executa motores e não autentica as revisões recebidas.

## CLI

Use os JSONs produzidos pelo comando `review` ou presentes nas exportações:

```sh
python scripts/workbench.py compare-reviews revisao-anterior.json revisao-posterior.json --output evolucao.json
```

Código de saída 0: comparação produzida; 1: bloqueada por versões incompatíveis; 2: entrada inválida, inacessível ou saída já existente. Mesmo bloqueada, a saída JSON contém a razão e as limitações. O comando preserva arquivos existentes. A leitura tem o limite de 32 MiB por revisão e rejeita chaves duplicadas conforme o leitor compartilhado.

## Exportação do projeto

O pacote continua incluindo a revisão atual. Quando há uma revisão anterior no histórico capturado para a exportação, também inclui `review-baseline.json`, `review-evolution.json` e `review-history.json`. A baseline e a comparação ficam vinculadas aos registros escolhidos, sem trocar silenciosamente por uma nova revisão criada durante a operação.

Os originais continuam opcionais. Ao marcar sua inclusão, `originals/` contém os arquivos da revisão atual e `baseline-originals/` os da baseline exportada. Nenhuma decisão é reaplicada ou descartada pela comparação. O esquema SQLite permanece 1; o histórico usa os registros já persistidos, sem migração.

O diferencial de produto é tornar mudanças e lacunas revisáveis com origem. Novidade de mercado e utilidade prática ainda precisam ser avaliadas com usuários.
