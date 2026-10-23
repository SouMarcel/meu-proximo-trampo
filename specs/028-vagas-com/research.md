# Research: Vagas.com na busca de vagas

**Data**: 2026-10-23. Pedidos espaçados, só à parte pública: robots.txt, duas buscas, uma página de vaga e os termos
de uso.

## R1. Termos de uso

Fonte: `https://www.vagas.com.br/candidatos/termos-de-uso`, lido em 23/10/2026. Trechos literais:

- "É proibido o uso de qualquer dispositivo, software ou outro recurso que venha a interferir nas atividades e
  operações da Vagas.com, tanto pelo site quanto por outros sistemas ou bancos de dados."
- "12. DIREITO DE PROPRIEDADE […] Você não deverá usar indevidamente ou reproduzir, total ou parcialmente, tais
  conteúdos, salvo quando houver autorização expressa."

Não há cláusula sobre robôs ou crawlers. Para ficar longe da "interferência":
- poucos pedidos (até 3 páginas por cargo e 30 vagas por busca);
- pausa sorteada entre eles;
- parar no primeiro bloqueio, com espera de 24 horas.

As vagas não são republicadas: ficam no computador da pessoa, que se candidata no próprio site.

## R2. Formato do site

- **robots.txt**: `User-Agent: *` bloqueia `/auth/`, `/api/`, `/v1/`, `/users/`, `/vagas/pesquisas` e outras áreas
  internas; a busca `/vagas-de-<cargo>` e as vagas `/vagas/v<id>/<slug>` ficam livres.
- **Lista**: `vagas-de-<cargo>?ordenar_por=mais_recentes`; a página N com `&pagina=N&q=<cargo>` (o link "mostrar
  mais vagas" traz `data-url` com esse endereço e `data-total` com o número de páginas). São 40 cards `li.vaga`, com:
  - o link `a.link-detalhes-vaga` (com `data-id-vaga` e o título inteiro no atributo `title`);
  - `span.emprVaga`, `span.nivelVaga` e o trecho do texto em `div.detalhes`;
  - `div.vaga-local` ("Cidade / UF", "100% Home Office" ou "Localização não informada", com um balão de ajuda em
    `div.tooltip-place`);
  - `span.data-publicacao` ("Hoje", "Ontem", "Há N dias", data) e `span.vaga-pne` ("Exclusivo para PCD").
- **Busca ampla**: "analista de dados" trouxe "Analista de Customer Service", então o filtro pelo título é necessário.
- **Página da vaga**: dois JSON-LD, `WebSite` e `JobPosting` (`title`, `description`, `identifier`, `datePosted`,
  `validThrough`, `hiringOrganization`, `jobLocation`). O `link.extrair_jobposting` lê o segundo.
- **Verificação real** (23/10/2026):
  - "analista de dados" em São Paulo: 3 páginas, 1 vaga que bate com o cargo, descrição com 2.652 caracteres;
  - 27 s com a pausa;
  - o Adicionar Vaga com o mesmo id.
