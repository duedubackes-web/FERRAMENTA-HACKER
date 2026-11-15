# Licenças e proveniência

| Fonte | Declaração observada | Ação de preparação |
|---|---|---|
| REA | MIT; avisos terceiros separados | LICENSE e THIRD_PARTY_NOTICES preservados |
| Craft Anything | MIT OR Apache-2.0 em Cargo.toml | Textos disponíveis preservados; escolha e atribuições ao incorporar |
| Wireshark | GPLv2; maioria GPLv2-or-later, exceções por arquivo | COPYING e README consultados; examinar cada componente usado |
| Hydra | AGPLv3 no README | LICENSE preservado; avaliar entrega e acesso em rede se houver derivação |
| kali-meta | GPL-3.0+ em debian/copyright | Copyright e declaração preservados |
| Kali live-build | LICENSE contém GPLv2 | Preservado; permissões específicas exigem revisão dos arquivos usados |
| Nmap | NPSL 0.95, licença própria | LICENSE preservado; revisar redistribuição, incorporação e condições OEM |
| sqlmap | GPLv2-ou-posterior com esclarecimentos e exceções próprios | LICENSE e avisos terceiros preservados; o texto trata execução e parsing de resultados |
| John the Ripper jumbo | GPLv2-ou-posterior, exceção OpenSSL/unRAR e termos por componente | LICENSE, doc/LICENSE e doc/COPYING preservados; sem incorporação do motor na base MIT |

Kali como distribuição não tem uma única licença que cubra todos os seus pacotes.
Metadados do GitHub não substituem textos de licença do commit ou declarações por arquivo.

Os ZIPs entregues preservam as árvores e os avisos originais. Cópias locais completas das licenças disponíveis ficam em `third_party/notices/`.
O corpus não é um SBOM transitivo de uma instalação; bibliotecas de sistema, dependências resolvidas e ferramentas opcionais não foram enumeradas integralmente.

Esta base não incorpora implementações dos alvos no código da CLI. Preserva referências, inventários, evidências e excertos seletivos para pesquisa.
Não se afirma um processo clean room independente: a análise leu código-fonte e Craft Anything foi executado em modo Deep.
Separar processos pode ajudar a arquitetura, mas não é uma garantia automática sobre obrigações de licença.

O repositório fornecido pelo proprietário já contém LICENSE MIT, copyright 2026 duedubackes-web. Essa licença foi preservada e se aplica ao código original da base, não relicencia material de terceiros.
Não aplicar uma licença permissiva global sobre arquivos de terceiros. Marcas, imagens e textos dos sites não são concedidos pela licença de ferramentas.
O HTML do Wireshark é evidência de pesquisa, não uma licença para reutilizar sua interface ou identidade visual.

O novo importador XML é código original, não inclui nem executa os motores. NPSL discute explicitamente a leitura de resultados fornecidos por usuários e usos que não requerem os direitos concedidos pela licença; isso não concede automaticamente direitos para redistribuir o motor. O relatório NMAP-SQLMAP cita as linhas relevantes dos dois projetos.

Na coleta John, doc/LICENSE é um link simbólico para a licença raiz. O snapshot mantém seu tipo e texto de destino; a pasta de avisos disponibiliza uma cópia regular do texto da licença. Não se infere licença uniforme para dependências ou componentes de terceiros.


## Ampliação do diretório

Avisos raiz disponíveis foram preservados para ZAP, Nuclei, mitmproxy, Aircrack-ng, Zeek, Trivy, DefectDojo, CALDERA, Gemini CLI e Google Gen AI SDK.
Os registros sem árvore coletada mantêm somente metadados da licença retornados pelo GitHub. Metadados SPDX ou avisos raiz não substituem análise de arquivos, dependências e condições de integração.
Nos dois projetos abertos relacionados a Gemini, o texto raiz consultado é Apache-2.0. Essa licença não foi atribuída ao app hospedado ou aos seus bundles.
O material público proprietário do app foi estudado localmente; o Git recebe uma observação original, URLs, hashes e limitações, sem republicação dos bundles completos ou dados inline de bootstrap.
A existência de uma página pública não é tratada como concessão de licença para copiar a implementação ou a identidade visual do serviço.
