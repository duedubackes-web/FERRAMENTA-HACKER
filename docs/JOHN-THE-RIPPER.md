# John the Ripper — fontes, arquitetura e evidências

## Coleta e identidade

Fonte oficial: https://github.com/openwall/john, vinculada ao projeto https://www.openwall.com/john/.
Foi coletada a branch de desenvolvimento `bleeding-jumbo`, no commit `37bebbe4b6442c8dd3888e5848ef062c0783e9f3`.
Esse snapshot não equivale automaticamente à release estável ou à árvore core.

São **2.128 entradas rastreadas** novas. O corpus total passa a **24.995 entradas em nove repositórios**.
O lock registra o ZIP `john-37bebbe4b644.zip` e seu SHA-256 `2f9f3fb793c34296132289ab3bdef8786ba35e5fa97ca10bcf624e42abf95a1f`.
O ZIP preserva os bytes dos arquivos rastreados e fica fora do histórico do projeto. Para recuperar a árvore fixada, use `scripts/fetch_sources.py` em um diretório novo.
Histórico completo, dependências instaladas, resultados de compilação e suporte efetivo no hardware não são inferidos dessa coleta.

## Constatações seletivas

- **J01** A árvore coletada é a variante comunitária jumbo, não uma garantia de equivalência com uma release core. [Arquivo e linha](https://github.com/openwall/john/blob/37bebbe4b6442c8dd3888e5848ef062c0783e9f3/README.md#L10).

- **J02** A licença geral declara GPLv2-ou-posterior; o mesmo texto descreve exceções e termos específicos por componente. [Arquivo e linha](https://github.com/openwall/john/blob/37bebbe4b6442c8dd3888e5848ef062c0783e9f3/LICENSE#L8).

- **J03** A interface de formatos possui um marcador explícito de versão da estrutura. [Arquivo e linha](https://github.com/openwall/john/blob/37bebbe4b6442c8dd3888e5848ef062c0783e9f3/src/formats.h#L24).

- **J04** A estrutura de formato reúne parâmetros, métodos, estado privado e encadeamento. [Arquivo e linha](https://github.com/openwall/john/blob/37bebbe4b6442c8dd3888e5848ef062c0783e9f3/src/formats.h#L420).

- **J05** A gestão de formatos possui uma função de registro explícita. [Arquivo e linha](https://github.com/openwall/john/blob/37bebbe4b6442c8dd3888e5848ef062c0783e9f3/src/formats.c#L452).

- **J06** O ponto de integração do programa reúne o registro dos formatos; condições de configuração/compilação afetam a seleção. [Arquivo e linha](https://github.com/openwall/john/blob/37bebbe4b6442c8dd3888e5848ef062c0783e9f3/src/john.c#L229).

- **J07** A persistência de sessão está separada em recovery.c; não foi testada dinamicamente. [Arquivo e linha](https://github.com/openwall/john/blob/37bebbe4b6442c8dd3888e5848ef062c0783e9f3/src/recovery.c#L234).

- **J08** A própria documentação OpenCL alerta que parte das instruções está desatualizada; elas não foram adotadas como recomendações atuais de drivers. [Arquivo e linha](https://github.com/openwall/john/blob/37bebbe4b6442c8dd3888e5848ef062c0783e9f3/doc/README-OPENCL#L7).

## Mapa de arquitetura

- `src/john.c`: entrada e composição/registro dos formatos.
- `src/formats.h` e `src/formats.c`: contratos de formato e gestão de registro/ciclo de vida.
- `src/recovery.c`: persistência e restauração de sessão, observadas por leitura seletiva.
- `src/` e documentação OpenCL: implementações e caminhos que dependem de build e plataforma; não houve medição de hardware.

O mapa descreve pontos de extensão e responsabilidades, não uma reconstrução completa do fluxo de processamento.
Não foi copiado código do motor para o núcleo MIT do FERRAMENTA-HACKER.

## Catálogo estático de declarações

O novo `scripts/catalog_john.py` lê apenas arquivos C rastreados no primeiro nível de `src/`, confirma o commit e recusa alterações rastreadas no checkout.
Ele remove comentários preservando linhas e coleta definições textuais diretas de `struct fmt_main` e valores literais isolados de `FORMAT_LABEL`.
Não avalia o pré-processador, não compila C e não associa automaticamente cada label a uma estrutura.

Resultado: **380 arquivos com correspondências, 404 definições textuais de estruturas e 366 definições de labels literais**.
Essas contagens não significam 404 algoritmos distintos nem 366 formatos habilitados em um executável.
Expressões de macro, declarações em headers, arrays e diretórios C aninhados ficam fora desse recorte.
O catálogo inclui caminho, linha, hash do arquivo e URL no commit. Não extrai vetores de teste, hashes de senhas, senhas ou listas de candidatos.

## Aplicação real de Craft Anything

Foi reutilizada a CLI 0.6.1 com `--deep core-archive-show --json PARAMETROS_JSON` sobre o ZIP coletado.
Parâmetros: `max_depth=1`, `max_entries=20000`, `limit=20000`, `max_total_bytes=1000000000` e caminho absoluto do ZIP.
O resultado reportou inventário completo de **2.128/2.128 entradas**, sem contêiner aninhado identificado.
Evidência: `ev_02d487eac0afd74b739368e02ef739ca4ea927c0879cc74a5763bbe3e736e2ff`.
Deep significa leitura dos arquivos originais; não se afirma uma implementação clean room independente.

## Aplicação real de REA

Foi reutilizada a CLI 6.9.0 com `inspect-artifact CAMINHO_DO_ZIP --format json`.
O alvo foi o **arquivo de fontes coletadas**, não um executável John. A operação executou a subetapa estática `inventory_artifact`, sem executar o conteúdo.
Evidência principal: `ev_fd9e99f63984bd441ccb80cb7a8de474621df1d43414c52eeb93a71c06e72641`.
A cobertura retornada foi `complete-within-substeps` e a do inventário `container-entries/complete`.
O grafo contém **2.129 ocorrências** contando o ZIP raiz e **2.071 nós** com conteúdo deduplicado. Nós de conteúdo não devem ser contados como arquivos distintos.
As limitações do REA explicam que o inventário ZIP cobre entradas do diretório central; não estabelece semântica específica dos arquivos ou comportamento do programa.
Não foram utilizados Ghidra, Hopper, IDA nem decompilação de um binário do John.

## Corroboração e reprodução

Os conjuntos de **2.128 caminhos** coincidiram entre os três inventários. Craft Anything conferiu os hashes das 2.128 entradas; REA apresentou hashes coincidentes para **2.126 arquivos regulares**.
REA registrou `doc/LICENSE` e `doc/README` como links simbólicos, sem ler seus destinos nem atribuir hashes às entradas. Essa lacuna acompanha a síntese: a cobertura global declarada pelo provedor não elimina a incerteza desses dois registros.
O inventário próprio e o ZIP preservam e verificam o texto dos destinos desses links, sem segui-los.
O resultado está em `research/evidence/john-inventory-crosscheck.json`; evidências completas comprimidas ficam ao lado.
Essa concordância verifica consistência dos bytes coletados, não autenticidade independente do upstream, segurança do código ou força de senhas.

Foi adicionado `scripts/verify_snapshots.py`, que confere tamanho/hash do ZIP, conjunto de entradas e hash de cada arquivo, sem extrair ou executar conteúdo:

```sh
python scripts/verify_snapshots.py /caminho/para/source-snapshots --source john
```

Sem `--source`, ele verifica todos os ZIPs fixados presentes no diretório; um arquivo ausente ou divergente encerra com falha.
Nesta rodada os nove ZIPs foram conferidos, incluindo os registros explícitos dos cinco gitlinks REA não baixados.

Para regenerar o catálogo em uma saída nova:

```sh
python scripts/catalog_john.py /caminho/para/checkout/john --output work/john-catalog.json
```

O destino não é sobrescrito. O diretório precisa existir e o checkout deve estar no commit fixado no lock.

## Licenças

Foram preservados os textos de `LICENSE`, `doc/LICENSE` e `doc/COPYING` do commit coletado. Nas cópias de avisos, `doc/LICENSE` contém o texto da licença à qual o link aponta; o ZIP mantém o link original.
O texto geral declara GPLv2-ou-posterior, com exceção de ligação para OpenSSL/unRAR e menção a termos mais permissivos por componente.
Não se aplica a MIT do projeto a esses materiais. Uma integração ou redistribuição do motor exige considerar os arquivos realmente incorporados e seus termos.

## Decisões para o produto e limites

O padrão de contratos e registro de módulos reforça a opção por adaptadores versionados e evidências com identidade de entrada/build.
Um catálogo de fonte deve ficar separado de um catálogo de capacidades observadas em um executável e hardware específicos.
A persistência de sessão é referência de arquitetura; não foi reproduzida a lógica de processamento de senhas.
Uma eventual integração de auditoria deve começar por metadados e resultados agregados/sanitizados, mantendo a rastreabilidade dos dados efetivamente fornecidos.
Essas escolhas são propostas de engenharia, não prova de inovação de mercado, desempenho ou segurança.

Não houve compilação, benchmark, quebra de hashes, processamento de senhas fornecidas por usuários ou execução de testes do John.
O inventário cobre a árvore rastreada; a revisão semântica foi seletiva. Pesquisa dinâmica em laboratório e avaliação das licenças de componentes específicos permanecem pendentes.
