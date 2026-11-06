# Research: Regiões e continentes nos filtros da busca internacional

## O que o código já dá

- `filtros.PAISES_DA_REGIAO` (`filtros.py` ~L733) já liga quatro regiões (América Latina, Américas, América do Norte,
  Europa) aos países delas. `_inclui(lugar, pais)` diz se o lugar exigido pela vaga contém o país.
- `filtros.LUGARES` traduz nomes do texto da vaga para país ou região, e `pais_do_local` / `_lugares` usam essa lista.
- `elegibilidade()` (~L813) tem cinco cortes:
  - os cortes 1 e 2 (lugar exigido) comparam com `pode = [casa, *autorizacao_trabalho]`;
  - o corte 3 (regiões aceitas) passa por `_regiao()`, que só conhece mundo, Américas, América Latina e Brasil, e
    exige a mesma região exata;
  - o corte 4 confere `paises_mudanca` por igualdade de país.
- `filtros.consultas()` faz um grupo `internacional:<país>` e um `mudanca:<país>` para cada país. `vagas.atende()`
  escolhe os portais de cada consulta por `AREAS`, `POR_PAIS` e `GLOBAL`.
- `linkedin.parametros()` manda o país em inglês no campo `location`. O LinkedIn é o único portal da lista que procura
  por nome de lugar livre.
- `banco.verificar_banco()` + `_cmd_integridade` são o modelo de "mostra o que mudaria, grava só com `--gravar`".
- No front (`frontend-react`):
  - `SearchFiltersModal.tsx` tem as pílulas de Regiões aceitas (`op.regioes`) e a grade de países de interesse
    (`op.paises`);
  - países para morar e autorização de trabalho são caixas de texto separadas por vírgula;
  - `contarConsultas` / `contarLinkedin` (`config.ts`) estimam as consultas.

## D1. Catálogo de regiões

- **Decisão:** um dicionário `REGIOES_PAISES` (nome da região em português → conjunto de países de `PAISES`). Ele
  substitui `PAISES_DA_REGIAO`, que fica como nome antigo do mesmo objeto. Os conjuntos (spec FR-001):
  - **América do Norte**: Estados Unidos, Canadá, México.
  - **América Central**: Costa Rica, Panamá.
  - **América do Sul**: Argentina, Brasil, Chile, Colômbia, Equador, Peru, Uruguai, Venezuela.
  - **América Latina**: América do Sul, América Central e México.
  - **Américas**: América do Norte e América Latina.
  - **União Europeia**: os 27 países-membros.
  - **Europa**: União Europeia, Reino Unido, Suíça, Noruega e Ucrânia.
  - **Ásia**: Arábia Saudita, Bahrein, Bangladesh, Catar, China, Coreia do Sul, Emirados Árabes Unidos, Filipinas,
    Hong Kong, Índia, Indonésia, Israel, Japão, Kuwait, Malásia, Omã, Paquistão, Singapura, Tailândia, Taiwan, Turquia
    e Vietnã.
  - **Oceania**: Austrália, Nova Zelândia.
  - **África**: África do Sul, Egito, Marrocos, Nigéria.
  - **Só reconhecidas no texto:**
    - **Oriente Médio**: Arábia Saudita, Bahrein, Catar, Emirados, Israel, Kuwait, Omã e Turquia;
    - **EMEA**: Europa, Oriente Médio e África;
    - **Ásia-Pacífico**: Ásia e Oceania.
- **Guarda (teste):** a soma dos continentes cobre todos os países de `PAISES`, e cada país fica num continente só.
- **Rationale:** um único lugar com os países de cada região. Tudo o mais (sobreposição, consultas, painel) sai dele.
- **Alternativas:**
  - lista de países à parte em cada campo: cada uma sairia diferente;
  - biblioteca de países (pycountry): dependência nova sem necessidade, contra a constituição III.

## D2. Códigos de Regiões aceitas

- **Decisão:** `REGIOES` (código → rótulo), nesta ordem:
  - `pais` (Seu país);
  - `america_norte`, `america_central`, `america_sul`, `latam`, `americas`;
  - `ue`, `europa`;
  - `asia`, `oceania`, `africa`.

  O rótulo de cada região é o nome dela no catálogo.
- **Códigos antigos:**
  - `brasil` vira `pais`, porque só tinha efeito para quem mora no Brasil;
  - `mundo` é ignorado (FR-002);
  - código desconhecido continua dando erro ao gravar.
- **Rationale:** os códigos `latam` e `americas` continuam valendo, e quem mora fora do Brasil passa a ter "Seu país".
- **Alternativa:** códigos com o nome do país (`brasil`, `portugal`…). Recusada: a opção depende do país da pessoa e não
  cabe numa lista fixa.

