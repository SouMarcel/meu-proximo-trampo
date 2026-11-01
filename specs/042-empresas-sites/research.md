# Pesquisa: empresas acompanhadas em qualquer página de vagas

Feita em 2026-11-01, com um pedido por vez a cada site e pausa entre eles, sem login.

## R1. Os três sites do pedido

| Empresa | Endereço | O que há por trás | robots.txt |
|---|---|---|---|
| EY | `careers.ey.com/ey/search/` | SAP SuccessFactors; já lido por `fontes/ey.py` (spec 039) | busca liberada; o RSS fica numa área bloqueada (spec 039) |
| Varejista (exemplo) | `carreiras.varejista.com.br/jobs` | Teamtailor, com domínio próprio | `/jobs` e `/jobs.rss` liberados; `Content-Signal: search=yes, ai-train=no, ai-input=yes` |
| Consultoria de TI (exemplo) | `consultoria.com.br/carreira/#vagas` | página WordPress (Elementor) feita à mão | só `/wp-admin/` bloqueado |

## R2. Teamtailor

- A página de vagas anuncia a lista pública: `<link rel="alternate" type="application/rss+xml" title="Jobs"
  href="https://<host>/jobs.rss">`. O HTML cita "teamtailor" dezenas de vezes.
- O feed (RSS 2.0, `xmlns:tt="https://teamtailor.com/locations"`) tem, por vaga:
  - `title`, `description` (HTML escapado), `pubDate` (RFC 822), `link` (`/jobs/<número>-<slug>`), `guid`;
  - `remoteStatus` (`none`, `onsite`, `hybrid`; o Teamtailor também usa `fully` e `temporary` para remoto);
  - `tt:locations/tt:location` (`tt:name`, `tt:city`, `tt:country`, `tt:address`, `tt:zip`), `tt:department`,
    `tt:role`.
- **Limite**: o feed trouxe 100 vagas, e `?page=2` devolve as mesmas. São as mais recentes (26/10 no começo, 16/10 no
  fim). Para a janela de dias da busca, basta. Empresa com mais de 100 vagas abertas tem as mais antigas fora.
- Na varejista: 84 `none`, 13 `onsite`, 3 `hybrid`, quase todas de loja.
- Empresas em `<empresa>.teamtailor.com` têm o mesmo feed.

## R3. Consultoria de TI (página própria)

- O trecho `id="vagas"` traz blocos repetidos: cargo, nível e modelo ("Home Office" ou "Presencial | Campinas"),
  "Envie seu currículo ➔" e a lista de requisitos. No fim de cada bloco: "*Vaga para atuar alocado em um grande
  cliente."
- Não há link por vaga, data nem sistema: a candidatura é pelo e-mail `recrutamento@…` do rodapé da seção.
- O texto visível da seção tem cerca de 6 mil caracteres. A página inteira tem 214 KB de HTML, quase tudo de estilo.

## R4. O aviso da EY na consulta "agilista"

- Pedido de 2026-11-01: `careers.ey.com/ey/search/?q=agilista&locationsearch=Brazil&...` → 200, a página "There are
  currently no open positions matching …".
- A página tem `data-row` seis vezes, todas no CSS embutido (`tr.data-row {…}`), nenhuma numa linha de vaga.
- `fontes/ey.py` acusa `ILEGIVEL` quando não acha vaga e a página contém `data-row`. Com o CSS novo do site, toda busca
  sem resultado vira o aviso. **Correção**: "no open positions" é zero sem aviso, e a linha de vaga é procurada no HTML
  (`<tr class="data-row…">`), não no texto todo.

## R5. A EY e outros sites da SAP

- `fontes/ey.py` usa endereços e padrões da EY (`careers.ey.com/ey/`, o padrão de link `/<site>/job/<título>/<id>`).
  Outros sites do SuccessFactors têm temas e caminhos diferentes. Generalizar exigiria uma pesquisa por site.
- **Decisão**: só a EY é reconhecida nesta spec. Outro site do SuccessFactors entra como página própria (pela IA).

## R6. O que já existe

- `fontes/ats.py`: `reconhecer(url)` (sem pedido), `_lista(e)` por sistema, `normalizar`, `_na_area`, bloqueio por
  sistema, `lembrar` (uma lista por empresa por busca).
- `filtros.py`: `empresas` no config (até 50), `_empresas` (valida pelo link), `acompanhar(url)`, `efetivos`.
- Painel: o botão Adicionar reconhece o link no próprio navegador (`empresaDoLink`, só Greenhouse, Lever e Ashby).
- `post_ia.py`: pedido à IA que só copia o texto, com e-mail e link conferidos no texto; `ia.responder` com a reserva
  (spec 032); `integridade.limpar`.
- `fontes/link.texto_de_html`: texto visível de um HTML, sem o que está oculto (spec 034).

## Decisões técnicas (plano, 2026-11-01)

