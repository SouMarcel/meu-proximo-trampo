# API do servidor local (dash/servidor.py)

Contrato HTTP que a página da ferramenta (`dash/front/`, o React da branch `frontend-react`; specs 022 e 025)
usa. Tudo aqui foi conferido no código; onde o formato completo mora em outro arquivo, a referência está indicada
(`arquivo.py:linha` no servidor, `src/...` na branch `frontend-react`).

## 1. Regras gerais

**Endereço.** O servidor roda em `http://127.0.0.1:8765` (porta padrão; `--porta` muda). Quando a página
é servida pelo próprio servidor (rota `/`), use caminhos que começam na raiz (`/api/...`). Quando a página vem
de outro servidor deste computador (Live Server em `dash/front/index.html`, Vite etc.), use o endereço absoluto
`http://127.0.0.1:8765`. A página faz assim em `src/services/api.ts` (`getApiBaseUrl`): caminho relativo com a
origem `http://127.0.0.1:8765` ou `http://localhost:8765`, e o endereço absoluto nas outras.

**Origem (CORS).** O servidor só responde a páginas abertas neste computador: origem exatamente
`http://127.0.0.1:<porta>` ou `http://localhost:<porta>` (qualquer porta, só `http`). Para essas origens
ele manda `Access-Control-Allow-Origin` e responde à pré-verificação `OPTIONS` (métodos GET, POST, PUT,
PATCH, DELETE; cabeçalho `Content-Type`). Página em outro domínio (ex.: a prévia hospedada do Figma
Make, `https://...`) é recusada: o navegador não deixa ler as respostas, e as escritas voltam 403.
O cabeçalho `Host` também precisa ser `127.0.0.1` ou `localhost` (senão 421 "host não permitido").

**Formato.** Corpo e resposta em JSON UTF-8 (`application/json; charset=utf-8`). Exceções: `GET /` devolve a
página (`dash/front/index.html`) e os arquivos dela (`/assets/...`), e `/arquivos/...` arquivos (PDF, DOCX, TXT).

**Escritas (POST, PUT, PATCH, DELETE).** Exigem `Content-Type: application/json`, **mesmo sem corpo e
mesmo em DELETE**; sem ele, 403 "pedido recusado". Corpo vazio vale como `{}`. O corpo precisa ser um
objeto JSON. Limite de 1 MB por pedido (15 MB em `POST /api/perfil/material`).

**Erros.** Sempre `{"erro": "mensagem em português"}` com status 4xx/5xx; a mensagem já serve para mostrar à
pessoa. Algumas rotas acrescentam campos (indicados em cada rota). Gerais:

| Status | Quando |
|---|---|
| 400 | dado inválido (a mensagem diz o quê) |
| 403 | "pedido recusado" (origem ou Content-Type) ou ação que só vale no computador da pessoa (ver `pode_alterar`) |
| 404 | "rota não encontrada" ou "vaga não encontrada" |
| 405 | "método não permitido" |
| 409 | conflito de estado (já rodando, sem IA, nada a tentar) |
| 421 | "host não permitido" |
| 500 | "erro interno no servidor do dashboard" (detalhe só na janela do servidor) |

A página trata assim (`src/services/api.ts`, `pedir`): resposta não-ok vira erro com `status`,
`message` = `erro` e `dados` = o JSON inteiro; sem resposta (servidor parado) mostra um aviso fixo e tenta
reconectar sozinho.

**`pode_alterar` (só no computador da pessoa).** Com `--rede`, o servidor também aceita celulares da mesma
rede. Pedidos que não vêm de `127.0.0.1`/`::1` são só leitura em boa parte da API: as rotas marcadas
**[local]** abaixo devolvem 403 ("Só dá para fazer isso no computador onde a ferramenta roda." ou, no
painel IA, "Só dá para mudar a IA no computador onde a ferramenta roda."). Algumas respostas trazem
`pode_alterar: boolean` para a página desligar os botões antes: `/api/ia`, `/api/busca`,
`/api/busca/pendentes`, `/api/curriculo/estado`, `/api/curriculo/catalogo`, `/api/analises-perfil`,
`/api/perfil/estado`. Rotas **sem** essa restrição: leitura de vagas, `PATCH`/`DELETE` de vaga,
`POST /api/vagas`, `POST /api/vagas/link`, `PUT /api/config`, `GET /arquivos/curriculos/...`.

**Acompanhar tarefas longas (polling).** Nada é empurrado pelo servidor; o front atual consulta:

| O quê | Rota | Intervalo | Para quando |
|---|---|---|---|
| Mudanças no banco, IA analisando, Forçar verificar, busca de outra origem | `GET /api/versao` | 4 s (`setInterval`), pulando com a aba escondida; também ao voltar para a aba | sempre |
| Recarregar a lista | `GET /api/vagas` + `GET /api/buscas/ultima` | quando `versao` muda ou o servidor volta | — |
| Busca de vagas | `GET /api/busca` | 2 s | `situacao` fora de `consultando, descricoes, gravando, cancelando, externa`, a análise parou e passaram 20 s da última ação (ou do fim de uma busca com nota) |
| Descrições pendentes | `GET /api/busca/pendentes` | 2 s | `situacao` deixa de ser `lendo` (aí recarrega as vagas) |
| Currículo, carta e respostas | `GET /api/curriculo/estado` | 2 s | `situacao` fora de `escrevendo, gerando, conferindo` |
| Leitura das contas conectadas | `GET /api/contas` + `GET /api/candidaturas/estado` | 1,5 s, só com o diálogo aberto | `situacao` fora de `lendo, aguardando_login` |

Na abertura, o front chama: `GET /api/vagas`, `GET /api/buscas/ultima`, `GET /api/ia`, `GET /api/config`,
`GET /api/busca`, `GET /api/busca/plano`, `GET /api/curriculo/estado`, `GET /api/perfil/estado` (sem perfil,
abre os primeiros passos uma vez por sessão) e, depois de carregar as vagas, `GET /api/busca/pendentes`.

## 2. Objeto vaga

Vem em `GET /api/vagas` (lista) e em várias respostas como `vaga`. É o documento gravado mais dois campos
calculados (`checklist`, `lembretes_pendentes`, de `banco.com_kit`). Campos ausentes = não informados.
Fontes: banco.py:498-604, vagas.py:719-739, kit.py.

**Identidade e origem**

| Campo | Tipo | Significado |
|---|---|---|
| `id` | string | `^[A-Za-z0-9_.:-]{1,64}$`; vaga manual começa com `m-`, post do LinkedIn com `lip-` |
| `origem` | `"busca"` \| `"link"` \| `"manual"` | busca automática; adicionada pelo link ou com "Relatório (decidir depois)"; adicionada direto no quadro |
| `plataforma` | string | uma de: Indeed, LinkedIn, Gupy, InHire, Catho, Startup Jobs, Nerdin, InfoJobs, Vagas.com, JobGether, Remotive, Himalayas, RemoteOK, Jobicy, We Work Remotely, Get on Board, Greenhouse, Lever, Ashby, Outra |
| `outras_plataformas` | string[] | outros portais onde o mesmo anúncio apareceu |
| `formato` | `"post"` | vaga tirada de um post ou texto colado (etiqueta "Post") |
| `busca_id`, `termos`, `grupos` | string, string[], string[] | busca que achou a vaga e os cargos/grupos que a acharam (`grupos` tipo `remoto`, `internacional:<país>`) |
| `encontrada_em`, `criada_em`, `atualizada_em` | data/hora ISO | |

**Anúncio**

