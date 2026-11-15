# Trabalhar no repositório existente

O proprietário criou https://github.com/duedubackes-web/FERRAMENTA-HACKER e autorizou continuar o trabalho nele.
A entrega preserva a licença MIT e o histórico inicial; o README inicial foi ampliado com o conteúdo do projeto.

```sh
git clone https://github.com/duedubackes-web/FERRAMENTA-HACKER.git
cd FERRAMENTA-HACKER
python scripts/workbench.py verify
python -m unittest discover -s tests -v
python scripts/workbench.py summary
git switch -c feature/offline-capture-import
```

Para recuperar o código original de referência:

```sh
python scripts/fetch_sources.py --destination work/upstream
```

Os ZIPs completos das fontes ficam fora do Git; o lock fixa origem e commit e a base inclui inventários por arquivo.
`ARTIFACTS.sha256` permite detectar alterações nos arquivos listados da entrega original, mas não substitui autenticação de origem.
Ao alterar os arquivos, atualize esse manifesto de forma intencional usando `python scripts/update_manifest.py` e revise o diff.
Não atualize hashes para ocultar falhas inesperadas: investigue a causa primeiro.
