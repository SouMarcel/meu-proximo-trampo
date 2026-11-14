# Implementation Plan: Análise de reprovação antes do currículo da vaga

**Branch**: `049-analise-reprovacao` (worktree saída da `master`) | **Date**: 2026-11-14 | **Spec**: [spec.md](spec.md)

## Summary

- **`reprovacao.py`** (raiz, novo). Guarda a análise de reprovação por vaga em `dash/dados/reprovacao.json`, só a
  última de cada vaga, com escrita atômica e trava como em `relatos.py`. Funções:
  - `curriculo_atual(vaga, formato)` escolhe o currículo analisado: o último gerado para a vaga; sem ele, o arquivo
    marcado no idioma do formato; sem ele, o último currículo base gerado; sem nenhum, o perfil. Devolve
    `{tipo, nome, rotulo, texto, avisos}`;
  - `montar_pedido_analise`, `ler_analise` (leitor tolerante) e `conferir_analise` (sem IA). A conferência:
    - confere se o trecho existe no currículo;
    - transforma em pergunta a frase que afirma falta;
    - descarta grupos desconhecidos;
    - tira as perguntas sensíveis;
    - limita a 10 perguntas;
  - `analisar(vaga, tecnicas, progresso)` faz a etapa 1 e grava;
  - `obter(vaga_id)` e `gravar_respostas(vaga_id, respostas)` (validação de cada resposta);
  - `levar_ao_perfil(analise)` grava os ⚠️ com destino "perfil" pelo `relatos.adicionar` e pelo
    `relatos.levar_ao_perfil`, e marca cada um como levado, o que impede a duplicação no "Tentar de novo";
  - `montar_pedido_reescrita`, `ler_reescrita` e `conferir_reescrita`. A conferência da reescrita usa os números e
    nomes de `conferir._fatos_do_texto` contra o currículo, o perfil e os ⚠️;
  - `extras_do_curriculo(analise)` monta o bloco dos ⚠️ "só neste currículo", que entra no perfil do pedido e da
    conferência, e o bloco do pedido com os trechos reescritos e os ❌;
  - `reescrever_e_gerar(vaga_id, progresso)` roda a etapa 3: leva ao perfil, reescreve, chama `curriculo_ia.gerar`
    com esses extras e liga o currículo à análise.
- **`curriculo_ia.py`**: `montar_pedido(…, adicional="")` e `gerar(…, adicional="", marca=None)`. O bloco adicional
  vai depois do alvo, e `marca` vai para o meta (`"reprovacao": true`). Sem esses argumentos, tudo segue igual (SC-001).
- **`dash/gerador.py`**:
  - `iniciar_reprovacao(vaga_id, tecnicas)`, tipo `reprovacao`, situação `analisando`;
  - `iniciar_reescrita(vaga_id)`, tipo `curriculo`, situações `reescrevendo` → `escrevendo` → `gerando` →
    `conferindo`;
  - `tentar()` repete os dois;
  - `preparar(vaga_id)` ganha `reprovacao: {disponivel, motivo, anterior}`.
- **`dash/servidor.py`** (rotas em [contracts/api.md](contracts/api.md)):
  - `POST /api/curriculo/reprovacao`;
  - `GET /api/curriculo/reprovacao?vaga=`;
  - `PUT /api/curriculo/reprovacao/{id}/respostas`;
  - `POST /api/curriculo/reprovacao/{id}/gerar`.

  As que alteram algo funcionam só deste computador.
- **Front** (`frontend-react`, worktree `../mpt-front-027b`):
  - `services/api/curriculo.ts`: tipos e chamadas, mais as situações novas em `SITUACOES_ATIVAS`;
  - `contexto/Geracao.tsx`: nome e aviso do tipo `reprovacao`;
  - `Curriculos.tsx`: checkbox no `GerarCurriculo` (só com vaga), aviso de substituição e a seção abaixo da lista
    no `SecaoCurriculos`;
  - `curriculo/Reprovacao.tsx` (novo): motivos por grupo, perguntas com Não tenho/Tenho/Pular, relato e destino,
    resumo ❌/⚠️, trechos "antes → depois" e o botão Reescrever e gerar o currículo.
