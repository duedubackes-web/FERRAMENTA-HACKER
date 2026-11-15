# Hipótese de produto e MVP

Público inicial proposto: equipes pequenas de engenharia, suporte e segurança que precisam explicar problemas de tráfego com evidências locais reproduzíveis.
Problema a validar: reconstruir o que ocorreu e comparar resultados exige juntar arquivos, ferramentas e relatórios manualmente.

## Proposta

Um espaço de trabalho local para importar capturas, registrar hashes e versões, produzir análises estruturadas e comparar execuções.
Português desde o início; referências clicáveis até o arquivo e a ferramenta que produziram cada observação.
Os diferenciais são hipóteses, não resultado de pesquisa de mercado nem alegação de novidade técnica.

## Recorte do primeiro produto

1. Importar PCAP/PCAPNG local com hash e registro de origem.
2. Usar TShark já instalado para resumos de protocolos, endpoints, DNS e TLS, com versão e limites registrados.
3. Mostrar observações com origem e distinguir dados ausentes de resultado vazio.
4. Comparar duas capturas e exportar JSON e relatório legível.
5. Guardar tudo localmente, permitindo remoção do projeto e exportação dos seus dados.

## Critérios de aceite propostos

- Corpus de capturas sintéticas com saídas de referência conferidas contra TShark.
- Arquivo truncado/malformado produz erro controlado e preserva a causa.
- O mesmo artefato com ferramenta e parâmetros iguais preserva resultados normalizados, excetuando timestamps e IDs de execução.
- Comparação não afirma ausência de tráfego quando a captura é parcial.
- Todas as constatações exportadas apontam a artefatos e execuções reais.
- Medir tempo, memória e utilidade em tarefas representativas antes de estabelecer metas comerciais.

## Validação comercial pendente

Entrevistar cinco potenciais usuários; observar uma tarefa real com material sanitizado;
comparar o fluxo com ferramentas existentes; medir tempo até encontrar a causa e qualidade da explicação.
Só ampliar para composição de laboratório ou novos conectores após o primeiro fluxo ser validado.


## Incremento disponível

A importação offline de XML Nmap já adiciona inventário de ativos à base: hash, hosts, endereços, estados, serviços e cobertura.
É o primeiro fluxo de ingestão de um resultado de ferramenta; ainda faltam comparação entre sessões, correlação com capturas e validação da hipótese comercial.
O objetivo é permitir investigação reproduzível com artefatos existentes, sem exigir que o usuário execute um motor pela aplicação.


## Comparação disponível

Agora é possível comparar dois XMLs existentes e gerar um relatório navegável com diferenças, lacunas e fontes.
O avanço prático é explicar quando uma diferença está acompanhada de mudança de cobertura e quando os registros não permitem um pareamento confiável.
Isso busca reduzir interpretações incorretas de inventário, como chamar uma porta não observada de fechada. A utilidade em tarefas reais ainda precisa ser medida.
A aplicação não atribui pontuações de risco nem declara vulnerabilidades a partir desses registros.


## Incremento: da observação à revisão

O fluxo Nmap/Trivy já produz uma fila de verificações sugeridas. A diferença prática é tornar explícito por que um item pede atenção e quais fatos sustentam esse pedido.
Esta inteligência é baseada em regras versionadas, não em respostas de um modelo. A fila dá visibilidade às lacunas de evidência antes das interpretações da mesma prioridade.
A prioridade não substitui risco de negócio ou revisão de aplicabilidade. A utilidade dessa ordem ainda precisa ser medida em tarefas reais com analistas.


## Alertas web e revisão contextual

A ferramenta passa a reunir três produtores na mesma fila: rede (Nmap), componentes (Trivy) e alertas web (ZAP), com contratos distintos e sem inventar correspondências entre ativos.
O avanço prático é mostrar risco e confiança separadamente, manter falsos positivos visíveis e reduzir a propagação de mensagens/payloads em relatórios derivados.
A classificação ainda é do produtor e a prioridade apenas organiza revisão humana. A validade dessas decisões em tarefas reais continua sendo objeto de avaliação.

## Versão local do produto: Atlas v0.1

O aplicativo web local reúne projetos persistentes, fontes versionadas, fila de revisão, histórico de decisões e chatbot. A busca padrão é determinística com referências; um modelo Ollama local pode ser configurado para gerar texto explicitamente marcado. O estúdio mapeia ZIPs de fonte e exporta plano, backlog e um protótipo próprio de quadro de tarefas com chat local.
Essa entrega implementa um fluxo completo local. Não estabelece equivalência com Lovable, Vercel ou v0, nem originalidade de mercado. A integração com REA/Craft/Kali continua no nível de pesquisa documentada; execução de motores não foi adicionada por implicação. Autenticação multiusuário, operação pública, cobrança e validação comercial permanecem trabalho futuro. Consulte `APLICATIVO-ATLAS.md` para o contrato efetivo.
