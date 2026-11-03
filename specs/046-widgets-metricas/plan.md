# Implementation Plan: Widgets reorganizáveis no painel Métricas & Funil

**Branch**: `046-widgets-metricas` (worktree saída da `master` com a 045) | **Date**: 2026-11-03 |
**Spec**: [spec.md](spec.md)

## Summary

- **Grade:** os 16 blocos do painel viram widgets numa grade de 12 colunas, com a biblioteca react-grid-layout
  (MIT), só na página (research D1 e D2).
- **Altura:** cada widget acompanha o conteúdo, como hoje, até a pessoa mudar a altura dele. Daí em diante a altura fica
  fixa, e o que passar rola dentro (D3).
- **Organizar painel:** liga o modo de edição. Nele, a pessoa arrasta o widget pelo título e muda o tamanho pelo canto;
  há Concluir e Restaurar o padrão (D4).
- **Conteúdo:** se ajusta à largura do widget por consultas de contêiner (container queries) do Tailwind (D5).
- **Telas estreitas:** abaixo de 768 px, uma coluna na ordem do layout, sem edição (D6).
- **Guardar:** o layout fica no `localStorage`, com leitura tolerante (D7).
- **Código da página:** a seção O que as vagas pedem é dividida em um hook com o estado e dez widgets (D8). O servidor
  não muda.

## Technical Context

**Language/Version**: TypeScript e React 19 na `frontend-react`. O Python não muda.

**Primary Dependencies**:
- **Nova:** `react-grid-layout` 2.3.0 (MIT), só no front. Ela traz `react-draggable`, `react-resizable`, `clsx`,
  `fast-equals`, `prop-types` e `resize-observer-polyfill`. O motivo e as alternativas estão no research (D1).
- **Do projeto:** Tailwind v4 (consultas de contêiner) e lucide-react (ícone da alça).

**Storage**:
- o layout no `localStorage`, na chave `mpt_pref_metricas_layout` (data-model §2);
- nada no servidor, no banco, no `config.json` ou no perfil.

**Testing**:
- `tsc --noEmit` e `vite build`;
- conferência por CDP sem janela (D10): só leituras e cliques de tela, nunca "Ler os requisitos";
- o quickstart, feito pela pessoa;
- a suíte Python roda inteira só para garantir que nada mudou: `python -m unittest discover -s tests`.

**Target Platform**: Windows primeiro; navegador no computador e no celular; dashboard em `127.0.0.1:8765`.

**Project Type**: ferramenta local; nesta spec, só a página React.

**Performance Goals**:
- arrastar e redimensionar a 60 quadros por segundo, com 16 widgets;
- o layout é aplicado no carregamento sem piscar: a animação da grade só liga depois da primeira medida (D3).

**Constraints**:
- fora do modo de edição, nada se move e os cliques funcionam como hoje (FR-008);
- no modo de edição, só a alça arrasta (FR-007);
- sem rolagem para o lado a 360 px (FR-015);
- o build continua saindo da Action `front.yml`. A pessoa não precisa de Node (constituição III).

**Scale/Scope**:
- **Front, arquivos novos:**
  - `src/components/painel/PainelWidgets.tsx`;
  - `src/components/painel/Widget.tsx`;
  - `src/components/painel/layout.ts`.
- **Front, arquivos que mudam:** `FunnelAnalytics.tsx`, `RequisitosVagas.tsx`, `storage.ts`, `index.css`,
  `package.json` e `pnpm-lock.yaml`.
- **Documentos:** `README.md` e `dash/README.md` (FR-016).

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ O layout fica no navegador da pessoa e não sai do computador. |
| II. Pública, sem dados pessoais | ✅ O layout padrão e os documentos não têm nada de uma pessoa. O diff passa pela busca de dados pessoais antes da `master`. |
| III. Simples e leve | ✅ com justificativa: uma dependência nova só no front. Ela entra no build da Action, e a pessoa continua sem precisar de Node. Escrever a grade à mão daria cerca de 300 linhas próprias de arrastar, colisão e compactação; a biblioteca é madura (MIT, usada pelo Grafana e pelo Metabase) e já cobre alça, canto, mínimos e máximos (research D1). Sem IA, o painel funciona igual. |
| IV. Só fatos | ✅ Nada muda nos números: os widgets mostram o mesmo conteúdo de hoje. |
| V. A pessoa decide | ✅ O layout só muda pela mão da pessoa. Restaurar o padrão pede confirmação. |
| VI. Respeito aos portais | ✅ Nenhum pedido a portal. |
| Fluxo | ✅ Spec aprovada em 2026-11-03 ("sim") e plano aprovado no mesmo dia ("pode seguir com o 46"), com a 045 já na `master`. Implementação, teste e `master`, cada um com o OK da pessoa. |

**Resultado:** passa. A dependência nova fica justificada no research D1 e citada na spec (Assumptions). A conferência
depois do desenho dá o mesmo resultado.

## Project Structure

```text
specs/046-widgets-metricas/  spec.md, plan.md, research.md, data-model.md, contracts/painel-widgets.md,
                             quickstart.md, tasks.md (próxima etapa), checklists/requirements.md

README.md, dash/README.md    # Organizar painel, Restaurar o padrão, layout neste navegador

frontend-react (worktree ao lado da pasta do projeto):
  package.json, pnpm-lock.yaml           # react-grid-layout 2.3.0
  src/components/painel/layout.ts        # novo: widgets, layout padrão, limites, leitura tolerante, ordem da coluna
  src/components/painel/Widget.tsx       # novo: moldura do widget (título que vira alça, corpo que rola, medida da altura)
  src/components/painel/PainelWidgets.tsx # novo: grade, modo de edição, aviso, Concluir, Restaurar, coluna única
  src/components/FunnelAnalytics.tsx     # monta os 16 widgets e entrega ao PainelWidgets
  src/components/RequisitosVagas.tsx     # vira useRequisitos (estado) + o conteúdo da barra e dos 9 blocos
  src/services/storage.ts                # chave mpt_pref_metricas_layout: ler, gravar, apagar
  src/index.css                          # estilo da grade: alça, canto, sombra do lugar novo, tema escuro
```

**Structure Decision**:
- **`painel/` é genérico:** recebe a lista de widgets e o layout padrão e não sabe o que há dentro deles. Outra aba
  pode usar depois (fora do escopo).
- **O estado fica no painel:** o estado de O que as vagas pedem (seleção, resumo, leitura, item aberto) sobe para um
  hook chamado no `FunnelAnalytics`. Mover ou redimensionar um widget não recarrega o resumo nem para a leitura.
- **O título é da moldura:** cada widget declara título, ícone e tipo (número, bloco ou seção). A moldura desenha o
  título, que no modo de edição vira a alça.

## Entrega (como nas specs anteriores)

1. Commit local na `046-widgets-metricas` (documentos) e na `frontend-react` (página).
2. Merge da `046-widgets-metricas` na branch pessoal. O build do front vai para `dash/front/` sem commit, e o dashboard
   é reiniciado para a pessoa testar.
3. Com o OK da pessoa:
   - busca de dados pessoais no diff;
   - merge na `master` e push;
   - push da `frontend-react`, `gh workflow run front.yml` e merge do PR `front/atualizacao` com squash;
   - `git merge origin/master` na branch pessoal;
   - apagar a worktree e a branch;
   - `graphify update .`.
