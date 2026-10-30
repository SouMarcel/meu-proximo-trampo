# Implementation Plan: Vagas sem análise sempre à vista, com a caixa "Analisadas"

**Branch**: `038-vagas-analisadas` (worktree `../mpt-038-vagas-analisadas`, saída da `master`; front na
`frontend-react`, worktree `../mpt-front-027b`) | **Date**: 2026-10-29 | **Spec**: [spec.md](spec.md)

## Summary

Tudo na página, em `src/components/TriageReport.tsx`, mais um campo nas preferências guardadas
(`src/services/storage.ts`):

- **Estado `soAnalisadas`**:
  - vem de `prefs.analisadas` e é salvo com os outros filtros em `saveTriagePreferences`;
  - `ScreenPreferences` ganha `analisadas?: boolean`.
- **Visível pela caixa**: `visivel(v) = !soAnalisadas || temNota(v)`. A regra `temNota` é a mesma do selo, então a nota
  provisória conta como analisada.
- **Números das abas** (`counts`) e **"Marcar todas"**: só contam as vagas visíveis.
- **Lista da aba** (`daTriagem`): as vagas da aba que estão visíveis.
- **Filtros** (`lista`):
  - a busca por texto vale para todas;
  - a vaga sem nota passa direto pelos outros filtros: Senioridade, Modo, Nota mínima e Publicada há até.
- **`filtrando`** inclui a caixa, e `limparFiltros` a desmarca. A linha "Mostrando X de Y" ganha "(N sem análise
  ocultas)" quando a caixa esconde alguma vaga da aba.
- **A caixa**: `<label title="Oculta as vagas ainda sem análise"><input type="checkbox"> Analisadas</label>`, na linha
  dos filtros secundários, depois de "Publicada há até".
- **README**: a frase dos filtros do Relatório ganha a caixa e a regra das vagas sem nota.

Não há dado novo, rota nova nem mudança no servidor. Por isso `data-model.md` e `contracts/` não se aplicam.

## Technical Context

- **Language/Version**: React 19 e TypeScript 5 na `frontend-react`. O README fica na `master`.
- **Primary Dependencies**: nenhuma nova.
- **Storage**: a preferência fica no `localStorage` do navegador, na mesma chave dos filtros do Relatório
  (`TRIAGE_FILTROS`).
- **Testing**: `tsc --noEmit` e `vite build`; `python -m unittest discover -s tests` (sem mudança no Python); teste
  do usuário na página.
- **Target Platform**: dashboard local, temas claro e escuro, celular.
- **Constraints**: as preferências antigas, sem `analisadas`, valem como caixa desmarcada.
- **Scale/Scope**: 2 arquivos do front e 1 parágrafo do README.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Preferência só no navegador; nada sai do computador. |
| II. Pública | ✅ Comportamento genérico. |
| III. Simples | ✅ Sem dependência; sem IA. |
| IV. Só fatos | ✅ Não toca em texto nem em nota. |
| V. A pessoa decide | ✅ A caixa só mostra ou oculta. "Marcar todas" passa a não marcar vaga escondida (FR-004), o que reforça a decisão da pessoa. |
| VI. Portais | ✅ Não toca em portal. |

Resultado: passa. Não há desvio, e a conferência foi refeita depois do desenho.

## Project Structure

```text
specs/038-vagas-analisadas/  spec.md, plan.md, research.md, quickstart.md, tasks.md, checklists/requirements.md
README.md                    # filtros do Relatório

frontend-react (../mpt-front-027b):
src/services/storage.ts                 # ScreenPreferences.analisadas
src/components/TriageReport.tsx         # soAnalisadas, visivel, counts, lista, Marcar todas, a caixa
```

**Structure Decision**: o front fica numa branch `front-038-vagas-analisadas` saída da `frontend-react`. A spec e o
README ficam na `038-vagas-analisadas`. A entrega segue a ordem de sempre:
1. teste na branch pessoal;
2. com o OK, merge na `master`;
3. Action do front e PR.

## Complexity Tracking

Sem desvios.
