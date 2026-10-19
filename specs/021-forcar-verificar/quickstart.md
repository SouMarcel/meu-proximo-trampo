# Quickstart: validar o Forçar verificar

`PY` = `.venv\Scripts\python.exe`, da raiz (worktree ou pasta principal na branch pessoal).

## 1. Testes sem rede

```powershell
PY -m unittest discover -s tests
```

Esperado: tudo passa, incluindo `tests/test_forcar.py` (fila com a vaga forçada, sem duplicar, falha que volta o
botão, descrição lida uma vez fora da espera e nenhuma na espera ou durante a busca, nota sem a descrição com a
marca, marca que sai quando o texto chega, rota com 202/409/404/403, `/api/versao` com `verificando` e `falhas`).

## 2. Página (na branch pessoal, com a IA ligada)

1. Reiniciar o servidor (`--sem-navegador`); abrir pelo Live Server.
2. Uma vaga "sem nota" com descrição: clicar em **Forçar verificar** → "Verificando…"; em alguns minutos, a nota.
3. Uma vaga do LinkedIn com descrição pendente:
   - fora da espera: um pedido de descrição (ver na janela do servidor) e a nota sem a marca;
   - na espera: nenhum pedido; nota com "sem a descrição" no selo e o banner no detalhe.
4. Depois de "Completar descrições" (fora da espera), a vaga com a marca volta a "aguardando" e ganha a nota nova.
5. Com a IA desligada no botão IA: o clique mostra "Para dar nota, ligue uma IA" com o atalho.
6. Uma vaga que já tem nota não mostra o botão.
