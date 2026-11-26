# Contrato: `calibrar_nota.py` (desenvolvimento)

```text
PY calibrar_nota.py --medir [ID]            tamanho do pedido de 1 vaga, por parte; sem IA
PY calibrar_nota.py --antes origin/master   regras antigas x atuais, na mesma IA (o modo recomendado)
PY calibrar_nota.py [--amostra 30] [--semente N]
PY calibrar_nota.py --ids ID1,ID2,...       as mesmas vagas de uma calibração anterior
```

## `--medir`

- Sem `ID`: uma vaga com descrição do banco, a de descrição mais longa entre as 20 mais recentes.
- Saída: total e as partes (regras, perfil, filtros, vaga) em caracteres, e "SC-001: PASSA/NÃO PASSA" (≤ 20.000).
- Grava o pedido montado em `.cache/pedido-<ID>.txt` (fora do Git), para conferir à mão.
- Não chama a IA e não grava nada no banco.

## Calibração

- Amostra: vagas com `analise_status` "feita", sem `nota_sem_descricao`, com descrição; espalhada pelas faixas
  (≥ 80, 65–79, 50–64, < 50) e pelas áreas (nacional, internacional); prefere as de `analise_modelo` igual ao da IA
  principal.
- Pedidos de até 3 vagas com `analise.montar_pedido` e `ia.responder`; pausa `ANALISE_PAUSA` entre pedidos; um 429
  espera como a análise automática e, com 3 recusas, para e mostra o que já tem.
- **Nunca grava no banco** nem muda o `config.json`.
- Saída no terminal: uma linha por vaga (id, nota antes → depois, diferença, fora antes/depois, modelo antes) e o
  resumo: respondidas, % com |diferença| ≤ 10, trocas de fora para dentro (e o contrário), "SC-002: PASSA/NÃO PASSA"
  (≥ 90% e nenhuma troca sem motivo; as trocas são listadas para a pessoa julgar o motivo).
- Arquivo: `.cache/calibracao-AAAAMMDD-HHMM.json` (formato em [../data-model.md](../data-model.md)).
- Código de saída: 0 PASSA, 1 NÃO PASSA, 2 sem IA ou sem vagas suficientes.
- `--antes REF` (acrescentado na calibração de 26/11): cada lote vai à mesma IA duas vezes, com o `montar_pedido` e as
  regras da versão REF do Git (`git show REF:dash/analise.py` e os arquivos da skill) e com os atuais; a base da
  comparação é a resposta às regras antigas, não a nota gravada. Custa o dobro de pedidos e mede só as regras. Sem
  `--antes`, o comando avisa quantas notas gravadas vieram de outra IA.
- Sem IA ligada: sai com código 2 e a mensagem.
