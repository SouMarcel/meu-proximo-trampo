# Implementation Plan: Pausa do LinkedIn ajustável

**Branch**: `017-linkedin-pausa` (worktree saída da `master`) | **Date**: 2026-10-17 | **Spec**: [spec.md](spec.md)

## Summary

`fontes/linkedin.py` ganha `pausa()`, que lê `LINKEDIN_PAUSA` por `segredos.ler` (o ambiente vence o `.env`) e
devolve a faixa da pausa:
- N entre 3 e 60 dá uma pausa sorteada de N a N + 4;
- valor fora dos limites vale o limite, com o motivo do ajuste;
- texto que não é número, ou ausência da variável, vale o padrão `PAUSA` (3 a 7).

`_pausar()` usa essa faixa, lida uma vez por busca (o estado zera em `_comum.esquecer`, no começo de cada busca).

`aviso_pausa(consultas)` monta o aviso com o tempo estimado: (consultas × 3 páginas + 20 descrições) × pausa média.
`vagas.aviso_pausa(f, fontes)` chama esse aviso só quando o LinkedIn está na busca e fora da espera de 6 horas. O
aviso aparece no começo do `vagas.py buscar` (terminal e chat) e no `buscador.plano()`, que a página mostra no diálogo
de busca ao lado do aviso de cargos.

## Technical Context

- **Language**: Python 3.10+ (biblioteca padrão); JavaScript ES5 na página.
- **Dependências**: nenhuma nova.
- **Storage**: `.env` (variável nova, opcional).
- **Testing**: `unittest`, com `segredos.ler` substituído, em `tests/test_linkedin.py` (classe `TestPausa`).
- **Plataforma**: Windows.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Fica no `.env` deste computador, fora do Git. As chaves continuam só no `.env`; a variável nova não é chave, e a escolha do arquivo é da pessoa. |
| II. Pública, sem dados pessoais | ✅ Nada da pessoa no código. Os exemplos usam valores genéricos. |
| III. Simples, sem IA obrigatória | ✅ Biblioteca padrão; sem a variável, nada muda. |
| IV. Só fatos confirmados | ✅ Não se aplica. |
| V. A pessoa decide | ✅ A pessoa edita o `.env`; a ferramenta só avisa. |
| VI. Respeito aos portais | ✅ Reforça: a variável só aumenta a pausa, com mínimo igual ao padrão de hoje. |

Resultado: **passa**.

## Source Code

```text
fontes/linkedin.py      # VAR_PAUSA, PAUSA_MIN/MAX/FAIXA, pausa(), aviso_pausa(), _pausar com a faixa da busca
vagas.py                # aviso_pausa(f, fontes); aviso no começo do buscar
dash/buscador.py        # plano(): aviso_pausa
dash/dashboard.html     # diálogo de busca mostra o aviso
README.md, .agents/skills/buscar-vagas/SKILL.md (+ sincronizar_skills.py)
tests/test_linkedin.py  # TestPausa
```
