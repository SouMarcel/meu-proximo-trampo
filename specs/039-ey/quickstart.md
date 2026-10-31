# Quickstart: verificar a EY na busca

Na worktree `../mpt-039-ey`, com o `.venv` da pasta principal (`PY` = `..\meu-proximo-trampo\.venv\Scripts\python.exe`).

1. **Testes sem rede**: `PY -m unittest tests.test_ey` e depois `PY -m unittest discover -s tests` (tudo passa).
2. **Busca real pequena**: `PY vagas.py buscar --fontes ey` com um cargo comum na EY (ex.: "desenvolvedor").
   - Esperado: vagas com a etiqueta "EY", data e descrição; o aviso da pausa só com `EY_PAUSA` no `.env`.
   - Repetir a busca: as páginas das vagas já lidas não são abertas de novo (só as listas).
   - `.cache/ey-datas.json` criado, sem dados da pessoa.
3. **Ordem por data**: as datas das vagas lidas vêm da mais nova para a mais antiga (confirma research D2).
4. **Adicionar Vaga**: colar um link `careers.ey.com/ey/job/…/<número>/` → cargo, empresa "EY", data e descrição, com o
   id `ey-<número>`.
5. **Desligada**: tirar "ey" de `fontes` → a busca não faz pedido a careers.ey.com.
6. **Página**: a etiqueta "EY" no Relatório (depois do PR do front).