| Campo | Tipo | Significado |
|---|---|---|
| `titulo`, `empresa`, `local` | string | |
| `url`, `url_candidatura` | string (http/https) | link da vaga e, se diferente, o da candidatura |
| `ats` | `"greenhouse"` \| `"lever"` \| `"ashby"` | sistema de candidatura reconhecido |
| `publicada_em` | `AAAA-MM-DD` ou null | |
| `descricao` | string (markdown simples, até 20.000) | texto do anúncio — **texto da internet: mostrar como texto** |
| `descricao_pendente` | boolean | o portal limitou os pedidos; a descrição chega depois e só então a vaga ganha nota |
| `salario` (texto), `moeda` (3 letras), `idioma` (2 letras), `tipo` (texto do portal) | | |
| `remoto` | boolean | marcação do portal |
| `modelo_trabalho` | `remoto` \| `hibrido` \| `presencial` \| `nao_informado` | da análise ou da fonte (vale mais que `remoto`) |
| `tipo_emprego` | string[] de `tempo_integral, pj, meio_periodo, estagio, temporario` | |
| `area` | `"nacional"` \| `"internacional"` | aba onde a vaga aparece (sem o campo: o front deduz por `grupos`, `src/utils/formatters.ts` `areaDe`) |
| `pais_vaga` | string | país da vaga internacional |
| `restricao_local` | string | onde a vaga aceita, informado pelo portal |
| `sinais` | string[] | sinais positivos lidos no anúncio (patrocínio de visto, relocation, frases da pessoa) |

**Triagem e quadro (o que a pessoa decide)**

| Campo | Tipo | Significado |
|---|---|---|
| `triagem` | `pendente` \| `seguir` \| `visitada` \| `fora` | Para decidir / Seguidas / Não seguidas / Fora dos critérios |
| `triada_em` | `AAAA-MM-DD` ou null | |
| `motivo_fora` | string[] | por que furou os filtros |
| `etapa` | `salva` \| `aplicada` \| `entrevista` \| `proposta` \| `encerrada` \| null | colunas do quadro: Salva, Aplicação Enviada, Entrevista, Proposta Recebida, Encerrada |
| `etapa_em` | `AAAA-MM-DD` | desde quando está na etapa |
| `resultado` | `nao_aprovado` \| `desisti` \| `cancelada` \| `contratado` \| null | só com etapa `encerrada` (Não aprovado, Desisti, Vaga cancelada, Contratado) |
| `entrevista_em` | `AAAA-MM-DD` ou null | |
| `anotacao` | string (até 5.000) | anotações da pessoa |
| `email_candidatura`, `assunto_candidatura` | string | vaga que pede o currículo por e-mail |
| `kit` | `{estados: {item: "a_fazer"\|"pronto"\|"nao_se_aplica"}, extras: string[], removidos: string[]}` | o que a pessoa marcou no checklist |
| `lembretes` | `{base: "aplicada:AAAA-MM-DD"\|"entrevista:AAAA-MM-DD", parar: bool, follow1?, follow2?, agradecimento?: "feito"\|"dispensado"}` | |
| `curriculos`, `documentos` | string[], `[{tipo, nome, criado_em}]` | arquivos gerados pela página para a vaga |

Regras do front: a vaga está **no quadro** quando `etapa` não é nula e (`origem == "manual"` ou
`triagem == "seguir"`). O **Relatório** mostra as de `origem != "manual"`, separadas por `area`
(aba Relatório de Vagas = nacional, aba Internacional).

**Análise (nota de aderência)**

| Campo | Tipo | Significado |
|---|---|---|
| `analise_status` | `pendente` \| `feita` \| `sem_dados` \| `sem_analise` | esperando a IA / analisada / sem dados para analisar / gravada sem nota |
| `aderencia` | inteiro 0-100 | faixas do front: ≥80 forte, ≥65 boa, ≥50 parcial, abaixo baixa; sem número = "sem nota" |
| `nota_sem_descricao` | boolean | nota provisória, dada sem o texto da vaga; refeita quando a descrição chegar |
| `resumo` | string (até 400) | |
| `encaixe`, `lacunas`, `alertas` | string[] (até 6) | facetas Encaixe, Lacunas, Atenção |
| `senioridade` | string[] de `junior, pleno, senior` | |
| `senioridade_origem` | `declarada` \| `sugerida` | "sugerida" = o anúncio não declara |
| `analise_provedor`, `analise_modelo`, `analisada_em` | string | qual IA deu a nota |
| `autorizacao` | `{valor: patrocina\|nao_precisa\|omisso\|nao_patrocina, frase}` | `frase` = trecho do anúncio |
| `ingles` | `{nivel: nao_pede\|basico\|intermediario\|fluente\|nativo, frase}` | |
| `contratacao` | `[{valor: contractor\|eor\|empregado_brasil\|relocation\|clt\|pj, frase}]` | |
| `fuso` | `{texto, frase}` | |
| `riscos` | `[{tipo: remuneracao\|remoto_hibrido, frase}]` | |
| `pede` | `[{item: curriculo_ingles\|carta\|formulario\|portfolio\|teste\|video, frase}]` | |
| `sistema_candidatura` | string | |

Rótulos desses códigos: kit.py:14-24 e `src/utils/rotulos.ts`.

**Calculados**

- `checklist`: `[{item, rotulo, origem: vaga|analise|anuncio|pessoa, estado: a_fazer|pronto|nao_se_aplica,
  frase, acao: curriculo|carta|respostas|candidatar|null, extra?, base?: {nome, url, idioma}, falta_base?: "pt"|"en"}]`.
  `base.url` é `/arquivos/curriculo-base/<pt|en>` (o currículo da própria pessoa). kit.py:156-198.
- `lembretes_pendentes`: no máximo um, `[{tipo: follow1|follow2|agradecimento, rotulo, desde: AAAA-MM-DD, base}]`.
  Follow-up aos 7 e 14 dias em Aplicação Enviada; agradecimento no dia seguinte à entrevista. kit.py:210-234.

Campos internos que o front não usa: `jk`, `ids_relacionados`, `fora_dos_criterios`.

## 3. Rotas por área

Notação: `*` = obrigatório; **[local]** = só no computador da pessoa (403 de outro aparelho).

### 3.1 Vagas e quadro

**`GET /api/vagas`** — todas as vagas.
Resposta: `{versao: number, vagas: Vaga[]}`. Tela: quadro, lista, Relatório, Internacional.

**`GET /api/buscas/ultima`** — a última busca registrada (linha do topo do Relatório).
Resposta: `{busca: null | {id, data (ISO), termos: string[], brutas, avaliadas, fora_criterios, com_nota: bool,
fontes, janela_horas, resumo, consultas, excluidas_titulo, ja_vistas, candidatas, fortes, boas, parciais, baixas,
origem, situacao}}` (registros antigos podem não ter todos; vagas.py:778-788).

**`PATCH /api/vagas/{id}`** — muda o que a pessoa decide. Só estes campos (outro = 400 "campo não editável"):

| Campo | Tipo |
|---|---|
| `triagem` | `pendente\|seguir\|visitada\|fora` |
| `etapa` | etapa ou null |
| `resultado` | resultado ou null |
| `etapa_em`, `triada_em`, `entrevista_em` | `AAAA-MM-DD` ou null |
| `anotacao` | string (corta em 5.000) |
| `email_candidatura` (validado), `assunto_candidatura` | string; vazio apaga |
| `kit` | objeto `kit` (até 10 extras) |
| `lembretes` | objeto `lembretes` |

