# Quickstart: verificação da IA com reserva (Windows)

Rode tudo na raiz da worktree (`..\meu-proximo-trampo-032`), com `PY` = `..\meu-proximo-trampo\.venv\Scripts\python.exe`.

## 1. Testes sem rede

```powershell
PY -m unittest tests.test_ia_reserva -v
PY -m unittest discover -s tests
```

Esperado: tudo passa. Cenários (contratos em [contracts/ia.md](contracts/ia.md)):
- a principal responde 503 e a reserva responde, com o aviso e a marca da reserva;
- a principal funcionando: zero chamadas à reserva;
- todas falham: o erro lista cada uma;
- uma IA só: a mensagem de hoje;
- reserva sem chave pulada;
- validação (até 3, sem repetida, sem "Sem IA");
- formato antigo;
- situação gravada e o alerta;
- `testar` com uma IA só;
- marca por thread.

## 2. Na branch pessoal de teste

1. Merge na branch de teste e reinício do dashboard (`--sem-navegador`).
2. Configuração do usuário: Gemini (`gemini-3.8-flash`) como principal e OpenRouter (`openrouter/free`) como reserva,
   pelo painel IA (depois do front) ou pelo `PUT /api/ia`.
3. Com o Gemini fora (ou simulando com um modelo inexistente na principal): "Preencher esta página" na candidatura
   assistida preenche com a reserva e mostra o aviso com o motivo.
4. O botão IA mostra o alerta da principal, e o painel mostra a situação de cada IA. O "Testar a sequência" dá uma
   linha por IA.
