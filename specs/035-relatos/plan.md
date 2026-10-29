# Implementation Plan: Relatos — a candidatura assistida aprende com a pessoa

**Branch**: `035-relatos` (worktree `../mpt-035-relatos`, saída da `master`) | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)

## Summary

- **`relatos.py`** (raiz, novo). Base de relatos em `dash/dados/relatos.json`:
  - `adicionar`, `listar`, `editar`, `apagar`;
  - `bloco()` monta a seção "Relatos da pessoa" e `com_relatos(perfil)` junta essa seção ao perfil;
  - `levar_ao_perfil(id)` grava pelo `primeiros_passos.gravar_perfil`, que guarda a versão anterior;
  - linha de comando `lista`.
- **Texto do perfil para a IA**: `curriculo_ia.perfil_texto`, `entrevista.perfil_texto`,
  `analise_perfil.perfil_texto`, `dash/analise.montar_pedido` e `conferir` (linha de comando) passam por
  `relatos.com_relatos`.
- **`candidatura_ia.py`**:
  - `SENSIVEIS` divide "salário ou pretensão" em "remuneração atual" (vem antes) e "pretensão salarial";
  - `adaptar_relatos(vaga, itens)` faz um pedido à IA para os relatos da página, com `validar_proposta` no formato e
    no limite do campo; sem IA, devolve o relato cortado.
- **`candidatura/formulario.py`**: `PESSOAL` (filiação, CPF, RG, passaporte, nascimento) marca como cadastro também o
  campo de texto longo.
- **`candidatura/memoria.py`**:
  - `NAO_LEMBRAR` passa a ser `{"pretensão salarial", "relocação"}`;
  - `fato(campo)` (remuneração atual, nome da mãe, nome do pai) é guardado na resposta e usado em `valor_para` quando a
    redação muda.
- **`candidatura/auto.responder`**: lê a página, adapta os relatos (comum + texto/área), preenche, grava os relatos
  (`guardar_relatos`) e devolve a fonte de cada campo.
- **Servidor**:
  - `preencher` passa `guardar_relatos`;
  - rotas novas `GET /api/perfil/relatos`, `PUT`/`DELETE /api/perfil/relatos/{id}` e
    `POST /api/perfil/relatos/{id}/perfil`, só deste computador.
- **Front** (`frontend-react`, sobre a branch da 034):
  - `CandidaturaAssistida`: relato × resposta literal, contador numa linha própria, lista do que foi preenchido, opção
    "Guardar meus relatos";
  - `perfil/Relatos.tsx` dentro de Meu perfil;
  - tipos e serviços.
- **Constituição IV** 5.1.2 → 5.2.0. **Documentação**: API.md, README, AGENTS.md e as skills.

## Technical Context

- **Language/Version**: Python 3.10+ (biblioteca padrão); React/TypeScript na `frontend-react`.
- **Storage**: `dash/dados/relatos.json` (fora do Git), escrita atômica com trava, até 300 relatos.
- **Testing**: `tests/test_relatos.py`, com `PaginaFalsa` de `test_candidatura_assistida.py`, IA falsa, banco e
  perfil temporários. Os testes da 027 e da 033 servem de não regressão.
- **Constraints**:
  - pergunta sensível e cadastral nunca vão à IA;
  - a pretensão salarial e a relocação nunca ficam guardadas;
  - nada entra no `perfil.md` sem o clique;
  - os documentos (CPF, RG) são mascarados.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Os relatos ficam em `dash/dados/`; à IA vão os relatos de perguntas comuns, nunca os dados sensíveis ou cadastrais. |
| II. Pública | ✅ Testes fictícios. |
| III. Simples | ✅ Biblioteca padrão; sem IA, o relato vai literal. |
| IV. Só fatos | ⚠ Emenda 5.2.0: a remuneração atual é guardável; o relato da pessoa é fato confirmado, e a IA só o reescreve, sem acrescentar fatos. |
| V. A pessoa decide | ✅ A pessoa escreve o relato e confere na janela; o `perfil.md` só muda no clique "Levar ao perfil"; ela pode desmarcar "Guardar meus relatos". |
| VI. Candidatura assistida | ✅ Só preenche campos. |

Resultado: passa com a emenda decidida pelo usuário.

## Decisões (research)

- **R1. Relato só em pergunta comum de texto.** Nas perguntas de opção, a pessoa escolhe a opção. Pergunta sensível e
  cadastral vão literais. Assim, dado sensível e documentos nunca chegam à IA nem à base de relatos.
- **R2. Uma chamada por clique.** Todos os relatos da página vão num pedido, no formato de `montar_pedido_campos`, com
  o perfil e os relatos já guardados. A resposta passa por `validar_proposta`, que trata limite, opção e número, e pela
  conferência sem IA (`conferir_respostas`).
- **R3. Relatos fora do perfil.md até o clique.** O `perfil.md` é curado; o relato entra nele só com "Levar ao perfil".
  Depois disso, o relato marcado `no_perfil` deixa de ser repetido no bloco.
- **R4. Fato com outra redação.** A memória continua pela pergunta exata. Ela ganha um fallback por `fato` só para três
  fatos estáveis de texto livre (remuneração atual, nome da mãe, nome do pai). Autorização e deficiência ficam na
  memória pela pergunta exata, porque perguntas parecidas podem ter sentido oposto ("tem autorização?" × "precisa de
  patrocínio?").
- **R5. Remuneração atual × pretensão.** "Atual", "current", "último salário" e "quanto ganha hoje" contam como
  remuneração atual. Salário ou remuneração sem "atual" contam como pretensão e continuam perguntados, porque na dúvida
  é melhor perguntar.

## Project Structure

```text
specs/035-relatos/  spec.md, plan.md, tasks.md, quickstart.md, checklists/requirements.md
relatos.py                       # novo
candidatura_ia.py                # SENSIVEIS divididos; adaptar_relatos
candidatura/auto.py              # responder com relatos e fontes
candidatura/formulario.py        # PESSOAL → cadastro
candidatura/memoria.py           # NAO_LEMBRAR; fato()
curriculo_ia.py, entrevista.py, analise_perfil.py, dash/analise.py, conferir.py   # com_relatos
dash/servidor.py                 # guardar_relatos; rotas /api/perfil/relatos
.specify/memory/constitution.md, AGENTS.md, README.md, dash/API.md, skills
tests/test_relatos.py
frontend-react: services/api/candidatura.ts, services/api/perfil.ts, components/kit/CandidaturaAssistida.tsx,
  components/perfil/Relatos.tsx, components/perfil/MeuPerfil.tsx
```
