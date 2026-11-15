# Implementation Plan: Revisão do perfil ao levar relatos

**Branch**: `050-revisao-relatos-perfil` (worktree saída da `049-analise-reprovacao`) | **Date**: 2026-11-15 |
**Spec**: [spec.md](spec.md)

## Summary

- **`revisao_perfil.py`** (raiz, novo). Guarda a revisão em `dash/dados/revisao_perfil.json`, uma por origem
  (`vaga:<id>` ou `relatos`), com escrita atômica e trava como em `relatos.py`. Funções:
  - `estrutura(perfil)` lê sem IA os lugares do perfil: as seções `## …` e, na Experiência, os cargos `### Cargo —
    Empresa (datas)`, com as linhas de cada um (R2). As seções permitidas são reconhecidas pelo começo do título
    ("Habilidades" casa com "Habilidades e ferramentas (com nível)", o nome que o `montar_perfil` escreve);
  - `montar_pedido(perfil, relatos)`, `ler_proposta` (leitor tolerante `lista_json` de `dash/analise.py`, o mesmo
    da 049) e
    `conferir_proposta(perfil, relatos, proposta)` (sem IA, R3):
    - o texto atual de "muda" e "sai" e o trecho do perfil das discordâncias precisam existir no perfil;
    - o lugar precisa existir; senão, o item vai para Experiência, com aviso, desmarcado;
    - número, data ou nome fora dos relatos e do perfil (`conferir._fatos_do_texto`) desmarca o item, com aviso;
    - afirmação de falta (a regra `NEGACAO` da 049) descarta o item; assunto sensível (`candidatura_ia.sensivel`) ou
      seção fora das permitidas desmarca;
  - `linhas_cruas(perfil, relatos)` acha sem IA a linha de cada relato já colado na seção "Relatos" e cria o item
    "sai" dela (FR-009);
  - `revisar(origem, ids, progresso)` chama a IA, confere e grava a proposta com a impressão do perfil (sha256) em que
    se baseou;
  - `decidir(origem, itens, discordancias)` grava as escolhas (aceito ou recusado; manter o perfil, usar o relato ou
    a correção escrita);
  - `aplicar(perfil, itens)` aplica sem IA os itens aceitos sobre o texto (acrescentar no fim de um cargo ou seção,
    trocar uma linha, tirar uma linha), de baixo para cima, para as posições não se moverem (R4);
  - `gravar(origem)` recusa se o perfil mudou, aplica, grava pelo `primeiros_passos.gravar_perfil` (versão anterior
    guardada, documentos mascarados), marca `no_perfil` nos relatos com algum item aceito e, na origem `vaga:<id>`,
    marca as respostas da análise como levadas;
  - `levar_sem_ia(origem, ids)` é o caminho de hoje (`relatos.levar_ao_perfil`) para quando não há IA (FR-016);
  - CLI `mostra <origem>` para o chat.
- **`reprovacao.py`**:
  - `levar_ao_perfil` vira `guardar_relatos`: no Reescrever e gerar, as respostas ⚠️ "Levar ao meu perfil" vão para
    `relatos.json` (fora do perfil, à espera de revisão) e a resposta guarda o id do relato. Como o relato está fora
    do perfil, o `relatos.com_relatos` já o põe no texto do perfil usado pelo currículo e pela conferência (FR-001);
  - `com_calculos` ganha `para_revisar` (ids dos relatos dessas respostas ainda fora do perfil) e `levadas_em`;
  - mudar a resposta já guardada como relato atualiza esse relato (o `relatos.adicionar` já atualiza o mesmo par
    pergunta e relato; o texto novo vira relato novo, e o antigo, fora do perfil, sai).
