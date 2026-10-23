---
description: "Tarefas da feature 028: Vagas.com na busca (Windows)"
---

# Tasks: Vagas.com na busca de vagas

**Input**: spec.md, research.md; mecanismos comuns da spec 026 (`fontes/_comum.py`).

- [X] T001 `tests/dados/vagascom/{lista.html, lista-2.html, vaga.html}` fictícios no formato da research R2
- [X] T002 `fontes/vagascom.py`: contrato, cards, datas relativas, lista por cargo com páginas e janela, `buscar`,
  `descrever`, `pausa`/`aviso_pausa` (`VAGASCOM_PAUSA`), `espera` de 24 h, `parada`, `id_do_link`
- [X] T003 Registro: `fontes/__init__.py`, `filtros.FONTES_NAC`/`FONTES_PADRAO`, `fontes/link.py` (`plataforma`,
  `_portal_paginas`), `dash/banco.PLATAFORMAS`, `config.exemplo.json`, `.env.exemplo`
- [X] T004 `tests/test_vagascom.py`: cards, datas, remoto e cidade com uma leitura, janela na paginação, fora do
  Brasil, descrição e link, bloqueio com espera, ligado por padrão
- [X] T005 README, `dash/README.md`, `dash/API.md`, AGENTS.md, skill buscar-vagas + `sincronizar_skills.py`
- [X] T006 `frontend-react`: "Vagas.com" em `src/types/api.ts`, cor e domínio em `src/utils/formatters.ts`, texto do
  `AddJobModal.tsx` (junto com o InfoJobs, tarefa T014 da spec 026; commit local na branch `front-026-portais`, sem push)
- [X] T007 Verificação: suíte inteira e busca real pequena (research R2)
