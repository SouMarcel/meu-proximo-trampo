# Implementation Plan: Forçar verificar só com a descrição no computador

**Branch**: `057-forcar-com-descricao` (a partir da `056-forcar-sequencial`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Contexto

No teste da spec 056, sete vagas forçadas falharam. As sete tinham uma coisa em comum: **nenhuma tinha a descrição
no computador**, e o Forçar verificar as mandou para a IA mesmo assim, na regra da nota provisória da spec 021.

- **LinkedIn (4 vagas):** às 22:07 de 23/11, o LinkedIn respondeu **HTTP 429** ao 3º pedido de descrição de um Forçar
  verificar, 90 s depois do anterior. A regra da ferramenta pôs o LinkedIn em espera de 6 h, até 04:07, e durante a
  espera `descrever_uma` devolve "espera" e não lê nada.
- **JobGether (3 vagas):** a API para assistentes **não traz descrição nenhuma**. Conferi de novo na documentação
  oficial (`llms.txt`, `/astroapi/ai/jobs/docs`, `/developers`, `openapi.json`):
  - só existe a busca, com 11 campos por vaga e nenhum de descrição;
  - não há consulta de uma vaga pelo `id`;
  - o MCP só tem `searchJobs`.

  Decisão da pessoa (24/11): **continua só a API** (spec 030). As vagas do JobGether usam o "Colar a descrição"; a
  página da vaga não é lida.

  Os outros campos da API ajudam a nota: `jobFunctions` e `experience`, que hoje são descartados, além de
  `contractType`, `salaryRange`, `remote` e `location`, que já são usados.
- **IA:** além disso, a IA falhou de vários jeitos:
  - Gemini 503 com o OpenRouter vazio;
  - resposta sem o JSON;
  - validação rígida: senioridade fora da lista e um campo de texto num formato inesperado derrubam a análise
    inteira.

**Decisões da pessoa (24/11):**

- O Forçar verificar garante a descrição no computador antes da IA.
- Uma coisa de cada vez: com uma busca rodando, a vaga espera na fila.
- **LinkedIn depois de um 429:** as 6 h de espera continuam. As vagas ficam "aguardando o LinkedIn (até HH:MM)", sem
  gastar a IA, e voltam sozinhas quando a espera acaba. Não muda a constituição.
- **Intervalo entre leituras do LinkedIn no Forçar:** `LINKEDIN_FORCAR_PAUSA`, de 30 a 600 s, padrão 60.
- **Entram também:** nova tentativa da IA, leitura tolerante da resposta e "Colar a descrição" no detalhe da vaga.

**Onde trabalhar:** a worktree `../mpt-057` e a branch `057-forcar-com-descricao` já foram criadas a partir da
`056-forcar-sequencial`, que ainda não está na `master`. As duas vão juntas para a `master` com o OK.

## Fluxo

Spec → plano → tarefas, em `specs/057-forcar-com-descricao/`. A pessoa aprovou seguir direto até o teste nas specs
anteriores; o mesmo vale aqui, depois do OK deste plano. Front delegado; o resto comigo. Merge na branch pessoal, dashboard
reiniciado e teste. `master` só com o OK.

## Back

**1. Descrição obrigatória** (`dash/analise.py`, `Fila._verificar_uma`, da spec 056). Sem descrição no computador, a
fila chama `vagas.descrever_uma(vid)` (vagas.py:530) e age pelo `motivo`:

| motivo | O que a fila faz |
|---|---|
| `None` (leu) | segue para a IA |
| `busca` (busca ou Completar descrições rodando) | `aguardando[vid] = {motivo: "busca"}`; sem IA |
| `espera` ou `bloqueio` | `aguardando[vid] = {motivo: "espera", portal, ate}`; o `ate` vem de `vagas.fontes_em_espera([nome])`; sem IA |
| `sem_fonte` com os dados do portal (JobGether: `funcoes` ou `experiencia`) | vai à IA **pelos dados do portal** (item 7), com a nota marcada; o cartão sugere colar a descrição para a nota completa |
| `sem_fonte` sem dados do portal | falha "O {portal} não entrega a descrição à ferramenta: abra o anúncio e cole o texto em Colar a descrição, no detalhe da vaga" |
| `erro` ou `vazia` | falha "não deu para ler a descrição no {portal}" ou "o anúncio não está mais no portal" |

- A IA nunca é chamada sem descrição. Sai do Forçar verificar o caminho `sem_descricao` / nota provisória.
- A nota provisória que já existe continua com o botão "Reverificar" (T006 da 056), que agora exige a descrição.

**2. Retomar sozinho** (`Fila`):

- novo `self._aguardando: dict[str, dict]`, protegido pela trava;
- `_retomar_aguardando()`: devolve ao fim da fila a vaga `busca` sem busca rodando (`vagas.ocupada() is None` e
  `_LEITURA` livre) e a vaga `espera` sem espera do portal;
- `_rodar` passa a ficar viva enquanto houver aguardando. Dorme num `threading.Event` com intervalo de até 60 s, que
  `forcar()` também acorda, e chama `_retomar_aguardando()` a cada volta;
- `forcar(vid)` numa vaga aguardando tira a vaga de aguardando e a põe no fim da fila;
- `aguardando()` devolve uma cópia;
- `/api/versao` ganha `aguardando: {id: {motivo, portal?, ate?}}`.

**3. Intervalo do LinkedIn** (`vagas.pausa_leitura`, da 056):

- `PAUSAS_FORCAR = {"LinkedIn": ("LINKEDIN_FORCAR_PAUSA", 60.0, 30.0, 600.0)}`;
- valor pelo `.env` (`segredos.ler`), com vírgula aceita, fora da faixa vai para o limite mais próximo, inválido vale o
  padrão;
- os outros portais ficam como na 056.

**4. Nova tentativa da IA** (`_verificar_uma`):

- `analisar([v])` levanta `ia.IAErro` (sem JSON, nenhuma IA respondeu, 503, vazio) → `_pausar_ia()` e uma segunda
  tentativa;
- falhou de novo → falha com o motivo;
- o "sem_dados" com descrição continua falha, sem nova tentativa.

**5. Leitura tolerante** (`banco.validar_analise`, dash/banco.py:353). Vale também para o caminho do chat. Muda nos
campos secundários:

- `senioridade` e `tipo_emprego` (minúsculas, sem acento): ficam os valores conhecidos e os outros são descartados.
  `senioridade_origem` inválida → `"sugerida"`;
- `modelo_trabalho`, `idioma` e `moeda` inválidos → ignorados;
- `resumo`, `fora_dos_criterios` e `analise_modelo` em outro tipo → `_texto_solto`: lista de textos é juntada,
  número ou booleano vira texto, objeto é ignorado;
- os descartes vão para a lista `ajustes` (devolvida no `print` da fila, não gravada);
- `aderencia` e `analise_status` continuam estritos.

**6. Colar a descrição:**

- `banco.colar_descricao(vid, texto)`:
  - exige de 50 a 30.000 caracteres;
  - grava a `descricao` com `aplicar_integridade`, tira `descricao_pendente` e `nota_sem_descricao`;
  - sem nota definitiva, põe `analise_status = "pendente"`;
  - marca `descricao_colada = agora()`;
  - roda `aplicar_criterios`.
- `PUT /api/vagas/<id>/descricao` com `{descricao}`:
  - só deste computador (`_local()`, como o Forçar);
  - grava;
  - com IA ligada e sem nota definitiva, `analise.FILA.forcar(vid)`;
  - resposta `{vaga: com_kit, verificando, verificando_agora}`.

**7. Dados do portal do JobGether** (`fontes/jobgether.py`, `normalizar`, linha 175):

- a vaga passa a guardar:
  - `funcoes`: os `jobFunctions`, até 6 textos de até 80 caracteres;
  - `experiencia`: o `experience`, por exemplo "Senior (5-10 years)", até 80 caracteres;
  - `contrato_portal`: o `contractType` original;
- `analise.montar_pedido` (dash/analise.py:106): toda vaga com esses campos ganha no pedido as linhas "Funções (do
  portal)", "Experiência pedida (do portal)" e "Contrato (do portal)". Isso vale também para quem tem descrição;
