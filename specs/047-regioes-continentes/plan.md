# Implementation Plan: Regiões e continentes nos filtros da busca internacional

**Branch**: `047-regioes-continentes` (worktree saída da `master`) | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

## Summary

Um catálogo único de regiões em `filtros.py` (research D1) passa a valer em quatro lugares:
- Regiões aceitas;
- países de interesse;
- países para morar;
- autorização de trabalho.

Comparar lugares passa a ser por sobreposição de países (D3), e assim:
- a América Latina passa com Américas marcada;
- o mundo todo sempre passa;
- a UE na autorização serve para "só Alemanha".

A leitura do texto da vaga reconhece Oceania, Ásia, África, APAC, EMEA e "EU" como União Europeia (D4).

Busca e revisão:
- **Região em países de interesse:** vira uma consulta por região no LinkedIn (`POR_REGIAO`, D6).
- **A etiqueta** segue o local quando ele diz o país (D7).
- **Revisão das vagas cortadas pela regra antiga:** o comando `dash/banco.py regioes` mostra quais voltariam ao
  relatório e só grava com `--gravar` (D10).

Na página (`frontend-react`):
- as pílulas novas;
- a linha Regiões em países de interesse;
- a contagem e o aviso (D8).

No perfil, a pergunta e a linha passam a dizer "países e regiões" (D9).

## Technical Context

**Language/Version**: Python 3.10+, só biblioteca padrão. Front em TypeScript e React na `frontend-react`.

**Primary Dependencies**: nenhuma nova.

**Storage**: `config.json` (os mesmos campos, com valores novos aceitos) e o banco de vagas. Só a revisão (`--gravar`)
grava no banco.

**Testing**:
- `unittest`, sem rede:
  - `tests/test_regioes.py` (novo);
  - ajustes em `tests/test_elegibilidade.py`, `tests/test_internacional.py` e `tests/test_primeiros_passos.py`;
- `tsc --noEmit` e `vite build` no front;
- roteiro do quickstart.

**Target Platform**: Windows primeiro; dashboard local em `127.0.0.1:8765`.

**Project Type**: ferramenta local (CLI + servidor HTTP + página React).

**Constraints**:
- nenhum pedido novo a portal além da consulta por região no LinkedIn, que só existe quando a pessoa marca uma região
  em países de interesse;
- nada muda para quem não usa regiões (FR-012);
- página nova com servidor antigo e o contrário funcionam (D8).

**Scale/Scope**:
- `filtros.py`: catálogo, leitura, sobreposição, validação, consultas, opções e texto para a IA;
- `vagas.py`: `atende`;
- `fontes/linkedin.py` e `fontes/__init__.py`;
- `dash/banco.py`: revisão;
- `primeiros_passos.py`;
- front: `SearchFiltersModal.tsx` e `config.ts`;
- documentos: `dash/API.md`, `README.md`, `AGENTS.md` (comando novo), `docs/novo-portal.md` (`POR_REGIAO`).

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Nada novo sai do computador. As regiões ficam no `config.json` local. |
| II. Pública, sem dados pessoais | ✅ O catálogo é geral. "Seu país" vem do config de cada pessoa. Nenhum dado pessoal entra na `master`. |
| III. Simples, sem IA obrigatória | ✅ Sem dependência nova. As regras são fixas, e a IA só recebe o texto dos critérios, como hoje. |
| IV. Só fatos | ✅ A autorização por região é declarada pela pessoa, e a ferramenta não deduz cidadania. As regiões só valem quando a vaga diz o lugar. |
| V. A pessoa decide | ✅ A revisão das vagas antigas mostra antes e só grava com `--gravar` e o OK. |
| VI. Respeito aos portais | ✅ Uma região é uma consulta no LinkedIn, em vez de uma por país. O Indeed não recebe região. As pausas e a espera de hoje continuam. Os nomes das regiões não foram testados com pedidos (D6). |
| Fluxo | ✅ Spec aprovada em 2026-11-06 ("sim"). Plano, tarefas e implementação seguem direto até o merge na branch pessoal, por decisão da pessoa. |

Resultado: **passa**, sem emenda. A conferência depois do desenho dá o mesmo resultado.

## Project Structure

```text
specs/047-regioes-continentes/  spec.md, plan.md, research.md, data-model.md, contracts/config-e-api.md,
                                quickstart.md, tasks.md (próxima etapa), checklists/requirements.md

filtros.py               # REGIOES_PAISES (+ PAISES_DA_REGIAO), REGIOES, REGIAO_EN, LUGARES, lugar_pt, paises_de,
                         # sobrepoe; efetivos, validar, opcoes, criterios_extra, consultas, area_da_vaga, elegibilidade
vagas.py                 # atende: consulta com "regiao" só para POR_REGIAO
fontes/__init__.py       # contrato: POR_REGIAO
fontes/linkedin.py       # POR_REGIAO = True; parametros: location = regiao
dash/banco.py            # rever_regioes + comando "regioes [--gravar]"
primeiros_passos.py      # pergunta, linha do perfil e proposta com lugar_pt
tests/test_regioes.py    # novo
tests/test_elegibilidade.py, tests/test_internacional.py, tests/test_primeiros_passos.py  # ajustes
dash/API.md, README.md, AGENTS.md, docs/novo-portal.md

frontend-react (worktree ../mpt-front-027b):
  src/components/modals/SearchFiltersModal.tsx  # pílulas, linha Regiões, rótulos, aviso, dica
  src/services/api/config.ts                    # Opcoes.regioes_lugar?, fontes_regiao?; contarConsultas com regiões
```

**Structure Decision**:
- **Tudo de regiões fica em `filtros.py`**, onde já estão os países, os lugares e a elegibilidade.
- **Nenhum módulo novo**, só funções pequenas:
  - `lugar_pt`: o nome do lugar;
  - `paises_de`: os países do lugar;
  - `sobrepoe`: dois lugares com país em comum.
- **No front**, a mudança fica no painel que já mostra esses campos.

## Entrega (como nas specs anteriores)

1. Commit local na `047-regioes-continentes` e na `frontend-react` (sem push).
2. Merge da `047-regioes-continentes` na branch pessoal. O build do front vai para `dash/front/` sem commit, e o
   dashboard é reiniciado para a pessoa testar.
3. Na branch pessoal, com o OK da pessoa já dado nesta sessão:
   - `config.json`: as regiões aceitas e a autorização combinadas com ela;
   - `perfil.md`: a linha de regiões e a de autorização.
4. Com o OK do teste:
   - busca de dados pessoais no diff;
   - merge na `master` e push, só com os testes passando;
   - push da `frontend-react`, `gh workflow run front.yml` e merge do PR `front/atualizacao`;
   - `git merge origin/master` na branch pessoal;
   - apagar a worktree e a branch;
   - `graphify update .`.
