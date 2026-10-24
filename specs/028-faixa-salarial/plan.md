# Plano: faixa salarial

**Spec**: [spec.md](spec.md) · **Data**: 2026-10-24

## Estrutura

```text
salarios.py               ler_valor, parecidas, resumo, links, faixa, anotar, remover; CLI
dash/servidor.py          _salario(): GET/POST /api/vagas/{id}/salario, DELETE /api/vagas/{id}/salario/{n}
entrevista.py             salario() devolve as anotações (pesquisas); a CLI mostra
dash/API.md               §3.1b
tests/test_salarios.py
frontend-react: src/components/kit/FaixaSalarial.tsx (seção do kit), src/components/modals/SalarioModal.tsx,
                botão no JobCard, src/services/api/vagas.ts
```

## Constituição

| Princípio | Como cumpre |
|---|---|
| I | Tudo local. As anotações ficam no banco da pessoa. |
| III | Só biblioteca padrão. Sem IA. |
| IV | Só números com fonte. Nada é estimado. |
| V | Nada é gravado sem o clique em Guardar. |
| VI | O Glassdoor bloqueou acesso automatizado (403), e a ferramenta não tenta: só monta links para a pessoa abrir. |

## Verificação

- `python -m unittest tests.test_salarios` e a suíte completa.
- Ponta a ponta com o Edge sem janela e um banco de teste:
  - botão no card → janela;
  - faixa, mediana e links;
  - anotar;
  - seção no detalhe.
