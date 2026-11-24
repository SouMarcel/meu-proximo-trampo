# Implementation Plan: Forçar verificar em fila, uma vaga por vez

**Branch**: `056-forcar-sequencial` | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary

`analise.Fila` troca o conjunto `_forcadas`, que era tratado numa rodada só, por uma fila ordenada com a vaga atual.
Cada vaga é tratada sozinha: a leitura da descrição, com a pausa do portal, e o pedido à IA, com a `FORCAR_PAUSA`. A
página recebe `verificando_agora` e mostra a posição na fila.

## Technical Context

- **Fila hoje** (`dash/analise.py:237`):
  - `forcar(vid)` põe a vaga num `set`;
  - `_rodar` junta todas em `_verificar(ids)`, que lê as descrições seguidas (`vagas.descrever_uma`) e chama
    `analisar(vagas, sem_descricao)` em lotes de até 10;
  - `verificando()` devolve `sorted(set)`.
- **Pausa dos portais:** `fonte.pausa() -> {"faixa": (mín, máx), ...}` (fontes/_comum.py:162), presente nos portais que
  leem páginas. Gupy e Indeed não têm.
- **`.env`:** lido por `segredos.ler(nome)`.
- **Front:**
  - `situacaoNota` (`src/utils/formatters.ts:374`) dá `{tipo: "verificando"}` quando o id está em
    `versao.verificando`;
  - o cartão (`TriageReport.tsx:338`) e o detalhe (`JobDetailModal.tsx:271`) mostram "Verificando…";
  - `App.tsx:337` atualiza `verificando` com a resposta do POST.

## Constitution Check

- **VI (respeito aos portais):** a leitura do Forçar verificar passa a seguir a pausa de cada portal, como a busca.
  Isso fica mais próximo do princípio do que hoje.
- **III:** biblioteca padrão.
- **V:** nada muda no que a pessoa decide.

Gate: passa.

## Decisões

**D1. Fila ordenada** (`dash/analise.py`):

- `self._forcadas: list[str]` (ordem dos cliques) e `self._atual: str | None`;
- `forcar(vid)`:
  - limpa a falha da vaga;
  - acrescenta a vaga ao fim, se ela não estiver na fila nem for a atual;
  - acorda a thread;
- `verificando()` devolve `[atual] + fila`, sem repetir. A rota e a página continuam usando esse campo;
- `agora()` devolve a vaga atual.

**D2. Uma por vez** (`_rodar`):

- enquanto houver vaga forçada:
  1. tira a primeira da fila e a guarda como atual;
  2. roda `_verificar_uma(vid)`;
  3. limpa a atual;
- depois, a análise automática em lotes, como hoje;
- `_verificar_uma` é o `_verificar` de hoje para uma vaga só:
  - vaga removida ou já com nota → sai sem IA;
  - descrição que falta → `_pausar_portal(plataforma)` e depois `descrever_uma`;
  - `_pausar_ia()` e depois `analisar([v], sem_descricao)`;
  - falha só nesta vaga, com o motivo.

**D3. Pausas** (a fila guarda o relógio, e o sono é injetável para os testes: `Fila(dormir=time.sleep, relogio=time.monotonic)`):

- `_pausar_portal(plataforma)`:
  - espera até `pausa_leitura(plataforma)` segundos desde a última leitura daquela plataforma;
  - depois, grava a hora.
- `vagas.pausa_leitura(plataforma) -> float`:
  - o mínimo da faixa de `fonte.pausa()`, com piso de 3 s;
  - portal sem `pausa()` → 3 s.
- `_pausar_ia()`:
  - espera até `pausa_ia()` segundos desde o último pedido da fila à IA;
  - depois, grava a hora.
- `analise.pausa_ia() -> float`:
  - `segredos.ler("FORCAR_PAUSA")`, com vírgula aceita;
  - fora de 0 a 60, vale o limite mais próximo;
  - inválido ou ausente → 5.

**D4. Servidor** (`dash/servidor.py`): `/api/versao` e a resposta do POST `/api/vagas/<id>/analisar` ganham
`"verificando_agora": analise.FILA.agora()`.

**D5. Front** (`frontend-react`, delegado):

- `Versao.verificando_agora?: string | null`;
- `situacaoNota`:
  - id em `verificando` e diferente de `verificando_agora`, com `verificando_agora` definido →
    `{tipo: "na_fila", posicao}`;
  - a posição é o índice do id na lista sem a atual, mais 1;
- o cartão e o detalhe mostram "Na fila (posição N)" no lugar de "Verificando…" e sem o spinner, com um ícone de
  relógio;
- `App.tsx:337` guarda também `verificando_agora` da resposta.

**D6. Documentação:**

- `.env.exemplo`: `# FORCAR_PAUSA=5   # Forçar verificar: segundos entre dois pedidos à IA (0 a 60; padrão 5)`;
- `dash/API.md`: `verificando_agora` em `/api/versao` e no POST;
- o `AGENTS.md` cita as pausas: acrescentar `FORCAR_PAUSA`.

## Testes (`tests/test_forcar.py`, classe nova `TestFilaSequencial`, com IA falsa e `dormir` falso que registra)

- três vagas → três pedidos, um id por pedido, na ordem dos cliques;
- `dormir` chamado com a pausa da IA entre os pedidos, e não antes do primeiro;
- duas vagas do mesmo portal sem descrição → pausa do portal entre as leituras; portais diferentes → sem essa pausa;
- falha da IA na segunda vaga → só ela em `falhas`, e a terceira ganha nota;
- `forcar` da vaga já na fila não duplica;
- `verificando()` e `agora()` durante a rodada;
- `pausa_ia()`: 0, 90 → 60, "abc" → 5, ausente → 5, "2,5" → 2.5;
- `pausa_leitura`: fonte com `pausa()` e sem ela.
