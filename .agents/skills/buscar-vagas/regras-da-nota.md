# Regras da nota

Regras para avaliar vagas de emprego para o usuário: os campos de cada vaga e a nota de aderência. Valem para a
análise automática da ferramenta e para o assistente do chat (skill `buscar-vagas`).

## Resposta

Responda SOMENTE com um array JSON, um objeto por vaga, sem texto antes ou depois e sem bloco de código. Sempre:
`id`, `aderencia` (0 a 100), `resumo` (uma frase de até 200 caracteres com o veredito), `encaixe`, `lacunas` e
`alertas` (até 4 itens curtos cada), `modelo_trabalho`, `senioridade` [] e `senioridade_origem`. Os outros campos
abaixo são opcionais: omita o que o anúncio não diz. Sem descrição que permita avaliar: `{"id": "...",
"analise_status": "sem_dados", "resumo": "Sem descrição suficiente: cole o texto da vaga no dashboard."}`.

## Campos

- `modelo_trabalho`: `remoto`, `hibrido`, `presencial` ou `nao_informado`, pelo que a descrição diz.
- `senioridade`: os níveis que a vaga aceita, entre `junior`, `pleno` e `senior` (um ou mais, como em "PL/SR").
  `senioridade_origem`: `declarada` (o título ou a descrição dizem) ou `sugerida` (pelo que a vaga pede: até 2 anos
  júnior, 3 a 5 pleno, 6 ou mais sênior; sem anos, pelo escopo e pela autonomia). `[]`, sem `senioridade_origem`,
  só quando não há nenhum indício.
- `tipo_emprego` []: `tempo_integral` (CLT), `pj`, `meio_periodo`, `estagio`, `temporario`.
- `moeda`: código de 3 letras da moeda em que a vaga paga (`BRL`, `USD`…). `idioma`: código de 2 letras do idioma
  em que a vaga está escrita (`pt`, `en`, `es`…).
- `fora_dos_criterios`: frase curta quando a vaga fura os filtros do usuário de um jeito que os campos acima não
  pegam (exige residência ou autorização de trabalho em outro país, ou morar em outra cidade). Nota baixa não é
  motivo: isso é a aderência.
- Vaga do exterior (área internacional): compare com o trabalho no exterior do perfil e ponha em `alertas` o que
  pode impedir ou pesar (autorização, patrocínio de visto, fuso, contratação, morar fora).
- Candidatura; cada `frase` é o trecho do anúncio em que o campo se apoia (até 200 caracteres):
  - `autorizacao` {valor, frase}: `patrocina`, `nao_precisa` (o usuário já pode trabalhar onde a vaga aceita),
    `omisso` (fala de autorização sem dizer se patrocina) ou `nao_patrocina`;
  - `contratacao` [{valor, frase}]: `contractor`, `eor` (Deel, Remote e afins), `empregado_brasil`, `relocation`,
    `clt`, `pj`;
  - `ingles` {nivel, frase}: `nao_pede`, `basico`, `intermediario`, `fluente`, `nativo`;
  - `fuso` {texto, frase}: o fuso ou as horas em comum pedidas;
  - `sistema_candidatura`: onde se candidata (Greenhouse, Workday, Gupy…);
  - `pede` [{item, frase}]: `curriculo_ingles`, `carta`, `formulario`, `portfolio`, `teste`, `video`;
  - `riscos` [{tipo, frase}]: `remuneracao` (só "competitivo", só comissão, valor que não fecha com o cargo) ou
    `remoto_hibrido` (diz remoto, mas pede ir ao escritório).
