# Research: LinkedIn com menos pedidos

## R1. A busca pública aceita "OR"? (PENDENTE: verificar com um pedido real)

- **Decision**: montar `keywords` como `"analista de dados" OR "product owner" OR designer`. Isso precisa ser confirmado
  antes da implementação da US1, com **um único pedido** à busca pública (`jobs-guest/.../search`). O pedido só é
  feito com o OK da pessoa e pelo menos 6 horas depois do último bloqueio. Comparar com um pedido só de um dos
  cargos não entra, para não gastar mais pedidos. O que conferir:
  - a resposta é 200;
  - vêm cards;
  - os títulos batem com mais de um dos cargos.
- **Tentativa 1 (2026-10-16)**: um pedido com 2 cargos fictícios ligados por OR, 2 dias depois do último bloqueio.
  Foi recusado logo no primeiro pedido ("limitou as consultas"). O código da resposta não foi registrado, porque o
  aviso de hoje não o mostra. Isso indica recusa ligada à rede (IP), não ao volume. A verificação do OR continua
  pendente. Próxima tentativa: outra rede, ou depois que o aviso com o motivo (US3) estiver pronto, para saber o
  código.
- **Tentativa 2 (2026-10-16, mesma rede, depois da US3)**: `"product manager" OR "data analyst"`, remoto, Brasil, 7
  dias. Resposta 200, 10 cards. Títulos: 7 de "product manager" e 3 de analista de produto ("Product Analyst",
  "Analista de Produtos"). Nenhum título exato de "data analyst" na primeira página.
- **Conclusão**: o OR é aceito, não dá erro e traz vagas de mais de um termo. Não é um OR estrito com a mesma
  quantidade de vagas por termo: o LinkedIn ordena por relevância, e um cargo pode dominar a primeira página. As 3
  páginas da consulta combinada compensam em parte. **Portão aprovado** (`AGRUPAR = True`), com a ressalva
  registrada. Se a pessoa notar falta de vagas de algum cargo, basta voltar `AGRUPAR = False` em
  `fontes/linkedin.py` (plano B) para ter uma consulta por cargo de novo.
- **Rationale**: a busca de vagas do LinkedIn aceita operadores booleanos na interface logada. A busca de convidado
  usa o mesmo parâmetro `keywords`, mas isso não está documentado.
- **Plano B** (se não aceitar): `AGRUPAR = False`. Fica uma consulta por cargo, com as US2 a US4 inteiras. O ganho
  continua grande, porque as descrições são o maior volume.
- **Alternatives considered**: palavras soltas ("analista dados product owner"), rejeitadas porque a relevância traz
  ruído e perde cargos.

## R2. Forma de cada cargo na expressão

- **Decision**:
  - um cargo entre aspas fica como está;
  - um cargo de uma palavra fica sem aspas;
  - um cargo de várias palavras sem aspas vai entre parênteses (`(product owner)`), para o OR não quebrar o cargo;
  - aspas soltas ou desequilibradas são removidas antes de montar.
  
  Com **um só cargo** no grupo, a consulta continua exatamente como hoje (`termo.strip('"')`), para não mudar o
  resultado de quem tem um cargo.
- **Rationale**: preservar o que a pessoa escreveu (FR-001) sem gerar expressão inválida.
- **Alternatives considered**: pôr aspas em todo cargo de várias palavras. Rejeitado porque mudaria o sentido (frase
  exata) de cargos que a pessoa escreveu sem aspas.

## R3. Tamanho máximo da expressão

- **Decision**: `MAX_EXPRESSAO = 200` caracteres. Acima disso, os cargos são divididos em partes, na ordem da
  configuração, preenchendo cada parte até o limite (`filtros.expressao_or` devolve uma lista de expressões).
- **Rationale**: URLs de busca do LinkedIn com `keywords` longas funcionam, mas não há limite documentado; 200 cobre
  cerca de 8 a 10 cargos típicos numa consulta só e evita resposta estranha.
- **Alternatives considered**: sem limite. Rejeitado por risco de erro silencioso com listas grandes.

## R4. Páginas por consulta combinada

- **Decision**: `MAX_PAGINAS_AGRUPADA = 3` (30 vagas), parando antes se a página vier com menos de 10 vagas ou se
  já houver `por_termo` vagas. A consulta de um cargo só continua com 1 página.
- **Rationale**: decisão da pessoa. 3 páginas por grupo ainda dão menos pedidos que uma por cargo com 4 ou mais
  cargos.

## R5. Cargos da vaga encontrada pela consulta combinada

- **Decision**: `filtros.termos_no_titulo(titulo, termos)` devolve os cargos cujas palavras aparecem todas no título,
  comparando sem acento e sem diferenciar maiúsculas. Para um cargo entre aspas, as palavras precisam aparecer em
  sequência. Se nenhum cargo bater, a vaga fica com a expressão da consulta como termo.
- **Rationale**: `termos` aparece no relatório e no digest. Mostrar a expressão inteira em toda vaga não ajudaria a
  pessoa.

## R6. Quais vagas entram na fila de descrições e quando são "pendentes"

