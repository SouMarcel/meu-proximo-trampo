# Implementation Plan: Informações básicas no Meu perfil e idiomas com nível

**Branch**: `036-informacoes-basicas` (worktree `../mpt-036-informacoes-basicas`, saída da `master`; front na
`frontend-react`, worktree `../mpt-front-027b`) | **Date**: 2026-10-29 | **Spec**: [spec.md](spec.md)

## Summary

A maior parte é front: mudar componentes de lugar e uma pergunta nova. O backend muda só na pergunta de idiomas e em
um aviso.

- **`primeiros_passos.py`**:
  - `IDIOMAS_PERFIL` (Inglês, Português (BR), Francês, Alemão, Espanhol) e `NIVEIS_IDIOMA` (A1 a C2 e Nativo, cada um
    com `valor`, `rotulo` e `descricao`);
  - `ler_idioma(texto)` e `ler_idiomas(lista)` convertem respostas em texto livre nas linhas da lista. O nível só vem
    da sigla do CEFR ou de "nativo"/"native";
  - a pergunta `idiomas` continua `tipo: "lista"` e ganha `idiomas`, `niveis` e `linhas` (as linhas vêm de
    `perguntas_para`);
  - a pergunta `ingles` sai de `PERGUNTAS`, e `"ingles"` fica em `IDS` como id antigo;
  - na montagem do perfil, "Inglês (nível declarado)" só entra se a lista não tiver o inglês com nível do formato
    novo.
- **`candidatura_ia.py`**: o aviso da carta sem dados de contato aponta Meu perfil → Informações básicas.
- **Front** (`frontend-react`):
  - `perfil/InformacoesBasicas.tsx` (novo) junta dados de contato, respostas guardadas e sites;
  - `DadosContato.tsx` passa de `modals/` para `perfil/`;
  - `modals/ConfigCandidatura.tsx` vira `modals/LoginGuardado.tsx`, só com o login guardado;
  - `ConnectedAccountsModal` usa `LoginGuardado` e ganha a linha com o botão "Abrir Informações básicas";
  - `MeuPerfil` ganha a tela `basicas` e o botão na navegação, sempre visível;
  - `perfil/PerguntaIdiomas.tsx` (novo) traz as linhas, o + e o ×, a validação e a montagem do texto;
  - `App.tsx`: `perfilAberto.tela` aceita `"basicas"`;
  - `CandidaturaAssistida.tsx`: o texto de revogar passa a apontar Informações básicas;
  - `services/api/perfil.ts`: novos campos opcionais em `Pergunta`.
- **Documentação**: README, `dash/API.md` (§3.6 e §3.11b) e a skill `analisar-perfil`, com
  `python sincronizar_skills.py` depois.
- **Testes**:
  - `tests/test_primeiros_passos.py`: `ler_idioma(s)`, a pergunta sem `ingles`, as `linhas`, o perfil sem inglês
    duplicado;
  - `tests/test_analise_perfil.py`: o nível no formato novo é reconhecido.

## Technical Context

- **Language/Version**: Python 3.10+ (biblioteca padrão); React 19 e TypeScript 5 na `frontend-react`.
- **Primary Dependencies**: nenhuma nova.
- **Storage**: sem mudança de formato.
  - Idiomas: lista de textos em `respostas.idiomas` do progresso do perfil.
  - Contato: `dash/dados/contato.json`.
  - Respostas: `dash/dados/respostas_formulario.json`.
  - Sites: como hoje.
- **Testing**: `python -m unittest discover -s tests`; `tsc --noEmit` e `vite build` no front.
- **Target Platform**: dashboard local (Windows primeiro), tema claro e escuro, celular.
- **Project Type**: web local (servidor Python + página React montada pela Action).
- **Constraints**:
  - compatível com a página antiga, porque a `master` fica um tempo com o backend novo e o front antigo, até o PR da
    Action;
  - nada de nível estimado (constituição IV).
- **Scale/Scope**: 7 componentes do front e 2 módulos Python; sem rota nova.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Nenhum dado novo nem fluxo novo. Contato, respostas e sites continuam só neste computador e fora da IA; a aba usa as mesmas rotas [local]. |
| II. Pública | ✅ Listas genéricas de idiomas e níveis; testes com dados fictícios. |
| III. Simples | ✅ Biblioteca padrão, sem dependência e sem IA. A página antiga continua funcionando (a pergunta segue `tipo: "lista"`). |
| IV. Só fatos | ✅ A ferramenta não escolhe nível pela pessoa: só a sigla do CEFR ou "nativo" escritos por ela viram nível; o resto ela escolhe. |
| V. A pessoa decide | ✅ Nada grava sem clique: Próxima, Salvar e Revogar continuam explícitos; a proposta de contato não grava. |
| VI. Portais | ✅ O comportamento de Conectar, leitura e login guardado não muda. |

Resultado: passa. A conferência foi refeita depois do desenho, e não há desvio.

## Project Structure

### Documentation (this feature)

```text
specs/036-informacoes-basicas/
├── spec.md, plan.md, research.md, data-model.md, quickstart.md
├── contracts/pergunta-idiomas.md     # o que a pergunta de idiomas leva à página e o que volta
├── contracts/ui.md                   # o que fica em cada diálogo
└── checklists/requirements.md
```

### Source Code

```text
primeiros_passos.py              # IDIOMAS_PERFIL, NIVEIS_IDIOMA, ler_idioma(s), pergunta idiomas, sem "ingles"
candidatura_ia.py                # aviso da carta
README.md, dash/API.md, .agents/skills/analisar-perfil/SKILL.md (+ cópia em .claude/skills)
tests/test_primeiros_passos.py, tests/test_analise_perfil.py

frontend-react (../mpt-front-027b):
src/App.tsx
src/services/api/perfil.ts
src/components/modals/ConnectedAccountsModal.tsx
src/components/modals/ConfigCandidatura.tsx  → src/components/modals/LoginGuardado.tsx
src/components/modals/DadosContato.tsx       → src/components/perfil/DadosContato.tsx
src/components/perfil/InformacoesBasicas.tsx  (novo)
src/components/perfil/PerguntaIdiomas.tsx     (novo)
src/components/perfil/MeuPerfil.tsx
src/components/kit/CandidaturaAssistida.tsx
```

**Structure Decision**: o backend fica na `036-informacoes-basicas`, saída da `master`. O front fica na
`frontend-react`. A ordem de entrega é a das specs 033 a 035:
1. teste na branch pessoal, com o build copiado para `dash/front/`;
2. com o OK, merge na `master`;
3. Action do front e PR.

## Complexity Tracking

Sem desvios da constituição.
