# Quickstart: validar a Nerdin na busca

Rodar da raiz da worktree (ou da pasta principal, na branch pessoal). `PY` = `.venv\Scripts\python.exe`.

## 1. Testes sem rede

```powershell
PY -m unittest discover -s tests
```

Esperado: tudo passa, incluindo `tests/test_nerdin.py` (cards, modelo, salário "a combinar", janela, paginação,
filtro de título e de cidade, bloqueio sem nova tentativa, `descrever` pelo JSON-LD, `id_do_link`) e o padrão de
portais com a Nerdin.

## 2. Busca real pequena (com o OK da pessoa)

```powershell
PY vagas.py buscar --fontes nerdin --janela-horas 72
```

Esperado: vagas com etiqueta Nerdin, título que bate com os cargos, empresa, data, modelo e link
`nerdin.com.br/vaga_emprego/...`. Abrir 2 links no navegador e conferir que são as vagas certas. Sem aviso de erro.

## 3. Ligada por padrão

Com um `config.json` sem a chave `fontes` (cópia temporária fora do Git), a busca consulta Indeed, Gupy e Nerdin;
`filtros.efetivos({})["fontes"]` devolve `["indeed", "gupy", "nerdin"]`.

## 4. Página (na branch pessoal)

1. Merge da branch na branch pessoal; acrescentar `nerdin` em `fontes` no `config.json` pessoal (com o OK da pessoa).
2. Reiniciar o dashboard (`--sem-navegador`) e abrir pelo Live Server.
3. "Filtros da busca" → Portais: Nerdin aparece com a linha de termos; desmarcar e marcar muda o contador.
4. Buscar vagas: vagas da Nerdin no Relatório com a bolinha âmbar; descrição lida nas candidatas.
5. Adicionar Vaga com um link da Nerdin: portal "Nerdin", título, empresa e descrição preenchidos.
