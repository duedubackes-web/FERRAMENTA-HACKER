# Metasploit Framework no Atlas

O Metasploit já estava entre os 38 projetos do catálogo. Agora tem uma ficha destacada na tela **Tecnologias** e pode ser consultado no Assistente Atlas pelos nomes **Metasploit Framework**, **MSF** e **msfconsole**.

Pergunte: **Como o Metasploit está integrado?** A resposta identifica a referência documental e permite abrir sua ficha. A busca por aliases também funciona na CLI:

```sh
python scripts/workbench.py catalog --query msfconsole
```

## Estado efetivo

A referência inicial foi ampliada para inventário da árvore rastreada e dossiê seletivo de arquitetura. O recorte atual está em [Metasploit e SET](METASPLOIT-SET.md). A integração continua estática: não instala nem executa Metasploit, não abre msfconsole, não conecta RPC e não fornece módulos, payloads, sessões ou automação de exploração. O Atlas continua analisando seus formatos de relatório já implementados. Um adaptador de exportação Metasploit ainda não foi desenvolvido nem validado.

Foram consultados README.md e LICENSE do repositório oficial `rapid7/metasploit-framework`, fixados pelo commit registrado em `research/metasploit-reference.json`. Os bytes UTF-8 foram conferidos contra os hashes dos objetos Git. O README apresenta msfconsole como interface principal; LICENSE declara BSD-3-clause para o framework e lista componentes de terceiros sob outras licenças. Isso não estabelece automaticamente os direitos de redistribuição de cada componente.

O registro inicial `research/metasploit-reference.json` preserva a consulta desses dois arquivos. A rodada posterior acrescenta lock, inventário e evidências do snapshot completo da árvore rastreada, com um gitlink não coletado. A análise semântica permanece seletiva, sem auditoria de módulos. Não houve execução do framework nem acesso a alvos. O registro antigo da API GitHub sobre licença permanece identificado como metadado, separado desta consulta documental.

## Estado atualizado: fontes indexadas

A rodada seguinte coletou a árvore rastreada e acrescentou um dossiê de arquitetura com REA/Craft. As observações anteriores sobre apenas dois arquivos descrevem a primeira consulta, não o recorte atual. Consulte [Metasploit e SET](METASPLOIT-SET.md). O motor e o adaptador de relatórios continuam não integrados.
