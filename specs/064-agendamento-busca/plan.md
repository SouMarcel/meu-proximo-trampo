# Implementation Plan: Busca agendada e retomada depois da espera

**Branch**: `064-agendamento-busca` | **Date**: 2026-11-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/064-agendamento-busca/spec.md`

## Summary

Um relógio dentro do servidor do dashboard (`dash/agendador.py`, uma thread que olha a cada 30 s) dispara a busca do
dia no horário escolhido na aba "Agendamento" dos filtros, pela mesma busca da página (`buscador.BUSCA`), com a origem
"agendada": sem as confirmações do diálogo (a escolha está no agendamento), sem os portais com login e com a análise
automática. Ela é pulada se houve busca manual concluída nas 4 horas antes, e não roda se o servidor não estava ligado
no horário (tolerância de 15 min).

Com "Continuar de onde parou", toda busca (página, terminal, chat, agendada ou retomada) que termina com um portal
bloqueado grava em `.cache/retomadas.json` o que faltou daquele portal: as consultas que não rodaram depois do
bloqueio e, pelo banco, as descrições pendentes. O relógio retoma cada portal a cada 6 horas, só com essas consultas e
descrições, até ele terminar com sucesso, até a próxima busca agendada (que assume o lugar) ou, sem busca agendada
ligada, até 24 horas depois da busca que criou a retomada. Uma tentativa perdida (servidor desligado) ou com o portal
ainda em espera é pulada e vai para 6 horas depois.

A espera de cada portal depois de um bloqueio sai das constantes `ESPERA` e passa a ser lida do `.env`
(`<PORTAL>_ESPERA`, minutos, 60 a 2880, padrão 360), com o mesmo leitor tolerante das pausas.

## Technical Context

**Language/Version**: Python 3.11+ (biblioteca padrão); front React + TypeScript na branch `frontend-react`

**Primary Dependencies**: nenhuma nova; usa `dash/buscador.py` (BUSCA), `vagas.py` (executar, TravaBusca,
fontes_em_espera, ler_descricoes), `fontes/_comum.py` (esperas e leitor do `.env`), `filtros.py` (config),
`dash/analise.py` (FILA), `segredos.py`

**Storage**: `config.json` ganha a chave `agendamento` ({ligado, horario, continuar}); `.cache/retomadas.json` (as
retomadas pendentes), `.cache/agendamento.json` (o que o relógio fez: o dia da última agendada e um histórico curto) e
`.cache/buscas-historico.json` (as últimas 20 buscas de qualquer origem, gravadas pela `TravaBusca`); tudo fora do Git.
`.env`: as seis `<PORTAL>_ESPERA`

**Testing**: `python -m unittest discover -s tests` (novos `tests/test_agendamento.py` e `tests/test_espera_env.py`,
com relógio falso e um portal falso que bloqueia na 3ª consulta); os testes dos portais que mexem em `ESPERA` passam a
usar a variável do `.env`; front com `npm run typecheck` e `npm run build` na `frontend-react`

**Target Platform**: servidor local do dashboard (Windows primeiro), página React em `/`; terminal para ver e mudar o
agendamento

**Project Type**: ferramenta local (servidor HTTP da biblioteca padrão + página React + CLI)

**Performance Goals**: o relógio olha a cada 30 s e só lê o `config.json` e dois JSON pequenos; a busca agendada
começa em até 1 min depois do horário (SC-001 pede 2)

**Constraints**: uma busca por vez (a `TravaBusca` de sempre); a busca agendada e a retomada nunca usam a sessão dos
portais com login (rodam fora de `_sessao.na_pagina`); a retomada só faz pedidos ao portal que bloqueou e só os que
faltaram; nunca antes do fim da espera do portal; nunca duas retomadas do mesmo portal; nenhum pedido no relógio em si
(ele só decide e chama a busca)

**Scale/Scope**: 1 busca agendada por dia; até 6 portais com retomada; histórico de 20 buscas e 30 eventos do relógio

## Constitution Check

| Princípio | Como a 064 cumpre |
|---|---|
| I. Local e privado | Tudo roda no servidor local; nada sai do computador além dos pedidos de sempre aos portais. Os arquivos novos ficam em `.cache/` e o agendamento no `config.json`, fora do Git. |
| II. Sem dados pessoais | O `config.json` ganha só ligado, horário e a caixa. Os testes usam portal falso e relógio falso. |
| III. Simples, sem IA obrigatória | Biblioteca padrão (uma thread com `threading.Event.wait`); sem Agendador de Tarefas do Windows nem dependência nova. Sem IA ligada, a busca agendada grava as vagas sem nota, como a manual. |
| IV. Só fatos / texto é dado | Nada muda: as vagas passam pelo mesmo `executar` e pelo filtro de integridade. |
| V. A pessoa decide | A busca sem clique só acontece porque a pessoa ligou o agendamento e marcou "Continuar de onde parou" (pedido explícito, desligado por padrão, revogável na aba e por comando). A página mostra a próxima busca, as retomadas (com Cancelar) e o que aconteceu. O assistente só muda o agendamento pelo terminal com o OK da pessoa. |
| VI. Respeito aos portais | Continua parando no primeiro bloqueio, sem nova tentativa dentro da busca. A retomada não contorna nada: só roda depois que a espera do portal acabou, como a pessoa clicando em Buscar de novo, no máximo a cada 6 horas, e só com o que faltou (menos pedidos que uma busca nova). Uma busca agendada por dia, pulada se houve busca manual nas 4 h antes. Portais com login ficam de fora (só no botão da página). A espera ajustável tem mínimo de 60 minutos; os portais com termos contrários (JobGether, FullStack, InfoJobs, MyGreenhouse) seguem as regras de pausa e parada de cada um. |

Resultado: passa. Ponto a registrar (não é violação): a retomada repete o portal a cada 6 horas enquanto ele bloquear;
o teto é a próxima busca agendada (ou 24 horas sem ela), o que dá no máximo 4 tentativas por dia por portal. Revisto
depois do desenho (Phase 1): continua passando.

## Project Structure

### Documentation (this feature)

```text
specs/064-agendamento-busca/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/api.md     # rotas HTTP, comando do terminal e variáveis do .env
└── tasks.md             (/speckit-tasks)
```

### Source Code (repository root)

```text
agendamento.py               # novo: regras puras (hora devida, pular, retomadas, histórico), arquivos .cache/, comando
vagas.py                     # executar(): só certas consultas por portal e "faltaram" no resultado; TravaBusca grava
                             #   o histórico; cmd_buscar registra as retomadas; subcomando "agendamento"