Resposta: `{vaga: Vaga}`. Erros: 400, 404. Combinações que o front manda:
- "Seguir com a vaga": `{triagem: "seguir", etapa: "salva", etapa_em: hoje, triada_em: hoje}`
- "Não seguir" e "Marcar todas como não seguidas" (uma por vez): `{triagem: "visitada", etapa: null, triada_em: hoje}`
- "Voltar para triagem": `{triagem: "pendente", etapa: null, resultado: null, triada_em: null}`
- Mover de coluna (arrastar, menu ⋯, seletor Etapa): `{etapa, etapa_em: hoje}` + `resultado: null` se não for `encerrada`
- Resultado (menu ou seletor): `{resultado}`; Salvar no detalhe: `{anotacao, email_candidatura, assunto_candidatura}`
- Data da entrevista: `{entrevista_em}`; checklist: `{kit}`; lembrete Feito/Dispensar/Parar: `{lembretes}`
O front faz uma escrita por vez por vaga (fila) e troca a vaga local pela devolvida.

**`DELETE /api/vagas/{id}`** — "Remover do quadro". Vaga `manual` é apagada; as outras só saem do quadro
(viram `triagem: visitada`, `etapa: null`). Resposta `{ok: true}`. Erro 404.

**`POST /api/vagas/{id}/analisar`** **[local]** — "Forçar verificar" (Relatório, vaga sem nota ou com
`nota_sem_descricao`, triagem pendente ou fora). Corpo `{}`. Resposta 202 `{verificando: string[]}` (ids na
fila). Erros: 404; 409 "a vaga já tem nota"; 409 `{erro: "Para dar nota, ligue uma IA", sem_ia: true}`.
O andamento chega por `/api/versao` (`verificando`, `falhas`).

### 3.1b Faixa salarial (botão no card do quadro e seção na aba Candidatura do detalhe)

Spec 028. A faixa salarial usa só números com fonte. Nada é buscado na internet e nada é estimado pela IA.

**`GET /api/vagas/{id}/salario`** devolve:

```text
{vaga: {id, titulo, empresa, salario (texto), valor: Valor|null},
 moeda,
 parecidas: [Valor + {id, titulo, empresa, plataforma, salario, url, semelhanca}],
 resumo: {n, moeda, minimo, maximo, mediana|null}|null,
 pesquisas: [{texto, fonte, em}],
 links: [{rotulo, url}],
 conversao}
```

Cada campo:
- **`Valor`:** `{min, max, moeda, periodo: "mes"|"ano"|"hora"|"dia"|"semana", mensal_min, mensal_max}`.
- **`parecidas`:** vagas do banco com cargo parecido (semelhança ≥ 0,5), mesma moeda e nível compatível que
  informam salário. Benefícios (VR, VA, auxílio) não contam.
- **`resumo`:** os valores por mês (ano ÷ 12, hora × 220, dia × 22). A mediana só vem com 3 vagas ou mais.
- **`pesquisas`:** o que a pessoa anotou.
- **`links`:** pesquisas para abrir no navegador da pessoa (Glassdoor, salários do Indeed). A ferramenta não lê
  essas páginas, porque o Glassdoor bloqueia acesso automatizado.

| Rota | Corpo | Resposta |
|---|---|---|
| `POST /api/vagas/{id}/salario` | `{texto, fonte}` (até 300 e 120 caracteres) | o mesmo objeto do GET; 400 sem texto ou sem fonte, ou com mais de 20 anotações |
| `DELETE /api/vagas/{id}/salario/{indice}` | — | o mesmo objeto do GET; 400 se a anotação não existe |

A preparação de entrevista (`GET /api/entrevista/{id}`) devolve as anotações em `salario.pesquisas`.

### 3.2 Adicionar vaga (botão Adicionar Vaga)

Fluxo do front: cola o link → `POST /api/vagas/link`. Se for post do LinkedIn ou texto colado, a IA
preenche (`POST /api/vagas/extrair`), a pessoa confere o formulário e só então `POST /api/vagas`.

**`POST /api/vagas/link`** — corpo `{url*: string}` (até 1.000). Respostas:
- 201 (nova) ou 200 (já estava): `{vaga: Vaga, nova: bool, analise_automatica?: bool, empresa?}` — gravada no Relatório.
  Com link de vaga do Greenhouse, do Lever ou do Ashby, `empresa: {sistema, id, nome, url, acompanhada: bool}`: o front
  oferece "Acompanhar" quando `acompanhada` é falso (spec 031).
- 200 de link de post do LinkedIn ainda não gravado: `{post: {id, url, texto, autor, autor_tipo: "empresa"|"pessoa"|...},
  parcial: {url, plataforma: "LinkedIn", formato: "post", post_id, descricao, empresa?, publicado_por?, area, pais_vaga},
  ia: {disponivel: bool, local: bool, provedor: string, modelo: string}}` — **nada gravado**; o front abre o formulário.
- 422 link que não deu para ler: `{erro, parcial: {url, area, pais_vaga, ...o que deu para ler}}` → formulário pré-preenchido.
  Link do JobGether (`jobgether.com/offer/…`): sempre 422, sem pedido à página (ela recusa a ferramenta), com
  `parcial: {url, plataforma: "JobGether", area, pais_vaga}`; a pessoa completa cargo, empresa e descrição.
- 422 post que não deu para ler: `{erro, sugestao: "colar", parcial: {url, plataforma, formato}}` → caixa "colar texto".
- 400 link inválido.

**`GET /api/empresas`** — `{empresas: [{sistema, id, nome, url}], maximo: 50}`: as empresas acompanhadas (spec 031).

**`POST /api/empresas`** — "Acompanhar". Corpo `{url*: string}` (até 1.000): link da página de vagas ou de uma vaga do
Greenhouse, do Lever ou do Ashby (inclusive `embed/job_app?for=…`). Grava só a lista `empresas` do `config.json`, sem
pedido ao sistema da empresa. Respostas: 201 `{empresa, nova: true, empresas}`; 200 com `nova: false` (já estava); 400
link não reconhecido ou "a lista de empresas está cheia (50); remova uma no painel Filtros da busca".

**`PUT /api/config`** e as empresas: o front manda `empresas` no nível de cima; sem essa chave (front antigo), vale
`internacional.empresas`. A lista é gravada sempre em cima.

**`POST /api/vagas/extrair`** **[local]** — a IA tira os campos de um texto livre; nada é gravado.
Corpo `{texto*: string, autor?: string, autor_tipo?: string}`. Resposta `{campos: {titulo, empresa, local, url,
email_candidatura, assunto_candidatura}, parece_vaga: bool, vagas: number, provedor, modelo}`.
Erros: 400 texto vazio; 409 "nenhuma IA configurada"; 502 a IA falhou.

**`POST /api/vagas`** — grava a vaga do formulário.

| Campo | Tipo | Observação |
|---|---|---|
| `titulo*`, `empresa*` | string | 400 sem eles |
| `plataforma` | string da lista | outra vira "Outra" |
| `url` | http/https | link de vaga do JobGether: a vaga fica com o id da busca (`jobgether-…`) e, se já existe, volta a que existe (200, `nova: false`) |
| `local`, `descricao` (até 20.000) | string | |
| `etapa` | `"relatorio"` ou uma etapa | `relatorio` = vai para o Relatório (`origem: link`); etapa = direto no quadro (`origem: manual`); padrão `salva` |
| `area`, `pais_vaga` | `nacional\|internacional`, string | |
| `email_candidatura`, `assunto_candidatura` | string | e-mail validado |
| `formato`, `post_id`, `publicado_por` | `"post"`, `lip-…`, string | só de post |

