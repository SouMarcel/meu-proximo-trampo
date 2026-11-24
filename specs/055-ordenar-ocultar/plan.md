# Implementation Plan: Ordenar as listas e ocultar empresas excluídas

**Branch**: `055-ordenar-ocultar` | **Date**: 2026-11-23 | **Spec**: [spec.md](spec.md)

## Summary

O back calcula a marca `empresa_excluida` de cada vaga entregue à página, com a mesma regra da busca. O front ganha
três coisas: um módulo de ordenação comum, o seletor Ordenar em Aplicações com opções novas também nas Vagas, e a
caixa "Ocultar vagas de empresas excluídas", com a preferência guardada no navegador.

## Technical Context

- **Back:** Python com biblioteca padrão.
  - `filtros.criterios` (filtros.py:1092) já tem a regra: `sem_acento(e) in sem_acento(empresa)`.
  - `banco.com_kit` (dash/banco.py:737) monta toda vaga que vai para a página: `/api/vagas`, PATCH, Adicionar Vaga.
- **Front:** branch `frontend-react`, validada com typecheck e build.
  - `TriageReport.tsx` já ordena: `OrdemFiltro`, `ORDENS`, `criterio`, com a preferência por área em
    `ScreenPreferencesService`.
  - `KanbanBoard.tsx` não ordena: `pipelineVagas` vira `vagasPorEtapa` no quadro, e a lista usa `pipelineVagas`.
  - As preferências ficam em `src/services/storage.ts`, só preferências de tela.

## Constitution Check

- **II:** os testes usam empresas fictícias.
- **III:** biblioteca padrão, sem IA.
- **V:** a caixa e a ordem são visão; nada é gravado no banco nem no config.

Gate: passa.

## Decisões

**D1. Regra única** (`filtros.empresa_excluida(empresa, nomes) -> str | None`):

- `nomes` é a lista já sem acento;
- devolve o nome da lista que bateu, ou None;
- `criterios()` passa a usar essa função, e o texto do motivo não muda.

**D2. Marca na vaga** (`banco.com_kit(v, base=None, excluir=None)`):

- acrescenta `"empresa_excluida": bool`;
- `excluir=None` lê a lista do config (`_nomes_excluir()`, com o config ausente ou com erro → `[]`);
- `/api/vagas` lê a lista uma vez e a passa a todas as vagas;
- calculada a cada leitura, nunca gravada.

**D3. Ordenação comum** (`src/utils/ordenacao.ts`):

- `type OrdemVaga = "aderencia" | "menor_nota" | "publicacao" | "encontrada" | "empresa" | "plataforma" | "modo" | "etapa_recente" | "etapa_antiga"`;
- `ordenar(vagas, ordem, modoDe)` devolve uma cópia ordenada;
- o que falta (nota ou data) vai para o fim;
- empate: maior nota e depois anúncio mais recente;
- empresa com `localeCompare(…, "pt-BR", { sensitivity: "base" })`;
- datas pelos campos `publicada_em`, `encontrada_em` (senão `criada_em`) e `etapa_em`.

**D4. Vagas** (`TriageReport.tsx`):

- `OrdemFiltro` e `ORDENS` ganham `menor_nota`, `encontrada` e `empresa`;
- a ordem passa a usar `ordenar` (D3);
- rótulos: "Menor Aderência", "Encontradas há menos tempo" e "Empresa (A–Z)";
- o padrão continua `aderencia`.

**D5. Aplicações** (`KanbanBoard.tsx`):

- seletor "Ordenar" na barra, com as 8 opções da US1:
  - padrão `etapa_recente` ("Na etapa há menos tempo");
  - `etapa_antiga` ("Na etapa há mais tempo");
  - `aderencia`, `menor_nota`, `publicacao` ("Anúncio mais recente"), `encontrada`, `empresa` e `plataforma`;
- `pipelineVagas` sai ordenado, então cada coluna e a lista herdam a ordem;
- a preferência fica em `ScreenPreferencesService.getOrdemAplicacoes()` e `saveOrdemAplicacoes()`.

**D6. Caixa** (`ScreenPreferencesService.getOcultarExcluidas()` e `setOcultarExcluidas()`):

- a chave é uma só, com padrão `true`;
- o estado fica no `App.tsx` e desce como props (`ocultarExcluidas`, `onOcultarExcluidas`) para `TriageReport` e
  `KanbanBoard`. Assim as duas telas mostram a mesma escolha;
- cada tela filtra `v.empresa_excluida` antes dos outros filtros e mostra "N vaga(s) de empresas excluídas
  oculta(s)", contando a sub-aba atual nas Vagas e o quadro inteiro nas Aplicações;
- os contadores das sub-abas e do menu não mudam.

**D7. Documentação:**

- `dash/API.md`: `empresa_excluida` no objeto vaga;
- `specs/lista-de-desejos.md`: "levar para Fora as vagas antigas de empresas excluídas".

## Testes

`tests/test_ordenar_ocultar.py`, com empresas fictícias:

- `empresa_excluida` sem acento, sem diferenciar maiúsculas, por trecho e com a lista vazia;
- `criterios` com o mesmo motivo de antes;
- `com_kit` com `excluir` passado e lido do config;
- `/api/vagas` traz a marca.

No front: typecheck e build.

## Project Structure

```text
filtros.py, dash/banco.py, dash/servidor.py, dash/API.md, specs/lista-de-desejos.md, tests/test_ordenar_ocultar.py
frontend-react: src/utils/ordenacao.ts, src/services/storage.ts, src/types/api.ts, src/components/TriageReport.tsx,
                src/components/KanbanBoard.tsx, src/App.tsx
```
