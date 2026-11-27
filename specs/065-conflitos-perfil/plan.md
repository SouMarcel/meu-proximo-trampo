# Implementation Plan: Conflitos do Meu perfil mais claros e seguros

**Branch**: `065-conflitos-perfil` | **Date**: 2026-11-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/065-conflitos-perfil/spec.md`

## Summary

Três mudanças no assistente do Meu perfil. (P1) A Revisão avisa, antes de gravar, quando o rascunho é mais antigo que
o perfil gravado, mostra os itens do perfil atual que sairiam, pede um "gravar mesmo assim" e oferece refazer o
rascunho herdando as escolhas de conflito que ainda valem; o Gravar passa a recusar se o perfil mudou depois que a
Revisão abriu. (P2) Cada opção de conflito ganha `nota` separada do `valor`, o pedido à IA diz isso, e o Diagnóstico
aponta data de experiência escolhida com texto a mais. (P3) A aba Conflitos recolhe num resumo os conflitos já
resolvidos ao abrir.

Servidor e pedido à IA na `master` (`primeiros_passos.py`, `dash/servidor.py`, `dash/API.md`, testes); tela na
`frontend-react` (`MeuPerfil.tsx`, `services/api/perfil.ts`), montada pela Action.

## Technical Context

**Language/Version**: Python 3.11+ (biblioteca padrão) no servidor; TypeScript + React no front (`frontend-react`)

**Primary Dependencies**: nenhuma nova

**Storage**: `.cache/primeiros-passos.json` (o progresso do assistente, já existe; ganha `rascunho.gerado_em` e
`opcoes[].nota`); `perfil.md` (data da última mudança lida do próprio arquivo)

**Testing**: `python -m unittest discover -s tests` (`tests/test_primeiros_passos.py`); front: `npm run typecheck` e
`npm run build`

**Target Platform**: Windows primeiro (página local em http://127.0.0.1:8765)

**Project Type**: ferramenta local (servidor HTTP próprio + página React)

**Performance Goals**: a prévia continua instantânea; o cálculo do que sairia é sobre algumas centenas de linhas

**Constraints**: nada grava o perfil sem o clique da pessoa; refazer o rascunho só com IA ligada (as outras opções
seguem sem IA)

**Scale/Scope**: 1 pessoa; perfil de até ~200 linhas; dezenas de conflitos no máximo

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Como o plano atende |
|---|---|
| I. Local e privado | Tudo no computador; nada novo vai para fora além do pedido de rascunho que já existe (o mesmo texto) |
| II. Ferramenta pública | Regras genéricas; nada de nomes, datas ou empresas de uma pessoa no código ou nos testes |
| III. Sem IA obrigatória | O aviso, a lista do que sairia, o recolher e o Diagnóstico funcionam sem IA; só "Refazer o rascunho" pede IA, e o aviso diz isso |
| IV. Só fatos confirmados | A `nota` da IA nunca entra no perfil; a herança de escolhas só vale com o mesmo campo e o mesmo valor; nada é cortado por adivinhação |
| V. A pessoa decide | Gravar exige o clique e, com o aviso, uma confirmação a mais; refazer o rascunho só no clique |
| VI. Portais | Não se aplica |

Sem violações. Re-check depois do design: mantém.

## Project Structure

### Documentation (this feature)

```text
specs/065-conflitos-perfil/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/api.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
primeiros_passos.py          # FORMATO/pedido (nota), normalizar_rascunho (gerado_em, nota), herdar_escolhas,
                             # itens_que_sairiam, previa (aviso + perfil_versao), diagnosticar (data com texto a mais)
dash/servidor.py             # POST /api/perfil/rascunho herda escolhas; PUT /api/perfil confere perfil_versao (409)
dash/API.md                  # contrato novo
tests/test_primeiros_passos.py

# branch frontend-react (fonte da página)
src/services/api/perfil.ts            # tipos: opcoes[].nota, Previa.aviso, perfil_versao; gravar(md, versao)
src/components/perfil/MeuPerfil.tsx   # Conflitos recolhidos + nota; aviso da Revisão; gravar mesmo assim; 409
```

**Structure Decision**: o mesmo par de sempre (servidor na `master`, tela na `frontend-react`), como nas specs 060 a
064. Não há módulo novo.

## Complexity Tracking

Nada a justificar.
