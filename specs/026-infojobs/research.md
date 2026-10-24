# Research: InfoJobs na busca de vagas e pausa por portal

**Data**: 2026-10-23. Poucos pedidos, espaçados, só à parte pública: a lista de uma busca, uma página de vaga, o
robots.txt e os termos de uso.

## R1. Termos de uso: proíbem a consulta automatizada (bloqueia a busca)

Fonte: "Aviso legal para candidatos" (`https://www.infojobs.com.br/legal/aviso-legal-para-candidatos__15727.aspx`),
lido em 23/10/2026. Trechos literais:

- Obrigações dos usuários: "Não utilizar mecanismos, software ou scripts em relação à utilização do Website e não
  bloquear, sobrescrever, modificar ou copiar, a não ser que isso seja necessário para a correta utilização dos
  serviços dos websites, e com a devida autorização expressa do Infojobs quanto ao seu uso. Por exemplo, cópias
  mediante tecnologias de buscador tipo "Robot/Crawler" não são necessárias para a correta utilização dos serviços
  do Website, de modo que estão expressamente proibidas."
- "Não prejudicar a funcionalidade da ferramenta da infraestrutura do Portal, especialmente para sobrecarrega-la."
- Licença ao usuário: "visualizar, copiar e imprimir o Conteúdo publicado no Portal pelo InfoJobs exclusivamente
  para seu uso pessoal, e em conexão com o uso do Portal".
- "fica terminantemente proibida a utilização dos textos, imagens, anúncios e qualquer outro elemento incluído no
  presente Portal para sua posterior inclusão, total ou parcial, em outros websites alheios ao Portal, sem contar com
  a autorização prévia e por escrito do InfoJobs."

Conclusão:
- A leitura da busca por script (US1 a US3, US5) contraria os termos, mesmo que o robots.txt permita as páginas.
- Pela premissa da spec e pelo princípio VI, a leitura da busca não segue sem uma decisão da pessoa.
- A exceção prevista nos termos é a "autorização expressa do Infojobs".
- O serviço oficial que os termos oferecem para receber vagas é o alerta por e-mail ("Avisos de vagas").

Diferença para o LinkedIn: os termos dele também proíbem a coleta automatizada, e a busca pública entrou por decisão
da pessoa (emenda 2.0.0 da constituição, spec 014). O precedente existe, mas foi uma decisão explícita, não um padrão.

## R2. Formato do site (para o caso de a busca seguir)

- **Sem API, RSS ou sitemap**: `sitemap.xml`, `rss.aspx` e `feed` redirecionam; a página não chama endpoint de dados.
  O python-jobspy não tem o InfoJobs.
- **robots.txt**:
  - permite `/vagas-de-emprego-<termo>.aspx` e `/vaga-de-<titulo>-em-<cidade>__<id>.aspx`;
  - bloqueia `/detailvacancy.aspx`, `/candidate`, `/company`, `/Concursos`, `*.ashx`;
  - `User-agent: proximic` bloqueado por inteiro.
- **Lista**: `empregos.aspx?palabra=<termo>`, com a forma canônica `vagas-de-emprego-<termo>.aspx`. São 20 cards em
  HTML com título, selo "NOVA", data "20 out" (sem ano), empresa (às vezes "confidencial"), "Cidade - UF", salário
  ("R$ 5.500,00 a R$ 6.000,00"), experiência, escolaridade e modelo (Presencial, Home office, Híbrido).
- **Filtros na URL**:

  | Parâmetro | Valores |
  |---|---|
  | `Antiguedad` | 1 hoje, 2 últimos 3 dias, 3 última semana, 4 últimos 15 dias, 5 último mês |
  | `tipocontrato` | 2, 4, 6, 9, 15–19 (rótulos não lidos) |
  | `isr` | faixa salarial, "a partir de R$ N mil" |
  | `wo` | 1, 2, 5, 6, 12 (provavelmente o modelo de trabalho; não confirmado) |
  | `im`, `def1`, `categoria` | outros filtros (não lidos) |

- **Página da vaga**: tem JSON-LD `JobPosting` com `title`, `employmentType` e `description` (com área, senioridade,
  local, regime e jornada no começo do texto). Dá para reaproveitar `link.extrair_jobposting`.
- **Paginação**: não confirmada (não há link de página no HTML; provavelmente "carregar mais" por script). Ficou
  sem pesquisa por causa do R1.

## R3. Pausa por portal e espera (independem do InfoJobs)

- `fontes/linkedin.py` já tem `pausa()`/`aviso_pausa()` com `LINKEDIN_PAUSA`:
  - aceita vírgula decimal e valor não finito;
  - mínimo 3, máximo 60, sorteio de N a N+4.

  Dá para extrair isso para `fontes/_comum.py` sem mudar o comportamento.
- `fontes/nerdin.py` tem pausa fixa `PAUSA = 3.0` e só sai do resto da busca no bloqueio.
- A espera do LinkedIn (`_bloquear`/`espera`, `.cache/linkedin-espera.json`, 6 h) pode ir para `_comum` como
  mecanismo comum. O `vagas.py` (`fontes_em_espera`, `confirmar_espera`, código 5, `--confirmar-espera`) já trata
  qualquer fonte que tenha `espera()`.
