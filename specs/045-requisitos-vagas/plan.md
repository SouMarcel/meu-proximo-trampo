# Implementation Plan: O que as vagas pedem, no painel Métricas & Funil

**Branch**: `045-requisitos-vagas` (worktree saída da `master`) | **Date**: 2026-11-03 | **Spec**: [spec.md](spec.md)

## Summary

- **Requisitos de cada vaga:** a análise da IA passa a guardar os requisitos de cada vaga no campo `requisitos`:
  habilidades, certificações e cursos, tempo de experiência, formação e idiomas (research D1 a D3).
- **Vagas já analisadas:** uma leitura em segundo plano pede à IA só os requisitos, sem mexer na nota (D4).
- **Contas no servidor:** um módulo novo, `dash/requisitos.py`, faz as contas da seleção e compara com o perfil sem IA
  (D5 a D9).
- **Saídas:** o mesmo resumo vai para a página, para o terminal e para o chat (D11).
- **Página:** no painel Métricas & Funil, a seção nova O que as vagas pedem substitui o quadro antigo (D10).

## Technical Context

**Language/Version**: Python 3.10+, só a biblioteca padrão. TypeScript e React na `frontend-react`.

**Primary Dependencies**: nenhuma nova. Reaproveita:
- `ia.py`: `responder`, `marca` e `mascarar`;
- `analise.py`: `LOTE`, `lotes`, `_secao`, `FILA.rodando` e `ligada`;
- `integridade.limpar`;
- `conferir`: `norm` e `_contem`;
- `analise_perfil.perfil_texto`;
- os rótulos de `kit.py`.

**Storage**:
- o campo `requisitos` no documento da vaga (SQLite com JSON, sem migração; data-model §1);
- a seleção do painel no `localStorage` (`mpt_pref_metricas_requisitos`).

Nada vai para o `config.json` ou para o perfil.

**Testing**:
- `tests/test_requisitos.py` (D12), com banco temporário e IA falsa;
- a suíte inteira: `python -m unittest discover -s tests`;
- o `test_skills` para a cópia das skills;
- front com `tsc --noEmit` e `vite build`;
- CDP sem janela, só leituras;
- o quickstart, feito pela pessoa.

**Target Platform**: Windows primeiro; dashboard local em `127.0.0.1:8765`.

**Project Type**: ferramenta local (CLI + servidor HTTP + página React).

**Performance Goals**:
- o resumo de cerca de 300 vagas sai em menos de 1 s;
- a leitura de algumas centenas de vagas leva alguns minutos, em lotes de 10, com andamento na tela.

**Constraints**:
- a leitura nunca muda nota, resumo, Encaixe, Lacunas, alertas, triagem ou etapa (FR-005, SC-003);
- à IA da leitura vai só o texto do anúncio e os nomes da lista do perfil (FR-006);
- sem IA, a seção ainda mostra os indicadores que já existem e Suas habilidades (FR-007).

**Scale/Scope**:
- **Python:** `dash/requisitos.py` (novo); mudanças em `dash/banco.py`, `dash/analise.py` e `dash/servidor.py`.
- **Front:** `RequisitosVagas.tsx` (novo), `services/api/requisitos.ts` (novo), `FunnelAnalytics.tsx`, `App.tsx`,
  `storage.ts` e `types/api.ts`.
