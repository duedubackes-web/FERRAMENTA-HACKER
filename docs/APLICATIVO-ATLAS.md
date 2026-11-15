# Atlas — aplicativo local v0.2.0

Atlas transforma a base FERRAMENTA-HACKER em um aplicativo web local com projetos, evidências, decisões, chat e estúdio de produto. O código do aplicativo é próprio; as fontes de pesquisa continuam com suas licenças e proveniência.

## Iniciar

Requer Python 3.11+ com SQLite (incluído nas distribuições usuais do Python). A execução padrão não precisa de npm, chave de API, serviço externo ou instalação de ferramentas de pentest.

```sh
python scripts/app_server.py
```

Abra **http://127.0.0.1:8765**. No Windows, também pode usar `start-atlas.bat`; no Linux/macOS, `sh scripts/start_atlas.sh`.
Porta e banco podem ser definidos explicitamente:

```sh
python scripts/app_server.py --port 8766 --database work/meu-workspace.sqlite3
```

O processo permanece aberto até Ctrl+C. Os dados persistem no SQLite em `work/atlas.sqlite3`. Reinicie com o mesmo arquivo para recuperar projetos, fontes, revisões, mensagens, análises e decisões. Não apague esse arquivo para atualizar o código. Faça backup com o aplicativo encerrado; restaurar consiste em apontar `--database` para a cópia íntegra.

## Fluxo completo

1. Explore a demonstração: quatro relatórios sintéticos, oito itens de revisão, nenhum alvo acessado.
2. Crie um projeto e importe seus relatórios: Nmap XML anterior/atual, Trivy JSON v2, ZAP Traditional JSON/Plus.
3. Gere a fila, filtre prioridades e abra fatos/referências de cada item.
4. Registre estado, justificativa e responsável declarado. As decisões anteriores continuam no histórico.
5. Converse com o Assistente Atlas e abra as referências retornadas.
6. Confira a reprodução e exporte o pacote ZIP.
7. Use o estúdio para mapear código-fonte local e gerar um plano, backlog e protótipo original.

Cada papel usa a última fonte importada na próxima revisão. A importação não altera uma revisão existente: a interface sinaliza quando ela ficou anterior às fontes atuais. Fontes antigas ficam preservadas para reprodução. O chat usa o recorte da última revisão gerada, não incorpora silenciosamente novas importações.
Decisões são vinculadas ao registro de revisão e ao item; não são transportadas automaticamente a uma revisão nova. O responsável é um texto declarado, sem autenticação de identidade.

## Dois modos de chat

**Busca local com referências, padrão:** intenções explícitas e recuperação lexical sobre a revisão, tecnologias e registros do estúdio. Não é um LLM, não usa embeddings, não navega na internet e não executa sugestões. Pode responder sobre prioridades, limitações, fontes, regras, ferramentas, estrutura e plano. Quando não encontra suporte, informa a lacuna. Cada resposta indica seu modo.

