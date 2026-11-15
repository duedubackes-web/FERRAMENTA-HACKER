# Importar um relatório Nmap existente

Requer Python 3.11+; não requer instalação do Nmap, credenciais ou acesso à rede.

```sh
mkdir -p work
python scripts/workbench.py import-nmap tests/fixtures/nmap-synthetic.xml --output work/nmap-report.json
```

Para usar um relatório próprio, substitua o caminho do XML. Sem `--output`, o JSON é escrito na saída padrão.
O destino precisa ter diretório existente; um arquivo existente nunca é sobrescrito. O XML original é lido e preservado.

## Contrato v1

`schema_version: 1` e `artifact` guardam formato, tamanho, caminho absoluto e SHA-256 dos bytes originais.
`analysis_run` identifica o adaptador e sua versão; o ID é determinístico para a mesma entrada e não representa uma nova execução do Nmap.
`producer` guarda versão e conclusão declaradas no XML. `coverage` inclui scaninfo e contagens, sem afirmar cobertura real da rede.
`hosts` inclui status, endereços, hostnames, portas, estado, atributos de serviço e extraports.
`warnings` e `limitations` acompanham dados incompletos e campos não interpretados.

A confiança de um serviço é a string fornecida pelo produtor, não uma certeza atribuída pelo importador.
Entradas de varredura de protocolo IP retêm `protocol` e o identificador numérico no campo `port`; interprete o número junto ao protocolo.
Porta ausente significa não observada neste recorte, não fechada. Um XML bem formado sem hosts não prova ausência de ativos.

UTF-8/US-ASCII, entrada máxima de 32 MiB; sem validação completa do DTD Nmap.
DOCTYPE simples é aceito; entidades customizadas, DTD externa/interna e outras codificações são recusadas.
Scripts e estilos mencionados no XML nunca são executados ou buscados. Corpos de scripts, fingerprint de SO, traces e metadados aninhados de serviços não são interpretados nesta versão.
O JSON pode conter endereços e nomes presentes no arquivo de entrada; escolha onde salvá-lo e compartilhá-lo.
