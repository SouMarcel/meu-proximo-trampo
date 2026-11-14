---
description: "Tarefas da spec 049 — análise de reprovação antes do currículo da vaga"
---

# Tasks: Análise de reprovação antes do currículo da vaga

**Input**: os documentos em `specs/049-analise-reprovacao/`: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md), [contracts/api.md](contracts/api.md) e
[quickstart.md](quickstart.md).

**Tests**: há testes, porque o projeto testa cada spec (`python -m unittest discover -s tests`) e o quickstart os
lista. Ficam em `tests/test_reprovacao.py`, com IA falsa, banco, perfil e `curriculos/` temporários (padrão de
`tests/test_relatos.py`).

**Caminhos**: o backend fica na worktree `049-analise-reprovacao`, saída da `master`. O front fica na worktree
`../mpt-front-027b`, branch `frontend-react`, e os caminhos dele aparecem como `front:src/...`.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [X] T001 Criar o esqueleto de `reprovacao.py` na raiz, no estilo de `relatos.py`:
  - docstring com o uso;
  - `RAIZ` e o `sys.path` de `dash/`;
  - `import banco`;
  - `class ReprovacaoErro(ValueError)`;
  - `TRAVA = threading.Lock()`;
  - `arquivo()` devolve `banco.ARQUIVO.parent / "reprovacao.json"`;
  - `_carregar()` devolve `{}` com erro;
  - `_gravar(dados)` com escrita atômica (`.tmp` + `os.replace`);
  - as constantes `GRUPOS` (as cinco chaves de data-model.md, com os rótulos da página), `MAX_PERGUNTAS = 10`,
    `MAX_MOTIVOS = 30` e os tamanhos ("motivo str (≤ 400)", "trecho_cv str (≤ 500)", "trecho_vaga (≤ 500)",
    "texto (≤ 300)", "relato (≤ 4000)", "original (≤ 600)", "novo (≤ 800)").
- [X] T002 [P] Criar `tests/test_reprovacao.py` com a base dos testes:
  - `TRAMPO_BANCO` num diretório temporário;
  - `perfil.md` temporário (`conferir.perfil_padrao` e `primeiros_passos.caminho_perfil` apontando para ele);
  - `curriculo_ia.CURRICULOS` temporário;
  - `IAFalsa`, que troca `ia.responder`, `ia.disponivel` e `ia.marca` e devolve respostas em fila;
  - uma vaga fictícia gravada no banco, com descrição.

---

## Phase 2: Foundational (bloqueia todas as histórias)

- [X] T003 Em `curriculo_ia.py`, acrescentar dois argumentos opcionais, sem mudar nada quando faltam (SC-001):
  - `montar_pedido(perfil, vaga, tecnicas, adicional: str = "")`: o bloco `adicional` entra no fim do pedido;
  - `gerar(vaga, tecnicas, progresso=None, perfil=None, adicional="", marca: dict | None = None)`: repassa
    `adicional` ao pedido e faz `meta.update(marca)` antes de gravar o `.meta.json`.
- [X] T004 Em `dash/gerador.py`, preparar a fila para os tipos novos:
  - `ETAPAS` ganha `"analisando": "Analisando como um recrutador…"` e
    `"reescrevendo": "Reescrevendo os trechos genéricos…"`;
  - `NOMES` ganha `"reprovacao": "a análise de reprovação"`;
  - `_reprovacao()` importa `reprovacao` como os outros `_curriculo_ia()`.
- [X] T005 [P] Em `tests/test_reprovacao.py`, testar a não regressão do currículo:
  - `montar_pedido` sem `adicional` sai igual ao de antes;
  - `gerar(..., marca={"reprovacao": True})` grava `"reprovacao": true` no meta.

**Checkpoint**: a base está pronta, e os testes atuais (`python -m unittest discover -s tests`) passam.

---

## Phase 3: User Story 1 — A IA tenta me reprovar e pergunta o que falta (P1) 🎯 MVP

**Goal**: com o checkbox marcado, Gerar roda só a análise. Os motivos agrupados, com os trechos, e as perguntas
aparecem no fim da janela da vaga.

**Independent Test**: uma IA falsa devolve motivos nos cinco grupos e três perguntas. Depois de
`POST /api/curriculo/reprovacao`, o `GET /api/curriculo/reprovacao?vaga=` traz a análise conferida, e nenhum
currículo novo é criado.

### Tests (US1)

