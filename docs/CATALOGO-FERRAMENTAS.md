# Catálogo de pesquisa: pentest, Red Team e ferramentas relacionadas

## Escopo da ampliação

O diretório reúne **39 projetos** por categoria e um índice separado de **409 candidatos de pacotes diretamente declarados em 29 perfis kali-tools-*** do commit fixado de kali-meta.
As declarações de pacotes não são 409 projetos distintos nem uma lista de software instalado. Alternativas, versões, arquiteturas, campos Depends/Recommends/Suggests e substituições não resolvidas são preservados.
Não houve resolução APT, fechamento transitivo, instalação dos pacotes ou execução dos motores catalogados.

O catálogo é uma seleção verificável, não um levantamento exaustivo de todo o ecossistema. Os registros de IA são uma área de pesquisa relacionada, não ferramentas de pentest por essa razão.

## Estados que não devem ser confundidos

- **cataloged-only:** endereço e metadados retidos; sem árvore de código coletada nesta base.
- **source-indexed:** há commit e inventário da árvore rastreada em sources.lock.json; isso não é teste de funcionamento.
- **public-page-inspected:** observação pública do app hospedado, sem código de backend.
- **runtime_evidence:** registra o uso limitado de REA/Craft como CLIs de inspeção; os demais motores não foram executados.

São 20 projetos com fontes indexadas, representados por 21 snapshots, pois a composição Kali tem duas árvores separadas.
As revisões semânticas são seletivas. Não há ranking de eficácia, indicação automática de execução ou encadeamento operacional das ferramentas.

## Projetos

