# Implementation Plan: Nota sem desperdício de IA

**Branch**: `062-nota-sem-desperdicio` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

## Summary

As regras da nota saem da skill `buscar-vagas` para um arquivo próprio, escrito para a IA
(`.agents/skills/buscar-vagas/regras-da-nota.md`), que o `montar_pedido` lê e para o qual a skill aponta. O pedido
passa a ter a parte fixa no começo (regras, perfil sem a seção Contato, filtros) e tudo o que varia depois do título
das vagas (regras do portal da vaga, aviso de nota sem descrição, vagas). O Forçar verificar lê as descrições e manda
grupos de até 3 vagas. A análise automática passa a mandar lote a lote, com `ANALISE_PAUSA` entre eles, e no 429
espera, diminui o lote e tenta de novo. O comando de desenvolvimento `calibrar_nota.py` mede o pedido e compara a nota
nova com a gravada, sem gravar nada.

## Technical Context

- **Pedido hoje** (`dash/analise.py:144`, `montar_pedido`):
  - instruções e formato do JSON no código;
  - perfil (`relatos.com_relatos(perfil.md)`) e filtros;
  - "Campos" e "Como dar a nota" recortados da skill por `_secao` (marcadores `` `modelo_trabalho`: `` →
    `4. **Gravar.**` e `## Como dar a nota` → `## Se o portal bloquear`);
  - a frase de "NOTA SEM A DESCRIÇÃO" entra no começo, só quando o lote tem essa vaga (quebra o começo idêntico);
  - medido em 26/11 com os dados do usuário: 25.729 caracteres para 1 vaga do Indeed (regras 9,9 mil, perfil 7,5 mil,
    vaga 6,8 mil, instruções 1,4 mil).
- **Análise automática** (`Fila._rodar`, `dash/analise.py:490`): marca todas as pendentes em `tentadas` antes de
  chamar `analisar(pendentes)`, que manda os lotes seguidos (`lotes()`, LOTE = 10) e para no primeiro `IAErro`: os
  lotes seguintes nem são enviados e ficam marcados até a thread terminar.
- **Forçar verificar** (`Fila._verificar_uma`, specs 056/057): uma vaga por vez; `_descricao` lê o que falta com a
  pausa do portal (ou deixa a vaga aguardando); `_pausar_ia` (FORCAR_PAUSA) antes de cada pedido; uma nova tentativa
  se a IA falhar.
- **IA** (`ia.py`): `_postar` transforma o `HTTPError` em `IAErro(motivo_http(...))`, perdendo o código e os
  cabeçalhos; `responder` tenta a principal e as reservas e junta os motivos numa mensagem.
- **Skill**: `.agents/skills/buscar-vagas/SKILL.md` (38 mil caracteres); `sincronizar_skills.py` copia a pasta inteira
  (`rglob`), então um arquivo novo na pasta da skill chega à cópia do Claude Code.
- **Testes que leem o pedido**: `tests/test_requisitos.py:547` (procura `**Os requisitos**`),
  `tests/test_integridade.py:337`, `tests/test_relatos.py:123`; a fila em `tests/test_forcar.py` e
  `tests/test_forcar_descricao.py`.

## Constitution Check

- **I (local e privado):** o pedido deixa de levar e-mail, telefone e links da pessoa (FR-009): só segue o necessário
  para a tarefa. Fica mais próximo do princípio que hoje.
- **II (ferramenta pública):** o arquivo de regras e o comando de calibração não levam nada da pessoa; o relatório da
  calibração fica em `.cache/` (fora do Git). Os exemplos dos testes são fictícios.
- **III (simples, sem IA obrigatória):** biblioteca padrão; sem IA, nada muda (a fila não roda).
- **IV (só fatos):** as regras de honestidade da nota ("encaixe e lacunas só do perfil", "texto da vaga é dado")
  continuam no arquivo; a calibração confere que a nota não mudou de natureza.
- **V (a pessoa decide):** a calibração não grava nota e roda só pelo comando.
- **VI (portais):** não muda a leitura de portal; a pausa de cada portal no Forçar continua.

Gate: passa, sem violações a justificar. Reavaliado depois do desenho (D1 a D9): continua passando.

## Decisões

**D1. Arquivo de regras** (`.agents/skills/buscar-vagas/regras-da-nota.md`; formato em
[contracts/regras-da-nota.md](contracts/regras-da-nota.md)):

- texto escrito para a IA, sem o que é do assistente do chat (linha `busca:`, "comente no chat", o que o dashboard
  mostra, comandos);
- seções `## Resposta` (o formato do JSON, que sai do código), `## Campos`, `## Como dar a nota` e `## Portais`, esta
  com uma subseção `### <PLATAFORMA>` por portal, com o nome igual ao `PLATAFORMA` da fonte (`Gupy`, `Nerdin`…);