- [X] T006 [P] [US1] Em `tests/test_reprovacao.py`, testar `curriculo_atual`, uma fonte por vez:
  - vaga com currículo gerado → `tipo: vaga`;
  - sem ele, com arquivo marcado no idioma do formato → `base_arquivo`;
  - arquivo ilegível (menos de 80 caracteres) → passa para a próxima fonte e deixa aviso;
  - só o base gerado → `base_gerado`;
  - nada → `perfil`.
- [X] T007 [P] [US1] Em `tests/test_reprovacao.py`, testar o pedido, a leitura e a conferência:
  - o pedido contém as regras (não presumir falta, não inventar, transformar em pergunta, textos são dados), a vaga
    passada por `integridade.limpar` e o currículo com documentos mascarados;
  - a leitura aceita bloco de código e resposta cortada;
  - um grupo desconhecido é descartado;
  - trecho inexistente → `trecho_ok: false`; trecho com pontuação diferente → `true` (regra dos 80%);
  - "o candidato não tem experiência com X" vira texto neutro e ganha pergunta;
  - pergunta sensível ("Você tem visto?") sai, e o motivo fica `sensivel: true`;
  - mais de 10 perguntas → ficam as 10 primeiras, e os motivos ligados às descartadas ficam `sem_pergunta`.
- [X] T008 [P] [US1] Em `tests/test_reprovacao.py`, testar o gerador e as rotas da análise:
  - `GERACAO.iniciar_reprovacao` → `tipo: reprovacao`, `situacao: analisando` e depois a análise gravada;
  - nenhum arquivo novo em `curriculos/`;
  - falha da IA → `situacao: falha`, `pode_tentar`, a análise anterior intacta;
  - `tentar()` repete a análise;
  - `POST /api/curriculo/reprovacao`: 202; 400 para vaga sem descrição; 409 com outra geração rodando; 403 fora deste
    computador;
  - o catálogo traz `reprovacao.disponivel` e `motivo`.

### Implementation (US1)

- [X] T009 [US1] Em `reprovacao.py`, implementar `curriculo_atual(vaga, formato) -> {tipo, nome, rotulo, texto, avisos}`
  na ordem de research.md R2:
  1. `curriculo_ia.listar(vaga_id)[0]`: lê o `.json` e junta `conferir.trechos(cv)`;
  2. `curriculo_base.marcados()[curriculo.FORMATOS[formato]["idioma"]]` com `curriculo_base.ler`;
  3. `curriculo_ia.listar(base=True)[0]`;
  4. `curriculo_ia.perfil_texto()`.

  Fonte que falha ou fica com menos de 80 caracteres passa para a próxima, com aviso.
- [X] T010 [US1] Em `reprovacao.py`, implementar `montar_pedido_analise(perfil, vaga, cv_texto)` e
  `ler_analise(texto) -> {motivos, perguntas}`:
  - o pedido segue o texto do usuário na spec (recrutador criterioso, cinco grupos, trecho do currículo, frase da
    vaga, perguntas). Também proíbe afirmar falta, inventar e perguntar sobre autorização, visto, salário,
    deficiência e relocação, e manda não perguntar o que o perfil já responde;
  - a resposta pedida é JSON, no formato de research.md R3;
  - os textos passam por `_mascarar` (`primeiros_passos.mascarar_documentos`), e a vaga por
    `curriculo_ia.texto_da_vaga`;
  - a leitura tolera erros: tenta o objeto inteiro e, se falhar, usa `analise.lista_json` em cada chave.
- [X] T011 [US1] Em `reprovacao.py`, implementar `conferir_analise(bruto, cv_texto) -> (motivos, perguntas)` com as
  regras de data-model.md:
  - descarta grupos fora de `GRUPOS`;
  - corta os textos nos limites;
  - `trecho_ok` com `conferir.norm` e a regra dos 80% (R5); trecho vazio ou "não aparece" vira `null`;
  - troca a negação sobre a pessoa por texto neutro e cria pergunta (R4);
  - aplica `candidatura_ia.sensivel` às perguntas (R6);
  - limita a `MAX_PERGUNTAS` e `MAX_MOTIVOS`, renumera as perguntas de 1 a n e remapeia `motivos[].perguntas`.
