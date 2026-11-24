# Implementation Plan: A mesma vaga em vários portais

**Branch**: `058-vagas-repetidas` (a partir da `057-forcar-com-descricao`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary

Uma regra só de "mesma empresa" (`banco.empresa_base` e `banco.mesma_empresa`) passa a valer no `IndiceVistas`, que
a busca e o Adicionar Vaga já usam, e no casamento do Atualizar candidaturas.

Sobre essa regra entram:

- `banco.juntar`, que junta vagas repetidas;
- a prévia das repetidas já gravadas (comando e rotas);
- o "Link do anúncio original" no detalhe;
- as etiquetas de todos os portais, que já existem em `outras_plataformas` e passam a aparecer no front.

## Constitution Check

- **V:** a junção da revisão só acontece com o OK, depois da cópia do banco. O link original só é lido no clique.
- **VI:** a leitura do link usa o leitor do Adicionar Vaga (`fontes/link.py`), com as regras de cada portal.
- **II:** os testes usam empresas fictícias.

Gate: passa.

## Decisões

**D1. Nome-base da empresa** (`banco.empresa_base(nome) -> str`):

- `_sem_acento`;
- tudo que não é letra nem número vira espaço;
- saem as palavras de `SUFIXOS_EMPRESA`: ltda, sa, s, a, me, epp, eireli, inc, llc, ltd, corp, corporation, co,
  company, group, grupo, holding;
- saem as palavras iniciais de `PREFIXOS_EMPRESA`, só no começo: seja, carreiras, carreira, trabalhe, conosco, na, no;
- as palavras restantes são coladas, sem espaço: "Alfa Web" e "Alfaweb" dão "alfaweb";
- empresa genérica (`EMPRESAS_GENERICAS`) dá "".

`mesma_empresa(a, b)`: os dois nomes-base não vazios, e iguais, ou o menor, com pelo menos 5 letras, contido no
maior.

**D2. Reconhecimento:**

- `chave_vaga` passa a usar o nome-base;
- `IndiceVistas(vagas=None, so_recentes=True)` ganha `por_cargo: {titulo_norm: [(base, id)]}`. `achar()` tenta, nesta
  ordem: os ids; a chave exata; e, por último, o mesmo cargo com `mesma_empresa`;
- `so_recentes=False` serve para a sincronia;
- `dash/sincronia.py` (`proposta`, linha 42) troca o `por_chave` pelo `IndiceVistas(vagas, so_recentes=False)`;
- `vagas.py` (linha 389): o agrupamento dentro da busca usa `(tn, empresa_base(empresa) or normalizar(empresa))`.

**D3. Juntar** (`banco.juntar(principal, outros) -> dict`). Numa transação, a principal recebe:

- `outras_plataformas`: as plataformas das outras e as `outras_plataformas` delas, sem repetir a dela;
- `ids_relacionados`: os ids das outras e os relacionados delas;
- `descricao`, se ela não tinha: a primeira das outras que tiver, com `aplicar_integridade` e `analise_status`
  pendente, se ela não tinha nota definitiva;
- etapa: a mais adiantada (`contas.avancou`), com `etapa_em` e `resultado` dessa vaga. A triagem vira "seguir" se
  alguma estava em Aplicações;
- `anotacao`: as anotações somadas, sem repetir;
- `curriculos` e `documentos`: a união;
- `url_candidatura`: a primeira que houver.

Cada uma das outras vira `_ficha_curta(doc)` (spec 054), com `juntada_a = principal`. A ficha curta já tem
`arquivada_em`, então a vaga sai das listas. A busca continua reconhecendo os ids dela.

**D4. Principal** (`banco._principal(vagas)`): a ordem é etapa (em Aplicações) → descrição → nota definitiva → a mais
antiga (`encontrada_em`/`criada_em`).

**D5. Repetidas gravadas:**

- `banco.grupos_repetidos()` olha só as vagas não arquivadas. Duas vagas são do mesmo grupo quando têm um id em
  comum (`ids_da_vaga`) ou o mesmo cargo com `mesma_empresa`, encontradas até 60 dias uma da outra;
- os grupos são montados por união;
- devolve `[{"principal": resumo, "outras": [resumo], "etapa_final": etapa}]`, com
  `resumo = {id, titulo, empresa, plataforma, etapa, triagem, aderencia, tem_descricao}`;
- `banco.juntar_repetidas(grupos_ids)`:
  - recalcula os grupos;
  - só junta os grupos pedidos que ainda batem;
  - faz `backup_diario("repetidas")` antes;
  - devolve `{"juntados": n, "vagas": m, "ignorados": [...]}`;
- comando: `PY dash/banco.py repetidas [--gravar]`, que sem `--gravar` só mostra a prévia;
- rotas:
  - `GET /api/repetidas` → `{grupos}`;
  - `POST /api/repetidas/juntar` com `{grupos: [[principal, outro, ...], ...]}` → o resultado. Só deste computador.

**D6. Link original** (`PUT /api/vagas/<id>/link-original` com `{url}`; só deste computador):

1. `dados = link.ler(url)`. `LinkErro` → 422 `{erro}`.
2. `existente = IndiceVistas().achar({**dados, "id": dados["id"]})`, desde que seja diferente da vaga atual.
3. **A vaga do link já está no dashboard:** `principal = _principal([existente, atual])` e `juntar(principal, [a outra])`
   → `{juntada: principal_id, vaga: com_kit(principal)}`.
4. **Não está:** `banco.completar_pelo_link(vid, dados, url)`:
   - `descricao` (se veio), `url_candidatura = url`;
   - `ids_relacionados += dados.id` e `outras_plataformas += dados.plataforma`;
   - sem nota definitiva → pendente;
   - com IA ligada, `FILA.forcar(vid)`;
   - resposta `{juntada: null, vaga, verificando, verificando_agora}`.

**D7. Front** (dois briefs, pelo rodízio):

- **(a) Etiquetas e link no detalhe:**
  - as etiquetas de `outras_plataformas` no cartão (`TriageReport.cartao` e o `JobCard` do quadro) e no detalhe;
  - no detalhe, o campo "Link do anúncio original" com o botão "Ler o link";
  - os avisos: "A vaga já estava no dashboard: juntada à de {plataforma}." (e fecha o detalhe, se a vaga atual saiu) ou
    "Descrição lida: a vaga entrou na fila de verificação.".
- **(b) Aba Limpeza, seção "Vagas repetidas":**
  - o botão "Procurar repetidas" e os grupos;
  - em cada grupo, a principal, as outras e a etapa final, com uma caixa de seleção, marcada por padrão;
  - "Juntar N grupos", com confirmação.

**D8. Documentação:**

- `dash/API.md`: as rotas, `juntada_a` e a regra da empresa;
- `AGENTS.md`: o comando `repetidas`;
- `.agents/skills/buscar-vagas/SKILL.md`: o Fluxo E ganha "repetidas", depois `sincronizar_skills.py`.

## Testes (`tests/test_repetidas.py`, empresas fictícias)

- **empresa_base e mesma_empresa:**
  - "Alfaweb", "Alfaweb Corp", "Seja Alfaweb" e "Alfa Web Ltda." são a mesma empresa;
  - a ordem das palavras conta: "Web Alfa" não é "Alfaweb";
  - "Ita" ≠ "Itaú", e a genérica não casa.
- **IndiceVistas:** acha pela empresa contida com o mesmo cargo; não acha com outro cargo.
- **Sincronia:** casa "Seja Alfaweb" com "Alfaweb".
- **juntar:**
  - etiquetas, ids, descrição, etapa mais adiantada, anotações e currículos;
  - as outras com `arquivada_em` e `juntada_a`;
  - a busca acha a juntada pelo id.
- **grupos_repetidos, a principal e juntar_repetidas:** com o backup, e o grupo que mudou é ignorado.
- **Rotas:**
  - repetidas;
  - link original, com o leitor falso: a vaga que já existe é juntada; a nova é completada; o erro dá 422.

## Verificação

- A suíte inteira, mais o typecheck e o build.
- Na branch pessoal:
  - `PY dash/banco.py repetidas` mostra o grupo da Alfaweb;
  - na página: Limpeza → Vagas repetidas → juntar;
  - o cartão da Gupy mostra Gupy e JobGether.
