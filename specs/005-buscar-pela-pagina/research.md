# Research: Buscar vagas pela página

## 1. Uma busca só, com duas portas de entrada

- **Decision**: separar o miolo de `vagas.py cmd_buscar` numa função `executar(...)` que devolve o
  resultado (o mesmo dicionário gravado hoje em `.cache/candidatas.json`) sem imprimir, com dois
  ganchos opcionais: `progresso(evento)` e `cancelado()`. O `cmd_buscar` passa a ser o embrulho que
  imprime, como hoje. Da mesma forma, `gravar()` vira `gravar_resultado(dados, ...) -> resumo`
  (sem imprimir) mais o embrulho de linha de comando.
- **Rationale**: SC-005 pede o mesmo resultado pelos dois caminhos; uma implementação só garante
  isso. A pausa entre consultas, os cortes, as repetidas e as descrições ficam idênticos (FR-001,
  FR-012).
- **Alternatives considered**: rodar `vagas.py buscar --gravar` como subprocesso e ler a saída
  (frágil para progresso e cancelamento; o processo pode sobreviver ao servidor); copiar a lógica
  para o servidor (duplicação).

## 2. Segundo plano no servidor

- **Decision**: uma linha de execução (thread) no servidor, no molde de `dash/analise.py` (`Fila`):
  `dash/buscador.py` com a classe `Busca` (estado em memória protegido por trava, `iniciar`,
  `cancelar`, `estado`). O cancelamento é um `threading.Event` olhado entre as consultas e entre as
  leituras de descrição; a consulta em andamento termina (não há como interromper o portal no meio).
- **Rationale**: biblioteca padrão, mesmo padrão já usado na análise automática; se o servidor for
  fechado, a busca morre junto (spec: "interrompida, nada gravado").
- **Alternatives considered**: subprocesso com arquivo de progresso (mais peças, processo órfão);
  fila externa (dependência nova).

## 3. Uma busca por vez entre processos (página, terminal, chat)

- **Decision**: trava do sistema operacional num arquivo `.cache/busca.trava`
  (`msvcrt.locking` no Windows, `fcntl.flock` no macOS e Linux), segurada durante a parte que
  consulta os portais. A informação de quem busca fica num arquivo separado, `.cache/busca.json`
  (`{origem, inicio, situacao, fim, pid}`), porque no Windows a região travada não pode ser lida
  por outro processo. O sistema solta a trava quando o processo morre, então não sobra trava
  "presa".
- **Rationale**: funciona entre o servidor (página) e o `vagas.py` (terminal e chat) sem depender
  de PID: no Windows, `os.kill(pid, 0)` não testa o processo (o sinal 0 é CTRL_C_EVENT).
- **Alternatives considered**: arquivo com PID (precisa testar se o processo vive, frágil no
  Windows); porta de rede como trava (estranho para a pessoa ver).
- **Interrompida**: se `busca.json` diz `rodando` e a trava está livre, a busca anterior foi
  interrompida (servidor ou terminal fechado no meio); a página mostra isso.

## 4. Intervalo mínimo e aviso de busca recente

- **Decision**: `INTERVALO_MINIMO = 30 min` e `AVISO_RECENTE = 6 h`, contados do `fim` da última
  busca em `busca.json` com situação `concluida` ou `falha` (todos os portais falharam conta:
  insistir piora o bloqueio). Busca cancelada ou interrompida não conta. Sem `busca.json` (instalação
  antiga), vale a data da última busca gravada no banco. Vale para iniciar pela página; o terminal
  continua sem esse limite (spec: "continua igual"), mas as buscas dele contam para a página.
- **Rationale**: valores das Assumptions da spec; o README já recomenda algumas buscas por semana.

## 5. Arquivos de trabalho separados

- **Decision**: a busca da página grava as candidatas em `.cache/pagina/` (mesmo formato), e o
  terminal continua em `.cache/`. Assim a busca pela página não apaga as candidatas de uma busca do
  chat que esperam avaliação (FR-014).

## 6. Nota pela IA

- **Decision**: com IA disponível, perfil gravado e sem "buscar sem nota", as candidatas são gravadas
  com `analise_status: "pendente"` e a busca chama `analise.FILA.pedir()`: a análise automática já
  existente (mesmo pedido, lotes de 10, registro do provedor e do modelo, último erro visível) dá as
  notas. Sem IA, sem perfil ou com "buscar sem nota": `sem_analise`, como o `--gravar` de hoje, e
  nenhum pedido sai. O andamento "n de N" vem de quantas vagas ainda esperam nota (`analise.precisa`)
  e de `FILA.rodando`; "tentar de novo" chama `FILA.pedir()` de novo.
- **Rationale**: FR-006 pede o mesmo pedido da análise automática; não há código novo de IA.
- **Registro**: a busca registrada ganha `origem` (`pagina` ou `terminal`; o chat usa o terminal) e
  `situacao: "concluida"`; com IA, `com_nota: true` (as notas chegam em seguida).

## 7. Andamento na página

- **Decision**: `GET /api/versao` passa a trazer `busca: {situacao, origem}` (a página já consulta a
  cada 4 s); enquanto há busca, a página consulta `GET /api/busca` a cada 2 s (SC-002 ≤ 5 s).
  Eventos de progresso: `consulta` (portal, cargo, grupo, feitas/total, encontradas), `descricoes`
  (lidas/total), `gravando`, `analisando`.
- **Estimativa de duração**: `consultas × 8 s` mais `vagas × 1 s` só para portais que leem a
  descrição à parte (aproximada; mostrada como "cerca de N minutos").

## 8. Rotas e segurança

- **Decision**: `GET /api/busca/plano`, `GET /api/busca`, `POST /api/busca` (iniciar),
  `DELETE /api/busca` (cancelar) e `POST /api/busca/analisar` (tentar a nota de novo). Escrita só do
  próprio computador (`_local()`), com as proteções atuais (host, origem, JSON). Leitura também pela
  rede (`--rede`), com `pode_alterar: false`.

## 9. Mensagens no terminal

- **Decision**: com busca pela página em andamento, `vagas.py buscar` sai com código 4 e "Há uma
  busca rodando pela página do dashboard (desde HH:MM). Espere ela terminar ou cancele por lá." A
  skill `buscar-vagas` ganha uma linha sobre isso e sobre o botão Buscar vagas.

## 10. Testes

- **Decision**: `tests/test_busca.py` com uma fonte falsa (troca de `vagas.FONTES` no teste):
  progresso, cancelamento sem gravar nada, resultado igual pelos dois caminhos, estados de análise,
  trava entre processos (um subprocesso segura a trava) e cálculo do intervalo. A validação do
  quickstart sobe o servidor dentro do roteiro, com a fonte falsa e a IA falsa, sem consultar
  portais de verdade; uma busca real pequena (um cargo, um portal) fica como conferência opcional.
