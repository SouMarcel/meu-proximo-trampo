# Implementation Plan: IA com reserva e aviso de indisponibilidade

**Branch**: `032-ia-reserva` (worktree `../meu-proximo-trampo-032`, saída da `master`) | **Date**: 2026-10-27 |
**Spec**: [spec.md](spec.md)

## Summary

**`ia.py`** (o centro da mudança):
- a escolha gravada ganha `reservas`: até 3 `{provedor, modelo, url_base}`, validadas como a principal, sem repetir e
  sem "Sem IA";
- `sequencia(cfg)` devolve a principal e as reservas;
- `responder(...)` sem `escolha` explícita percorre a sequência:
  - cada falha (`IAErro`) vira uma linha de motivo, e a próxima é tentada;
  - a primeira que responder vence;
  - se todas falharem, o erro lista cada uma com o motivo (com uma IA só, a mensagem fica igual à de hoje);
  - com `escolha` explícita, como no Testar, é uma IA só e sem reserva;
- `ultima()`, por thread, diz quem respondeu e quais falharam; `aviso_reserva()` monta o aviso;
  `marca()` substitui os `_marca_ia` (registra a IA que respondeu de fato);
- a situação de cada IA (último sucesso ou falha, com hora e motivo) é gravada em `.cache/ia-estado.json`;
- `estado_para_pagina` passa a trazer a sequência com a situação e o alerta da principal.

**Chamadores**:
- `candidatura_ia` (propostas de respostas), `curriculo_ia`, `analise_perfil` e `dash/gerador`/`dash/analise` usam
  `ia.marca()`;
- onde a função já devolve aviso (candidatura assistida: `aviso_ia`; documentos: `ia`), entra o aviso da reserva.

**Servidor**:
- `PUT /api/ia` aceita `reservas`;
- `GET /api/ia` traz `sequencia` e `alerta`;
- `/api/versao` traz `ia_alerta` para o botão IA;
- `POST /api/ia/testar` registra a situação.

**Front** (`frontend-react`):
- painel IA com a lista de reservas (adicionar, remover, subir e descer), o aviso de privacidade, a situação de cada
  uma e o "Testar a sequência";
- alerta no botão IA;
- aviso da reserva na candidatura assistida e nos documentos.

**Por último**: a configuração do usuário (Gemini e OpenRouter gratuito) e a documentação.

## Technical Context

**Language/Version**: Python 3.10+, só biblioteca padrão. Front em TypeScript, na `frontend-react`.

**Primary Dependencies**: nenhuma nova.

**Storage**:
- `config.json` → `ia.reservas`, sem chave;
- `.cache/ia-estado.json`, fora do Git: `{"<provedor>|<modelo>": {"ok", "em", "motivo"}}`;
- chaves no `.env`, como hoje.

**Testing**: `unittest` sem rede, com `ia._postar` e `ia._claude_code` trocados. Os testes atuais de `test_ia.py` e dos
chamadores servem de não regressão (a mensagem com uma IA só não muda).

**Constraints**:
- nenhuma chave no `config.json`, na página ou nas mensagens (`mascarar` em cada motivo);
- pergunta sensível nunca vai à IA;
- uma tentativa por IA em cada pedido;
- a situação é gravada em cada chamada, sem teste automático.

**Scale/Scope**: no pior caso, um pedido faz até 4 chamadas (principal e 3 reservas), cada uma com o seu tempo limite.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Chaves só no `.env`. A situação em `.cache/` não tem chave nem texto do pedido. O painel avisa que a reserva recebe os mesmos pedidos. |
| II. Pública, sem dados pessoais | ✅ Testes com provedores simulados; nenhum dado da pessoa. |
| III. Simples, IA opcional | ✅ Sem IA continua funcionando. A reserva é opcional, e o formato antigo continua valendo. |
| IV. Só fatos | ✅ Não muda o que a IA recebe nem as regras de conferência. Pergunta sensível nunca vai à IA. |
| V. A pessoa decide | ✅ A pessoa monta a sequência. Nada troca de IA sem estar na lista dela, e o aviso diz quem respondeu. |
| VI. Respeito aos portais | ✅ Não se aplica (provedores de IA, com a chave da pessoa). Uma tentativa por IA, sem insistir. |
| Fluxo | ✅ Spec aprovada em 27/10 → plano → tarefas. |

Resultado: passa, sem desvio.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Verificação só no Windows | Decisão da pessoa | Mesmo motivo das specs anteriores |

## Project Structure

### Documentation (this feature)

```text
specs/032-ia-reserva/
├── spec.md, plan.md, research.md (R1–R4 + decisões D1–D7)
├── data-model.md, quickstart.md
├── contracts/ia.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
ia.py                   # reservas, sequencia, responder com reserva, ultima, aviso_reserva, marca, situação
candidatura_ia.py, curriculo_ia.py, analise_perfil.py   # ia.marca(); aviso da reserva
dash/servidor.py        # PUT/GET /api/ia, /api/versao (ia_alerta), testar registra a situação
dash/analise.py         # erro da análise automática com o motivo de cada IA (já vem do IAErro)
dash/API.md, README.md (seção IA)
tests/test_ia_reserva.py
frontend-react: src/services/api/ia.ts, src/components/modals/AISettingsModal.tsx, botão IA (Header),
  src/contexto/Ferramenta.tsx; aviso nos documentos e na candidatura assistida
```

**Structure Decision**: a reserva fica toda dentro de `ia.responder`, a porta única das chamadas. Os chamadores não
precisam saber que existe reserva; só trocam `_marca_ia` por `ia.marca()` e mostram o aviso onde já mostram avisos.