## D3. Regra de sobreposição

- **Decisão:**
  - `paises_de(lugar)` devolve o conjunto de países de um país ou de uma região. Para "mundo todo", devolve `None`
    (todos).
  - `sobrepoe(a, b)` é verdadeiro quando um dos dois é o mundo todo ou quando os conjuntos têm país em comum.
  - `_inclui(lugar, pais)` passa a ser `sobrepoe`. Com um país, dá o mesmo resultado de hoje.
- **Cortes 1 e 2 (lugar exigido):** a vaga serve quando algum lugar exigido sobrepõe o país da pessoa ou um lugar da
  autorização de trabalho (FR-005).
- **Corte 3 (regiões aceitas):** só com regiões marcadas e com lugar declarado pela vaga, sem mundo todo. Corta quando
  nenhum lugar da vaga sobrepõe alguma região marcada. `pais` conta como o país da pessoa. O motivo continua começando
  por "Vaga aberta a:", o que permite a revisão (D10).
- **Corte 4 (mudança):** o país da vaga precisa sobrepor algum lugar de `paises_mudanca` (FR-007).
- **Mudança de comportamento:** hoje o corte 3 só olha regiões. Agora ele também olha o país exigido. Exemplo: "só
  Alemanha", com Américas marcada e a autorização na UE que deixa passar o corte 1, vai para Fora, porque a Alemanha
  não está nas regiões marcadas. Isso é o que a pessoa disse ao marcar.
- **Alternativa:** a vaga estar contida numa região marcada (subconjunto). Recusada: com só União Europeia marcada, a
  vaga aberta à Europa seria cortada, embora inclua a UE.

## D4. Leitura do texto da vaga

- **Decisão:** mudanças em `LUGARES`:

  | Texto | Lido como |
  |---|---|
  | `eu`, `european union`, `uniao europeia` | União Europeia (antes, Europa) |
  | `south america`, `america do sul` | América do Sul (antes, América Latina) |
  | `central america`, `america central` | América Central |
  | `america do norte` | América do Norte (`north america` já existia) |
  | `oceania`, `anz` | Oceania |
  | `asia` | Ásia |
  | `apac`, `asia pacific` (o hífen vira espaço na leitura) | Ásia-Pacífico |
  | `africa` | África |
  | `emea` | EMEA (antes, Europa) |
  | `middle east`, `oriente medio`, `mena` | Oriente Médio |

- **Rationale:**
  - "south africa" continua África do Sul, porque `pais_do_local` prefere o nome que começa antes e, no empate, o mais
    longo;
  - "asia" não casa dentro de "malaysia", porque a busca usa borda de palavra.
- **Alternativa:** deixar EMEA como Europa. Recusada: corta, sem motivo, vaga aberta ao Oriente Médio para quem tem
  autorização lá.

## D5. Campos de país aceitam região

- **Decisão:** `lugar_pt(nome)` devolve o país (`pais_pt`) ou a região do catálogo. Ela aceita o nome em português,
  sem acento ou com acento, e o nome em inglês.
  - Valem só as regiões marcáveis. EMEA, Ásia-Pacífico e Oriente Médio não entram.
  - `efetivos` e `validar` usam `lugar_pt` em `paises`, `paises_mudanca` e `autorizacao_trabalho`.
  - O erro passa a ser "<campo>: país ou região desconhecido: X".
  - Em `paises` e `paises_mudanca`, o país da pessoa continua de fora. Uma região que o contém é aceita.
- **Rationale:** as caixas de texto do painel e o config aceitam o nome como a pessoa escreve.

## D6. Busca por região

- **Decisão:**
  - **Em `consultas()`:** o lugar de interesse que é região faz o grupo `internacional:<Região>` (e `mudanca:<Região>`)
    com `pais: None`, `pais_nome: <Região>` e `regiao: <nome em inglês>`.
  - **Atributo novo das fontes, `POR_REGIAO`:** `vagas.atende` só deixa rodar consulta com `regiao` a fonte que tem
    `POR_REGIAO = True`. Hoje só o LinkedIn tem.
  - **Em `linkedin.parametros`:** `location = consulta["regiao"]`.
  - **Nomes em inglês (`REGIAO_EN`):** North America, Central America, South America, Latin America, Americas,
    European Union, Europe, Asia, Oceania, Africa.
- **Rationale:**
  - É uma consulta por região e cargo, ou por região só quando os cargos se juntam por OR, em vez de uma por país
    (SC-004).
  - O Indeed (jobspy) exige um país, e o JobGether recusa local desconhecido (400 em `locations`). Os dois ficam de
    fora, como diz a spec.
