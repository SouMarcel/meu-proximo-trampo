# Quickstart: verificação do JobGether (Windows)

Rode tudo na raiz da worktree (`..\meu-proximo-trampo-030`), com o Python do projeto (`PY` =
`..\meu-proximo-trampo\.venv\Scripts\python.exe` ou o `.venv` da worktree).

## 1. Testes sem rede

```powershell
PY -m unittest tests.test_jobgether -v
PY -m unittest discover -s tests
```

Esperado: tudo passa. Cenários cobertos pelos testes (contrato em [contracts/jobgether.md](contracts/jobgether.md)):
- lista com vagas que batem e que não batem com o cargo;
- janela de tempo que corta a segunda página;
- `hasMore` falso;
- consulta da cidade e de mudança, sem pedido;
- local do país, `anywhere` e `includeHybrid`;
- 400 de local desconhecido;
- 403 e 429 com espera e zero pedidos a mais;
- pausa padrão, pelo `.env`, abaixo do mínimo e inválida;
- portal desligado, sem pedido;
- `id_do_link` e vaga republicada com o mesmo id;
- Adicionar Vaga com o id do link.

## 2. Busca real pequena

```powershell
PY vagas.py buscar --fontes jobgether
```

Faça isso com um cargo em inglês no `config.json` da worktree (ex.: "project manager"), o Brasil e a busca remota.

Esperado:
- poucas vagas com a etiqueta "JobGether";
- local "Remoto (… Brazil …)" ou "Anywhere";
- link para `jobgether.com/offer/…`;
- nenhum erro, e o aviso de pausa só com `JOBGETHER_PAUSA` definida;
- uma segunda busca logo depois não traz de novo as mesmas vagas.

## 3. Página

1. Reinicie o dashboard (`python iniciar.py --sem-navegador`).
2. No painel "Filtros da busca", o JobGether aparece desligado, com o resumo dos termos.
3. Cole no Adicionar Vaga um link `https://jobgether.com/offer/<id>-<slug>`. O formulário abre com a plataforma
   JobGether. Ao salvar, a vaga fica com o id `jobgether-<id>`.
4. No detalhe de uma vaga do JobGether, a etiqueta e a cor do portal aparecem. Isso depende do PR do front.

## 4. Bloqueio (simulado nos testes)

Com `.cache/jobgether-espera.json` recente, `PY vagas.py buscar --fontes jobgether` sai com código 5 e pergunta antes
de seguir sem ele. `--confirmar-espera` segue sem pedido ao JobGether.
