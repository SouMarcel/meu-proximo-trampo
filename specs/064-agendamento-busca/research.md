# Research: Busca agendada e retomada depois da espera

Decisões do desenho. As do clarify (27/11) estão na spec; aqui ficam as que o código pedia.

## R1. Onde mora o relógio

- **Decision**: uma thread daemon no servidor do dashboard (`dash/agendador.py`), iniciada no `main()` do
  `servidor.py`, que acorda a cada 30 s (`threading.Event.wait(30)`, interrompível para os testes e para o
  encerramento) e decide pela hora do computador (`datetime.now()`, sem fuso, como o resto da ferramenta).
- **Rationale**: a spec pede "só com o servidor ligado"; uma thread não tem dependência nem permissão do sistema. O
  `ThreadingHTTPServer` já convive com as threads da busca e da análise.
- **Alternatives considered**: Agendador de Tarefas do Windows (fora da spec; exigiria permissão e outro processo);
  `sched`/`threading.Timer` com a hora exata (frágil quando o computador dorme: o tick periódico percebe o atraso).

## R2. Hora devida, tolerância e o computador que dorme

- **Decision**: a busca do dia é devida quando `agora` está entre o horário H e H + 15 min, ainda não houve execução
  (ou pulada) com a data de hoje e o agendamento está ligado. Passado H + 15 min sem o servidor ter visto a janela, o
  dia fica como "perdida" (registrada só para o histórico) e nada roda. Uma vez vista dentro da janela, ela fica
  "devida" na memória e espera o que estiver rodando terminar, mesmo que passe de H + 15 min (FR-004).
- **Rationale**: o clarify escolheu "não roda atrasada"; a tolerância cobre o computador que sai do modo de espera. A
  espera por outra busca não pode perder o dia por causa da tolerância.
- **Alternatives considered**: tolerância de 2 min (o computador que acorda devagar perderia o dia); sem tolerância.

## R3. "Busca manual nas 4 horas antes"

- **Decision**: a `TravaBusca` passa a acrescentar cada busca (origem, início, fim, situação) a
  `.cache/buscas-historico.json` (últimas 20). Manual = origem `pagina`, `terminal` ou `chat`. Conta a busca manual
  concluída (`concluida`) ou ainda rodando que começou entre H − 4 h e H. Cancelada, erro e falha não contam.
- **Rationale**: toda busca, de qualquer processo, passa pela `TravaBusca`; o `.cache/busca.json` guarda só a última,
  e o banco só as gravadas. Uma busca manual rodando às 08:00 começou antes de H, então também pula (o FR-004 vale,
  na prática, para a retomada, o Completar descrições e o Forçar verificar rodando no horário).
- **Alternatives considered**: tabela `buscas` do banco (não guarda as que falharam nem a origem de forma confiável);
  `busca.json` (só a última: uma retomada depois da manual apagaria a pista).

## R4. A busca agendada pela busca da página

- **Decision**: `Busca.iniciar(origem="agendada")` reaproveita a thread, o andamento e a gravação da página. Com
  origem diferente de `pagina`: não pede confirmação de busca recente nem de portal em espera (o portal em espera fica
  de fora, com aviso no resultado), não respeita o intervalo mínimo de 30 min (o pulo de 4 h já cobre) e roda fora de
  `_sessao.na_pagina`, então os portais com login ficam de fora pelo `fontes_com_login_fora(pagina=False)`, com aviso.
  Usa `com_nota` como a página (IA e perfil). A `TravaBusca` recebe a origem (`agendada`, `retomada`), e o
  `gravar_resultado` grava essa origem na busca.
- **Rationale**: uma busca só, um código só; a página já sabe mostrar o andamento e o resultado.
- **Alternatives considered**: subprocesso `vagas.py buscar --gravar` (perderia o andamento na página e a análise
  automática pela FILA).

## R5. O que é "o que faltou" de um portal

- **Decision**: em `executar`, para cada portal com `parada()` (os que têm espera), a consulta em que o portal
  bloqueou e as seguintes dele entram em `resultado["faltaram"][nome]` (os dicionários de consulta, que já são JSON).
  As descrições pendentes não são copiadas: já ficam no banco (`descricao_pendente`) e o `ler_descricoes` as pega pela
  `banco.pendentes_de_descricao`. Se a busca não for gravada (bloqueio provável em todos os portais), "faltaram" vira
  todas as consultas do portal, porque as vagas das consultas anteriores se perderam.
- **Rationale**: depois do bloqueio, o `buscar()` do portal volta vazio sem pedido; essas consultas nunca foram
  feitas. O bloqueio na fase das descrições deixa "faltaram" vazio e só descrições pendentes.
- **Alternatives considered**: refazer a busca inteira do portal na retomada (mais pedidos, contra a constituição VI
  "só o necessário"); guardar só (termo, grupo) e recalcular (os filtros podem ter mudado; a consulta guardada é a que
  faltou).

## R6. Quando uma retomada nasce, anda e termina