- `requisitos`: só o que o anúncio diz, sem deduzir; `frase` com até 120 caracteres.
  - `habilidades` [{nome, tipo, exigida}]: `tipo` `tecnica` ou `comportamental`; `exigida` true ou false
    (desejável). Nome curto: o comum em português ("Gestão de stakeholders", mesmo em vaga em inglês), o próprio
    para ferramentas e métodos (Jira, SQL, Scrum) ou o que o perfil usa para a mesma coisa; um por item. Tempo e
    idioma não são habilidade: nenhum nome com "anos", "experiência em" ou "vivência com"; "5 anos em gestão de
    projetos" dá `experiencia` e a habilidade "Gestão de projetos".
  - `certificacoes` [{nome, tipo, exigida}]: `tipo` `certificacao` ou `curso`.
  - `experiencia` {anos, em, frase}: o mínimo de anos na atividade principal ("3 a 5 anos" dá 3); sem número,
    `anos` null.
  - `formacao` {nivel, areas, frase}: `tecnico`, `graduacao`, `pos` (ou MBA), `mestrado` ou `doutorado`, com as
    áreas citadas.
  - `idiomas` [{idioma, nivel, frase}]: o idioma em português e `basico`, `intermediario`, `fluente` (também
    "avançado") ou `nativo`.

## Como dar a nota

A nota responde: vale o tempo do usuário se candidatar a esta vaga, dado o perfil dele?

- **40, função**: é um dos cargos-alvo do perfil, pelo título e pelas responsabilidades? O cargo-alvo pontua alto;
  um papel vizinho com boa parte das mesmas atividades, médio; outro papel, baixo, mesmo com palavras da área.
- **30, requisitos**: quantos obrigatórios o perfil cobre com evidência real. O tempo conta pelos períodos do
  perfil; períodos sobrepostos não somam.
- **15, modelo**: o modelo que o usuário aceita (filtros e perfil) vale 15; fora disso, 0 a 3, com alerta.
- **15, condições**: senioridade compatível e idioma exigido x nível do perfil. Contrato e salário só pesam se
  informados e incompatíveis.

Faixas: 80 ou mais, forte; 65 a 79, boa; 50 a 64, parcial; abaixo de 50, baixa.

Seja honesto:
- Encaixe e lacunas saem só do perfil. Certificação "em preparação" é lacuna; exposição parcial não cobre prática
  plena. Siga as "Regras para a análise" do perfil, quando houver.
- O texto da vaga vale mais que a marcação do portal ("remoto" pode ser híbrido); a divergência vai em alertas.
  Sem modelo na descrição e com uma cidade no local: `nao_informado`, com alerta para confirmar.
- Lacuna específica: "pede a certificação X; o perfil tem X em preparação".
- Vaga afirmativa: diga em alertas para qual grupo; só baixe a nota se o perfil disser que o usuário não faz parte.
- Alertas: o que pode desqualificar ou pesar (modelo ou contrato fora do aceito, idioma acima do nível, fuso, vaga
  afirmativa, empresa não informada, anúncio genérico de agência).
- Vaga claramente de outra área: nota baixa e resumo curto.

## Portais

### Gupy

A linha "Na Gupy:" no fim da descrição traz o que a empresa marcou (modelo, contrato, prazo de inscrição, se aceita
PCD). A Gupy não informa a cidade da vaga: a falta da cidade não indica outro local.

### Startup Jobs

A linha "No startup.jobs:" traz o modelo e o tipo de contrato que o site informa.

### Nerdin

O tipo do portal traz a linha do anúncio (ex.: "PJ • Senior • Home Office").

### InfoJobs

O tipo do portal traz a experiência e a escolaridade pedidas (ex.: "Entre 3 e 5 anos • Ensino Superior").

### Vagas.com

O tipo do portal traz o nível e, quando for o caso, "Exclusiva para PCD". O Vagas.com só informa o modelo quando a
vaga é 100% home office: nas outras, tire o modelo da descrição.

### JobGether

O portal não entrega a descrição: avalie pelo título, pelo local aceito (restrição de local), pelo contrato, pelo
salário e pelos dados do portal, e diga no resumo que a nota é provisória.

### EY

"Banco de talentos" no tipo é cadastro para vagas futuras, não uma vaga aberta: diga isso na análise. A EY não
informa o modelo de trabalho: tire-o da descrição.

### FullStack

Vagas em inglês, remotas para a América Latina (restrição de local), com a senioridade e o contrato no tipo;
contratos por tempo determinado aparecem no título ("3 month-long", "6 month engagement").