- [X] T012 [US1] Em `reprovacao.py`, implementar a guarda e a análise:
  - `analisar(vaga, tecnicas, progresso=None)`: avisa `analisando`, chama `ia.responder` (`tempo=600`), confere e grava
    `{vaga, criada_em, tecnicas, curriculo_analisado, avisos, motivos, perguntas, respostas: {}, respostas_em: None,
    reescritos: [], curriculo_gerado: None, gerado_em: None, levados: []}`, substituindo a anterior da vaga. Inclui
    o aviso de integridade quando a vaga tem a marca da spec 034. `ia.IAErro` vira `ReprovacaoErro`;
  - `obter(vaga_id)` devolve a análise com os campos calculados (`motivos[].estado`, `resumo`,
    `pronta_para_gerar`, `respostas_mudaram`) ou `None`;
  - `disponivel(vaga)` devolve `(bool, motivo)`, falso quando a vaga não tem descrição.
- [X] T013 [US1] Em `dash/gerador.py`:
  - `iniciar_reprovacao(vaga_id, tecnicas)`: confere ocupado, IA, perfil, vaga e `disponivel`; valida as técnicas
    com `curriculo_ia.validar_tecnicas`; guarda `_ultimo_pedido = ("reprovacao", vaga_id, tec)`; roda `_rodar_reprovacao` numa
    thread (`tipo: "reprovacao"`, `situacao: "analisando"`, alvo da vaga);
  - `_rodar_reprovacao`: no fim, `pronto` com o `nome` vazio, ou `falha` com a mensagem (erro inesperado vai ao
    stderr, como em `_rodar`);
  - `tentar()` passa a repetir `reprovacao`;
  - `preparar(vaga_id)` ganha `reprovacao: {disponivel, motivo, anterior}` quando há vaga.
- [X] T014 [US1] Em `dash/servidor.py`, dentro de `_curriculo` (só local), acrescentar `POST /api/curriculo/reprovacao`
  (`{vaga_id, tecnicas}` → 202 estado, com 400 e 404 como no contrato). No GET de `/api/curriculo`, acrescentar
  `/api/curriculo/reprovacao?vaga=` → `{analise, pode_alterar}`.
- [X] T015 [P] [US1] Em `front:src/services/api/curriculo.ts`:
  - tipos `Reprovacao`, `MotivoReprovacao`, `PerguntaReprovacao`, `RespostaReprovacao` e `Reescrito`, conforme
    contracts/api.md;
  - `Catalogo.reprovacao?`, `EstadoGeracao.tipo` com `"reprovacao"`, `SituacaoGeracao` com `"analisando"` e
    `"reescrevendo"`, e `SITUACOES_ATIVAS` com as duas;
  - `MetaCurriculo.reprovacao?: boolean`;
  - as funções `reprovacao(vagaId, tecnicas)` e `obterReprovacao(vagaId)`.
- [X] T016 [P] [US1] Em `front:src/contexto/Geracao.tsx`, acrescentar o nome "A análise de reprovação" e o aviso de
  pronto "saiu: responda as perguntas no fim da janela da vaga." para o tipo `reprovacao`.
- [X] T017 [US1] Em `front:src/components/curriculo/Curriculos.tsx` (`GerarCurriculo`):
  - checkbox **Análise de reprovação** só com `vagaId` e `c.reprovacao`, desmarcado, com a dica "a IA tenta te
    reprovar para a vaga e pergunta o que falta antes de gerar";
  - desabilitado com `c.reprovacao.motivo` quando `disponivel` é falso;
  - marcado, `gerar` chama `curriculoApi.reprovacao`, e o botão vira "Analisar".
- [X] T018 [US1] Criar `front:src/components/curriculo/Reprovacao.tsx` (`SecaoReprovacao({vagaId})`), que carrega
  `obterReprovacao` quando abre e quando muda a `versao` da geração, e mostra:
  - o título "Análise de reprovação", a data e o `curriculo_analisado.rotulo`;
  - os avisos;
  - os motivos agrupados pelos cinco rótulos, só os grupos com motivo; cada um com o texto, o "Trecho do currículo"
    (ou "não aparece no currículo", ou "trecho não encontrado no currículo" quando `trecho_ok` é falso), a "Frase da
    vaga" e "responda na candidatura" quando sensível;
  - a lista de perguntas, por enquanto só para ler.