- **Decision**: depois de cada busca (qualquer origem, com "Continuar de onde parou" ligado), `agendamento.depois_da_busca(
  resultado, origem)` atualiza `.cache/retomadas.json`:
  - origem `agendada`: apaga todas as retomadas antes (ela assume o lugar delas, FR-007);
  - portal que rodou e bloqueou: cria ou atualiza a retomada (faltaram, `proxima = agora + 6 h`, `tentativas + 1`
    se a origem é `retomada`, `criada_em` mantido);
  - portal que rodou sem bloquear: retomada apagada se não sobrou descrição pendente dele (sucesso); se sobrou só por
    causa do limite por busca (`MAX_DESCRICOES`), fica com `faltaram` vazio e `proxima = agora + 6 h`.
  - portal que não rodou (em espera, desligado, com login): nada muda.
  O relógio, a cada tick: tentativa com `proxima` mais de 15 min no passado vira "perdida" e avança de 6 em 6 h até o
  futuro; tentativa devida com o portal ainda em espera vira "pulada" e vai para 6 h depois; senão, roda quando nada
  estiver rodando. Sem a busca agendada ligada, a retomada é apagada 24 h depois de `criada_em`. Desmarcar a caixa
  apaga todas.
- **Rationale**: o clarify pediu "a cada 6 h até terminar com sucesso ou até a próxima agendada". Sem agendada, sem um
  teto a retomada correria para sempre num portal que bloqueia todo dia (o caso do LinkedIn desde 17/11); 24 h faz o
  papel da "próxima agendada".
- **Alternatives considered**: exigir o agendamento ligado para a caixa funcionar (a pessoa que busca à mão também
  quer a retomada); sem teto.

## R7. A retomada roda como

- **Decision**: `Busca.iniciar(origem="retomada", retomada=nome)` chama `executar` com
  `so_consultas={nome: faltaram}` (novo parâmetro: os portais da lista rodam só essas consultas; os outros não rodam).
  Sem consultas, o `executar` vai direto às descrições pendentes do portal. Grava pelo `gravar_resultado` como uma busca
  (as vagas novas das consultas e as descrições completadas), e a análise automática dá as notas (FR-008).
- **Rationale**: o `executar` já tem a pausa, a parada no bloqueio, a fila de descrições e o limite por portal; a
  retomada é uma busca menor.
- **Alternatives considered**: `completar_pendentes` mais um laço próprio de consultas (duplicaria a parada e o
  andamento).

## R8. Espera no `.env`

- **Decision**: `_comum.espera_do_env(var, padrao=360, minimo=60, maximo=2880) -> {"duracao", "definida", "ajuste"}`,
  irmã do `pausa_do_env` (aceita vírgula, valor fora da faixa vira o limite com o aviso, inválido usa o padrão). Cada
  portal troca a constante `ESPERA` por `duracao_espera()`, lida a cada uso (mudar o `.env` vale na próxima conferência
  sem reiniciar). Variáveis: `LINKEDIN_ESPERA`, `INFOJOBS_ESPERA`, `VAGASCOM_ESPERA`, `JOBGETHER_ESPERA`,
  `FULLSTACK_ESPERA`, `MYGREENHOUSE_ESPERA`. O aviso de ajuste entra no começo da busca, junto do aviso de pausa. A
  espera em curso usa a duração atual (a hora gravada é o começo do bloqueio): baixar a variável encurta a espera que
  já estava rolando.
- **Rationale**: o mesmo padrão das pausas, que a pessoa já conhece; ler a cada uso evita guardar estado.
- **Alternatives considered**: horas (o clarify pediu minutos); gravar o fim da espera no arquivo (mudar o `.env` não
  valeria para a espera em curso).

## R9. Concorrência com Completar descrições e Forçar verificar

- **Decision**: o relógio só inicia algo quando `BUSCA.rodando()` é falso, `vagas.ocupada()` é `None`,
  `COMPLETAR.rodando()` é falso e a `_LEITURA` está livre (o Forçar verificar). Se não, fica "devida" e tenta no próximo
  tick. O Completar descrições e o Forçar continuam recusando enquanto a busca agendada ou a retomada roda (já recusam
  com a busca da página).
- **Rationale**: SC-003 (nunca duas ao mesmo tempo) e uma leitura por vez no portal.

## R10. Terminal

- **Decision**: `PY vagas.py agendamento` mostra o agendamento, a próxima busca, as retomadas e a última execução;
  `--ligar HH:MM`, `--desligar`, `--continuar sim|nao` e `--cancelar-retomada <portal>` mudam (grava com
  `filtros.salvar_agendamento`). O `vagas.py buscar` também registra as retomadas, que o relógio do servidor executa
  quando estiver ligado.
- **Rationale**: FR-010; o mesmo validador da página.

## R11. Página

- **Decision**: aba "Agendamento" no diálogo de filtros (ligar, horário com `input type=time`, a caixa, o texto "roda só
  com o dashboard ligado; portais com login ficam de fora"); um quadro curto junto do Buscar vagas: próxima busca,
  retomadas (portal, hora, o que falta, Cancelar) e a última execução; o andamento da busca mostra "Busca agendada" ou
  "Retomada do LinkedIn" pela `origem`. Contrato em [contracts/api.md](contracts/api.md).
