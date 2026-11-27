# Research: Conflitos do Meu perfil mais claros e seguros

Não sobraram dúvidas no Technical Context. As decisões abaixo saíram da leitura do código atual
(`primeiros_passos.py`, `dash/servidor.py`, `MeuPerfil.tsx` na `frontend-react`).

## R1. Como saber que o rascunho é mais antigo que o perfil

- **Decision**: `normalizar_rascunho` e `rascunho_sem_ia` gravam `gerado_em` (ISO, segundos). A prévia compara com a
  data de modificação do `perfil.md`. Rascunho sem `gerado_em` (feito antes desta spec) conta como "data desconhecida".
- **Rationale**: a data do arquivo pega qualquer caminho que mude o perfil (assistente, relatos, revisão, edição à mão,
  assistente no chat), sem cada caminho ter de registrar nada.
- **Alternatives considered**: um registro de "última gravação" em cada caminho (frágil: a edição à mão escapa);
  guardar uma cópia do perfil no rascunho (mais dado e mais texto pessoal no `.cache`).

## R2. O que "sairia" do perfil

- **Decision**: `itens_que_sairiam(atual, novo)`: as linhas do perfil atual que são item de lista (`- `) ou título
  (`#`), cuja forma normalizada (`_chave`: sem acento, minúscula, espaços únicos) não aparece no texto novo. Até 60
  itens, na ordem do perfil.
- **Rationale**: o `diferencas` de hoje é um diff de linhas e mistura o que muda de lugar ou de pontuação com o que some;
  a pessoa precisa ver o que **some**. Linha igual em outro lugar não conta como perda.
- **Alternatives considered**: pedir à IA a comparação (caro e contra o princípio III); o diff atual só com as linhas
  "-" (mostra reescritas como perda e esconde a ordem).

## R3. Quando o aviso aparece

- **Decision**: `aviso` existe quando há perfil gravado, o rascunho é da IA (`origem == "ia"`; sem IA a Revisão já
  começa do perfil atual) e (a) `gerado_em` é anterior à data do perfil, ou (b) `gerado_em` não existe e
  `itens_que_sairiam` não está vazio. A prévia recalculada com o texto editado pela pessoa refaz a lista.
- **Rationale**: segue FR-002 e FR-003 da spec.

## R4. Perfil mudou com a Revisão aberta

- **Decision**: a prévia devolve `perfil_versao` (SHA-256 do texto do perfil, 16 primeiros hex; `null` sem perfil). O
  `PUT /api/perfil` aceita `perfil_versao` e responde 409 quando não bate. Sem o campo, grava como hoje (o pedido
  antigo continua funcionando).
- **Rationale**: hash do texto não depende de relógio e pega a mudança feita no mesmo minuto.
- **Alternatives considered**: comparar a data do arquivo (mesma precisão de segundos, pior no Windows com cópias).

## R5. Refazer o rascunho herdando escolhas

- **Decision**: no `POST /api/perfil/rascunho`, depois de montar o novo, `herdar_escolhas(novo, antigo)`: para cada
  conflito novo, procura no antigo um conflito com o mesmo `campo` normalizado que tenha escolha; se o valor escolhido
  (normalizado) é igual ao `valor` de uma opção nova, marca essa opção. O resto fica sem escolha.
- **Rationale**: FR-005; casa só o que é inequívoco (princípio IV).
- **Alternatives considered**: casar por posição (a IA reordena os conflitos); casar por fonte (a mesma fonte pode
  mudar de valor quando o perfil mudou).

## R6. Valor e nota separados

- **Decision**: `FORMATO` passa a `"opcoes": [{"valor", "nota", "fonte"}]` e uma regra nova no pedido: "o valor é só o
  dado (a data, o nome, o cargo), sem explicação; a explicação vai em nota". `normalizar_rascunho` guarda `nota`
  (até 200 caracteres, documentos mascarados; vazia se não vier). `_escolher` usa só `valor` (já é assim).
- **Rationale**: FR-006 e FR-007; nada é cortado por regra do lado da ferramenta (se a IA não separar, o valor fica
  como veio e o Diagnóstico aponta as datas).
- **Alternatives considered**: cortar o que está entre parênteses no valor (estraga nomes como "Licenciatura (EAD)").

## R7. Diagnóstico de data com texto a mais

- **Decision**: em `diagnosticar`, para `inicio` e `fim` de cada experiência que têm marcador de conflito já escolhido,
  resolve o valor com `_escolher`; se não for "só data" (`mm/aaaa`, `aaaa`, `mês/aaaa` por extenso ou abreviado, ou
  "atual"), acha `fraco`: "A data escolhida em <cargo> traz texto a mais: <valor>." com `ir: "conflitos"`.
- **Rationale**: FR-008; a data da experiência é o único lugar em que o formato é conhecido. Formação e certificações
  são texto livre e ficam com o aviso da Revisão e o refazer.

## R8. Conflitos recolhidos na tela

- **Decision**: ao entrar na tela Conflitos, o front guarda o conjunto de índices com `escolha != null` naquele
  momento; esses vão para um `<details>` "N resolvidos (mudar)", fechado; os demais aparecem abertos. Escolher durante a
  visita não move o conflito (FR-010). Tudo resolvido: frase "Todos os conflitos estão resolvidos." acima do resumo.
  A `nota` aparece sob o valor, em letra menor.
- **Rationale**: só tela, sem campo novo no servidor; a escolha continua gravada a cada clique, como hoje.

## R9. Botões do aviso na Revisão

- **Decision**: "Refazer o rascunho" (com IA: chama o rascunho, volta à tela Conflitos se houver conflito sem escolha,
  senão remonta a Revisão; sem IA, desabilitado com o motivo), "Manter o perfil atual" (vai para a tela Concluído sem
  gravar) e o Gravar, que vira "Gravar mesmo assim (substitui o perfil)" e só grava depois de "Ver o que muda".
- **Rationale**: as três saídas da spec (US1) sem fluxo novo no servidor.
