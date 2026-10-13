# Research: LinkedIn na busca de vagas

## 1. Como consultar o LinkedIn

**Decisão**: módulo próprio `fontes/linkedin.py` com `urllib` (biblioteca padrão), na busca pública de convidado
`https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search`, que devolve um trecho de HTML com até 10
cards por página (conferido na busca real). A descrição vem da vaga pública `jobs-guest/jobs/api/jobPosting/<id>`, que o "Adicionar pelo link"
já lê (`fontes/link.py:_ler_linkedin`).

**Motivo**: o jobspy 1.2.0 (já instalado) tem um raspador do LinkedIn, mas:
- só filtra remoto (`f_WT=2`), sem híbrido nem presencial;
- ignora o país;
- busca a descrição de todas as vagas, sem pausa;
- para em silêncio no primeiro bloqueio, só com uma linha de log.

Com o módulo próprio, o controle dos filtros, da pausa e do bloqueio fica na ferramenta, e a leitura dos cards usa
`html.parser`, como o `link.py`.

**Alternativas**:
- jobspy com `site_name=["linkedin"]`: rejeitada pelos motivos acima.
- Importar a busca que a pessoa faz no navegador (botão nos favoritos): rejeitada pelo usuário, que quer o LinkedIn na
  busca automática.

## 2. Parâmetros da consulta

| Parâmetro | Uso |
|---|---|
| `keywords` | o termo (cargo) |
| `location` | país em inglês (`filtros.PAISES` → nome com a primeira letra maiúscula, ex.: "Brazil"), "Cidade, Estado, País" ou "Worldwide" |
| `distance` | raio da cidade em milhas (km ÷ 1,609, como no Indeed) |
| `f_WT` | modelo: 1 presencial, 2 remoto, 3 híbrido; vários separados por vírgula ("1,3") |
| `f_JT` | tipos: F tempo integral, C contrato, P meio período, I estágio, T temporário (vírgula) |
| `f_TPR` | janela: `r<segundos>` (`janela_horas` × 3600) |
| `start` | 0 (uma página de 10 vagas por consulta) |

Cada grupo de `filtros.consultas` vira uma consulta:
- `remoto`: país, `f_WT=2`.
- `pais`: país, `f_WT` com os modelos marcados entre presencial e híbrido. Remoto também entra quando a consulta não
  tem o filtro de remoto e o remoto está marcado.
- `local`: cidade, `f_WT` com presencial/híbrido marcados.
- `internacional:<p>`: país, `f_WT=2`.
- `mudanca:<p>`: país, `f_WT=1,3`.
- `internacional:global`: "Worldwide", `f_WT=2`, ou `1,2,3` com `aceita_mudar` (a elegibilidade corta o resto).

**Modelo da vaga**: quando o `f_WT` da consulta tem um valor só, a vaga recebe `modelo_trabalho` (remoto, presencial
ou híbrido). Com mais de um, fica sem e a análise decide, como no Indeed.

## 3. Respeito ao portal e bloqueio

**Decisão**:
- **Sem login:** pedidos sem cookies nem login, com o `User-Agent` de navegador que o `link.py` já usa.
- **Pausa:** aleatória de 3 a 7 s desde o último pedido ao LinkedIn, valendo para a lista e para a descrição. O
  intervalo global de 2 s entre consultas continua.
- **Sinal de bloqueio:**
  - HTTP 429 ou 999 (o código que o LinkedIn usa para robôs);
  - qualquer outro 4xx/5xx em sequência;
  - redirecionamento para `authwall`, `signup`, `login` ou `checkpoint`. O redirecionamento não é seguido: um
    handler que recusa redirecionar trata o 3xx como bloqueio.
- **No primeiro sinal:**
  - marca "bloqueado nesta busca";
  - levanta `FonteErro("o LinkedIn limitou as consultas; tente mais tarde")`;
  - nas consultas e descrições seguintes, levanta o mesmo erro com `repetido=True` (o aviso sai uma vez), sem pedido
    nenhum.
- **Reset:** o estado é zerado em `_comum.esquecer()`, no início de cada busca.
- **Sem nova tentativa:** o `_comum.baixar` tenta de novo no 429, então o LinkedIn usa o seu próprio `_baixar`, que
  nunca repete.

**Motivo**: é o que a emenda do princípio VI pede: não contornar bloqueio, só o necessário, nunca a conta da pessoa.

## 4. Rodar também na consulta global

**Decisão**: atributo opcional `GLOBAL = True` no contrato das fontes ("roda nas consultas por país e na global").
`vagas.atende` passa a aceitar `getattr(fonte, "GLOBAL", False)` para a consulta global. `filtros.consultas` cria o
grupo `internacional:global` também quando o LinkedIn está nos portais e a busca internacional está ligada. Para isso,
`efetivos` passa a expor `fontes` (os portais nacionais).

**Alternativa**: duas fontes ("linkedin" e "linkedin_global"). Rejeitada: a pessoa veria dois LinkedIns no painel.

## 5. Tipo de emprego

O "Employment type" da vaga (critério da página pública, em inglês ou português) vira o código de
`filtros.TIPOS_EMPREGO`:

| LinkedIn | Código |
|---|---|
| Full-time / Tempo integral | `tempo_integral` |
| Contract / Contrato / Freelance | `pj` |
| Part-time / Meio período | `meio_periodo` |
| Internship / Estágio | `estagio` |
| Temporary / Temporário | `temporario` |

"Volunteer" e "Other" ficam sem código. O `vagas.documento()` passa a copiar `tipo_emprego` da fonte (hoje só copia
`restricao_local`, `ats`, `moeda` e `modelo_trabalho`).

## 6. Portais na página

**Decisão**:
- `filtros.FONTES_NAC = {"indeed", "gupy", "linkedin", "startupjobs"}`, com o rótulo e o `TERMOS` de cada módulo;
- `opcoes()["fontes_nac"]`;
- `validar` aceita `fontes` (pelo menos um, só os conhecidos);
- `efetivos` devolve `fontes` (padrão `["indeed","gupy"]`).

O painel "Filtros da busca" ganha a seção Portais. O startup.jobs avisa que precisa da chave no `.env`.

O contador:
- conta o plano como hoje (por portal);
- mostra à parte as consultas do LinkedIn: todos os grupos, inclusive o global quando a busca internacional está
  ligada;
- avisa acima de 20, como já faz.

## 7. Constituição

Emenda 1.0.0 → 2.0.0, MAJOR porque redefine um princípio. O princípio VI passa a dizer:
- preferir APIs públicas e oficiais;
- consultas espaçadas e só o necessário;
- em portais sem API aberta (Indeed, LinkedIn), só a busca pública, sem login e sem a conta da pessoa, parando no
  primeiro bloqueio sem contornar;
- o perfil da pessoa não é lido de portais, só dos arquivos que ela baixa;
- nada de automação de candidatura.

O relatório de impacto vai no topo do arquivo, como comentário, e o motivo vai no commit.

## 8. Testes sem rede

O HTML de exemplo é fictício (`tests/dados/linkedin/lista.html` e `vaga.html`), na estrutura atual dos cards:
`base-search-card`, `data-entity-urn="urn:li:jobPosting:<id>"`, `base-search-card__title`,
`base-search-card__subtitle`, `job-search-card__location` e `time.job-search-card__listdate[datetime]`. O `_baixar` do
módulo é substituído nos testes.

A estrutura é conferida com uma consulta real na validação (com o OK do usuário), sem gravar a resposta no
repositório.
