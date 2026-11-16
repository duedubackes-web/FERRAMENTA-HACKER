# Metasploit Framework no Atlas

O Metasploit já estava entre os 38 projetos do catálogo. Agora tem uma ficha destacada na tela **Tecnologias** e pode ser consultado no Assistente Atlas pelos nomes **Metasploit Framework**, **MSF** e **msfconsole**.

Pergunte: **Como o Metasploit está integrado?** A resposta identifica a referência documental e permite abrir sua ficha. A busca por aliases também funciona na CLI:

```sh
python scripts/workbench.py catalog --query msfconsole
```

## Estado efetivo

Esta integração é documental: não instala nem executa Metasploit, não abre msfconsole, não conecta RPC e não fornece módulos, payloads, sessões ou automação de exploração. O Atlas continua analisando seus formatos de relatório já implementados. Um adaptador de exportação Metasploit ainda não foi desenvolvido nem validado.

Foram consultados README.md e LICENSE do repositório oficial `rapid7/metasploit-framework`, fixados pelo commit registrado em `research/metasploit-reference.json`. Os bytes UTF-8 foram conferidos contra os hashes dos objetos Git. O README apresenta msfconsole como interface principal; LICENSE declara BSD-3-clause para o framework e lista componentes de terceiros sob outras licenças. Isso não estabelece automaticamente os direitos de redistribuição de cada componente.

A base mantém somente URLs, hashes e observações desses dois arquivos. Não foi adicionada uma árvore completa de fontes ou feita auditoria de módulos. Não houve execução do framework nem acesso a alvos. O registro antigo da API GitHub sobre licença permanece identificado como metadado, separado desta consulta documental.
