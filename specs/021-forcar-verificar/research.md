# Research: Forçar verificar a nota de uma vaga

Levantamento do código em 19/10/2026 (master `4aff31f`).

## R1. Como a nota sai hoje

- `dash/analise.py`: `FILA.pedir()` acorda uma thread única ("analise-automatica") que pega
  `[v for v in banco.listar_vagas() if precisa(v) and v["id"] not in tentadas]` e chama `analisar()` em lotes de 10.
- `precisa(v)` exige `analise_status == "pendente"`, descrição e nada de `descricao_pendente`.
- `tentadas`: uma tentativa por vaga enquanto a thread vive; uma vaga que a IA não devolveu só é tentada de novo
  quando a thread recomeça.
- Nada volta uma vaga de `sem_analise` ou `sem_dados` para `pendente`; o PATCH da página não aceita `analise_status`.
- O estado exposto é global: `FILA.rodando` e `FILA.erro()` em `GET /api/versao`, consultado pela página a cada 4 s.

## R2. Onde fica o pedido da pessoa

- **Decision**: na própria `Fila`: `forcar(vid)` põe o id em `_forcadas` (conjunto, sem duplicar) e liga
  `_pedido`; a rodada processa as forçadas antes das automáticas e tira cada id do conjunto quando termina.
  `verificando()` devolve a lista; `falhas` guarda `{id: {"motivo", "em"}}` da última tentativa que não deu nota.
- **Rationale**: uma análise por vez continua (a IA local do Claude Code não roda em paralelo); a vaga forçada não
  espera o lote automático inteiro; nada de fila nova nem de estado gravado no banco.
- **Alternatives considered**: gravar `analise_status = "pendente"` pelo PATCH e chamar `pedir()` (não funciona para
  vaga já tentada nem para descrição pendente, e perde o "verificando" por vaga); estado "verificando" no banco
  (sobraria preso se o servidor fechasse no meio).

## R3. Ler a descrição de uma vaga

- **Decision**: `vagas.descrever_uma(vid) -> {"descricao": str, "motivo": str | None}`:
  1. acha a fonte pela `plataforma` (`FONTES` com `descrever`); sem fonte → `motivo = "sem_fonte"`, sem pedido;
  2. busca rodando (`ocupada()`) → `motivo = "busca"`, sem pedido (a busca usa o mesmo estado da fonte);
  3. portal em espera (`fontes_em_espera([nome])`) → `motivo = "espera"`, sem pedido;
  4. `_comum.esquecer()` e `fonte.descrever(v)` (um pedido, com a pausa e o bloqueio da própria fonte);
     exceção → `motivo = "erro"`; `fonte.parada()` depois do pedido → `motivo = "bloqueio"` (a espera já foi gravada
     pela fonte);
  5. texto → `banco.completar_descricao(vid, texto, v.get("tipo_emprego"))`.
- **Rationale**: reaproveita a leitura de cada portal (LinkedIn, Nerdin, startup.jobs) e as regras de espera da
  spec 015/019; um pedido por clique.

## R4. Nota sem a descrição

- **Decision**: `analisar(vagas, sem_descricao=set())`. Para esses ids, `montar_pedido` troca o bloco "Descrição"
  por uma instrução: avaliar só pelo cargo, empresa, local, salário e sinais; dar a nota mesmo assim; dizer no
  resumo que é provisória, sem a descrição. A regra geral "sem descrição suficiente → `sem_dados`" passa a excluir
  essas vagas. As análises voltam com `nota_sem_descricao: true`; `validar_analise` aceita o campo e
  `aplicar_analises` tira a marca das análises que não a trazem.
- **Se a IA devolver `sem_dados` mesmo assim**: conta como falha da vaga ("a IA não conseguiu dar nota sem a
  descrição"), e o botão volta.

## R5. Refazer a nota quando a descrição chega

- **Decision**: em `banco.completar_descricao`, com texto e `nota_sem_descricao`, a marca sai e
  `analise_status` volta a `pendente` (a nota provisória fica visível até a nova chegar). Quem chama já pede a fila:
  `Completar._rodar` (`analise.FILA.pedir()`) e a busca pela página; pelo terminal, a vaga fica `pendente` e a
  fila a pega ao abrir o servidor ou no próximo pedido.

## R6. Rota e permissões

- **Decision**: `POST /api/vagas/<id>/analisar`, tratada antes de `_id_da_rota` (que recusa "/" no id). Só deste
  computador (`_local()`, mensagem `SO_LOCAL_PERFIL`), como `/api/busca/analisar`; as checagens de host e origem
  (`_host_ok`, `_escrita_ok`) valem como em toda escrita.
- Respostas: 202 `{"verificando": [ids]}`; 409 `{"erro": "Para dar nota, ligue uma IA", "sem_ia": true}`; 409
  `{"erro": "a vaga já tem nota"}` (com nota e sem a marca); 404 vaga não encontrada; 403 de outro computador.
- Vaga com `nota_sem_descricao` pode ser forçada de novo (a nota é provisória).

## R7. Página

- `S.verificando` (lista) e `S.falhas` (objeto) vêm de `/api/versao` em `conferir()`; mudança → `render()`.
- Botão `button.btn-plain[data-forcar=id]` "Forçar verificar" numa linha própria dentro de `.decide`, embaixo dos
  botões de decisão, para `!temNota(v) || v.nota_sem_descricao`, triagem `pendente` ou `fora`. Desligado com
  `!S.canWrite`. Verificando → botão desligado "Verificando…" e a dica "a nota chega em alguns minutos". Falha →
  `<p class="hint">Não deu para verificar: motivo</p>` com o botão de volta.
- Clique: `API.send("POST", "/api/vagas/<id>/analisar", {})`; 409 com `sem_ia` → toast com o atalho `abrirIA()`;
  outros erros → toast com a mensagem.
- Selo da nota: com `nota_sem_descricao`, o rótulo pequeno vira "sem a descrição"; chip "Nota sem a descrição";
  banner no detalhe explicando que a nota é provisória e será refeita quando o texto chegar.

## R8. Casos de borda

- Dois cliques/duas abas: `_forcadas` é conjunto; o segundo pedido só devolve o estado.
- Vaga removida no meio: `banco.obter` devolve None e a vaga sai do conjunto sem erro.
- Servidor fechado no meio: o conjunto some; a vaga continua como estava (ou `pendente`, se a descrição foi lida) e
  a fila automática retoma o que estiver `pendente` ao abrir.