- vaga sem descrição que tem esses dados vai à IA com o aviso `SEM_DESCRICAO_COM_DADOS`: "avalie pelo cargo, empresa,
  local, salário e pelos dados do portal (funções, experiência, contrato); a nota é provisória". A nota sai com
  `nota_sem_descricao: True`, e o selo "provisória" e o "Reverificar" da 056 continuam;
- **vagas do JobGether já gravadas:** na próxima busca que trouxer a mesma vaga, ela ganha só os campos de dados do
  portal que faltam (`funcoes`, `experiencia`, `contrato_portal`), sem mexer no resto. É um ajuste pequeno no caminho
  da vaga repetida (`vagas.py`, `banco.registrar_outros_portais`, ou uma função irmã `completar_dados_portal`).

## Front (frontend-react, delegado num brief)

- `Versao.aguardando`. `situacaoNota` ganha `{tipo: "aguardando", motivo, portal?, ate?}`, verificado antes de
  `falha`.
- Cartão (`TriageReport.tsx`) e detalhe (`JobDetailModal.tsx`):
  - "Aguardando o LinkedIn (até 04:07)" ou "Aguardando a busca terminar", com relógio;
  - botão desligado, com a dica "volta sozinha".
- `JobDetailModal`:
  - na vaga sem descrição (ou com `descricao_pendente`), a seção "Colar a descrição": textarea, contador e botão
    "Gravar e verificar" (`vagasApi.colarDescricao`);
  - a falha de `sem_fonte` aponta para essa seção;
  - a nota provisória pelos dados do portal mostra "Nota pelos dados do portal (sem a descrição): cole o texto do
    anúncio para a nota completa";
  - na aba Análise, as funções e a experiência do portal aparecem quando existem.
