# Google Gemini — pesquisa pública e projetos abertos relacionados

## O que foi observado no app

URL solicitada: https://gemini.google.com/app?hl=pt-BR.
O GET público, sem cookies ou credenciais de conta, respondeu HTTP 200 com HTML e referências a scripts.
Os textos observados incluíram o título Google Gemini, Fazer login e Google Apps. Não houve conversa, submissão de prompt, leitura de conta ou chamada a modelo.
Esses dados não comprovam o funcionamento das demais telas ou recursos do produto.

Foram retidos localmente dois scripts iniciais referenciados no HTML, dos domínios gemini.gstatic.com e www.gstatic.com, com **175.835 bytes no total**.
O script de telemetria de outra origem não foi coletado. Scripts inline de bootstrap e chunks carregados dinamicamente não foram analisados neste recorte.
A página e os bundles completos ficam apenas no diretório de trabalho; o repositório contém metadados, hashes, URLs e um resumo original da observação, sem republicar código proprietário ou contexto inline de sessão.
As URLs identificam versões observadas; sua disponibilidade futura não é garantida.

## Aplicação real de Craft Anything e REA

Craft Anything 0.6.1 executou core-archive-show em modo Deep no diretório local contendo os dois scripts. Reportou inventário completo de 2/2 arquivos nesse diretório.
REA 6.9.0 executou analyze-javascript-application sobre o mesmo material inerte, com entrega summary e exportação da evidência completa em arquivo local.
Parâmetros adicionais: max-semantic-nodes=30000 e analysis-timeout-ms=60000. Não houve execução do JavaScript coletado.

O analisador reportou 2 arquivos JavaScript analisados, zero falhas de parse e 78 findings estáticas. Findings não são vulnerabilidades confirmadas.
A expansão de aliases atingiu seu orçamento e parte das relações permaneceu desconhecida. A cobertura complete-within-view da síntese não significa que todo o grafo do app esteja completo.
O ID principal, ID da síntese, estatísticas, limitações, URLs e hashes estão em research/gemini-public-observation.json.
O arquivo de evidência completo permanece local e tem seu tamanho e SHA-256 registrados; não foi incluído no Git por poder conter trechos extensos dos bundles proprietários.

## Produtos abertos relacionados, separados do app

| Fonte | Commit fixado | Entradas |
|---|---|---:|
| [gemini-cli](https://github.com/google-gemini/gemini-cli) | `4ed06ed0ddc523a6d356a4ad35ddfea331041888` | 3057 |
| [google-genai-js](https://github.com/googleapis/js-genai) | `4e849b1434ba0c7dbb3a49e35ca31d5d689b2af4` | 972 |

Gemini CLI é um agente aberto de terminal, com interface e núcleo em workspaces separados. O Google Gen AI SDK é um cliente de APIs para JavaScript/TypeScript.
Essas árvores não são o código de servidor do Gemini web, os pesos do modelo ou uma implementação equivalente do serviço hospedado.
Os avisos Apache-2.0 disponíveis foram preservados. Essa licença não se estende automaticamente ao app web ou aos bundles públicos dele.
Não foram instaladas dependências desses projetos, iniciado agente Gemini, configuradas credenciais, registradas integrações MCP ou feitas chamadas pagas.

- **G01** A documentação do Gemini CLI distingue interface de terminal e núcleo em workspaces separados. [Fonte no commit](https://github.com/google-gemini/gemini-cli/blob/4ed06ed0ddc523a6d356a4ad35ddfea331041888/GEMINI.md#L21).

- **G02** O SDK JavaScript declara um cliente GoogleGenAI; a classe não é implementação dos modelos ou do app hospedado. [Fonte no commit](https://github.com/googleapis/js-genai/blob/4e849b1434ba0c7dbb3a49e35ca31d5d689b2af4/src/client.ts#L152).

## O que a pesquisa não obteve

Não houve acesso a backend, pesos, dados de treinamento, instruções internas, conversas privadas ou interfaces protegidas.
Não foi realizada reconstrução funcional completa, comparação entre modelos, teste de qualidade de respostas ou decompilação de um binário do serviço.
O código aberto relacionado e os ativos públicos observados são material de pesquisa; não se afirma uma cópia do Gemini.

## Direção para o nosso produto

A distinção observada entre interface, núcleo e cliente de API favorece manter a busca do corpus separada de futuros adaptadores de IA.
A base já oferece busca offline por categoria e evidência; uma futura interface conversacional pode fundamentar respostas nos registros e exibir origem, cobertura e desconhecidos antes de propor ações.
Qualquer integração com Gemini deve usar a API documentada e um escopo de credenciais/custos definido, em vez de reproduzir endpoints privados observados no cliente web.
Isso é uma proposta de arquitetura, ainda sem agente de IA ou serviço de geração implementado nesta entrega.

## Fontes oficiais

- [Gemini web](https://gemini.google.com/app?hl=pt-BR)
- [Documentação Gemini CLI](https://google-gemini.github.io/gemini-cli/docs/)
- [Gemini API](https://ai.google.dev/gemini-api/docs)
- [Central de privacidade dos apps Gemini](https://support.google.com/gemini/answer/13594961)