Resposta 201 `{vaga, nova: true, analise_automatica: bool}` ou 200 `{vaga, nova: false}` (post ou vaga
repetida: devolve a que já existe). A vaga pode cair direto em `triagem: fora` (o front avisa o motivo).

### 3.3 Busca e descrições pendentes (Relatório: Buscar vagas, Completar descrições)

**`GET /api/busca/plano`** — o que o diálogo de confirmação da busca mostra.
`{filtros_ok, perfil_ok, consultas, portais: string[], cargos: string[], janela_horas, resumo, estimativa_min,
ia: {ligada, nome, modelo, cobranca: "uso"|"assinatura"|"gratuito"|""}, ultima: {origem, situacao, inicio, fim}|null,
proxima_em: ISO|null (antes disso não dá para buscar), recente: bool (última há menos de 6 h),
espera: [{portal, ate, motivo}] (portal em espera depois de bloqueio), so_espera: bool, aviso_cargos, aviso_pausa}`.

**`POST /api/busca`** **[local]** — "Buscar agora". Corpo `{sem_nota?: bool, confirmar_recente?: bool,
confirmar_espera?: bool}`. Resposta 202 = estado (abaixo) + `pode_alterar: true`. Erros: 400 sem cargos;
409 `{erro, precisa_confirmar: bool, estado}` (busca rodando, intervalo mínimo de 30 min, busca recente ou portal
em espera sem confirmar).

**`GET /api/busca`** — andamento. `{situacao, origem: "pagina"|"terminal"|..., inicio, fim, com_nota, feitas, total,
encontradas, consulta: {portal, cargo, grupo}|null, descricoes: {lidas, total}|null, erros: string[],
mensagem, resumo: null|{brutas, novas, fora_criterios, ja_vistas, excluidas_titulo, fora_da_janela, busca_id,
com_nota, pendentes, completadas}, analise: {rodando, faltam, erro: {motivo, em}|null}, pode_alterar}`.
`situacao`: `ociosa`, `consultando`, `descricoes`, `gravando`, `cancelando`, `concluida`, `cancelada`, `falha`,
`interrompida`, `externa` (busca do terminal ou do chat). buscador.py:97-113, 200-203, 251-256.

**`DELETE /api/busca`** **[local]** — "Cancelar" (termina a consulta atual e não grava nada). Resposta = estado + `pode_alterar`.

**`POST /api/busca/analisar`** **[local]** — "Tentar a nota de novo". Corpo `{}`. Resposta `{analise: {rodando, faltam, erro}}`.

**`GET /api/busca/pendentes`** — descrições pendentes. `{situacao: "parada"|"lendo"|"pronta"|"erro", lidas,
total, inicio, completadas, restantes, erros, fim, mensagem, pendentes: number, espera: [{portal, ate, motivo}],
pode_alterar}` (campos conforme a situação; buscador.py:283-319).

**`POST /api/busca/pendentes`** **[local]** — "Completar descrições" (lê só as descrições, sem buscar vagas).
Resposta 202 `{situacao: "lendo", lidas, total, inicio}`. Erro 409 (busca rodando ou portal em espera).

### 3.4 Configuração da busca (Filtros da busca, Filtros da busca internacional)

**`GET /api/config`** — `{filtros, consultas: number, opcoes, existe: bool}` (`existe: false` = ainda sem
cargos; o front mostra o aviso de primeira vez).
- `filtros`: `{termos: string[] (cargo entre aspas = frase exata), localidade: {pais, estado, cidade, raio_km},
  modelos: {remoto, hibrido, presencial: bool}, internacional: {ativo, paises, termos, regioes, salario_min_anual_usd,
  fuso_horas, contratacao, aceita_mudar, paises_mudanca, passaporte, autorizacao_trabalho, precisa_sponsor, fontes,
  frases_restricao, frases_positivas}, empresas: [{sistema, id, nome, url}] (até 50; nas duas áreas, spec 031),
  idiomas_aceitos, janela_horas,
  tipos_emprego, senioridades, moedas_aceitas, empresas_excluir, fontes: string[] (indeed, gupy, nerdin, infojobs,
  vagascom, linkedin,
  startupjobs, jobgether)}` (filtros.py:231-273).
- `opcoes`: `{paises, modelos, tipos_emprego, senioridades, moedas, moeda_do_pais, janelas (chaves "24","72","168",
  "360","720"), raios_km, idiomas, regioes, contratacao, fontes_int: [{nome, rotulo, termos}], fontes_nac:
  [{nome, rotulo, termos, precisa}]}` (filtros.py:450-471).