- `services/api/vagas.ts`: `colarDescricao(id, texto)`.

## Documentação

- `.env.exemplo`: `LINKEDIN_FORCAR_PAUSA`;
- `dash/API.md`: `aguardando` e a rota de colar descrição;
- `AGENTS.md`;
- `specs/021-forcar-verificar` não é editada: a 057 registra que a nota provisória sai do Forçar.

## Testes (`tests/test_forcar.py`, `tests/test_banco_tolerante.py`, vagas fictícias e IA falsa)

- **Atualizar os testes da 021 que esperavam nota provisória pelo Forçar:** `test_na_espera_nota_sem_a_descricao` e
  `test_sem_dados_sem_a_descricao_e_falha` passam a esperar aguardando ou falha, sem IA.
- **Novos:**
  - busca rodando → aguardando, sem IA; a busca termina → `_retomar_aguardando` → nota;
  - espera do portal → aguardando com `ate`; a espera acaba → volta;
  - `sem_fonte` → falha com "cole", zero pedidos à IA;
  - `erro` → falha, sem IA;
  - LinkedIn: 60 s entre leituras; `LINKEDIN_FORCAR_PAUSA` = 10 → 30, 900 → 600, "x" → 60;
  - IA falha uma vez e acerta na segunda; falha duas vezes → falha;
  - `forcar` numa vaga aguardando a devolve à fila;
  - validação tolerante: senioridade `["senior", "especialista"]` → `["senior"]`; resumo em lista → texto;
    `fora_dos_criterios: true` → texto; `aderencia` inválida continua erro;
  - `colar_descricao`: limites, status pendente, integridade; a rota com e sem IA, e 403 fora do computador;
  - `jobgether.normalizar` guarda `funcoes`, `experiencia` e `contrato_portal`; `montar_pedido` traz as linhas "do
    portal";
  - Forçar na vaga do JobGether sem descrição e com dados → um pedido à IA com `SEM_DESCRICAO_COM_DADOS` e a nota
    provisória; sem os dados → falha "cole", sem IA;
  - a vaga repetida da busca ganha os dados do portal que faltavam.

## Verificação

1. `python -m unittest discover -s tests` verde; typecheck e build do front.
2. Na branch pessoal, com o dashboard reiniciado:
   - forçar uma vaga do LinkedIn com a espera ativa → "Aguardando o LinkedIn (até …)", sem pedido à IA;
   - forçar uma vaga do JobGether gravada antes da 057, ainda sem dados do portal → falha pedindo para colar; colar a
     descrição → a vaga entra na fila e ganha nota;
   - depois de uma busca que traga vagas do JobGether → Forçar dá a nota provisória pelos dados do portal;
   - forçar durante uma busca → "Aguardando a busca terminar", e ela volta sozinha no fim.
3. Teste da pessoa. Com o OK: 056 e 057 para a `master`, merge do PR do front e `git merge master` na branch pessoal.