- **`dash/gerador.py`**: `iniciar_revisao(origem, ids)`, tipo `revisao_perfil`, situação `revisando` ("Revisando o
  seu perfil…"). O `alvo` é `{vaga_id, titulo, empresa}` na origem da vaga e `{perfil: true}` em Seus relatos.
  `tentar()` repete. `_comecar` passa a aceitar o alvo pronto.
- **`dash/servidor.py`** (rotas em [contracts/api.md](contracts/api.md)):
  - `POST /api/perfil/revisao` (202; sem IA, 200 com o caminho de hoje e o aviso);
  - `GET /api/perfil/revisao?origem=`;
  - `PUT /api/perfil/revisao/decisoes`;
  - `POST /api/perfil/revisao/gravar` (409 quando o perfil mudou);
  - `DELETE /api/perfil/revisao?origem=` (descartar).

  As que alteram algo funcionam só deste computador. O `GET /api/curriculo/reprovacao` passa a trazer
  `para_revisar` e `levadas_em`. O `POST /api/perfil/relatos/{id}/perfil` continua, para o caminho sem IA.
- **Front** (`frontend-react`, worktree `../mpt-front-027b`):
  - `services/api/perfil.ts`: tipos e chamadas da revisão;
  - `contexto/Geracao.tsx`: nome e aviso do tipo `revisao_perfil`; `ehDoAlvo` reconhece o alvo `perfil`;
  - `perfil/RevisaoPerfil.tsx` (novo, usado nos dois lugares): itens agrupados pelo lugar, com "antes → depois",
    aceitar ou recusar, avisos, discordâncias com os dois trechos e as três opções, Gravar no perfil e Descartar;
  - `curriculo/Reprovacao.tsx`: "N respostas para levar ao seu perfil", o botão Revisar e levar ao perfil e a
    revisão abaixo; "levadas ao perfil em DD/MM HH:MM";
  - `perfil/Relatos.tsx`: caixa de marcação por relato, Revisar e levar ao perfil para os marcados, e o "Levar ao
    perfil" de um relato abrindo a mesma revisão.
- **Documentação**: `dash/API.md` (rotas dos relatos), README (parágrafo da análise de reprovação e de Seus relatos),
  AGENTS.md (`PY revisao_perfil.py mostra <origem>`) e uma frase na skill analisar-perfil (a página faz a mesma
  revisão), com `python sincronizar_skills.py`.

## Technical Context

- **Language/Version**: Python 3.10+ (biblioteca padrão); React/TypeScript na `frontend-react`.
- **Primary Dependencies**: nenhuma nova. A IA é a escolhida no painel IA (`ia.responder`, com a reserva da spec 032).
- **Storage**: `dash/dados/revisao_perfil.json` (fora do Git), `{origem: revisão}`. O perfil é gravado pelo
  `primeiros_passos.gravar_perfil`, que guarda a versão anterior em `anexos/perfis-anteriores/`.
- **Testing**: `tests/test_revisao_perfil.py` (unittest, IA falsa, perfil, relatos e análise temporários). Os testes
  da 049 que esperavam o relato no `perfil.md` depois do Reescrever e gerar passam a esperar o relato à espera de
  revisão (SC-001).
- **Target Platform**: Windows primeiro, servidor local em `127.0.0.1:8765`.
- **Constraints**:
  - o perfil muda só no Gravar no perfil, e só com os itens aceitos;
  - uma geração por vez, na mesma fila;
  - documentos mascarados antes da IA e antes de gravar;
  - Objetivo, Contato e Trabalho no exterior ficam fora da proposta.
- **Scale/Scope**: até 20 relatos por revisão, até 40 itens e 10 discordâncias, cada texto com até 600 caracteres.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ A proposta fica em `dash/dados/`. À IA vão o perfil e os relatos escolhidos, como nos outros pedidos, com os documentos mascarados. |
| II. Pública | ✅ Nada da pessoa no código. Os testes usam perfis e relatos fictícios. |
| III. Simples | ✅ Biblioteca padrão. Sem IA, "Levar ao perfil" segue como hoje, com aviso. |
| IV. Só fatos | ✅ O texto novo vem só dos relatos (fatos confirmados pela pessoa) e do perfil. Número, data ou nome fora deles vem desmarcado, com aviso. A IA não escolhe nas discordâncias. Afirmação de falta é descartada. Assuntos sensíveis não são mexidos. |
| V. A pessoa decide | ✅ A revisão roda só no clique. O perfil muda só no Gravar no perfil, item a item, com a versão anterior guardada. Discordância sem escolha impede a gravação. |
| VI. Portais | ✅ Não toca em portal. |

Sem violações; a tabela de complexidade não se aplica.

## Project Structure

### Documentation (this feature)

```text
specs/050-revisao-relatos-perfil/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/api.md
├── checklists/requirements.md
└── tasks.md            # /speckit-tasks
```

### Source Code

```text
revisao_perfil.py              # novo
reprovacao.py                  # guardar_relatos, para_revisar, levadas_em
relatos.py                     # sem mudança de regra (levar_ao_perfil fica para o caminho sem IA)
dash/gerador.py                # iniciar_revisao, alvo perfil
dash/servidor.py               # rotas /api/perfil/revisao
dash/API.md
tests/test_revisao_perfil.py   # novo
tests/test_reprovacao.py       # FR-001
README.md, AGENTS.md, .agents/skills/analisar-perfil/SKILL.md

# frontend-react (../mpt-front-027b)
src/services/api/perfil.ts
src/contexto/Geracao.tsx
src/components/perfil/RevisaoPerfil.tsx   # novo
src/components/perfil/Relatos.tsx
src/components/curriculo/Reprovacao.tsx
```

**Structure Decision**: o mesmo desenho da 049. Um módulo novo na raiz com a regra e a guarda, o gerador para a
fila, o servidor para as rotas e um componente de front usado nos dois lugares.
