---

description: "Tarefas da feature 022: front novo em React, montado pelo GitHub Actions"
---

# Tasks: Front novo em React, montado pelo GitHub Actions

**Input**: [spec.md](spec.md), [plan.md](plan.md)

**Tests**: `unittest` sem rede (constituição); a Action pelo GitHub.

## Phase 1: Servidor (US2)

- [X] T001 [US2] Rota `/novo/` em `dash/servidor.py` (`_front`, `FRONT`, `TIPOS_FRONT`, aviso sem front, 308 de
  `/novo`) e a linha "Front novo" na saída do servidor quando o front existe
- [X] T002 [P] [US2] `tests/test_front_estatico.py`: arquivos e tipos, redirecionamento, caminhos para fora da pasta
  e tipo desconhecido, front não montado, `/` intacto
- [X] T003 [US2] Conferência com um build local da `frontend-react` (`ae682e0`) na porta 8799: `/novo/`, JS, SVG,
  `../config.json` e `%2e%2e` (404)

## Phase 2: Action (US1)

- [X] T004 [US1] `.github/workflows/front.yml` (disparo manual + 6 h, sem novidade não faz nada, build com
  `--base ./`, `ORIGEM.json`, testes Python, PR `front/atualizacao`)
- [X] T005 [P] [US1] `.gitattributes`: `dash/front/** linguist-generated=true`
- [ ] T006 [US1] Com o OK da pessoa: ligar "Allow GitHub Actions to create and approve pull requests" no repositório
- [ ] T007 [US1] Depois do push: `gh workflow run front.yml`, conferir o PR de teste e uma segunda execução sem
  novidade

## Phase 3: Guia do Figma Make (US3)

- [X] T008 [P] [US3] `dash/API.md` com as rotas que o front usa
- [X] T009 [P] [US3] `specs/022-front-react/prompt-figma.md`
- [X] T010 Documentação: `dash/README.md` e `AGENTS.md`

## Phase 4: Entrega

- [ ] T011 Merge na branch pessoal, `python -m unittest discover -s tests`, teste da pessoa em `/novo/`
- [ ] T012 Com o OK: dados pessoais conferidos, merge na `master`, push, `graphify update .`