fontes/_comum.py             # espera_do_env() (o leitor tolerante, em minutos) e ler_espera com a duração da hora
fontes/{linkedin,infojobs,vagascom,jobgether,fullstack,mygreenhouse}.py   # ESPERA → duracao_espera() (<PORTAL>_ESPERA)
filtros.py                   # agendamento_padrao / validar_agendamento / salvar_agendamento; efetivos() com a chave
dash/buscador.py             # Busca.iniciar(origem=...) para "agendada" e "retomada" (sem confirmações, fora da sessão)
dash/agendador.py            # novo: a thread do relógio (tick a cada 30 s) e o estado para a página
dash/servidor.py             # rotas /api/agendamento (GET, PUT), DELETE /api/agendamento/retomadas/<nome>; inicia o relógio
dash/API.md                  # 3.3b Agendamento e retomada; origem nova no estado da busca
.env.exemplo                 # as seis <PORTAL>_ESPERA
README.md, AGENTS.md         # agendamento, retomada, esperas no .env (e o fim das "24 horas")
tests/test_agendamento.py    # novo
tests/test_espera_env.py     # novo
tests/test_{linkedin,infojobs,vagascom,jobgether,fullstack,mygreenhouse}.py   # ESPERA pela variável

# branch frontend-react
src/services/api/agendamento.ts                   # novo: tipos e chamadas
src/components/filters/AgendamentoTab.tsx          # novo: ligar, horário, Continuar de onde parou
src/components/search/AgendamentoStatus.tsx        # novo: próxima busca, retomadas com Cancelar, última execução
(arquivos do diálogo de filtros e do Buscar vagas)  # a aba nova e a origem "agendada"/"retomada" no andamento
```

**Structure Decision**: as regras ficam num módulo da raiz, `agendamento.py`, porque o terminal (`vagas.py buscar`)
também cria retomadas e o comando `vagas.py agendamento` mostra e muda o agendamento sem o servidor. O relógio, que só
existe com o servidor ligado, fica em `dash/agendador.py` e dispara a busca pelo `buscador.BUSCA`, para a página mostrar
o andamento como o de uma busca dela. O front muda na `frontend-react` e chega à `master` pela Action (specs 022/025).
Os caminhos do front são indicativos; o `tasks.md` confere os nomes reais na `frontend-react`.

## Complexity Tracking

Nenhuma violação a justificar.