- [X] T019 [US1] Em `front:src/components/curriculo/Curriculos.tsx` (`SecaoCurriculos`):
  - `ehDoAlvo(estado, vagaId, ["curriculo", "reprovacao"])`;
  - mensagem de falha que diz "A análise não saiu" quando `estado.tipo === "reprovacao"`;
  - `<SecaoReprovacao vagaId={vagaId} />` logo abaixo da lista (ou de "Nenhum currículo gerado pela página ainda."),
    só com `vagaId`.

**Checkpoint**: US1 funciona sozinha. A análise roda, aparece na janela da vaga, e o checkbox desmarcado não muda nada.

---

## Phase 4: User Story 2 — Eu respondo: ❌ não tenho ou ⚠️ tenho, e conto (P1)

**Goal**: cada pergunta aceita Não tenho, Tenho (com relato e destino) ou Pular. As respostas ficam guardadas, e os
motivos mostram ❌, ⚠️ ou sem resposta, com o resumo.

**Independent Test**: com uma análise gravada, o `PUT .../respostas` grava as três formas de resposta. O `GET`
devolve os estados e o resumo certos, e as respostas continuam lá depois de recarregar.

### Tests (US2)

- [X] T020 [P] [US2] Em `tests/test_reprovacao.py`, testar `gravar_respostas`:
  - `nao`, `tenho` com relato, `pular`;
  - "relato obrigatório e não vazio quando tenho": `tenho` vazio é gravado, mas não conta como respondido;
  - destino inválido, pergunta inexistente e resposta inválida → `ReprovacaoErro`;
  - CPF no relato sai mascarado;
  - o estado de cada motivo (❌, ⚠️, sem resposta, sem pergunta; com ❌ e ⚠️ no mesmo motivo, vale ⚠️), o `resumo`, o
    `pronta_para_gerar` e o `respostas_mudaram`;
  - a rota `PUT /api/curriculo/reprovacao/{id}/respostas`: 200, 400, 404 sem análise, 403 fora deste computador;
  - mudar o destino de uma resposta já levada dá 400.

### Implementation (US2)

- [X] T021 [US2] Em `reprovacao.py`, implementar `gravar_respostas(vaga_id, respostas) -> analise`:
  - valida pelo data-model ("resposta: nao | tenho | pular", "destino: perfil | so_aqui; padrão so_aqui",
    "relato ≤ 4000", documentos mascarados);
  - mescla com as respostas já gravadas, porque gravações parciais são aceitas;
  - recusa mudar o destino de uma resposta com `levado`;
  - grava `respostas_em`, tudo sob `TRAVA`.
- [X] T022 [US2] Em `dash/servidor.py`, acrescentar `PUT /api/curriculo/reprovacao/{vaga_id}/respostas` (só local):
  `ReprovacaoErro` → 400, sem análise → 404.
- [X] T023 [P] [US2] Em `front:src/services/api/curriculo.ts`, acrescentar
  `gravarRespostasReprovacao(vagaId, respostas)`.
- [X] T024 [US2] Em `front:src/components/curriculo/Reprovacao.tsx`, tornar as perguntas respondíveis:
  - para cada pergunta, os botões **Não tenho**, **Tenho** e **Pular**;
  - com Tenho, uma caixa de texto para o relato ("conte com as suas palavras onde e como") e os botões de destino
    **Levar ao meu perfil** e **Usar só neste currículo** (padrão: só neste currículo);
  - resposta já levada mostra "levado ao seu perfil" e trava o destino;
  - gravação automática com espera de cerca de 600 ms depois da última mudança, e "salvo" discreto;
  - cada motivo ganha a marca ❌ "não tenho esse requisito", ⚠️ "tenho, mas o currículo não deixa claro" ou "sem
    resposta";
  - o resumo "❌ N · ⚠️ N · sem resposta N".

**Checkpoint**: US1 e US2 funcionam. A pessoa responde, fecha a janela e as respostas continuam lá.

---

## Phase 5: User Story 3 — Reescrever os trechos genéricos e gerar o currículo (P1)

**Goal**: um clique leva os ⚠️ marcados ao perfil, reescreve os trechos genéricos só com o que foi confirmado e gera
o currículo da vaga com isso.

**Independent Test**: com as respostas da US2 e uma IA falsa, o `POST .../gerar` cria o currículo com
`reprovacao: true`, a análise ganha `reescritos` e `curriculo_gerado`, e o relato com destino perfil está no
`perfil.md`. O pedido do currículo leva os ⚠️ "só aqui", os trechos e os ❌.

### Tests (US3)