- **Decision**:
  - **Fila**:
    1. as vagas do banco com `descricao_pendente` da mesma plataforma, com `triagem == "pendente"` e sem `etapa`
       (não descartadas e fora do quadro), da mais recente para a mais antiga (`publicada_em`, depois
       `encontrada_em`);
    2. as candidatas novas, da mais recente para a mais antiga;
    3. as novas "fora dos critérios", como hoje.
  - **Limite**: 20 pedidos por busca, contando os que falham.
  - **Marca**: só candidatas e pendentes recebem `descricao_pendente`, e só quando ficaram sem texto por limite,
    bloqueio ou espera. As "fora dos critérios" sem texto ficam como hoje: não vão para a IA e não precisam de nota.
  - **Erro que não é bloqueio** (404, vaga removida, página que mudou): a marca sai e a vaga segue com o que tem
    (FR-009).
- **Rationale**: as candidatas são as que a IA analisa; as "fora" só são lidas para a pessoa conferir o motivo.
- **Como saber se foi bloqueio**: `fonte.espera()` ou o estado `bloqueado` da fonte depois da chamada. Se a fonte
  estiver parada, a vaga fica pendente; se não, o erro é da vaga.

## R7. Onde a pendente do banco é completada

- **Decision**: `executar` continua sem gravar. Ele devolve `resultado["descricoes_completadas"]`, uma lista de
  `{id, descricao, tipo_emprego}`, e `gravar_resultado` aplica a lista com `banco.completar_descricao`, que:
  - grava o texto e o tipo de emprego;
  - tira a marca;
  - roda `aplicar_criterios`: o tipo de emprego pode mandar a vaga para "Fora dos critérios".
  
  O `buscador` pede a análise (`analise.FILA.pedir()`) também quando houver completadas.
- **Rationale**: mantém o desenho atual (executar sem efeito colateral, gravar no fim) e funciona igual no terminal,
  onde o resultado vai para `candidatas.json` e o `gravar` vem depois.

## R8. Espera depois do bloqueio

- **Decision**:
  - **Arquivo**: `.cache/linkedin-espera.json` com `{"desde": ISO, "motivo": texto}`.
  - **`linkedin.espera()`**: devolve `{"ate": ISO, "motivo"}` enquanto `agora < min(desde, agora) + 6 h`; senão
    devolve `None`. Arquivo ilegível também dá `None`.
  - **Gravação**: só em `_bloquear`.
  - **Durante a espera**: `buscar` devolve `[]` com o aviso uma vez por busca e `descrever` não faz pedido.
  - **Testes**: `ESPERA = timedelta(hours=6)` e o caminho do arquivo podem ser trocados (`linkedin.ARQ_ESPERA`).
- **Rationale**: a espera vale para a página, o terminal e o chat, porque todos usam a mesma fonte e a mesma
  `.cache/`.
- **Alternatives considered**: guardar no banco, rejeitado porque a espera é estado do portal, não dado da pessoa;
  memória do servidor, rejeitado porque o terminal e o chat não veriam.

## R9. Confirmação antes de buscar durante a espera

- **Decision**:
  - **Página**: `buscador.plano()` ganha `espera` (lista de `{portal, ate, motivo}` das fontes ligadas em espera) e
    `so_espera`, verdadeiro quando todas as fontes estão em espera. `iniciar(confirmar_espera=False)` recusa:
    - com `so_espera`, sem confirmação possível;
    - com `espera` sem confirmação, com `precisa_confirmar=True`, como já acontece na busca recente.
    
    O diálogo mostra o aviso e o botão "Buscar sem o LinkedIn".
  - **Terminal**: `vagas.py buscar` confere antes de travar.
    - Com `so_espera`: avisa e sai com o código 5.
    - Com espera e `sys.stdin.isatty()`: pergunta `[s/N]`.
    - Sem terminal interativo: precisa de `--confirmar-espera`; sem ela, avisa e sai com o código 5.
  - **Skill**: ao receber o código 5, mostra o aviso, pergunta à pessoa e repete com `--confirmar-espera` se ela
    confirmar.
- **Rationale**: reaproveita o padrão de confirmação que já existe (`precisa_confirmar`) e dá ao assistente um sinal
  claro (código de saída) para perguntar.

## R10. Motivo do bloqueio no aviso

- **Decision**: `BLOQUEIO` continua como texto-base; o aviso fica `"{BLOQUEIO} ({motivo}); em espera até HH:MM"`. Os
  motivos:

  | Resposta | Motivo |
  |---|---|
  | 429 | excesso de pedidos |
  | 999 | recusa automática, costuma ser a rede: VPN, Wi-Fi corporativo ou internet compartilhada |
  | 3xx | pediu login |
  | 401/403 | acesso negado (código N) |

- **Rationale**: a pessoa sabe se espera ou se troca de rede (pedido original da conversa).

## R11. Aviso de cargos

- **Decision**: `filtros.aviso_cargos(f, fontes) -> str | None`. Avisa quando `len(f["termos"]) > 5` ou, com a busca
  internacional ligada, quando os cargos do exterior passam de 5, desde que `linkedin` ou `indeed` estejam entre as
  fontes. Constante `MAX_CARGOS_AVISO = 5`. Na página, o painel replica a regra em JS ao lado do contador (que já
  avisa "muitas consultas" acima de 20), e o diálogo de busca mostra `plano.aviso_cargos`.

## R12. Contagem de consultas

- **Decision**: `vagas.contar_consultas` conta, para fontes com `AGRUPAR`, os grupos distintos multiplicados pelo
  número de partes da expressão, e não grupos × cargos. A página (`contarLinkedin` em `dashboard.html`) passa a
  usar a mesma regra, com 1 parte por grupo (a divisão por tamanho é rara; o número exato vem do `plano`). O tempo
  estimado da busca segue a contagem.
