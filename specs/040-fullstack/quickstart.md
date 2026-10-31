# Quickstart: verificar a FullStack na busca

Na worktree `../mpt-039-ey`, com o `.venv` da pasta principal (`PY` = `..\meu-proximo-trampo\.venv\Scripts\python.exe`).

1. **Testes sem rede**: `PY -m unittest tests.test_fullstack` e depois `PY -m unittest discover -s tests`.
2. **Desligada por padrão**: config sem a lista de portais → `PY vagas.py buscar` não faz pedido à FullStack; o painel
   mostra a FullStack desligada, com o resumo dos termos.
3. **Busca real pequena**: `PY vagas.py buscar --fontes fullstack` com um cargo de tecnologia (ex.: "engineer").
   - Esperado: vagas com a etiqueta "FullStack", "Remoto", data e descrição; nenhuma vaga repetida por cidade.
   - Nenhum e-mail de recrutador nas vagas gravadas.
4. **Ordem por data**: confirma research D3 (a lista para na janela).
5. **Adicionar Vaga**: colar `talent.fullstack.com/jobs/<id>` → mesma vaga, com o id `fullstack-<jobId>`.
6. **Espera simulada**: um `.cache/fullstack-espera.json` recente → a busca pergunta antes de seguir sem a FullStack
   (código 5) e o Adicionar Vaga não faz pedido.
7. **Página**: a etiqueta "FullStack" no Relatório (depois do PR do front).