| Projeto | Categorias | Coleta |
|---|---|---|
| [Kali Linux](https://gitlab.com/kalilinux/packages/kali-meta) | Plataforma e composição | source-indexed |
| [Craft Anything](https://github.com/storytold/craft-anything) | Inspeção e engenharia reversa | source-indexed |
| [REA](https://github.com/morluto/rea) | Inspeção e engenharia reversa | source-indexed |
| [Nmap](https://github.com/nmap/nmap) | Descoberta de ativos | source-indexed |
| [Wireshark](https://gitlab.com/wireshark/wireshark) | Análise de tráfego | source-indexed |
| [THC Hydra](https://github.com/vanhauser-thc/thc-hydra) | Auditoria de senhas | source-indexed |
| [sqlmap](https://github.com/sqlmapproject/sqlmap) | Avaliação de aplicações web | source-indexed |
| [John the Ripper](https://github.com/openwall/john) | Auditoria de senhas | source-indexed |
| [ZAP](https://github.com/zaproxy/zaproxy) | Avaliação de aplicações web | source-indexed |
| [Nuclei](https://github.com/projectdiscovery/nuclei) | Avaliação de vulnerabilidades, Avaliação de aplicações web | source-indexed |
| [httpx](https://github.com/projectdiscovery/httpx) | Descoberta de ativos, Avaliação de aplicações web | cataloged-only |
| [Subfinder](https://github.com/projectdiscovery/subfinder) | Descoberta de ativos | cataloged-only |
| [OWASP Amass](https://github.com/owasp-amass/amass) | Descoberta de ativos | cataloged-only |
| [Nikto](https://github.com/sullo/nikto) | Avaliação de aplicações web | cataloged-only |
| [ffuf](https://github.com/ffuf/ffuf) | Avaliação de aplicações web | cataloged-only |
| [Gobuster](https://github.com/OJ/gobuster) | Avaliação de aplicações web, Descoberta de ativos | cataloged-only |
| [RustScan](https://github.com/bee-san/RustScan) | Descoberta de ativos | cataloged-only |
| [Aircrack-ng](https://github.com/aircrack-ng/aircrack-ng) | Avaliação de redes sem fio | source-indexed |
| [bettercap](https://github.com/bettercap/bettercap) | Análise de tráfego, Avaliação de redes sem fio | cataloged-only |
| [mitmproxy](https://github.com/mitmproxy/mitmproxy) | Análise de tráfego, Avaliação de aplicações web | source-indexed |
| [Zeek](https://github.com/zeek/zeek) | Monitoramento de rede, Análise de tráfego | source-indexed |
| [Suricata](https://github.com/OISF/suricata) | Monitoramento de rede | cataloged-only |
| [Trivy](https://github.com/aquasecurity/trivy) | Componentes e cadeia de software, Avaliação de vulnerabilidades | source-indexed |
| [Syft](https://github.com/anchore/syft) | Componentes e cadeia de software | cataloged-only |
| [Semgrep](https://github.com/semgrep/semgrep) | Análise de código | cataloged-only |
| [TruffleHog](https://github.com/trufflesecurity/trufflehog) | Identificação de segredos | cataloged-only |
| [Gitleaks](https://github.com/gitleaks/gitleaks) | Identificação de segredos | cataloged-only |
| [osquery](https://github.com/osquery/osquery) | Visibilidade de endpoints | cataloged-only |
| [Velociraptor](https://github.com/Velocidex/velociraptor) | Investigação e resposta, Visibilidade de endpoints | cataloged-only |
| [DefectDojo](https://github.com/DefectDojo/django-DefectDojo) | Gestão de resultados | source-indexed |
| [CALDERA](https://github.com/apache/caldera) | Emulação de adversário | source-indexed |
| [Atomic Red Team](https://github.com/redcanaryco/atomic-red-team) | Validação de detecções, Emulação de adversário | cataloged-only |
| [BloodHound CE](https://github.com/SpecterOps/BloodHound) | Análise de identidades e relações | cataloged-only |
| [Impacket](https://github.com/fortra/impacket) | Bibliotecas de protocolos | cataloged-only |
| [Metasploit Framework](https://github.com/rapid7/metasploit-framework) | Frameworks de testes de intrusão | source-indexed |
| [Social-Engineer Toolkit (SET)](https://github.com/trustedsec/social-engineer-toolkit) | Frameworks de testes de intrusão | source-indexed |
| [Google Gemini (app)](https://gemini.google.com/app?hl=pt-BR) | Assistentes e interfaces de IA | public-page-inspected |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | Assistentes e interfaces de IA | source-indexed |
| [Google Gen AI SDK](https://github.com/googleapis/js-genai) | Assistentes e interfaces de IA | source-indexed |

## Novas fontes e evidências

Foram coletadas oito árvores adicionais de segurança: ZAP, Nuclei, mitmproxy, Aircrack-ng, Zeek, Trivy, DefectDojo e CALDERA.
O pedido posterior acrescentou o estudo público do Gemini e as árvores abertas Gemini CLI e Google Gen AI SDK; esses produtos são tratados separadamente em GEMINI.md.
O total atual é **75.124 entradas rastreadas em 21 repositórios**. Gitlinks não baixados estão registrados; conteúdos externos e Git LFS não foram hidratados.
Os ZIPs ficam fora do Git do projeto, com hashes no lock e recuperação das árvores pelo script fetch_sources.py.

Craft Anything 0.6.1 inventariou os dez novos ZIPs. REA 6.9.0 executou inspect-artifact nos oito ZIPs de segurança.
As verificações correlacionaram os caminhos raiz e todos os hashes disponíveis com os inventários próprios; entradas sem hash no REA permanecem explícitas.
A cobertura Craft de Trivy é parcial para conteúdo aninhado: 22 arquivos internos não foram abertos na profundidade 1, embora os bytes dos arquivos rastreados tenham sido conferidos no snapshot.
Nos demais casos, a palavra complete retornada pelas ferramentas se refere ao escopo declarado do inventário, não à análise semântica integral do programa.

| Fonte | Entradas rastreadas | Gitlinks não baixados | Cobertura Craft | Hashes raiz REA |
|---|---:|---:|---|---:|
| zaproxy | 2268 | 0 | complete | 2268 |
| nuclei | 1559 | 0 | complete | 1559 |
| mitmproxy | 1291 | 0 | complete | 1290 |
| aircrack-ng | 725 | 0 | complete | 725 |
| zeek | 12267 | 24 | complete | 12237 |
| trivy | 3454 | 0 | partial | 3451 |
| defectdojo | 8746 | 0 | complete | 8742 |
| caldera | 406 | 16 | complete | 390 |
| gemini-cli | 3057 | 0 | complete | Não aplicado ao ZIP; aplicado aos scripts públicos do app |
| google-genai-js | 972 | 0 | complete | Não aplicado ao ZIP; aplicado aos scripts públicos do app |

CALDERA e Zeek contêm gitlinks não baixados recursivamente. Não é correto atribuir à coleta todos os plugins, dependências ou capacidades desses projetos.
O detalhe por entrada, limitações e IDs estão em research/evidence/expanded-inventory-crosschecks.json e nas sínteses individuais REA/Craft.

## Arquitetura observada seletivamente

- **X01** ZAP possui um ponto explícito de carregamento de extensões; os add-ons não foram executados. [Fonte no commit](https://github.com/zaproxy/zaproxy/blob/17c25b45ad0f79631ae8d611a6fa647275aa131b/zap/src/main/java/org/parosproxy/paros/extension/ExtensionLoader.java#L162).

- **X02** Nuclei declara um componente Engine; isso identifica uma fronteira de arquitetura, não comprova cobertura de templates. [Fonte no commit](https://github.com/projectdiscovery/nuclei/blob/fe3421e77f96f8081c39105b12b82789b59b9006/pkg/core/engine.go#L45).

- **X03** mitmproxy separa a gestão de extensões em AddonManager. [Fonte no commit](https://github.com/mitmproxy/mitmproxy/blob/f7701d5f6b69e103bcc4995a641447ae70574e99/mitmproxy/addonmanager.py#L131).

- **X04** Aircrack-ng expõe uma abstração de interface sem fio; nenhum hardware foi acessado. [Fonte no commit](https://github.com/aircrack-ng/aircrack-ng/blob/7e2256f38f3590af4c19a6ae14ed79bab02242e6/include/aircrack-ng/osdep/osdep.h#L87).

- **X05** Zeek declara um contrato de plugin; submódulos não foram baixados recursivamente. [Fonte no commit](https://github.com/zeek/zeek/blob/f98a92789a560b77d57aa27e625c6a7bdf85ecee/src/plugin/Plugin.h#L635).

- **X06** Trivy possui um tipo explícito de relatório, referência para futura ingestão offline. [Fonte no commit](https://github.com/aquasecurity/trivy/blob/239be7b2671a3c9706bbfec2ba4677210cbdcdec/pkg/types/report.go#L20).

- **X07** DefectDojo separa a importação de resultados em um componente dedicado. [Fonte no commit](https://github.com/DefectDojo/django-DefectDojo/blob/f6cee25f3e0fca85c8ccfc6e3764a4e69a2f0c0f/dojo/importers/default_importer.py#L47).

- **X08** O recorte CALDERA contém um serviço de dados; isso não demonstra execução de plugins ou capacidades operacionais. [Fonte no commit](https://github.com/apache/caldera/blob/cb8d6a8160e0f4990af323a7c071d5e8482b42c7/app/service/data_svc.py#L48).

Essas referências orientam a separação entre extensões, contratos de dados, importação e análise na implementação própria. Não demonstram equivalência funcional ou incorporação do código desses projetos.

## Buscar no catálogo offline

```sh
python scripts/workbench.py catalog --query "red team"
python scripts/workbench.py catalog --category web-testing --source-indexed
python scripts/workbench.py packages --profile kali-tools-web
python scripts/workbench.py packages --query nmap
```

A busca de projetos considera nomes, endereços, categorias e aliases, ignorando caixa e acentos. Nenhum desses comandos executa uma ferramenta ou faz requisições de rede.
O índice Kali preserva candidatos e cláusulas, sem presumir equivalência entre nome de pacote e repositório do catálogo.

## Atualizar a pesquisa

Os metadados consultados estão em research/tool-repository-metadata.json; a classificação editorial em research/tool-curation.json.
Os derivados são regenerados offline com:

```sh
python scripts/build_tool_catalog.py
```

Isso não busca versões novas. Uma nova coleta precisa registrar origem, data e eventuais mudanças de endereço antes de atualizar os metadados.
Nesta pesquisa foram corrigidas as referências consultadas RustScan/RustScan → bee-san/RustScan e mitre/caldera → apache/caldera.
Licenças no catálogo são metadados ou avisos raiz preservados, sem avaliação completa de integração por componente.

## Fontes de descoberta

- [Metapacotes oficiais Kali](https://www.kali.org/docs/general-use/metapackages/)
- [Índice oficial de ferramentas Kali](https://www.kali.org/tools/all-tools/)
- [Documentação de desenvolvimento ZAP](https://www.zaproxy.org/docs/developer/quick-start-build/)
- [BloodHound Community Edition](https://specterops.io/open-source-tools/bloodhound-community-edition/)
- Os endpoints GitHub e repositórios canônicos de cada registro estão retidos no conjunto de metadados.

A rodada de 16/11/2026 acrescentou Metasploit e SET. Ambos têm inventários e hashes raiz conferidos por REA/Craft; há um gitlink não coletado no Metasploit e conteúdo aninhado não aberto. Consulte `METASPLOIT-SET.md` para parâmetros e limites.
