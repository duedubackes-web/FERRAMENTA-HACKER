# Relatório de extração e análise — primeira rodada

Coleta UTC: 2026-11-15T13:42:57.910339+00:00; data local de referência: 15/11/2026, America/Sao_Paulo.

## Cobertura real

| Fonte | Arquivos rastreados | Bytes inventariados | Commit |
|---|---:|---:|---|
| craft-anything | 1082 | 22507817 | `88d1d9cac852aec1c7fd97886db451e005e49d2a` |
| hydra | 134 | 2935318 | `707c822e88938c526279fcabc10a8a265bbc53c4` |
| kali-live-build | 56 | 3536995 | `adb2e38941662f105b57134e0155ec468da294ad` |
| kali-meta | 13 | 181900 | `6af96b4cbc8d1741a8bf859886f1324639175cab` |
| rea | 8614 | 107968149 | `1c90a0fcdb83a6d1178367b0ba2c361613955bd9` |
| wireshark | 9461 | 391171228 | `7f040529364d6d572134867bbb34fd9525306fbf` |

Os números indicam indexação, não auditoria de cada linha. `research/corpus-summary.json` detalha extensões e submódulos não baixados.

## Constatações de código

- **K01** Kali compõe perfis por metapacotes; não é um único aplicativo. [Fonte fixada](https://gitlab.com/kalilinux/packages/kali-meta/-/blob/6af96b4cbc8d1741a8bf859886f1324639175cab/debian/control#L421); `debian/control:421`.

- **K02** Hydra integra pelo menos um perfil declarado dos metapacotes. [Fonte fixada](https://gitlab.com/kalilinux/packages/kali-meta/-/blob/6af96b4cbc8d1741a8bf859886f1324639175cab/debian/control#L253); `debian/control:253`.

- **K03** Wireshark integra pelo menos um perfil declarado dos metapacotes. [Fonte fixada](https://gitlab.com/kalilinux/packages/kali-meta/-/blob/6af96b4cbc8d1741a8bf859886f1324639175cab/debian/control#L1156); `debian/control:1156`.

- **K04** A construção da imagem delega trabalho ao live-build; não foi construída uma ISO. [Fonte fixada](https://gitlab.com/kalilinux/build-scripts/live-build-config/-/blob/adb2e38941662f105b57134e0155ec468da294ad/build.sh#L332); `build.sh:332`.

- **W01** O README declara GPLv2 e ressalva licenças por componente. [Fonte fixada](https://gitlab.com/wireshark/wireshark/-/blob/7f040529364d6d572134867bbb34fd9525306fbf/README.md#L220); `README.md:220`.

- **W02** A leitura de capturas tem um ponto de entrada explícito em file.c. [Fonte fixada](https://gitlab.com/wireshark/wireshark/-/blob/7f040529364d6d572134867bbb34fd9525306fbf/file.c#L524); `file.c:524`.

- **W03** TShark chama o motor EPAN para dissecação. [Fonte fixada](https://gitlab.com/wireshark/wireshark/-/blob/7f040529364d6d572134867bbb34fd9525306fbf/tshark.c#L3604); `tshark.c:3604`.

- **W04** O motor EPAN expõe a operação de dissecação. [Fonte fixada](https://gitlab.com/wireshark/wireshark/-/blob/7f040529364d6d572134867bbb34fd9525306fbf/epan/epan.c#L818); `epan/epan.c:818`.

- **W05** dumpcap contém o fluxo de aquisição separado da interface. [Fonte fixada](https://gitlab.com/wireshark/wireshark/-/blob/7f040529364d6d572134867bbb34fd9525306fbf/dumpcap.c#L4319); `dumpcap.c:4319`.

- **H01** O núcleo registra serviços em uma tabela; isso permite estudar a interface entre núcleo e módulos. [Fonte fixada](https://github.com/vanhauser-thc/thc-hydra/blob/707c822e88938c526279fcabc10a8a265bbc53c4/hydra.c#L461); `hydra.c:461`.

- **H02** O núcleo contém persistência de estado para retomada. [Fonte fixada](https://github.com/vanhauser-thc/thc-hydra/blob/707c822e88938c526279fcabc10a8a265bbc53c4/hydra.c#L689); `hydra.c:689`.

- **H03** O projeto declara AGPLv3; preservar licença e direitos dos autores. [Fonte fixada](https://github.com/vanhauser-thc/thc-hydra/blob/707c822e88938c526279fcabc10a8a265bbc53c4/README#L9); `README:9`.

- **R01** O guia REA dispensa a ferramenta para análise ordinária de repositório fonte. [Fonte fixada](https://github.com/morluto/REA/blob/1c90a0fcdb83a6d1178367b0ba2c361613955bd9/.agents/skills/reverse-engineer-anything/SKILL.md#L3); `.agents/skills/reverse-engineer-anything/SKILL.md:3`.

- **C01** O próprio projeto diferencia clean room de isolamento do sistema operacional. [Fonte fixada](https://github.com/storytold/craft-anything/blob/88d1d9cac852aec1c7fd97886db451e005e49d2a/README.md#L143); `README.md:143`.

- **C02** O workspace declara MIT OR Apache-2.0. [Fonte fixada](https://github.com/storytold/craft-anything/blob/88d1d9cac852aec1c7fd97886db451e005e49d2a/Cargo.toml#L8); `Cargo.toml:8`.

## Evidências de execução das ferramentas

REA 6.9.0 foi executado sobre 11 scripts inline extraídos do HTML recebido da página Wireshark. Registro: `ev_9a5bde89d723d4b96cf81046ba0a3707e5a83121524be811eb490fd19895eba8`. O resultado é análise sintática estática; não demonstra comportamento de navegador, backend, TShark ou Wireshark. Scripts externos e páginas internas não foram recuperados. O HTML usa atributos de geração Astro; isso descreve a página recebida, não o aplicativo nativo.

Craft Anything 0.6.1 executou `core-archive-show` em modo Deep nos quatro ZIPs de produto/composição, lendo e verificando inventários. Os resultados completos são preservados; inventário não equivale a reconstrução funcional. Não foi executado `rebuild`.

## Questões e situação

| Questão | Situação | Evidência ou próximo passo |
|---|---|---|
| Quais fontes foram obtidas? | Respondida no recorte | Lock, ZIPs e inventários SHA-256 |
| Como Kali agrupa ferramentas? | Parcialmente respondida | Metapacotes e live-build; resolver fechamento de dependências por arquitetura |
| Como Wireshark separa leitura e dissecação? | Parcialmente respondida | file.c, tshark.c e epan; executar corpus de capturas sintéticas |
| Como Hydra organiza módulos e retomada? | Parcialmente respondida | Tabela de serviços e persistência; não houve execução |
| O produto proposto é inovador e competitivo? | Hipótese | Entrevistas, comparação adicional e métricas de protótipo |
| Há vulnerabilidades confirmadas? | Não avaliado | Nenhuma vulnerabilidade foi demonstrada |
| Houve varredura de todo o Kali? | Não | ISO, kernel e fontes de todos os pacotes não foram adquiridos |

## Limitações materiais

Página Kali: HTTP 403, sem tentativa de contorno. Fontes oficiais Kali obtidas pelo GitLab. A clonagem é rasa: árvore do commit, sem histórico completo. Git LFS não foi hidratado e submódulos não foram baixados recursivamente. Não houve compilação dos alvos, decompilação de binários, análise de RAM, execução de Hydra, captura de tráfego, benchmark, revisão CVE ou prova de equivalência. Os resultados não estabelecem segurança, desempenho, ausência de falhas, compatibilidade ou conformidade jurídica do futuro produto.

A continuação Nmap/sqlmap está em `NMAP-SQLMAP.md`. O lock e a síntese de corpus atuais já abrangem nove repositórios; a tabela acima registra a primeira rodada de seis.
