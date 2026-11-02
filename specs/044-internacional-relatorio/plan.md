# Implementation Plan: Aba Internacional com o layout do Relatório de Vagas

**Branch**: `044-internacional-relatorio` (worktree saída da `master`) | **Date**: 2026-11-02 | **Spec**: [spec.md](spec.md)

## Summary

A aba Internacional passa a usar o mesmo componente do Relatório de Vagas (research D1):

- **Front** (`frontend-react`):
  - o `TriageReport` ganha `area="internacional"`, com a linha compacta, os filtros de moeda e visto, os botões de
    filtros e prontidão, os extras do cartão e as preferências numa chave própria (D2 a D8);
  - o App usa o `TriageReport` nas duas abas;
  - o `InternationalHub.tsx` é apagado.
- **Servidor, busca e gravação**: sem mudança.
- **Documentos**: README e `dash/README.md` descrevem a aba nova.

## Technical Context

**Language/Version**: TypeScript e React na `frontend-react`. Python 3.10+ sem mudança.

**Primary Dependencies**: nenhuma nova.

**Storage**: só a preferência de tela nova no navegador (`mpt_pref_internacional_filtros`, data-model). Nada no banco
nem no `config.json`.

**Testing**:
- `tsc --noEmit` e `vite build`;
- `python -m unittest discover -s tests` (sem teste novo: o Python não muda);
- a conferência por CDP com o Edge sem janela, só com leituras e trocas de aba, ordem e filtro, sem botão que grava
  (D9);
- o roteiro do quickstart, feito pela pessoa na branch pessoal.

**Target Platform**: Windows primeiro; dashboard local em `127.0.0.1:8765`.

**Project Type**: ferramenta local (CLI + servidor HTTP + página React).

**Constraints**:
- o Relatório de Vagas nacional não muda para a pessoa, e os filtros guardados dele continuam valendo (D2);
- nenhum pedido novo ao servidor ou a portal;
- tudo o que a aba Internacional mostra hoje continua (spec SC-003).

**Scale/Scope**:
- front: `TriageReport.tsx`, `App.tsx`, `services/storage.ts` e o `InternationalHub.tsx` apagado;
- documentos: 2.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ A preferência nova fica no navegador da pessoa; nada sai do computador. |
| II. Pública, sem dados pessoais | ✅ Só tela; nenhum dado da pessoa no código ou nos documentos. |
| III. Simples, sem IA obrigatória | ✅ Sem dependência nova. A aba funciona sem IA (as vagas sem nota aparecem com a situação). O front segue o fluxo de build da spec 025. |
| IV. Só fatos | ✅ A tela mostra só o que a vaga traz (nota, motivo, país, contratação, sinais). |
| V. A pessoa decide | ✅ Os botões gravam o mesmo que hoje, só no clique dela. Marcar todas pede o segundo clique. |
| VI. Respeito aos portais | ✅ Nenhum pedido a portal. |
| Fluxo | ✅ Spec aprovada em 2026-11-02. A pessoa pediu para seguir direto até o teste na branch pessoal; master e push esperam o OK dela. |

Resultado: **passa**, sem emenda. Depois do desenho, a conferência dá o mesmo resultado: só tela, sem gravação nova,
pedido ou dependência.

## Project Structure

```text
specs/044-internacional-relatorio/  spec.md, plan.md, research.md, data-model.md, contracts/aba-internacional.md,
                                    quickstart.md, tasks.md (próxima etapa), checklists/requirements.md

README.md        # "Vagas internacionais": a aba com as abas internas, a ordem e os filtros
dash/README.md   # a aba Internacional no mesmo desenho do Relatório de Vagas

frontend-react (numa worktree ao lado da pasta do projeto):
  src/components/TriageReport.tsx       # area; linha compacta; moeda e visto; botões; extras do cartão
  src/components/InternationalHub.tsx   # apagado
  src/services/storage.ts               # chave da Internacional; moeda e visto em ScreenPreferences
  src/App.tsx                           # TriageReport nas duas abas
```

**Structure Decision**:
- Um componente para as duas abas, com `area` (D1). A nacional usa o padrão e não precisa mudar a chamada, além do que
  já recebe.
- O `CONTRATACAO`, o `paisDe` e os ícones que hoje estão no `InternationalHub` passam a ser importados no
  `TriageReport`.
- O App continua dono das listas e dos botões que gravam. Só troca o componente da aba Internacional e passa
  `onAbrirFiltrosInternacional` e `onAbrirProntidao`.

## Entrega (como nas specs anteriores)

1. Commit local na `044-internacional-relatorio` e na `frontend-react`.
2. Merge da `044-internacional-relatorio` na branch pessoal; o build do front copiado para `dash/front/` sem commit; o
   dashboard reiniciado para a pessoa testar.
3. Com o OK:
   - busca de dados pessoais no diff;
   - merge na `master` e push, só com os testes passando;
   - push da `frontend-react`, `gh workflow run front.yml` e merge do PR `front/atualizacao` com squash;
   - `git merge origin/master` na branch pessoal;
   - apagar a worktree e a branch;
   - `graphify update .`.
