# Research: Análise de reprovação (spec 049)

## R1. Onde guardar a análise

- **Decision**: `dash/dados/reprovacao.json`, um objeto `{vaga_id: análise}`, com escrita atômica (`.tmp` +
  `os.replace`) e uma trava de thread, como em `relatos.py`.
- **Rationale**: o documento da vaga no banco vai inteiro para a lista de vagas da página; uma análise com cerca de
  30 motivos deixaria a lista pesada à toa. Um arquivo à parte é lido só quando a janela da vaga abre. "Só a última"
  sai de graça: a chave é a vaga.
- **Alternatives**: campo no documento da vaga (pesa a lista); um arquivo por análise em `curriculos/` (exigiria
  limpar as antigas e misturaria dados com documentos).

## R2. Qual texto é o "currículo atual"

- **Decision**: nesta ordem:
  1. `curriculo_ia.listar(vaga_id)[0]`: o JSON do currículo vira texto por `conferir.trechos(cv)`, linha por seção;
  2. o arquivo marcado em `curriculo_base.marcados()` no idioma do formato escolhido (`curriculo.FORMATOS[f]["idioma"]`),
     lido por `curriculo_base.ler` (com OCR, como na spec 037);
  3. `curriculo_ia.listar(base=True)[0]`;
  4. `curriculo_ia.perfil_texto()`.

  Fonte que falha (arquivo apagado, menos de 80 caracteres) passa para a próxima e deixa um aviso.
- **Rationale**: foi a decisão do usuário. O idioma do formato evita analisar um currículo em inglês para um
  currículo em português.
- **Alternatives**: sempre o base (rejeitada pelo usuário).

## R3. Formato pedido à IA e leitura tolerante

- **Decision**: a resposta é um objeto JSON `{motivos: [{grupo, motivo, trecho_cv, trecho_vaga, perguntas: [n]}],
  perguntas: [{n, texto}]}`. A leitura procura o objeto entre o primeiro `{` e o último `}`, tolera bloco de código e
  vírgula sobrando e, se o objeto vier cortado, aproveita os itens inteiros com `analise.lista_json` em cada chave.
  A reescrita usa um array `[{original, novo, motivos: [i]}]`, lido por `analise.lista_json`.
- **Rationale**: as IAs gratuitas cortam a resposta (spec 045). O leitor tolerante já existe e foi testado.
- **Alternatives**: duas chamadas (motivos e perguntas): o dobro de custo e de tempo.

## R4. Garantir que a IA não decida "não tem"

- **Decision**: o pedido proíbe afirmar falta. A conferência sem IA procura, em cada motivo, expressões de negação
  sobre a pessoa ("não tem", "não possui", "sem experiência", "falta experiência", "lacks", "does not have", "no
  experience"). O motivo afirmativo fica com o texto neutro "a vaga pede: <trecho_vaga>". Se ele não tiver pergunta
  ligada, ganha uma: "Você tem experiência com o que a vaga pede aqui: <trecho_vaga>? Conte onde e como." O estado ❌
  só existe em `respostas` (resposta `nao`).
- **Rationale**: é a regra central do pedido ("NÃO presuma que eu não tenho…") e da constituição IV. A lista de
  expressões é curta e testável.
- **Alternatives**: confiar só no pedido (não verificável).

## R5. Trecho do currículo existe?

- **Decision**: o trecho e o currículo passam por `conferir.norm` (sem acento, minúsculas, espaços únicos). O trecho
  vale se estiver contido no currículo ou se 80% das palavras dele aparecerem numa janela do currículo. Senão, o
  motivo fica com `trecho_ok: false`, e a página mostra "trecho não encontrado no currículo". Trecho vazio ou "não
  aparece" vira `trecho_cv: null`.
- **Rationale**: as IAs ajustam pontuação e espaços; a margem de 80% aceita isso sem deixar passar uma frase
  inventada.

## R6. Perguntas sensíveis

- **Decision**: `candidatura_ia.sensivel(texto)`, já usado na candidatura assistida, tira a pergunta. O motivo ligado
  a ela fica `sem pergunta`, com a nota "responda na candidatura". O pedido também proíbe esses assuntos.
- **Rationale**: reusa o detector que a constituição IV já cobre.

## R7. "Levar ao meu perfil" e "Usar só neste currículo"

- **Decision**:
  - **perfil**: no clique em Reescrever e gerar, `relatos.adicionar(pergunta, relato, vaga=vaga)` seguido de
    `relatos.levar_ao_perfil(id)`. A resposta guarda `levado: id do relato`, e um "Tentar de novo" não leva duas vezes.
    O relato aparece em Seus relatos como "no perfil" e no `perfil.md`, na seção Relatos, com a versão anterior
    guardada;
  - **só neste currículo**: nada é gravado fora da análise. O relato entra num bloco "Respostas confirmadas nesta
    análise (valem como fatos só para este currículo)", somado ao perfil no pedido do currículo e na conferência
    (`curriculo_ia.gerar(perfil=…)`). Assim a conferência não marca o fato como inventado (FR-018).
- **Rationale**: reusa o caminho de levar ao perfil que já guarda a versão anterior. A conferência já recebe o
  perfil como parâmetro.
- **Nota**: a resposta "só neste currículo" fica guardada dentro da análise da vaga (FR-014, para mudar e gerar de
  novo). Ela não vira relato nem fato do perfil, e some quando uma análise nova substitui esta.

## R8. Fila, situações e tipos no gerador

- **Decision**: a análise usa o tipo `reprovacao` com a situação `analisando`. Reescrever e gerar usa o tipo
  `curriculo` com as situações `reescrevendo`, `escrevendo`, `gerando` e `conferindo`. O alvo é sempre
  `{vaga_id, titulo, empresa}`, e `_ultimo_pedido` guarda `("reprovacao", vaga_id, tec)` ou
  `("reescrita", vaga_id, None)`.
- **Rationale**: a seção da vaga já mostra o andamento das gerações do tipo `curriculo`; basta incluir `reprovacao`
  no filtro `ehDoAlvo`. As situações novas entram em `ETAPAS` e em `SITUACOES_ATIVAS` no front.

## R9. Pedido do currículo com o resultado da análise

- **Decision**: `curriculo_ia.montar_pedido` ganha `adicional`, um bloco final "## Resultado da análise de reprovação
  (a pessoa confirmou)" com:
  - os trechos reescritos, como texto-base para as seções correspondentes;
  - a lista "A pessoa respondeu que NÃO tem (nunca apresente como competência nem experiência)".

  Os ⚠️ "só neste currículo" vão no perfil (R7). O meta ganha `"reprovacao": true`.
- **Rationale**: muda pouco no gerador do currículo e não altera nada quando o argumento falta (SC-001).

## R10. Respostas que mudam depois do currículo

- **Decision**: a análise guarda `respostas_em` (hora da última gravação) e `gerado_em` (hora do último currículo
  gerado por ela). A página mostra "as respostas mudaram desde o último currículo" quando
  `respostas_em > gerado_em`. Reescrever e gerar sempre usa as respostas atuais.

## R11. Vaga já com análise: perguntar de novo?

- **Decision**: a análise nova recebe o perfil com os relatos (já com os levados ao perfil). O pedido diz para não
  perguntar o que o perfil já responde. Não há outra checagem automática.
