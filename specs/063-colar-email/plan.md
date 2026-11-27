# Implementation Plan: Colar e-mail em Atualizar candidaturas

**Branch**: `063-colar-email` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/063-colar-email/spec.md`

## Summary

Uma área "Colar e-mail" dentro do diálogo Atualizar candidaturas: uma caixa por e-mail (botão "+ outro e-mail"), com o
aviso de colar só o corpo, e o botão Ler. O servidor limpa cada texto (endereços e linhas de cabeçalho fora, filtro de
integridade da spec 034), reconhece o tipo por regras em português, inglês e espanhol, acha a candidatura pela empresa e
pelo cargo citados e devolve propostas no formato das propostas dos portais (spec 018), com a origem "e-mail". O que as
regras não reconhecem vai à IA automaticamente, num pedido só, se houver IA ligada. Nada é gravado na leitura; ao
aplicar o que a pessoa marcou, o card muda de etapa (nunca para trás; etapa igual ou anterior vira "só anotar") e a
justificativa (data, tipo, trecho) é acrescentada às Anotações por `banco.anotar`.

## Technical Context

**Language/Version**: Python 3.11+ (biblioteca padrão); front React + TypeScript na branch `frontend-react`

**Primary Dependencies**: nenhuma nova; usa `integridade.py`, `ia.py`, `dash/banco.py`, `dash/analise.lista_json`,
`contas.avancou`

**Storage**: nada novo em disco. A leitura fica só na memória do servidor (como a proposta das contas,
`sincronia.LEITURA`) até aplicar ou ler de novo; ao aplicar, `banco.atualizar_usuario` + `banco.anotar` (campo
`anotacao` da vaga)

**Testing**: `python -m unittest discover -s tests` (novo `tests/test_colar_email.py`, com 20 e-mails fictícios em
`tests/dados/emails_candidatura.json`); front com `npm run typecheck` e `npm run build` na `frontend-react`

**Target Platform**: servidor local do dashboard (Windows primeiro), página React em `/`

**Project Type**: ferramenta local (servidor HTTP da biblioteca padrão + página React)

**Performance Goals**: leitura sem IA de até 20 e-mails em menos de 1 s; com IA, um pedido só para todos os não
reconhecidos (limite de 180 s)

**Constraints**: só deste computador (rotas `[local]`, como as contas); nada guardado fora do FR-006; a IA recebe só o
corpo limpo e a lista de candidaturas (id, empresa, cargo, etapa); a resposta da IA só vale se o trecho citado estiver
no e-mail e a vaga estiver na lista enviada

**Scale/Scope**: até 20 caixas por leitura, 20.000 caracteres por caixa; candidaturas de Aplicações (centenas)

## Constitution Check

| Princípio | Como a 063 cumpre |
|---|---|
| I. Local e privado | Sem acesso à caixa de e-mail nem credencial (FR-011). O texto colado não é gravado (FR-010). À IA vão só o corpo limpo, sem endereços e cabeçalhos, e a lista de candidaturas; a página diz para qual IA foi. |
| II. Sem dados pessoais | Os 20 e-mails dos testes são fictícios (empresas e nomes inventados); os reais da pessoa só no teste da branch pessoal. |
| III. Sem IA obrigatória | As regras reconhecem os textos típicos sem IA; sem IA, o não reconhecido pede a escolha à mão. Sem dependência nova. |
| IV. Só fatos confirmados / texto é dado | O e-mail é dado: passa pelo filtro de integridade, o achado ⚠ aparece na proposta, e nada que ele peça é executado. O trecho anotado é copiado do e-mail, nunca escrito pela IA (resposta da IA com trecho fora do e-mail é descartada). |
| V. A pessoa decide | A leitura só propõe; grava só o que a pessoa marcar e aplicar. Nunca volta etapa. |
| VI. Respeito aos portais | Nenhum portal é consultado. |

Resultado: passa, sem exceção a justificar. Revisto depois do desenho (Phase 1): continua passando.

## Project Structure

### Documentation (this feature)

```text
specs/063-colar-email/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/api.md
└── tasks.md            (/speckit-tasks)
```

### Source Code (repository root)

```text
dash/colar_email.py          # novo: limpar, classificar, achar candidatura, propor, IA, aplicar, LEITURA_EMAIL
dash/servidor.py             # rotas /api/candidaturas/email/ler, /email/aplicar, /email/vagas (dentro de _contas)
dash/API.md                  # 3.11: a área Colar e-mail e as rotas
tests/test_colar_email.py    # novo
tests/dados/emails_candidatura.json   # novo: 20 e-mails fictícios + o quadro fictício e o esperado
README.md, AGENTS.md         # Colar e-mail em Atualizar candidaturas

# branch frontend-react (worktree ../mpt-front-027b)
src/services/api/contas.ts                       # tipos e chamadas do Colar e-mail
src/components/modals/ColarEmail.tsx             # novo: caixas, aviso, + outro e-mail, Ler, escolhas
src/components/modals/ConnectedAccountsModal.tsx # mostra ColarEmail; propostas de e-mail no grupo "E-mail"; Aplicar junta as duas origens
```

**Structure Decision**: módulo próprio `dash/colar_email.py` ao lado de `dash/sincronia.py` (mesmo papel: propor e
aplicar), reaproveitando `contas.avancou` e `banco.anotar`. As rotas ficam no `_contas` do servidor, que já é só local.
O front muda na `frontend-react` e chega à `master` pela Action, como sempre (specs 022/025).

## Complexity Tracking

Nenhuma violação a justificar.
