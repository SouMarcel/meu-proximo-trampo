# Implementation Plan: Abas no painel Filtros da busca

**Branch**: `043-abas-filtros` (worktree saída da `master`) | **Date**: 2026-11-02 | **Spec**: [spec.md](spec.md)

## Summary

O painel Filtros da busca ganha quatro abas: Geral, Portais, Portais internacionais e Empresas acompanhadas/excluídas
(research D4 a D8).
- **Front** (`frontend-react`, `SearchFiltersModal.tsx`):
  - o estado da aba no próprio painel, que abre sempre na Geral;
  - as seções de hoje redistribuídas, sem mudar o texto;
  - as Fontes do exterior saem do modo internacional;
  - contadores nas abas;
  - o erro no rodapé;
  - as abas no padrão de acessibilidade, com as setas.
- **Servidor**: só um dado novo, a lista fixa `filtros.PORTAIS_A_MAPEAR` em `opcoes.portais_a_mapear` (D1). Ela traz
  InHire e Catho em estudo e Glassdoor, que não deu (D3). Um teste de guarda confere que nenhum portal da busca
  continua na lista (D2).
- **Filtros, gravação e busca**: sem mudança.

## Technical Context

**Language/Version**: Python 3.10+, só biblioteca padrão. Front em TypeScript e React na `frontend-react`.

**Primary Dependencies**: nenhuma nova.

**Storage**: nenhum. A lista de próximos é uma constante do código, e o `config.json` não muda.

**Testing**:
- `unittest`: `tests/test_abas_filtros.py`, sem rede;
- `tsc --noEmit` e `vite build`;
- roteiro na página (quickstart), com a conferência automática por CDP com o Edge sem janela, só com leituras e
  cliques nas abas, sem salvar.

**Target Platform**: Windows primeiro; dashboard local em `127.0.0.1:8765`.

**Project Type**: ferramenta local (CLI + servidor HTTP + página React).

**Constraints**:
- nenhum pedido novo a portal;
- página nova com servidor antigo e o contrário funcionam (D9);
- textos de hoje mantidos (FR-003 a FR-006).

**Scale/Scope**:
- servidor: 1 constante e 1 campo em `opcoes()` (`filtros.py`), 1 arquivo de teste;
- front: 1 componente (`SearchFiltersModal.tsx`) e 1 tipo (`config.ts`);
- documentos: 5.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Nada novo sai do computador nem é gravado. |
| II. Pública, sem dados pessoais | ✅ A lista de próximos é sobre portais públicos e serve a qualquer pessoa; nada da pessoa. |
| III. Simples, sem IA obrigatória | ✅ Sem dependência nova, sem IA. O front segue o fluxo de build da spec 025. |
| IV. Só fatos | ✅ A lista só diz o que está registrado (a pesquisa de 23/10/2026 do Glassdoor), sem previsão de data. |
| V. A pessoa decide | ✅ O bloco novo é só leitura; a gravação continua só no Salvar filtros. |
| VI. Respeito aos portais | ✅ Nenhum pedido a portal; "Próximos a mapear" não consulta nada. |
| Fluxo | ✅ Spec aprovada em 2026-11-02 ("ok"). Plano e tarefas esperam o OK. |

Resultado: **passa**, sem emenda. A conferência depois do desenho dá o mesmo resultado: o desenho não acrescenta
gravação, pedido nem dependência.

## Project Structure

```text
specs/043-abas-filtros/  spec.md, plan.md, research.md, data-model.md, contracts/api.md, contracts/painel.md,
                         quickstart.md, tasks.md (próxima etapa), checklists/requirements.md

filtros.py                 # PORTAIS_A_MAPEAR; opcoes() + "portais_a_mapear"
tests/test_abas_filtros.py # forma da lista e guarda contra portal que já está na busca
dash/API.md                # §3.4: opcoes.portais_a_mapear e as abas do painel
dash/README.md             # o painel com as quatro abas
.agents/skills/buscar-vagas/SKILL.md (+ cópia em .claude/skills/ por sincronizar_skills.py)  # caminhos com a aba
docs/novo-portal.md        # tirar da lista o portal que entra; registrar o que não deu
specs/lista-de-desejos.md  # a lista do painel acompanha "Mais portais do Brasil"

frontend-react (numa worktree ao lado da pasta do projeto):
  src/components/modals/SearchFiltersModal.tsx  # abas, contadores, Próximos a mapear, Portais internacionais,
                                                # erro no rodapé, fim do painel internacional
  src/services/api/config.ts                    # PortalAMapear; Opcoes.portais_a_mapear?
```

**Structure Decision**:
- A mudança fica num componente só.
- O `App.tsx` não muda, porque o painel continua montado ao trocar de modo (research, "O que o código já dá").
- O `PortaisLogin.tsx` entra inteiro na aba Portais, sem mudança.
- Sem componente de abas compartilhado: o detalhe da vaga e o `InterviewCoach` têm abas próprias, e unificá-las
  ficaria fora do escopo.

## Entrega (como nas specs anteriores)

1. Commit local na `043-abas-filtros` e na `frontend-react`.
2. Merge da `043-abas-filtros` na branch pessoal; o build do front copiado para `dash/front/` sem commit; o dashboard
   reiniciado para a pessoa testar.
3. Com o OK:
   - busca de dados pessoais no diff;
   - merge na `master` e push, só com os testes passando;
   - push da `frontend-react`, `gh workflow run front.yml` e merge do PR `front/atualizacao` com squash;
   - `git merge origin/master` na branch pessoal;
   - apagar a worktree e a branch;
   - `graphify update .`.
