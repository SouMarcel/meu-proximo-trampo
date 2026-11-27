---
description: "Tarefas da spec 063: Colar e-mail em Atualizar candidaturas"
---

# Tasks: Colar e-mail em Atualizar candidaturas

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md),
[contracts/api.md](contracts/api.md), [quickstart.md](quickstart.md).

**Tests**: pedidos pela spec (SC-001 com 20 e-mails fictícios). Suíte: `.venv\Scripts\python.exe -m unittest discover -s tests`.
Front: `npx -y pnpm@10.34.3 exec tsc --noEmit` e `npx -y pnpm@10.34.3 exec vite build --base ./` na `frontend-react`.

**Delegação**: as tarefas `[D minor]` vão a um funcionário pelo `delegar.py`, com o brief em `delegacao/T00X.md`.

## Format: `[ID] [P?] [D tamanho?] [Story] Description`

## Phase 1: US1 + US2 no servidor (P1)

- [X] T001 [D minor] [US1] → agy, GO na tentativa 1. `dash/colar_email.py` sem IA: `limpar`, `classificar`, `achar`, `propor` (research R2–R5),
  com `tests/dados/emails_candidatura.json` (20 e-mails fictícios, PT/EN/ES, todos os tipos, com o quadro fictício e o
  esperado) e `tests/test_colar_email.py` (SC-001: ≥ 18 de 20; nunca volta etapa; "só anotar"; escolher entre duas da
  mesma empresa; e-mail com instrução à IA vira dado com alerta).
- [X] T002 [D minor] [US1] → copilot, GO na tentativa 1 (corrigi a contagem de aplicados). Em `dash/colar_email.py`: IA no não reconhecido (R6), `aplicar` (data-model, Transições) e
  `LeituraEmail` (guarda a última leitura na memória; `aplicar` usa o conteúdo do servidor); testes com IA falsa.
- [X] T003 [US1] [US2] (feita por mim: pequena) Rotas em `dash/servidor.py` (contracts/api.md): `POST /api/candidaturas/email/ler`,
  `POST /api/candidaturas/email/aplicar`, `GET /api/candidaturas/email/vagas`; só locais; teste de rota com servidor
  de verdade em porta livre.

## Phase 2: Página (frontend-react)

- [X] T004 [D minor] → copilot, GO na tentativa 1 (ajustes meus no aviso ⚠ e no botão dos portais). [US1] [US2] `src/services/api/contas.ts`, `src/components/modals/ColarEmail.tsx` (novo) e
  `src/components/modals/ConnectedAccountsModal.tsx`: área Colar e-mail com aviso, caixas e "+ outro e-mail", Ler,
  propostas no grupo "E-mail" com trecho e ⚠, escolhas de vaga e tipo, Aplicar das duas origens.

## Phase 3: Fechamento

- [X] T005 [US1] Documentação: `dash/API.md` (3.11), `README.md`, `AGENTS.md` (FR-013).
- [X] T006 Validação (validada pela pessoa na branch pessoal em 27/11; Colar e-mail passou a ser o primeiro item do diálogo): suíte inteira, typecheck e build do front, merge na branch pessoal, front copiado para
  `dash/front/` sem commit, dashboard reiniciado; quickstart passos 2 a 6 pela pessoa.

## Dependências

T001 → T002 → T003. T004 depende só do contrato (pode rodar junto de T002/T003). T005 depois de T003. T006 no fim.