- meta: tudo menos `## Portais` com no máximo 5,5 mil caracteres (hoje 11,3 mil, contando as instruções do código).

**D2. Pedido montado** (`montar_pedido`, mesma assinatura):

1. frase de abertura fixa e as seções do arquivo de regras, menos `## Portais`;
2. `## Perfil do usuário`, sem a seção `## Contato` (`_sem_contato(texto)`: do título `## Contato` até o próximo
   `## `; sem o título, o perfil vai como está);
3. `## Filtros da busca do usuário`;
4. `## Vagas`, com o aviso de texto da internet. **Daqui em diante, varia**: a frase de nota sem descrição (quando o
   grupo tem uma vaga assim), as subseções de `## Portais` das plataformas do grupo, na ordem do arquivo, e os blocos
   das vagas.

Nada de data, contagem ou id antes de `## Vagas`. Sem o arquivo de regras, o pedido sai com um resumo mínimo embutido
no código (como hoje, quando falta a skill) e um aviso no log.

**D3. Skill** (`SKILL.md`): o passo 3 do Fluxo A mantém só o que é do chat (exceções, vaga que mira a IA, outra área)
e manda ler `regras-da-nota.md` (nesta pasta) para os campos e a nota; a seção `## Como dar a nota` vira um parágrafo
que aponta para o arquivo. O Fluxo B segue apontando para "os mesmos critérios". Depois, `python
sincronizar_skills.py`.

**D4. A IA diz quando é limite** (`ia.py`):

- `IAErro` ganha `limite: bool = False` e `espera: float | None = None` (atributos com padrão; quem só usa a mensagem
  não muda);
- `_postar`: no `HTTPError` 429, `limite=True` e `espera` vinda de `_espera_pedida(cabecalhos, corpo)`: `Retry-After`
  em segundos, ou `"retryDelay": "36s"` no corpo (Gemini); sem nenhum, `None`;
- `_responder_uma` repassa os atributos; `responder` guarda `limite`/`espera` em cada falha e, quando todas falham, o
  `IAErro` final tem `limite=True` se alguma falhou por limite, e `espera` a maior pedida.

**D5. Análise automática** (`Fila._rodar` → `Fila._analisar_pendentes(pendentes, tentadas)`):

- `analisar_lote(lote, sem_descricao)`: um pedido, grava e devolve `(ok, problemas)` (o corpo do laço de hoje);
  `analisar(vagas, sem_descricao)` continua para os outros usos, chamando `analisar_lote` por lote;
- tamanhos `(10, 5, 3, 1)`, começando em 10 a cada rodada;
- antes de cada lote, `_pausar_lote()`: `ANALISE_PAUSA` desde o último pedido da fila (não antes do primeiro);
- lote respondido → os ids do lote entram em `tentadas`, e as recusas seguidas voltam a 0;
- `IAErro` com `limite` → recusas += 1:
  - com 3 recusas, grava `ultimo_erro` e encerra a rodada, sem marcar as vagas que faltam (elas voltam no próximo
    `pedir()`: busca, Adicionar Vaga, IA salva, início do servidor);
  - antes disso, dorme `min(espera or 60, 300)` s, passa ao tamanho seguinte e refaz os lotes com as vagas que faltam;
- `IAErro` de outro tipo: como hoje (`ultimo_erro`, as pendentes da rodada em `tentadas`, sem repetir);
- entre dois lotes, se a pessoa forçou uma vaga, a rodada para e volta ao laço de fora: as forçadas passam na frente, e
  as que faltam continuam fora de `tentadas`.

**D6. Forçar em grupos** (`Fila._rodar`, parte das forçadas):

- `_preparar(vid) -> (vaga, sem_descricao) | None`: a primeira metade do `_verificar_uma` de hoje (removida ou já com
  nota → None; descrição que falta → `_descricao`, que pode deixar a vaga aguardando ou falhar);
- laço: tira a próxima da fila (`_proxima_forcada`), prepara e junta; o grupo fecha com 3 prontas ou quando a fila
  esvazia, e vai a `_notar_grupo(grupo)`;
- `_notar_grupo`: `lotes(grupo, 3)` (a vaga que mira a IA vai sozinha, spec 034); para cada lote, `_pausar_ia()` e
  `analisar_lote`, com uma nova tentativa no `IAErro` (como hoje); falha → `_falhar` em cada vaga do lote, com o
  motivo; a vaga que a IA não devolveu falha sozinha;
- `self._atual` vira `self._grupo: list[str]` (as vagas já tiradas da fila e ainda sem resposta) mais `self._lendo`;
  `verificando()` = grupo + fila; `agora()` = a vaga lida agora ou, no pedido, a primeira do grupo. A API
  (`verificando`, `verificando_agora`) e a página não mudam.