**`PUT /api/config`** — grava os filtros. Corpo = o objeto `filtros` inteiro. Resposta `{filtros, consultas,
opcoes}`. Erro 400 com a regra que falhou (ex.: "informe pelo menos um cargo", "para híbrido ou presencial,
informe a cidade"; filtros.py:355-433). Também usado por "Gravar filtros" nos primeiros passos.

### 3.5 IA (botão IA)

A chave nunca volta para a página: só se existe, os 4 últimos caracteres e a origem.

**`GET /api/ia`** — `{escolha: {provedor, modelo, url_base, reservas?: [{provedor, modelo, url_base}]}|null, efetiva: string (id do provedor), modelo_efetivo,
cobranca_efetiva: "uso"|"assinatura"|"gratuito"|"" (a da escolha; "gratuito" = openrouter/free ou modelo :free do OpenRouter),
url_efetiva, provedores: [{id, nome, precisa_chave, aceita_chave, cobranca: "uso"|"assinatura"|"", modelo_padrao,
url_padrao, onde_obter_chave, dica}], chaves: {id: {cadastrada, final (4 últimos ou ""), origem: "arquivo"|"ambiente"|null}},
claude_instalado, pode_alterar, disponivel: bool (IA pronta para uso), ultimo_erro, sequencia, alerta}`.
- `sequencia` (spec 032): `[{provedor, nome, modelo, url_base, gratuito, chave_ok, principal: bool, situacao: {ok, em
  ("AAAA-MM-DDTHH:MM"), motivo}|null}]`, a principal e as reservas, com a última tentativa de cada uma (gravada em
  `.cache/ia-estado.json`, sem chave nem pedido).
- `alerta`: `{nome, modelo, motivo, em}` quando a última tentativa com a principal falhou; senão `null`. O mesmo vem em
  `GET /api/versao` → `ia_alerta`, para o botão IA.

Reserva: sem escolha explícita, toda chamada à IA tenta a principal e, se ela falhar por motivo do provedor (5xx, 429,
sem crédito, chave recusada, modelo inexistente, tempo esgotado, sem conexão, falta de chave), a próxima reserva, sem
nova tentativa na que falhou. Com mais de uma falhando, o erro lista cada uma: "nenhuma IA respondeu: {nome}: {motivo};
…". Quando a resposta vem de uma reserva, o documento gravado leva `ia: {provedor, modelo, reserva: true, aviso}`, e a
candidatura assistida traz o aviso em `aviso_ia`.
Ids: `claude_code, anthropic, openai, openrouter, groq, deepseek, gemini, compativel, nenhum`.

**`PUT /api/ia`** **[local]** — "Salvar". Corpo `{provedor*, modelo?, url_base? (obrigatório em compativel),
chave?, reservas?: [{provedor*, modelo?, url_base?, chave?}]}`. Resposta = o mesmo de `GET /api/ia`.
- `reservas`: até 3, sem repetir a principal nem outra, sem "nenhum".
- A `chave` de cada reserva vai para o `.env`, nunca para o `config.json`.
- Sem `reservas`, a lista gravada fica como está; `reservas: []` apaga a lista.
- Erro 400 com a regra ("no máximo 3 reservas", "reserva repetida: …", "Sem IA não pode ser reserva").

**`POST /api/ia/testar`** **[local]** — "Testar conexão" (a chave passada não é gravada). Corpo de uma IA só
(`{provedor, modelo?, url_base?, chave?}`); "Testar a sequência" chama uma vez para cada. Resposta `{ok: bool,
mensagem}`, e a situação daquela IA é gravada.

**`DELETE /api/ia/chave/{provedor}`** **[local]** — "Remover" a chave do `.env`. Resposta = estado de `GET /api/ia`
+ `aviso?` (chave definida nas variáveis do sistema). Erro 404 "provedor sem chave".

### 3.6 Perfil (botão Meu perfil / Primeiros passos)

Etapas: `ia, materiais, rascunho, conflitos, anamnese, diagnostico, revisao, filtros, concluido`. Nada é
gravado no `perfil.md` sem a confirmação da pessoa (`PUT /api/perfil`).

**`GET /api/perfil/estado`** — `{existe_perfil, perfil_do_curriculo: {arquivo, data}|null, etapa, materiais:
[{id, tipo: curriculo_pdf|curriculo_docx|linkedin_pdf|linkedin_zip|texto, nome, avisos, trecho (600), tem_texto,
arquivo}], rascunho: null|{objetivo, resumo, formacao, certificacoes, habilidades, idiomas: [{texto, fonte}],
experiencias: [{cargo, empresa, inicio, fim, itens, fonte}], conflitos: [{campo, opcoes: [{valor, fonte}], escolha}],
origem: "ia"|"sem_ia"}, respostas: {id: valor}, contato: {email?, telefone?, linkedin?},
contatos_achados: {emails, telefones, linkedin}, perguntas: [{id, tipo: texto|lista|multi|opcoes|sim_nao, texto,
opcoes?: [{valor, rotulo}], condicao?}], ia_disponivel, pode_alterar}` (primeiros_passos.py:869-895, 483-534).

| Rota | Corpo | Resposta | Botão |
|---|---|---|---|
| `PUT /api/perfil/progresso` [local] | `{etapa?, respostas?: {id: valor\|null}, escolhas?: {"<n>": opção}, contato?}` | estado | trocar de passo, responder/pular pergunta, escolher conflito, contato |
| `DELETE /api/perfil/progresso` [local] | — | estado | Recomeçar / Atualizar o perfil (apaga só o progresso) |
| `POST /api/perfil/material` [local] | `{nome, base64}` (PDF, DOCX, ZIP até 10 MB) ou `{nome, texto}` | 201 `{material, estado}` | escolher/arrastar arquivo, Adicionar texto |
| `DELETE /api/perfil/material/{id}` [local] | — | estado | Remover material |
| `POST /api/perfil/rascunho` [local] | `{sem_ia?: bool}` | estado (com `rascunho`) | Gerar rascunho com IA / Montar sem IA (com IA, até minutos) |
| `POST /api/perfil/previa` [local] | `{markdown?}` | `{markdown, diagnostico: [{tipo: falta\|fraco\|info, mensagem, pergunta, ir}], textos: [{nome, texto}], diferencas: [{tipo: "+"\|"-", texto}]\|null, conflitos_pendentes}` | Diagnóstico, Revisão, "Ver o que muda" |
| `PUT /api/perfil` [local] | `{markdown*}` | `{gravado: caminho, anterior: caminho\|null}` | Gravar perfil / Confirmar e gravar (a versão anterior é guardada) |
| `GET /api/perfil/filtros-propostos` | — | `{filtros, mudancas: [{campo, atual, proposto}], avisos, sugestao_en}` | passo Filtros |
| `POST /api/perfil/filtros-propostos` [local] | `{sugerir_en: true}` | idem, com cargos em inglês sugeridos pela IA | Sugerir os cargos em inglês |

Erros: 400 com a mensagem (ex.: conflito sem escolha no texto, arquivo .doc, IA sem resposta).

**Já tem currículo ("Usar este currículo e ir para as vagas")**

| Rota | Corpo | Resposta |
|---|---|---|
| `GET /api/perfil/curriculos` [local] | — | `{curriculos: [{arquivo, nome, idioma: "pt"\|"en"\|null, data}], curriculo_base: {pt, en: caminho\|null}, existe_perfil}` |
| `POST /api/perfil/do-curriculo` [local] | `{arquivo}` ou `{material_id}` | proposta, **não grava**: `{arquivo, nome, texto, idioma, avisos, perfil, dados: {..., origem?}, edicao: {cargos, cargos_en, cidade, estado, modelos}, filtros\|null, mudancas, existe_perfil, curriculo_base, ja_marcado}` (curriculo_base.py:291-305) |
| `GET /api/perfil/relatos` [local] | — | `{relatos: [{id, pergunta, relato, resposta, vaga: {id, titulo, empresa}\|null, em, no_perfil}]}`: os relatos da pessoa (spec 035), mais recentes primeiro; valem como fato junto do perfil |
| `PUT /api/perfil/relatos/{id}` [local] | `{relato}` | `{relatos}`; 400 relato vazio ou inexistente |
| `DELETE /api/perfil/relatos/{id}` [local] | — | `{relatos}`; 400 inexistente |
| `POST /api/perfil/relatos/{id}/perfil` [local] | — | `{relatos, anterior}`: acrescenta o relato à seção "Relatos" do perfil.md (a versão anterior fica em `anexos/perfis-anteriores/`) e o marca `no_perfil`; 400 sem perfil |
| `POST /api/perfil/do-curriculo/confirmar` [local] | `{arquivo*, idioma, manter_perfil: bool, marcar_base: bool, perfil (markdown, se não mantém), edicao?: {cargos, cargos_en, cidade, estado, modelos: string[]}}` | `{perfil, anterior, filtros, curriculo_base}` |
| `PUT /api/curriculo-base` [local] | `{idioma*: "pt"\|"en", arquivo: caminho\|null}` | `{curriculo_base: {pt, en}}` — marca/desmarca "Seu currículo" |

### 3.7 Análises do perfil (Meu perfil → Análises; todas só no clique)

**`GET /api/analises-perfil`** — `{salvas: {lacunas?, plano?, cargos?, marcas?: {linkedin_en}}, prontidao: [{item, rotulo,
situacao: pronto|falta|nao_informado, origem, detalhe, acao: perfil|filtros_int|curriculo|marcar}], ia: bool,
existe_perfil, pode_alterar}`. Cada análise salva traz `data` (ISO).

| Rota [local] | Corpo | Resposta | Botão |
|---|---|---|---|
| `POST /api/analises-perfil/lacunas` | `{visao: "todas"\|"seguidas"}` | `{visao, vagas, itens: [{rotulo, termos, exemplo, variacoes, peso, parte (0-1), nivel: critica\|alta\|media, vagas, exemplos: [{id, titulo, empresa}]}], data}`; com poucas vagas `{visao, vagas, faltam, itens: []}` (não salva) | Analisar as vagas (sem IA) |
| `POST /api/analises-perfil/plano` | `{}` | `{itens: [{lacuna, passos: string[], semanas}], ia: {provedor, modelo}, data}` | Plano de estudo (IA) |
| `POST /api/analises-perfil/cargos` | `{}` | `{itens: [{titulo, titulo_en, tipo: lateral\|degrau\|vizinho, evidencia, lacuna, conferir: bool}], avisos, ia, data}` | Sugerir cargos (IA) |
| `POST /api/analises-perfil/cargos/filtros` | `{cargos*: [{titulo, titulo_en}], confirmar?: bool}` | `{filtros, mudancas, gravado: bool}`; sem `confirmar` é só a proposta | Levar os marcados para os filtros / Confirmar e gravar nos filtros |
| `PUT /api/analises-perfil/marcas` | `{linkedin_en: bool}` | `{marcas}` | "Meu LinkedIn tem a versão em inglês" |

Erros: 400 com a mensagem (ex.: sem IA, sem perfil, IA fora do formato).

### 3.8 Currículo (detalhe da vaga → Currículos para esta vaga; Meu perfil → Currículo base)

Uma geração por vez no servidor (currículo, carta ou respostas dividem a mesma fila).

**`GET /api/curriculo/catalogo?vaga={id}`** (sem `vaga` = currículo base) — o diálogo "Gerar currículo".
`{tecnicas: {ats|foco|xyz|resultado_primeiro|competencias_primeiro: {nome, padrao, explicacao}}, escolhas:
{paginas|formato|estilo: {nome, padrao, opcoes: {valor: rótulo}}}, sugestao: {<técnica>: bool, paginas, formato,
estilo, motivo}, ia: {ligada, nome, modelo, cobranca: "uso"|"assinatura"|"gratuito"|""}, perfil_ok, pode_alterar}`. Erro 404 vaga não encontrada.
Opções: `paginas` 1|2; `formato` br|us|eu; `estilo` padrao|compacto|executivo (curriculo.py:62-86).

**`POST /api/curriculo`** **[local]** — "Gerar". Corpo `{vaga_id: string|null, tecnicas: {ats, foco, xyz,
resultado_primeiro, competencias_primeiro: bool, paginas: number, formato, estilo}}`. Resposta 202 = estado.
Erros: 400 (sem IA, sem perfil, técnica inválida); 409 `{erro, estado}` (outra geração rodando).

**`POST /api/curriculo/tentar`** **[local]** — "Tentar de novo" o último pedido que falhou. Corpo `{}`. 202 = estado; 409 sem falha.

**`GET /api/curriculo/estado`** — `{situacao: ociosa|escrevendo|gerando|conferindo|pronto|falha, tipo: curriculo|carta|respostas,
alvo: {vaga_id, titulo, empresa} | {base: true}, tecnicas?, inicio, fim, nome, mensagem, veredito: ok|conferir|bloquear,
pronto: bool, pode_tentar: bool, etapa_texto, pode_alterar}` (gerador.py:64-69, 104-106).

**`GET /api/curriculo/lista?vaga={id}`** ou **`?base=1`** — `{curriculos: [meta]}`, mais recentes primeiro. Meta:
`{nome, alvo, tecnicas, arquivos: {json, docx, pdf|null}, disponivel: {pdf, docx, json: bool}, paginas|null, acima_do_limite,
sugestoes_corte, conferencia: {veredito, fatos: [{nivel, mensagem, valor?, trecho?}], ats: [...], requisitos: [{situacao,
texto}], cobertura: {achadas, total, faltando}|null}, pronto, ia, criado_em}` (curriculo_ia.py:202-213; conferir.py:380-387).
Os links de download são `/arquivos/curriculos/{arquivos.pdf|docx}`.

### 3.9 Kit da candidatura (detalhe da vaga → "O que esta candidatura pede")

O checklist vem no próprio objeto vaga (`checklist`) e é marcado com `PATCH /api/vagas/{id}` `{kit}`.

**`GET /api/kit/lista?vaga={id}`** — `{documentos: [meta]}` (cartas e respostas da vaga).
- Carta/mensagem: `{nome, tipo: "carta", formato: "carta"|"mensagem", limite, alvo, respostas: {por_que, problema,
  primeiro_movimento, tom, formato, limite?, idioma?}, idioma, palavras, caracteres, conferencia: {veredito, pontos:
  [{nivel, mensagem, valor}], palavras, ...}, pronto, arquivos: {txt, docx|null}, disponivel, texto, ia, criado_em}`
  (candidatura_ia.py:246-250).
- Respostas: `{nome, tipo: "respostas", alvo, itens: [{pergunta, sensivel: categoria|null, resposta, da_pessoa: bool,
  conferir?: string[]}], arquivos: {txt}, disponivel, ia|null, criado_em, atualizado_em}` (candidatura_ia.py:305-324).

**`POST /api/kit/carta`** **[local]** — "Escrever". Corpo `{vaga_id*, respostas: {formato: "carta"|"mensagem",
tom*: direto|caloroso|formal, por_que*, problema, primeiro_movimento (os dois obrigatórios na carta),
limite? (20-3000, padrão 400, só mensagem), idioma? (pt, en, es, fr, de, it)}}`. 202 = estado de geração (§3.8).

**`POST /api/kit/respostas`** **[local]** — "Preparar respostas". Corpo `{vaga_id*, perguntas*: string}` (uma por
linha, até 30). Perguntas sensíveis (autorização de trabalho, visto ou patrocínio, cidadania, salário ou
pretensão, deficiência, relocação, diversidade; candidatura_ia.py:44) **não vão para a IA** e voltam com
`sensivel` = a categoria. 202 = estado de geração.

Erros das duas: 400 (falta resposta, sem IA, sem perfil, vaga não encontrada); 409 `{erro, estado}`.

**`PUT /api/kit/respostas/{nome}`** **[local]** — "Salvar as suas respostas". Corpo `{pessoa: {"<nº da pergunta, de 1>":
texto}}`. Grava como a pessoa escreveu. Resposta `{documento: meta}`. Erro 400.

### 3.10 Entrevista (botão Preparar entrevista, no cartão em Entrevista e no detalhe)

Todas **[local]**. `{vid}` é o id da vaga. Vaga inexistente: 400 "vaga não encontrada" (id inválido: 404).

**`GET /api/entrevista/{vid}`** — `{vaga: {id, titulo, empresa, etapa, entrevista_em}, dossie: {titulo, empresa, local,
plataforma, salario, moeda, url, url_candidatura, resumo, encaixe, lacunas, alertas, autorizacao, contratacao, ingles,
fuso, riscos, anotacao, aderencia (só os preenchidos; os de análise no formato do objeto vaga), texto_empresa,
resumo_ia: {itens: [{ponto, origem: vaga|texto|deducao, trecho}], data}|null}, perguntas: [{texto, texto_en, tipo:
comportamental|tecnica, porque, origem: padrao|requisito|lacuna|rodada|ia}], historias: [{id, titulo, situacao, tarefa,
acao, resultado, reflexao, conquista, perguntas, conferir, criada_em, atualizada_em}], salario: {faixa, moeda, pretensao,
pontos: string[]}, simulacao: {idioma?, respostas: [{pergunta, resposta, retorno|null, data}]}, rodadas: [{data, etapa,
perguntas, bem, mal, proximos}], existe_perfil, ia: bool}` (entrevista.py:160-224).

| Rota | Corpo | Resposta | Aba / botão |
|---|---|---|---|
| `PUT /api/entrevista/{vid}/empresa` | `{texto}` (até 20.000; colado pela pessoa) | `{texto_empresa}` | Dossiê → Salvar o texto |
| `POST /api/entrevista/{vid}/resumo` | `{}` | `{resumo: {itens, data}}` | Dossiê → Resumir com IA |
| `POST /api/entrevista/{vid}/perguntas` | `{}` | `{perguntas}` (lista completa atualizada) | Perguntas → Mais perguntas com IA |
| `POST /api/entrevista/{vid}/historias` | `{}` | `{rascunhos: [história sem id, com conferir]}` — **não grava** | Histórias → Sugerir histórias com IA |
| `POST /api/entrevista/historias` | `{historia: {id? (atualiza), titulo*, situacao, tarefa, acao, resultado, reflexao, conquista, perguntas, conferir}}` (título e situação ou ação) | `{historia}` | Salvar esta história |
| `DELETE /api/entrevista/historias/{id}` | — | `{ok: true}` | Remover (dois cliques) |
| `POST /api/entrevista/{vid}/simulacao` | `{pergunta*, resposta*, idioma: "pt"\|"en", retorno?: false}` | `{retorno: {funcionou, faltou, mais_forte, conferir}\|null, simulacao, treinar: string[]}` (sem IA, `retorno` null) | Simular → Enviar resposta |
| `POST /api/entrevista/{vid}/rodada` | `{data, etapa, perguntas: string (uma por linha) ou string[], bem, mal, proximos}` | `{rodada}` | Depois → Salvar anotação |

Erros: 400 com a mensagem (sem IA, IA fora do formato, campos vazios).

### 3.11 Contas conectadas e candidaturas (botão Atualizar candidaturas)

Todas **[local]**. Portais ativos: `gupy` e `indeed` (LinkedIn desativado: 404 "portal desconhecido"). A
leitura só lê a área logada numa janela do navegador da própria ferramenta, com o login feito pela pessoa;
nada é gravado até ela aplicar o que marcou.

**`GET /api/contas`** — `{navegador: bool (Edge ou Chrome achado), ultima: ISO|null, portais: [{nome, plataforma,
icone (SVG do código do servidor), conectado: bool, aviso_login}]}`.

**`GET /api/candidaturas/estado`** — `{situacao: "parada"|"lendo"|"aguardando_login"|"pronta", portal?, inicio?, fim?,
resultado: null|{itens: [item], historico: [item], sem_mudanca: number, erros: {Plataforma: mensagem}, lidas_em}}`.
Item: `{chave, portal, plataforma, tipo: "mudar"|"quadro"|"nova"|"historico", vaga_id|null, titulo, empresa,
de: {etapa, resultado}|null, para: {etapa, resultado}, status (texto do portal), nota, avisos: string[], data, url,
marcado: bool}` (sincronia.py:32-86).

| Rota | Corpo | Resposta | Botão |
|---|---|---|---|
| `POST /api/contas/{portal}/conectar` | — | `{ok: true}` (abre a janela no login do portal) | Conectar |
| `POST /api/contas/{portal}/pronto` | — | `{conectado: bool}` (false = login ainda não concluído) | Pronto |
| `POST /api/contas/{portal}/desconectar` | — | `{ok: true}` (apaga a sessão do portal na janela) | Desconectar |
| `POST /api/candidaturas/ler` | — | estado `{situacao: "lendo", portal, inicio}`; 409 "conecte pelo menos um portal" | Atualizar agora / Ler de novo |
| `POST /api/candidaturas/aplicar` | `{chaves: string[]}` (até 500) ou `{historico: true}` | `{aplicados: number, erros: string[]}`; 400 sem proposta | Aplicar N mudanças / Importar como histórico |

Erros de navegador ou portal: 409 com a mensagem.

### 3.11b Candidatura assistida (detalhe da vaga → Candidatura; card → Candidatar com ajuda; Contas conectadas → logins e sites)

Spec 027. Todas **[local]**. A ferramenta **preenche campos** da página aberta na janela dela (a mesma das contas
conectadas). Ela **nunca clica** em botão ou link, nunca aperta Enter e nunca envia: quem avança e envia é a pessoa.
O recurso é ligado **vaga a vaga**, com o aviso de risco aceito a cada vez. A chave fica na vaga:
`candidatura_assistida: {ligada: bool, em: "AAAA-MM-DD"}`, que vem em `/api/vagas`. Numa vaga sem a chave ligada,
as rotas `vaga/{id}/abrir|ler|preencher|login` respondem 409.

**`GET /api/candidatura`** devolve:

```text
{aviso: texto do aviso de risco, navegador: bool, memoria: [{chave, pergunta, resposta, categoria, em}],
 dominios: {conhecidos: [{portal, rotulo, dominios, tem_login}], bloqueados: [{dominio, motivo}],
            liberados: [{dominio, em}]},
 credenciais: [{portal, rotulo, login: [host], guardada, usuario, final (4 últimos caracteres), no_ambiente}],
 contato: {nome?, sobrenome?, email?, telefone?, cidade?, estado?, pais?, linkedin?, portfolio?, endereco?, cep?},
 campos_contato: [nomes dos campos]}
```

A senha nunca volta.

**Dados de contato** (spec 033). Eles preenchem os campos de contato de qualquer formulário, sem IA: o campo é
reconhecido pelo `autocomplete`, pelo tipo e por sinônimos em português e inglês, e a pergunta inteira precisa bater.
Ficam em `dash/dados/contato.json`, fora do Git, e nunca vão para a IA.
- `POST /api/candidatura/contato/proposta` (sem corpo) → `{dados, fontes: {campo: "currículo"|"respostas
  anteriores"|"filtros da busca"}, avisos}`. Lê do currículo base, das respostas guardadas e dos filtros, sem gravar.
- `PUT /api/candidatura/contato` `{dados: {campo: valor}}` → `{contato}`. Erro 400 com a regra: "e-mail inválido", "o
  LinkedIn precisa ser um link do linkedin.com…", "parece um documento (CPF, RG ou data de nascimento) em <campo>…".
- `DELETE /api/candidatura/contato` → `{contato: {}}`.

Item de `itens`, devolvido por `ler`:

```text
{chave, tipo: "texto"|"area"|"selecao"|"lista"|"unica"|"multipla"|"caixa"|"arquivo"|"senha"|"data"|"outro",
 (lista = lista com busca, ex.: react-select do Greenhouse; as opções são lidas abrindo a lista)
 tipo_html, rotulo, obrigatorio, limite (0 = sem limite),
 opcoes: [{valor (índice em texto), texto, vazia}], valor (atual),
 marca: "comum"|"sensivel"|"cadastro"|"consentimento"|"arquivo"|"senha"|"outro",
 motivo (por que fica com a pessoa), proposta, conferir: string[]}
```

Formato da `proposta`, por tipo:
- **texto:** o texto;
- **selecao, lista e unica:** o índice da opção;
- **multipla:** os índices separados por vírgula;
- **caixa:** `"sim"` ou `"nao"`;
- **vazia:** sem proposta (a pessoa escreve).

| Rota | Corpo | Resposta |
|---|---|---|
| `PUT /api/candidatura/vaga/{id}` | `{ligada: bool, aceitar_aviso?: bool}` | `{vaga}` (com o kit); 409 ao ligar sem `aceitar_aviso`; 404 vaga inexistente |
| `POST /api/candidatura/dominios` | `{dominio: "host", acao: "liberar"\|"revogar"}` | `{dominios}`; 409 para domínio bloqueado ou inválido |
| `PUT /api/candidatura/credenciais/{portal}` | `{usuario, senha}` | `{credenciais}` (grava no `.env`); 409 para portal sem login central |
| `DELETE /api/candidatura/credenciais/{portal}` | — | `{credenciais}` |
| `POST /api/candidatura/vaga/{id}/login` | — | `{portal, rotulo, preenchidos: ["usuario","senha"], aviso}`; 409 fora do host exato de login, sem credencial ou com mais de um campo de senha |
| `POST /api/candidatura/vaga/{id}/abrir` | — | `{ok, url, dominio}`; abre o link da vaga na janela e a traz para a frente |
| `POST /api/candidatura/vaga/{id}/ler` | — | `{pagina: {url, dominio: {host, permitido, portal, origem, bloqueado, pode_liberar}, etapa: "perguntas"\|"login"\|"teste"\|"bloqueio"\|"desconhecida", aviso, assinatura}, itens, aviso_ia, ia}`. Os `itens` (com a proposta da IA) só vêm com `etapa: "perguntas"` e domínio permitido. Nada vai à IA antes disso |
| `POST /api/candidatura/vaga/{id}/auto` | — | "Preencher esta página": `{pagina, preenchidos: [{chave, rotulo, texto, fonte: "seus dados de contato"\|"sua resposta anterior"\|"seu perfil", conferir}], perguntas: [item + {lembrar, relato}], na_janela: [{chave, rotulo, motivo}], aviso_ia, aviso, documento}`. Preenche primeiro os campos de contato com os dados de contato salvos (spec 033, sem IA), depois com a memória (inclusive sensível) e com a IA (só campos comuns); `perguntas` é o que precisa da pessoa |
| `POST /api/candidatura/vaga/{id}/preencher` | `{assinatura, respostas: [{chave, valor, trocar?}], lembrar?: bool (padrão true), guardar_relatos?: bool (padrão true)}` | as respostas da pessoa (podem ir em pergunta sensível e dado cadastral, nunca em aceite, arquivo ou senha): `{preenchidos: [{chave, rotulo, valor, texto, fonte: "seu relato (adaptado pela IA)"\|"seu relato"\|"sua resposta"}], ficaram, aviso, aviso_ia, ia, lembradas, relatos, documento}`. Na pergunta comum de texto (item com `relato: true` em `auto`), o valor é um relato: a IA o transforma na resposta (um pedido por clique; sem IA, vai o relato cortado no limite) e, com `guardar_relatos`, ele fica em `dash/dados/relatos.json` (spec 035); 409 se a página mudou, se o domínio não está liberado ou se há bloqueio |
| `DELETE /api/candidatura/memoria/{chave}` | — | `{memoria}`; 404 se não existe |

Regras do servidor:
1. Só preenche campos `comum`, sem pisar em valor que já existe (salvo `trocar`).
2. Perguntas sensíveis e credenciais nunca vão à IA.
3. As respostas preenchidas viram um documento `respostas` no kit da vaga (`origem: "candidatura_assistida"`).
4. Domínios bloqueados (LinkedIn, Indeed, Nerdin) não podem ser liberados.

### 3.12 Arquivos

| Rota | Resposta |
|---|---|
| `GET /arquivos/curriculos/{nome}` | arquivo de `curriculos/`: `nome` = `[a-z0-9-]{1,90}.(pdf\|docx\|txt)`; PDF abre no navegador, DOCX e TXT baixam; 404 se não existe |
| `GET /arquivos/curriculo-base/{pt\|en}` **[local]** | o currículo marcado da pessoa naquele idioma (PDF ou DOCX); 404 sem marcação |
| `GET /`, `/index.html` e `/{arquivo}` | a página, servida de `dash/front/` (só `.html .js .css .svg .png .woff2`, só os arquivos da pasta); sem build, `/` mostra uma página avisando. O build usa caminhos relativos (`./assets/...`), que valem também no Live Server |
| `GET /novo`, `/novo/` e `/novo/{arquivo}` | 308 para o mesmo endereço na raiz (o front novo ficava ali enquanto o dashboard antigo existia) |
| `GET /favicon.ico` | 204 vazio |

Na página, são links `<a target="_blank">` com o endereço da API na frente (`urlArquivo("/arquivos/...")`).

### 3.13 Versão

**`GET /api/versao`** — consultado a cada 4 s. `{versao: number (sobe a cada escrita no banco; mudou =
recarregar /api/vagas), analisando: bool (IA dando notas), ia_erro: {motivo, em}|null (última análise automática
falhou), ia_alerta: {nome, modelo, motivo, em}|null (a IA principal falhou na última tentativa; spec 032), busca: {situacao, origem} (inclui `externa` para busca do terminal/chat), verificando: string[] (vagas do
Forçar verificar na fila), falhas: {id: {motivo, em}} (Forçar verificar que não deu nota)}`. Também serve para saber
se o servidor está no ar.

## 4. Comportamentos que a página mantém

Conferidos na página; a maior parte também é garantida pelo servidor.

1. **Confirmar antes de gravar ou apagar.**
   - Remover do quadro e "Marcar todas como não seguidas" pedem um segundo clique ("Confirmar remoção",
     "Confirmar: marcar todas"); remover história também. "Recomeçar" o perfil pede `confirm()`.
   - Perfil: com perfil existente, "Ver o que muda" mostra as diferenças antes de "Confirmar e gravar".
     Filtros propostos (primeiros passos, cargos-alvo, currículo) são só proposta até o botão de gravar.
   - IA no Adicionar Vaga só **preenche o formulário**; a pessoa confere e clica em adicionar.
   - Contas conectadas: a leitura só propõe; grava só os itens marcados, ou o histórico com botão próprio.
   - Rascunhos de histórias da IA não são salvos até "Salvar esta história".
2. **IA só no clique, com aviso de custo.** Busca, currículo, carta, respostas, análises e entrevista abrem
   um diálogo (ou botão explícito) que diz qual IA vai rodar e, se a cobrança é por uso, que consome créditos.
   O painel IA lista o que é enviado ao provedor antes de salvar. A nota automática das vagas novas roda
   sozinha só quando a pessoa já escolheu uma IA. Sem IA, os botões levam ao painel IA em vez de chamar.
3. **Nada é enviado em nome da pessoa.**
   - "Candidatar no …" só abre a página do portal, e "Enviar por e-mail" só abre o programa de e-mail (`mailto:`).
   - Cartas e respostas são para copiar e colar.
   - Os lembretes de follow-up só lembram ("a mensagem é você quem escreve e envia").
   - A candidatura assistida (3.11b) só preenche campos. Ela sempre termina com "Confira na janela e clique você
     em Continuar ou Enviar".
   - Não há rota de envio de candidatura.
4. **Perguntas sensíveis são da pessoa.** Autorização de trabalho, visto, cidadania, salário, deficiência,
   relocação e diversidade não vão para a IA (servidor) e o front deixa o campo para ela escrever.
5. **Contas conectadas só leitura.**
   - A leitura não muda nada no portal, e o login é feito pela pessoa na janela da ferramenta.
   - A única senha que a página recebe é a da credencial da candidatura assistida, que a pessoa guarda no campo de
     senha. Ela vai para o `.env` e nunca volta: a página só recebe os 4 últimos caracteres. Chaves de API: campo de senha, e só os 4 últimos caracteres voltam.
6. **Texto da internet é texto.** Descrição, título, empresa, posts, mensagens dos portais e respostas da IA
   passam por escape de HTML; a descrição usa um markdown mínimo aplicado **depois** do escape
   (`src/components/TextoDaVaga.tsx`, que monta elementos, sem HTML); links só `http`/`https`, abertos com
   `target="_blank" rel="noopener"`.
7. **Respeito aos portais.** O botão Buscar vagas fica desligado durante uma busca, até `proxima_em` e com
   portal em espera; o front repete o pedido com `confirmar_recente`/`confirmar_espera` só depois de mostrar
   o aviso na confirmação.
8. **Só leitura de outro aparelho.** Com `pode_alterar: false` (ou 403), desligar botões que gravam.
</content>
</invoke>
