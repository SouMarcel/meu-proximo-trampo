# Quickstart: validar a busca agendada e a retomada

Pré-requisitos: `.venv` pronto, `config.json` com cargos, dashboard parado. Rode tudo da raiz.

## 1. Testes automáticos

```text
.venv\Scripts\python.exe -m unittest discover -s tests
```

Devem passar `tests/test_agendamento.py` (relógio e portal falsos) e `tests/test_espera_env.py`, além dos testes dos
portais. Cenários cobertos:

- hora devida dentro de 15 min roda uma vez; fora disso, "perdida"; a mesma data não roda duas vezes (US1-1, US1-2);
- busca manual concluída às 07:30 pula a das 08:00; às 03:00, não pula (US1-3);
- retomada rodando às 08:00: a agendada espera e roda depois, e apaga as retomadas (US1-4, US2-6);
- portal falso que bloqueia na 3ª consulta: `faltaram` com a 3ª em diante; a retomada, depois de 6 h no relógio
  falso, roda só elas e as descrições pendentes; sem bloqueio, a retomada some (US2-1, US2-2, US2-4);
- bloqueio de novo: `proxima` + 6 h e `tentativas` + 1; portal ainda em espera na hora: pulada (US2-3, FR-007);
- servidor "desligado" (tick só depois de 7 h): tentativa perdida, próxima 6 h depois da perdida;
- sem agendamento ligado, a retomada some 24 h depois de criada; caixa desmarcada apaga todas;
- `<PORTAL>_ESPERA`: ausente = 360; 30 vira 60 com aviso; 5000 vira 2880; "abc" usa o padrão com aviso.

## 2. Busca agendada de verdade (branch pessoal)

1. Abra o dashboard (`python iniciar.py`), Filtros da busca → aba Agendamento: ligue, horário daqui a 2 minutos,
   marque "Continuar de onde parou", salve.
2. Sem clicar em nada: a busca começa até 1 min depois do horário, o andamento diz "Busca agendada", e no fim o quadro
   mostra "Hoje: rodou às HH:MM" e a próxima (amanhã). (SC-001)
3. Mude o horário para daqui a 2 minutos de novo: nada roda (a data de hoje já consta).

## 3. Retomada (branch pessoal)

1. Com o LinkedIn ligado e bloqueando (o caso de hoje), deixe a busca agendada ou uma manual terminar.
2. O quadro mostra "LinkedIn retoma às HH:MM", com o número de consultas e descrições que faltam, e o botão Cancelar.
3. Para não esperar 6 h: ponha `LINKEDIN_ESPERA=60` no `.env` e confira que a espera mostrada encurta; a retomada
   continua marcada para 6 h depois do bloqueio (a espera de 60 min só deixa o portal livre antes).
4. Para testar a execução sem esperar, edite `proxima` em `.cache/retomadas.json` para 1 minuto à frente: a retomada
   roda, o andamento diz "Retomada do LinkedIn", e as vagas que ganharem descrição recebem nota. (SC-002)
5. Cancelar no quadro tira a retomada; desmarcar a caixa tira todas.

## 4. Terminal

```text
.venv\Scripts\python.exe vagas.py agendamento
.venv\Scripts\python.exe vagas.py agendamento --ligar 25:00     (sai com código 2)
```

## 5. Portais com login

Com o MyGreenhouse ligado e conectado, a busca agendada roda sem ele, e o resultado traz o aviso. (FR-005)
