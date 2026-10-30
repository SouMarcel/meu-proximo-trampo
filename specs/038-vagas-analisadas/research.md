# Research: vagas sem análise e a caixa "Analisadas"

## R1. O que é "sem nota"

- **Decision**: a regra é `!temNota(v)`, ou seja, `aderencia` não é número. É a mesma do selo da vaga
  (`situacaoNota`):
  - aguardando a IA, descrição pendente e falha contam como sem nota;
  - nota provisória (`nota_sem_descricao`) conta como analisada.
- **Rationale**: é a decisão 4 do usuário. Também evita uma segunda regra que poderia divergir do selo.

## R2. Onde a vaga sem nota passa direto

- **Decision**: dentro do filtro da lista, depois da busca por texto, `if (!temNota(v)) return true`. Assim ela não
  passa por Senioridade, Modo, Nota mínima nem Publicada há até (decisão 2).
- **Rationale**:
  - a busca é a pessoa procurando algo específico;
  - os outros filtros dependem da análise (senioridade e modo) ou escondiam a vaga nova sem aviso;
  - "Publicada há até" entra junto, por decisão do usuário ("todos menos a busca").
- **Alternatives considered**: deixar a data de publicação valendo também. Foi descartada pelo usuário.

## R3. Números e "Marcar todas"

- **Decision**: com a caixa marcada, `counts` e os `ids` do "Marcar todas" usam só `visivel(v)`. Os filtros
  secundários não mudam os números das abas, como hoje.
- **Rationale**: é a decisão 3. Ninguém marca como não seguida uma vaga que não viu (princípio V).

## R4. "Mostrando X de Y"

- **Decision**: o Y é o total visível na aba, e a linha acrescenta "(N sem análise ocultas)" quando a caixa esconde
  vagas dela.
- **Rationale**: com o Y igual ao número da aba, a página fica coerente, e o efeito da caixa continua à vista.

## R5. Nome e lugar da caixa

- **Decision**: "Analisadas", com `title` "Oculta as vagas ainda sem análise", na linha dos filtros secundários, depois
  de "Publicada há até". Ela usa `<input type="checkbox">` com `<label>`, que dá acessibilidade sem trabalho extra.
- **Rationale**: é a decisão 1. O lugar é o mesmo dos outros filtros da lista.
