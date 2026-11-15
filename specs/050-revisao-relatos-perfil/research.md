# Research: Revisão do perfil ao levar relatos (spec 050)

## R1. Onde o relato espera a revisão

- **Decisão**: no `relatos.json`, fora do perfil (`no_perfil: false`). No Reescrever e gerar, a análise de reprovação
  guarda ali as respostas "Levar ao meu perfil" em vez de colá-las no `perfil.md`.
- **Motivo**: o `relatos.com_relatos` já põe os relatos fora do perfil no texto usado pelos pedidos à IA e pela
  conferência. O currículo da vaga continua usando a resposta como fato sem nada novo (FR-001), e Seus relatos
  mostra o relato à espera, então os dois lugares passam a ter a mesma fila de relatos para revisar.
- **Alternativas**: guardar a resposta só na análise até a revisão (rejeitada: o relato some se a pessoa rodar outra
  análise na vaga e não aparece em Seus relatos).

## R2. Como achar os lugares do perfil sem IA

- **Decisão**: o perfil segue o formato do `perfil.exemplo.md` e do `primeiros_passos.montar_perfil`: seções `## Nome`
  e, na Experiência, cargos `### Cargo — Empresa (datas)`, com itens `- …`. `estrutura(perfil)` devolve a lista de
  lugares (`secao`, `cargo` = o título `###` inteiro, início e fim das linhas). A IA recebe a lista dos lugares e
  devolve o lugar escolhido como está nela.
- **Motivo**: a IA só escolhe entre lugares que existem, e a conferência compara textos iguais em vez de adivinhar.
- **Alternativas**: deixar a IA devolver o perfil inteiro reescrito (rejeitada: a pessoa não teria como aceitar item a
  item, e qualquer mudança fora dos relatos passaria despercebida).

## R3. Conferência da proposta

- **Decisão**: sem IA, para cada item e discordância:
  - `atual` e `trecho_perfil` precisam existir no perfil (comparação de linha normalizada: espaços e caixa; a mesma
    ideia de `reprovacao.trecho_no_curriculo`, mas por linha inteira, porque "muda" e "sai" trocam linhas);
  - números, datas e nomes próprios do texto novo (`conferir._fatos_do_texto`) precisam estar nos relatos ou no
    perfil;
  - `reprovacao.NEGACAO` (afirmação de falta) descarta o item;
  - `candidatura_ia.sensivel` ou seção fora de Experiência, Habilidades, Formação, Certificações, Idiomas e Resumo
    desmarca o item, com aviso.
- **Motivo**: são as mesmas regras de "só fatos" já usadas pela 049 e pela conferência do currículo.

## R4. Aplicar os itens sem IA

- **Decisão**: `aplicar(perfil, itens)` trabalha por linhas:
  - "entra" num cargo: depois do último item `- ` do cargo (ou logo abaixo do título, se ele não tiver itens);
  - "entra" numa seção: depois da última linha não vazia da seção; seção que não existe é criada antes de "Relatos"
    (ou no fim);
  - "muda": troca a linha achada pelo texto novo;
  - "sai": tira a linha achada; a seção "Relatos" que ficar só com o título e a frase de abertura também sai.

  As posições são calculadas antes, e as mudanças aplicadas de baixo para cima. Uma linha não achada no momento de
  gravar torna o item inválido, e a gravação é recusada com a mensagem (não aplica pela metade).
- **Motivo**: a gravação fica previsível e testável, e o texto que a pessoa viu é o que entra.

## R5. Perfil que mudou entre a proposta e a gravação

- **Decisão**: a proposta guarda o sha256 do texto do perfil em que se baseou. O Gravar compara com o perfil atual e
  devolve 409 "o seu perfil mudou desde a proposta; revise de novo" (FR-013).
- **Alternativas**: tentar reaplicar sobre o perfil novo (rejeitada: os trechos podem ter mudado, e a pessoa decidiu
  sobre outro texto).

## R6. Uma revisão por origem

- **Decisão**: a chave é `vaga:<id>` (análise de reprovação) ou `relatos` (Seus relatos). Uma revisão nova na mesma
  origem substitui a anterior (FR-015). A revisão gravada fica guardada para a seção mostrar "levadas ao perfil em …"
  até a próxima.
- **Motivo**: simples de mostrar nos dois lugares e coerente com "só a última análise" da 049.

## R7. Fila e alvo do gerador

- **Decisão**: o tipo `revisao_perfil` entra na fila única. O alvo é o da vaga na origem `vaga:<id>` (a janela da
  vaga mostra o andamento) e `{perfil: true}` em Seus relatos. `ehDoAlvo` do front ganha esse caso.
- **Motivo**: uma geração por vez, com andamento, falha e "Tentar de novo" como as outras (FR-004).

## R8. Sem IA

- **Decisão**: `POST /api/perfil/revisao` sem IA responde 200 com `{sem_ia: true, levados, aviso}`, depois de levar
  os relatos pelo caminho de hoje (`relatos.levar_ao_perfil`). A página mostra o aviso.
- **Motivo**: um botão só nos dois lugares, e a ferramenta continua útil sem IA (constituição III).