- **Validação dos nomes:**
  - Os nomes são os que a caixa de local da busca do LinkedIn oferece.
  - Não foram conferidos com pedidos da ferramenta (constituição VI: só o necessário). A conferência fica no teste da
    pessoa (quickstart, passo 6).
  - Se o LinkedIn ignorar um nome, as vagas vêm de qualquer lugar. Nesse caso, a etiqueta segue o local da vaga (D7) e
    a elegibilidade continua valendo.
- **Alternativas:**
  - `geoId` do LinkedIn: não há lista pública confiável dos códigos das regiões, e a pesquisa não achou fonte
    oficial;
  - expandir a região em países: 27 consultas para a UE no Indeed e no LinkedIn, com risco de bloqueio.

## D7. Área e etiqueta da vaga achada por região

- **Decisão:** em `area_da_vaga`, quando o lugar da consulta é uma região:
  - o país do local vale, quando o local diz;
  - local no país da pessoa → nacional;
  - outro país → internacional com esse país;
  - sem país no local → internacional com o nome da região (FR-008).
- **Rationale:** a consulta à América do Sul pode trazer vaga do Brasil, e a etiqueta "Internacional · União
  Europeia" serve só quando o local não diz o país.

## D8. Painel (front)

- **Decisão:**
  - **`opcoes()` ganha dois campos:**
    - `regioes_lugar`: os nomes das regiões que entram nos campos de país;
    - `fontes_regiao`: os portais com `POR_REGIAO`.
  - **Regiões aceitas:** pílulas de `op.regioes`; a do código `pais` mostra "Seu país (<país>)".
  - **Países de interesse:** uma linha "Regiões" com as pílulas de `op.regioes_lugar` acima da grade de países. Elas
    entram e saem da mesma lista `paises`.
  - **Países para morar e autorização de trabalho:** continuam caixas de texto, com o rótulo "países ou regiões" e o
    exemplo "Portugal, União Europeia".
  - **Contagem:**
    - `contarConsultas(d, porGrupo, regioes)` não conta as regiões, porque o Indeed não as busca;
    - `contarLinkedin` conta as regiões.
  - **Aviso de região sem portal:** aparece quando há região em países de interesse ou em países para morar e nenhum
    portal de `fontes_regiao` está ligado. O texto: "nenhum portal ligado procura por região; o Indeed só procura nos
    países marcados um a um".
  - **Dica de Regiões aceitas:** "Passa a vaga aberta a uma região com país em comum com as marcadas; a aberta ao
    mundo todo sempre passa. Nenhuma marcada = sem restrição."
- **Compatibilidade:**
  - Página nova com servidor antigo: sem `regioes_lugar`, não aparece a linha Regiões.
  - Página antiga com servidor novo: as pílulas novas aparecem pela própria `op.regioes`.

## D9. Perfil e análise pela IA

- **Perfil (`primeiros_passos.py`):**
  - a pergunta `exterior_paises` passa a ser "De quais países ou regiões você aceita vagas? Um por linha (ex.:
    Estados Unidos, União Europeia).";
  - a linha do perfil vira "Países e regiões de interesse";
  - a proposta usa `lugar_pt` e avisa os nomes não reconhecidos.
- **IA (`criterios_extra`):** as regiões aceitas vão com os rótulos novos, e `pais` vai com o nome do país da pessoa. A
  autorização já vai pelos nomes, que agora podem ser regiões.

## D10. Revisão das vagas cortadas pela regra antiga

- **Decisão:** `banco.rever_regioes(gravar=False)` e o comando `python dash/banco.py regioes [--gravar]`.
  - Para cada vaga com `triagem == "fora"` e motivo que começa por "Vaga aberta a:":
    - o motivo de região é refeito pela regra nova (`filtros.elegibilidade` com o config de agora);
    - o motivo novo de região fica; os outros motivos não mudam.
  - Sem motivo nenhum, a vaga volta ao relatório: `triagem = "pendente"`, sem `motivo_fora` nem `triada_em`.
  - Sem `--gravar`, só mostra o que mudaria: quantas perdem o motivo de região, quantas voltam e uma linha por vaga.
- **Rationale:** é o mesmo padrão do `integridade` (spec 034). A pessoa vê antes e confirma (constituição V).

## D11. Compatibilidade e efeitos para quem não usa regiões (FR-012)

- `PAISES_DA_REGIAO` continua com o mesmo nome. `so_regioes` (ats) passa a reconhecer as regiões novas como "remoto".
- Uma vaga "Remote - Asia" de empresa acompanhada passa a ser lida como remota. É o efeito esperado de reconhecer a
  região.
- Os testes de hoje que mudam (SC-006):
  - "South America" e "EU", pelos nomes novos;
  - o caso "só LATAM, vaga do mundo todo", que passa a não cortar, por decisão da spec.