- [X] T025 [P] [US3] Em `tests/test_reprovacao.py`, testar a reescrita e a geração:
  - o pedido da reescrita traz o texto do usuário ("com base somente nas informações que eu confirmei…"), só os
    motivos dos grupos `experiencia_generica`, `competencia_sem_evidencia` e `resultado_pouco_claro`, os ⚠️ e o
    currículo;
  - a leitura tolera erros (`analise.lista_json`);
  - número que não está nas fontes vira aviso no `Reescrito`;
  - destino `perfil` → relato em `relatos.listar()` com `no_perfil` e linha no `perfil.md`, com versão anterior;
  - `so_aqui` → não aparece em nenhum dos dois, mas aparece no perfil passado a `curriculo_ia.gerar` e na
    conferência, sem ser acusado como fato inventado;
  - o pedido do currículo contém a lista dos ❌ com a regra;
  - "Tentar de novo" depois de falha da IA não duplica o relato no perfil;
  - sem perguntas, gera direto;
  - perguntas pendentes → 400 "responda ou pule as perguntas";
  - rota 202, 404, 409 e 403 fora deste computador.

### Implementation (US3)

- [X] T026 [US3] Em `reprovacao.py`, implementar `levar_ao_perfil(vaga_id) -> [ids]`. Para cada resposta `tenho`
  com `destino: perfil`, sem `levado` e com relato, chamar `relatos.adicionar(pergunta, relato, vaga=vaga)` e
  `relatos.levar_ao_perfil(id)`, depois gravar `levado` e acrescentar a `levados`. `relatos.RelatoErro` (sem perfil)
  vira `ReprovacaoErro`.
- [X] T027 [US3] Em `reprovacao.py`, implementar `montar_pedido_reescrita(perfil, vaga, analise, cv_texto)`,
  `ler_reescrita(texto)` e `conferir_reescrita(itens, fontes)`:
  - o pedido usa o texto do usuário, os motivos dos três grupos com `trecho_cv` e os ⚠️ (pergunta + relato);
  - a resposta pedida é o array `[{original, novo, motivos}]`;
  - a conferência corta pelos limites ("original (≤ 600)", "novo (≤ 800)") e marca avisos com
    `conferir._fatos_do_texto(novo, fontes, "conferir")`.
- [X] T028 [US3] Em `reprovacao.py`, implementar `extras_do_curriculo(analise) -> (bloco_perfil, adicional)`:
  - `bloco_perfil`: "## Respostas confirmadas nesta análise (valem como fatos só para este currículo)" com os ⚠️ `so_aqui`;
  - `adicional`: "## Resultado da análise de reprovação (a pessoa confirmou)", com os trechos reescritos como
    base e "A pessoa respondeu que NÃO tem (nunca apresente como competência nem experiência): …".
- [X] T029 [US3] Em `reprovacao.py`, implementar `reescrever_e_gerar(vaga_id, progresso=None) -> meta`:
  - confere `pronta_para_gerar` e chama `levar_ao_perfil`;
  - avisa `reescrevendo`; lê o currículo de novo com `curriculo_atual`, pelo tipo e nome guardados, ou usa o mesmo
    texto quando a fonte não existe mais;
  - pede a reescrita e grava `reescritos`;
  - chama `curriculo_ia.gerar(vaga, analise["tecnicas"], progresso, perfil=perfil_texto()+bloco_perfil,
    adicional=adicional, marca={"reprovacao": True})`;
  - grava `curriculo_gerado` e `gerado_em`.
- [X] T030 [US3] Em `dash/gerador.py`:
  - `iniciar_reescrita(vaga_id)`: confere ocupado, IA, perfil, análise existente e `pronta_para_gerar` (senão
    `ValueError("responda ou pule as perguntas")`); guarda `_ultimo_pedido = ("reescrita", vaga_id, None)`; roda numa
    thread com `tipo: "curriculo"`, `situacao: "reescrevendo"`;
  - `_rodar_reescrita` chama `banco.registrar_curriculo` e termina `pronto`, com `veredito`, ou `falha`;
  - `tentar()` passa a repetir a reescrita.
- [X] T031 [US3] Em `dash/servidor.py`, acrescentar `POST /api/curriculo/reprovacao/{vaga_id}/gerar` (só local),
  com 400, 404 e 409 conforme o contrato.