**IA local, opcional:** adaptador para o endpoint `/api/chat` do Ollama em `http://127.0.0.1:11434`. O modelo precisa estar instalado e em execução na máquina. Consulte [a API oficial](https://docs.ollama.com/api/chat) e use o nome exato de um modelo disponível no seu ambiente:

```sh
# Linux/macOS: substitua o valor pelo nome real do seu modelo instalado.
ATLAS_OLLAMA_MODEL="nome-do-modelo-instalado" python scripts/app_server.py
```

PowerShell:

```powershell
$env:ATLAS_OLLAMA_MODEL="nome-do-modelo-instalado"
python scripts/app_server.py
```

Selecione “Usar IA local” no chat. A configuração detectada não significa que o motor esteja acessível: indisponibilidade retorna erro explícito, sem simular uma resposta. Nenhum modelo é baixado pelo Atlas.
A IA recebe a pergunta, até três trocas recentes (com textos limitados) e até 16 mil caracteres do contexto selecionado, com orçamento de 900 tokens de geração e timeout de 60 segundos. Não recebe os relatórios brutos nem ferramentas executáveis. Não segue redirecionamentos, não usa proxy e só conecta ao endereço loopback fixo. As referências indicam o contexto fornecido; não comprovam automaticamente o texto gerado. A resposta é exibida como texto inerte e marcada como geração não validada.

A integração foi verificada com resposta e falha simuladas do transporte; não houve teste com um modelo real instalado, nem avaliação de qualidade de IA nesta entrega.

## Tecnologias dentro do chat

| Tecnologia | Integração nesta versão |
|---|---|
| Kali Linux | Catálogo e fontes indexadas; distribuição e pacotes não instalados |
| REA | Pesquisa e evidências documentadas; runtime não embutido |
| Craft Anything | Pesquisa e evidências documentadas; runtime não embutido |
| Nmap | Importação e comparação XML offline; scanner não executado |
| Trivy | Importação de campos selecionados JSON v2 |
| ZAP | Importação de campos selecionados Traditional JSON/Plus |

As fichas da interface e do chat usam `research/app-capabilities.json`. O catálogo de 38 tecnologias mantém as fontes e os limites de cada registro. “Embutir uma tecnologia” não é usado como sinônimo de simplesmente mencionar seu nome.

## Estúdio e produção própria

Envie um ZIP local de código-fonte: até 16 MiB comprimidos, 2.000 entradas, 32 MiB totais descomprimidos e 2 MiB por arquivo. Caminhos inseguros, duplicatas, links simbólicos, criptografia e compressão excessiva são recusados. A aplicação lê bytes limitados e verifica CRC, sem extrair em disco nem executar o conteúdo.
O resultado guarda inventário, hashes, linguagens por extensão, candidatos a entrada/licença, manifestos e dependências declaradas em `package.json`. Não é análise semântica de todo o software, engenharia reversa de binários, auditoria completa de dependências ou decisão sobre direitos de reutilização. O ZIP recebido não é persistido; apenas o mapa derivado é guardado.

Com nome e brief, o estúdio gera um plano baseado em template explícito, vinculado ao último mapa quando presente. A exportação contém:

- `product-plan.json`, `BACKLOG.md`, `README.md` e mapas de fontes;
- `prototype/index.html`, `prototype/app.css`, `prototype/app.js` e instruções;
- um quadro de tarefas funcional com adicionar, concluir, remover, restaurar e persistir no navegador;
- chat local sobre o brief e o backlog, sem alegação de IA generativa no protótipo.

Para usar o protótipo, extraia a exportação, entre na pasta `prototype` e execute:

```sh
python -m http.server 8787 --bind 127.0.0.1
```

Abra http://127.0.0.1:8787. Dados do protótipo ficam no armazenamento do navegador, não no SQLite do Atlas. O código gerado é um template próprio, não código arbitrário produzido pelo modelo nem clone dos motores de Lovable, Vercel ou v0. As trilhas de inspiração são hipóteses de produto; não afirmam equivalência funcional, novidade de mercado ou análise de sistemas privados.

## Exportação e armazenamento

A exportação da investigação inclui revisão JSON/HTML, hashes e metadados das fontes, reprodução, histórico de decisões, histórico completo de chat e registros do estúdio. Não inclui relatórios originais por padrão. Marque a opção explícita para incluir os originais usados na revisão em `originals/`.
A interface mostra as últimas 50 trocas de chat; a exportação e o backup SQLite preservam o conjunto completo até exclusão do projeto.
Fontes e derivados podem conter informações sensíveis. A minimização de ZAP não é anonimização completa. Excluir um projeto remove seus registros por cascata; exportações e backups independentes permanecem, e exclusão lógica não é apagamento forense do disco.

## Alcance da versão

Esta é uma versão local para um único usuário, acessível somente por `127.0.0.1`. Host e origem são validados; a sessão tem cookie HttpOnly/SameSite e mutações exigem token CSRF. Há CSP, saídas de texto inertes, consultas parametrizadas e limites de requisição. A interface não oferece shell, execução de motores nem navegação automática de alvos.
O arquivo SQLite não é criptografado pelo aplicativo. Qualquer pessoa com acesso à conta do sistema operacional pode ler os dados. O servidor padrão não fornece autenticação multiusuário, TLS, isolamento entre contas, cobrança, publicação em nuvem ou suporte operacional. Não o exponha por proxy como um SaaS: isso exige uma camada de operação própria e verificações adicionais.

## Verificar

```sh
python -m unittest discover -s tests
python scripts/workbench.py verify
```

Os testes opcionais de interface exigem Node compatível com `package.json`, atualmente a linha 22 a partir de 22.22.2, 24 a partir de 24.15 ou 26+:

```sh
npm ci --ignore-scripts
npm run check:ui
npm run test:ui
```

O fluxo usa DOM simulado e servidor HTTP real em porta efêmera. Verifica operações, persistência, chat, referências e downloads; não mede layout, acessibilidade visual ou comportamento de um navegador real. A sessão de desenvolvimento não tinha controle de navegador disponível, portanto essa validação visual permanece pendente.

## Manutenção e diagnóstico — v0.1.1

O botão **✓ Verificar workspace**, no cabeçalho, confere o manifesto dos arquivos, executa `quick_check`/`foreign_key_check` no SQLite e consulta a disponibilidade do modelo opcional. Também é possível verificar pelo terminal, sem iniciar o servidor:

```sh
python scripts/app_server.py --check --database work/atlas.sqlite3
```

Código de saída 0: verificações concluídas sem pendências; 1: resultado com atenção; 2: erro ao iniciar/acessar os recursos. A opção inicializa um banco novo quando o caminho ainda não existe, assim como a inicialização normal do aplicativo.
Nenhum checksum é regravado pelo diagnóstico e nenhum modelo é baixado. A consulta de modelos usa apenas `/api/tags` no Ollama loopback, com timeout de três segundos. Sem modelo configurado, a busca local continua disponível e nenhuma conexão é feita com Ollama. `ready` informa presença na lista; não testa inferência ou qualidade.

Para atualizar uma instalação: encerre o servidor, preserve uma cópia do arquivo SQLite e de exportações necessárias, execute `git pull --ff-only`, confira `python scripts/workbench.py verify` e reinicie com o mesmo `--database`. O banco permanece no esquema 1 nesta atualização, sem migração de dados. Diretórios `work/` e bancos/journals são ignorados pelo Git.

Correções da v0.1.1: respostas atrasadas não substituem a seleção atual de projeto; perguntas do chat preservam regras e recorte por produtor; fichas de tecnologia não substituem referências a fontes/limites por coincidência de nome; exportações conferem a mesma revisão incluída no ZIP, mesmo quando outra revisão é gerada durante a operação.

## Evolução das revisões — v0.2.0

A fila agora lista quantas revisões estão salvas e permite compará-las. O chat consulta as duas mais recentes ao perguntar “O que mudou?”. A exportação inclui a baseline e a comparação quando disponíveis, com originais opcionais de ambos os lados. Consulte [o contrato da comparação](EVOLUCAO-REVISOES.md). O esquema SQLite continua 1.