- **Documentação**: `dash/API.md` §3.8 e uma linha no README (currículo pela página).

## Technical Context

- **Language/Version**: Python 3.10+ (biblioteca padrão); React/TypeScript na `frontend-react`.
- **Primary Dependencies**: nenhuma nova. A IA chamada é a escolhida no painel IA (`ia.responder`, com a reserva da
  spec 032).
- **Storage**: `dash/dados/reprovacao.json` (fora do Git), `{vaga_id: análise}`, uma por vaga. Os relatos levados ao
  perfil vão para `relatos.json` (marcados `no_perfil`) e para o `perfil.md`, com a versão anterior guardada.
- **Testing**: `tests/test_reprovacao.py` (unittest, IA falsa, banco, perfil e pasta de currículos temporários). A
  não regressão vem dos testes atuais de `curriculo_ia`, `gerador`, `relatos` e servidor.
- **Target Platform**: Windows primeiro, servidor local em `127.0.0.1:8765`.
- **Constraints**:
  - uma geração por vez;
  - o texto da vaga é limpo pelo `integridade.limpar`;
  - documentos são mascarados antes de ir à IA e antes de guardar;
  - perguntas sensíveis nunca são feitas;
  - nada vai ao `perfil.md` sem o clique em Reescrever e gerar.
- **Scale/Scope**: uma análise por vaga, até 10 perguntas e cerca de 30 motivos, cada um com trecho de até 500
  caracteres.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ A análise e as respostas ficam em `dash/dados/`. À IA vão a vaga, o currículo e o perfil, como no currículo pela página, com os documentos mascarados. |
| II. Pública | ✅ Nada da pessoa no código. Os testes usam vagas e perfis fictícios. |
| III. Simples | ✅ Biblioteca padrão, sem dependência nova. Sem IA, o checkbox não aparece, e o currículo segue como hoje. |
| IV. Só fatos | ✅ O ❌ vem só da resposta da pessoa. A frase da IA que afirma falta vira pergunta. A reescrita e o currículo usam só o currículo, o perfil e os ⚠️ confirmados, conferidos sem IA. Os ❌ nunca viram competência. Os assuntos sensíveis não são perguntados. Cada motivo cita a frase da vaga e o trecho do currículo. |
| V. A pessoa decide | ✅ A análise roda só no Gerar com o checkbox marcado. O currículo sai só no clique em Reescrever e gerar. O `perfil.md` muda só pelos ⚠️ que a pessoa marcou com "Levar ao meu perfil", e a seção mostra quais foram. |
| VI. Portais | ✅ Não toca em portal: usa a vaga já gravada. |

Sem violação; não há o que justificar em Complexity Tracking.

**Re-check depois do design**: mantido. O contrato não abre rota de escrita para fora deste computador, e o dado
novo fica na pasta de dados.

## Project Structure

### Documentation (this feature)

```text
specs/049-analise-reprovacao/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/api.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code

```text
reprovacao.py                      # novo: análise, respostas, reescrita, guarda
curriculo_ia.py                    # montar_pedido/gerar com `adicional` e `marca`
dash/gerador.py                    # tipos reprovacao e reescrita na mesma fila
dash/servidor.py                   # 4 rotas
dash/API.md                        # §3.8
README.md                          # uma linha
tests/test_reprovacao.py           # novo

# branch frontend-react (worktree ../mpt-front-027b)
src/services/api/curriculo.ts
src/contexto/Geracao.tsx
src/components/curriculo/Curriculos.tsx
src/components/curriculo/Reprovacao.tsx   # novo
```

**Structure Decision**: módulo novo na raiz, ao lado de `relatos.py` e `curriculo_ia.py`, que já são importados pelo
`gerador` do mesmo jeito (`_raiz()`). O front segue o padrão das specs 022 e 025: o código-fonte na `frontend-react`
e o build na `master` pelo PR da Action.

## Complexity Tracking

Sem violações.
