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