- **D1. Onde fica cada leitura.** O `fontes/ats.py` continua sendo a fonte "Empresas acompanhadas" e distribui por
  sistema:
  - Greenhouse, Lever e Ashby, como hoje;
  - Teamtailor, em `fontes/teamtailor.py` (novo): lê e normaliza o feed;
  - EY, pela `fontes/ey.py`, que continua registrada em `FONTES` (descrição, link e Adicionar Vaga);
  - página própria, em `fontes/pagina_empresa.py` (novo): leitura, IA e memória.
- **D2. Reconhecer.**
  - `ats.reconhecer(url)` continua sem pedido: Greenhouse, Lever, Ashby, `*.teamtailor.com` e `careers.ey.com`.
  - Link de portal de vagas (`integridade.PORTAIS` e Indeed, menos a EY) é recusado com a dica de Portais.
  - `ats.descobrir(url)` faz **um** pedido à página quando o domínio não é conhecido. Com o feed do Teamtailor
    anunciado, é Teamtailor; senão, página própria. O nome vem do título do feed ou da página.
  - A rota nova `POST /api/empresas/reconhecer` (o botão Adicionar do painel) e o `POST /api/empresas` (Acompanhar)
    usam `descobrir`. O `PUT /api/config` aceita a empresa já reconhecida (com `sistema`) sem pedido; link solto de
    domínio desconhecido pede o botão Adicionar.
- **D3. Identificadores.**
  - Teamtailor: empresa `id` = host; vaga `teamtailor-<host>-<número>`, plataforma "Teamtailor".
  - EY: empresa `{sistema: "ey", id: "ey"}`; vaga `ey-<número>` (o de hoje), plataforma "EY".
  - Página própria: empresa `id` = host + caminho, sem o `#`; vaga `pagina-<empresa>-<cargo e local>`, plataforma
    "Site da empresa".
- **D4. Migração da EY** (em `filtros.efetivos`, gravada no próximo salvamento):
  - com `"ey"` em `fontes`, ou sem a chave `fontes` num config que já tem cargos (o padrão antigo incluía a EY): a EY
    entra em `empresas`, se não estiver;
  - `"ey"` sai de `fontes`, de `FONTES_NAC` e de `FONTES_PADRAO`;
  - `vagas.fontes_da_busca` passa a usar a lista de `efetivos`.
- **D5. Teamtailor.**
  - Um GET ao feed por empresa por busca, `xml.etree` com limite de tamanho, sem nova tentativa.
  - `fully`, `remote` e `temporary` contam como remoto, `hybrid` como híbrido e `onsite` como presencial. `none`: sem
    modelo, e a vaga não é remota.
  - O local junta cidade e país de cada `tt:location`; a vaga remota usa o país como restrição.
  - A descrição vem no próprio feed.
- **D6. Página própria.**
  - Um GET por busca. O texto vem de `link.texto_de_html` no trecho do `#âncora` do link (ou no corpo), passa por
    `integridade.limpar` e fica limitado a 20 mil caracteres.
  - A marca do texto (SHA-256) fica em `.cache/empresas-paginas/<id>.json`, com as vagas separadas e o dia em que
    cada uma foi vista primeiro.
  - Texto igual: sem IA. Texto novo, com a IA ligada: `ia.responder` com um pedido no molde do `post_ia`, que devolve
    `{"vagas": [{titulo, modelo, local, requisitos, email_candidatura, url}]}`.
  - Regras de limpeza:
    - o cargo precisa estar no texto da página, ou a vaga sai;
    - e-mail e link só valem se estiverem escritos no texto;
    - modelo só `remoto`, `hibrido` ou `presencial`;
    - os requisitos viram a descrição.
  - No máximo 10 páginas lidas pela IA por busca; as outras ficam para a próxima, com aviso.
  - Sem IA ou com as IAs falhando: aviso, e a empresa fica de fora nesta busca.
  - **Remota sem lugar** ("Home Office") conta como aberta ao país da pessoa, porque a página é da própria empresa que
    ela escolheu. Nenhum campo é preenchido com isso: a regra vale só para a área nacional.
- **D7. Bloqueio e erro.** Teamtailor e página própria param por host no primeiro 403, 429 ou 503, sem nova
  tentativa, até o fim da busca; 404 dá o aviso "remova ou troque o link". A EY segue as regras dela.
- **D8. Áreas.** As regras de `ats._na_area` valem para todos:
  - na nacional, remota aberta ao país ou presencial/híbrida na cidade;
  - na internacional, a consulta global.

  A EY roda só na nacional, como hoje.
- **D9. Adicionar Vaga e detalhe.** `ats.vaga_do_link` reconhece também links de vaga de `*.teamtailor.com` e da EY,
  para o "Acompanhar empresa". Domínio próprio de Teamtailor fica sem o botão no detalhe, porque saber o sistema pede
  um pedido.