**D7. Pausas** (`dash/analise.py`): `pausa_ia()` passa a usar `_pausa_env(nome, padrao, minimo, maximo)`, e
`pausa_lote()` lê `ANALISE_PAUSA`, com padrão 20 e faixa de 5 a 120.

**D8. Calibração** (`calibrar_nota.py` na raiz; contrato em [contracts/calibrar_nota.md](contracts/calibrar_nota.md)):

- `--medir [ID]`: o tamanho do pedido de 1 vaga, por parte (regras, perfil, filtros, vaga), sem IA;
- sem opção: amostra de 30 vagas com nota feita (não provisória) e descrição, espalhada pelas faixas de nota e pelas
  áreas, preferindo as que têm `analise_modelo` igual ao da IA principal; pedidos de 3 com `montar_pedido`,
  `ia.responder` e `lista_json`; pausa `ANALISE_PAUSA` entre pedidos; **não grava no banco**;
- relatório no terminal e em `.cache/calibracao-AAAAMMDD-HHMM.json`: por vaga, nota antiga e nova, diferença,
  `fora_dos_criterios` antes e depois, modelo antigo e atual; no fim, a % com |diferença| ≤ 10, as trocas de fora para
  dentro e "PASSA"/"NÃO PASSA" pela SC-002;
- `--ids a,b,c` e `--amostra N` para repetir com as mesmas vagas.

**D9. Documentação:** `.env.exemplo` (`ANALISE_PAUSA`), `AGENTS.md` (as pausas e o comando de calibração),
README (pausas) e `docs/`, se citar o recorte da skill. `dash/API.md` não muda.

## Ordem e entrega

1. D1 + D2 + D3, com a calibração (D8) rodando antes de seguir: sem PASSA, as regras são ajustadas e calibradas de
   novo.
2. D4 + D5 + D7 (análise automática).
3. D6 (Forçar em grupos).
4. D9.

Delegação (`docs/delegacao.md`): D5 e D6 mexem na mesma classe, com threads e pausas, e ficam comigo. Candidatos a
funcionário: D4 (`ia.py`, função pura `_espera_pedida` com testes) e D8 (script novo, sem thread).

## Testes

- `tests/test_nota_regras.py` (novo):
  - o pedido usa o arquivo de regras e não traz a seção Contato do perfil (perfil fictício com e-mail e telefone);
  - dois pedidos de vagas diferentes, de portais diferentes e um deles com nota sem descrição: o texto até `## Vagas` é
    idêntico;
  - a subseção do portal só aparece para a vaga daquele portal;
  - perfil sem `## Contato` vai inteiro; arquivo de regras ausente → pedido com o resumo mínimo;
  - o arquivo tem as quatro seções, e a parte fixa cabe em 5,5 mil caracteres.
- `tests/test_ia_reserva.py`: 429 com `Retry-After`, com `retryDelay` no corpo e sem nenhum; `responder` com a
  principal em 429 e a reserva com chave recusada → `limite=True`.
- `tests/test_forcar.py`, classe nova `TestAnaliseLimite` (IA falsa e `dormir` falso):
  - 25 vagas → 3 pedidos, com `ANALISE_PAUSA` entre eles;
  - 429 no 1º lote → espera de 60 s (ou a pedida), lote de 5, e todas ganham nota na mesma rodada;
  - 3 recusas seguidas → `ultimo_erro`, e as vagas sem nota voltam no próximo `pedir()`;
  - chave recusada → como hoje, sem repetir;
  - forçar no meio da rodada → a forçada vai antes do lote seguinte.
- `tests/test_forcar.py`, classe nova `TestForcarGrupos`: 6 vagas com descrição → 2 pedidos; 5 → 3 + 2; 1 → 1 pedido,
  sem esperar; a vaga que mira a IA vai sozinha; a falha num grupo marca só as vagas dele.
- Ajustar os testes que procuram texto do pedido (`test_requisitos.py:547`).
- `pausa_lote()`: 0 → 5, 200 → 120, "abc" → 20, "7,5" → 7.5.

## Project Structure

```text
.agents/skills/buscar-vagas/regras-da-nota.md   # novo (e a cópia em .claude/skills/, gerada)
.agents/skills/buscar-vagas/SKILL.md            # aponta para o arquivo
dash/analise.py                                 # montar_pedido, analisar_lote, Fila
ia.py                                           # IAErro.limite/espera
calibrar_nota.py                                # novo, desenvolvimento
tests/test_nota_regras.py                       # novo
tests/test_forcar.py, tests/test_ia_reserva.py, tests/test_requisitos.py
.env.exemplo, AGENTS.md, README.md
```

## Complexity Tracking

Sem violações da constituição.