- [X] T032 [P] [US3] Em `front:src/services/api/curriculo.ts`, acrescentar `gerarComReprovacao(vagaId)`.
- [X] T033 [US3] Em `front:src/components/curriculo/Reprovacao.tsx`:
  - botão **Reescrever e gerar o currículo**, desabilitado sem `pronta_para_gerar` (dica "responda ou pule as
    perguntas"), com outra geração ativa ou fora deste computador; com sucesso, chama `comecou(estado)` da geração;
  - aviso "as respostas mudaram desde o último currículo" quando `respostas_mudaram`;
  - lista "Trechos reescritos" com "antes → depois" e os avisos de cada trecho;
  - nota "Levados ao seu perfil: N relato(s)" quando há `levados`.
- [X] T034 [US3] Em `front:src/components/curriculo/Curriculos.tsx` (`ItemCurriculo`), mostrar o selo "com análise de
  reprovação" quando `m.reprovacao`.

**Checkpoint**: o fluxo inteiro funciona. Analisar → responder → reescrever e gerar → currículo novo na lista.

---

## Phase 6: User Story 4 — Só a última análise de cada vaga (P2)

**Goal**: uma análise por vaga, com aviso antes de substituir.

**Independent Test**: depois de duas análises na mesma vaga, só a segunda aparece. O catálogo traz `anterior` para o
aviso, e a análise de outra vaga não muda.

- [X] T035 [P] [US4] Em `tests/test_reprovacao.py`, testar a substituição:
  - a segunda análise substitui a primeira;
  - a de outra vaga continua;
  - `preparar()` devolve `reprovacao.anterior` com a data da análise atual;
  - os relatos levados pela primeira continuam no perfil.
- [X] T036 [US4] Em `front:src/components/curriculo/Curriculos.tsx` (`GerarCurriculo`), com o checkbox marcado e
  `c.reprovacao.anterior`, mostrar o aviso "a análise anterior desta vaga (de DD/MM) será substituída" (formatar com
  `diaMes`).

---

## Phase 7: Polish & Cross-Cutting

- [X] T037 [P] Atualizar `dash/API.md` §3.8 com o contrato de `contracts/api.md`: as mudanças no catálogo, no estado
  e no meta, e as quatro rotas.
- [X] T038 [P] Acrescentar ao `README.md` uma linha na seção do currículo pela página sobre a Análise de reprovação.
- [X] T039 Rodar `python -m unittest discover -s tests` na worktree e corrigir as regressões.
- [X] T040 No front (`../mpt-front-027b`), rodar `npm run build` (ou o `tsc` do projeto) para conferir os tipos;
  commitar na `frontend-react` e enviar (`git push origin frontend-react`), o que dispara a Action do front, só com o
  OK do usuário. Para o teste local, copiar o build para `dash/front/` na `marcel`, sem commit, como nas specs
  anteriores.
- [X] T041 Procurar dados pessoais nos arquivos alterados. Commitar na branch `049-analise-reprovacao`, fazer
  `git merge` na `marcel`, rodar `graphify update .`, reiniciar o dashboard (`python iniciar.py --sem-navegador`) e
  passar o roteiro de `quickstart.md` ao usuário.

---

## Dependencies & Execution Order

- **Setup (T001–T002)** → **Foundational (T003–T005)** → US1 → US2 → US3. A US4 depende só da US1.
- A US2 usa a análise gravada pela US1, e a US3 usa as respostas da US2. As três são P1 e formam o fluxo pedido. A
  US1 sozinha já mostra a análise (MVP).
- Dentro de cada história: testes → `reprovacao.py` → `gerador.py` → `servidor.py` → front.
- O front (`front:`) roda em paralelo com o backend da mesma história quando o contrato está fechado: T015 e T016,
  T023, T032.

## Parallel Example

```text
US1: T006, T007, T008 (testes) juntos; depois T009→T012 (reprovacao.py, em sequência);
     T015 e T016 (front: serviços e contexto) em paralelo com T013/T014.
US3: T025 (testes) e T032 (serviço do front) em paralelo; T026→T029 em sequência.
Polish: T037 e T038 em paralelo.
```

## Implementation Strategy

1. **MVP (US1)**: a análise aparece na janela da vaga. Já é útil para ler os motivos.
2. **US2**: respostas guardadas, com ❌ e ⚠️.
3. **US3**: reescrita e currículo melhorado, que completam o objetivo.
4. **US4 + Polish**: aviso de substituição, documentação, testes completos, merge na `marcel` para o teste do
   usuário. A `master`, o push e o PR do front só com o OK dele.