- **Documentos:** a skill `buscar-vagas`, `README.md`, `dash/README.md`, `dash/API.md` e `AGENTS.md`.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ O resumo e o campo novo ficam no computador da pessoa. À IA escolhida vão só o texto dos anúncios e os nomes das habilidades e certificações do perfil (FR-006), e a página mostra para qual IA vai. A rota que dispara a leitura só aceita pedidos deste computador. |
| II. Pública, sem dados pessoais | ✅ O código, os testes e os documentos usam exemplos fictícios. O diff passa pela busca de dados pessoais antes da `master`. |
| III. Simples, sem IA obrigatória | ✅ Sem dependência nova. Sem IA, a seção mostra senioridade, modelo, contratação, inglês e Suas habilidades, e a leitura pode ser pedida ao assistente no chat (D11). O front segue o build da spec 025. |
| IV. Só fatos | ✅ Só entra o que o anúncio diz (FR-001). Tempo, formação e idiomas guardam a frase. Cada número leva às vagas que o formam (FR-019). Os anos de experiência da pessoa não são estimados. A comparação com o perfil é por regra e não grava nada no perfil. Texto da vaga é dado: a vaga suspeita é lida sozinha. |
| V. A pessoa decide | ✅ A leitura só roda no clique e tem Parar. O que é gravado é a leitura de cada vaga, como a análise. Perfil e config não mudam. |
| VI. Respeito aos portais | ✅ Nenhum pedido a portal: só os textos já gravados. |
| Fluxo | ✅ Spec aprovada em 2026-11-03 ("sim"). Plano, tarefas, teste e master, cada um com o OK da pessoa. |

**Resultado:** passa, sem emenda. Depois do desenho, a conferência dá o mesmo resultado. O único dado novo que vai à
IA (os nomes da lista de habilidades) é uma parte do perfil que a análise já envia inteiro.

## Project Structure

```text
specs/045-requisitos-vagas/  spec.md, plan.md, research.md, data-model.md, contracts/api-requisitos.md,
                             contracts/painel-requisitos.md, quickstart.md, tasks.md (próxima etapa),
                             checklists/requirements.md

dash/requisitos.py      # novo: validar, chaves e comparação com o perfil, leitura do perfil, seleção, resumo,
                        #       pedido da leitura, Leitura (segundo plano) e CLI resumo|pendentes|gravar
dash/banco.py           # validar_analise grava requisitos; aplicar_requisitos (só o campo)
dash/analise.py         # linha de formato com "requisitos"; a análise passa a IA que leu (provedor/modelo)
dash/servidor.py        # GET /api/requisitos, POST /api/requisitos/ler e /parar
tests/test_requisitos.py
.agents/skills/buscar-vagas/SKILL.md  # item requisitos nos campos; ler os requisitos pelo chat; "o que as vagas pedem?"
.claude/skills/…        # cópia gerada (python sincronizar_skills.py)
README.md, dash/README.md, dash/API.md, AGENTS.md

frontend-react (worktree ao lado da pasta do projeto):
  src/components/RequisitosVagas.tsx     # novo: a seção inteira
  src/components/FunnelAnalytics.tsx     # sai o quadro antigo; entra a seção; plataformas no fim
  src/services/api/requisitos.ts         # novo: resumo, ler, parar
  src/services/storage.ts                # chave mpt_pref_metricas_requisitos
  src/types/api.ts                       # tipos do resumo e o campo requisitos na Vaga
  src/App.tsx                            # props novas do FunnelAnalytics
```

**Structure Decision**:
- **Um módulo só:** `dash/requisitos.py` concentra a regra (validação, contas, leitura e CLI).
  - O `banco` o importa dentro das funções, para não criar import circular, como faz com `filtros`.
  - O módulo importa `banco` e `analise` no topo e os da raiz (`ia`, `conferir`, `integridade`, `analise_perfil`) com
    `_raiz()`, como em `analise.py`.
- **A página só mostra:** o resumo chega pronto, e o componente cuida do seletor, da leitura, das listas e do clique.

## Entrega (como nas specs anteriores)

1. Commit local na `045-requisitos-vagas` e na `frontend-react`.
2. Merge da `045-requisitos-vagas` na branch pessoal. O build do front vai para `dash/front/` sem commit, e o dashboard
   é reiniciado para a pessoa testar.
3. Com o OK da pessoa:
   - busca de dados pessoais no diff;
   - merge na `master` e push, só com os testes passando;
   - push da `frontend-react`, `gh workflow run front.yml` e merge do PR `front/atualizacao` com squash;
   - `git merge origin/master` na branch pessoal;
   - apagar a worktree e a branch;
   - `graphify update .`.
