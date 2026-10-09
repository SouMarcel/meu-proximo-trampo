# Research: Kit de candidatura

## 1. Campos novos da análise

- **Decision**: entram no mesmo pedido da análise automática (`dash/analise.py`), que lê os campos da
  skill buscar-vagas no trecho entre "`modelo_trabalho`:" e "4. **Gravar.**"; a skill ganha os campos
  nesse trecho, e `banco.validar_analise` passa a aceitar:
  - `autorizacao`: `{valor: patrocina | nao_precisa | omisso | nao_patrocina, frase}`;
  - `contratacao`: lista de `{valor: contractor | eor | empregado_brasil | relocation | clt | pj, frase}`;
  - `ingles`: `{nivel: nao_pede | basico | intermediario | fluente | nativo, frase}`;
  - `fuso`: `{texto (até 80), frase}`;
  - `sistema_candidatura`: texto curto (Greenhouse, Lever, Workday, Gupy…), só quando a vaga não tem
    `ats` da fonte;
  - `pede`: lista de `{item: curriculo_ingles | carta | formulario | portfolio | teste | video, frase}`;
  - `riscos`: lista de `{tipo: remuneracao | remoto_hibrido, frase}`.
  Frase até 200 caracteres. Valor fora das opções vira "não informado" (o campo cai), sem derrubar a
  análise inteira.
- **Rationale**: uma chamada só por lote (custo e tempo iguais aos de hoje); os campos de hoje e a nota
  não mudam; a situação da pessoa (passaporte, autorização, sponsor) já vai no pedido por
  `filtros.criterios_extra`, e a regra "não precisa só quando o anúncio aceita um país onde ela pode
  trabalhar" vai escrita na skill.
- **Alternatives considered**: chamada separada para o kit (dobra o custo); só na abertura do detalhe
  (atrasa a página e foge do padrão de "nada roda sem pedido" ao contrário).

## 2. Sem IA

- `ats` da fonte (spec 009), sinais de patrocínio e relocation, `restricao_local` e o checklist por
  palavras do anúncio (PT/EN: "cover letter", "carta de apresentação", "portfolio", "portfólio",
  "video", "vídeo", "take-home", "teste técnico", "case", "coding challenge", "application form",
  "questionário"). Os outros campos mostram "vem com a análise".

## 3. Checklist

- **Decision**: calculado (`dash/kit.py checklist(v)`) a partir de: itens de toda vaga (currículo,
  candidatura), `pede` da análise, palavras do anúncio (sem IA) e itens da pessoa; o estado da pessoa
  fica gravado na vaga em `kit` (`{estados: {item: a_fazer|pronto|nao_se_aplica}, extras: [texto],
  removidos: [item]}`), editável pela rota de atualização da vaga. Nova análise só acrescenta itens: o
  estado gravado é por item e não é tocado.
- Currículo em inglês quando a vaga é em inglês (`idioma` da vaga) ou a análise pede.
- O servidor devolve o checklist e os lembretes calculados junto de cada vaga, para a página e para a
  skill (`PY dash/banco.py kit <id>`).

## 4. Carta e respostas pela página

- **Decision**: `candidatura_ia.py` (raiz), no molde de `curriculo_ia.py`: perfil + vaga + respostas →
  `ia.responder` → JSON → conferência → arquivos em `curriculos/` (fora do Git):
  `AAAA-MM-DD-empresa-cargo-carta.{txt,docx,meta.json}` e `…-respostas.{txt,meta.json}`. A fila de
  geração (`dash/gerador.py`) passa a aceitar o tipo (currículo, carta, respostas), uma geração por vez
  como hoje.
- **Carta**: quatro respostas obrigatórias (por que esta vaga, problema que resolveria, primeiro
  movimento, tom: direto, caloroso, formal); idioma da vaga; 350 a 420 palavras; o pedido manda usar
  só conquistas literais do perfil e das respostas.
- **Conferência da carta** (`conferir.conferir_carta`, sem IA, reaproveitando `numeros`, `datas` e
  `requisitos_da_vaga`): número ou data fora do perfil e das respostas → bloquear; tamanho fora da
  faixa, empresa da vaga não citada, nenhum requisito do anúncio citado ou expressões vazias (lista
  PT/EN: "sou apaixonado", "proativo", "team player", "fast-paced", "think outside the box"…) →
  conferir. Empresas e cargos citados: os que não aparecem no perfil nem são a empresa da vaga →
  conferir (nomes próprios são difíceis de reconhecer sem IA; a lista do perfil é a referência).
- **Respostas**: a pessoa cola as perguntas (uma por linha ou numeradas); `candidatura_ia.sensivel(p)`
  reconhece, por uma lista PT/EN, autorização, visto/sponsor, cidadania, salário/pretensão,
  deficiência/PCD, relocação/mudança e as perguntas de diversidade (gênero, raça, veterano). Essas
  nunca vão à IA e ficam com campo para a pessoa; as outras vão à IA com o perfil e voltam conferidas
  (fato fora do perfil → conferir). A resposta da pessoa é gravada como ela escreveu.
- **Alternatives considered**: ler as perguntas do formulário no portal (automação de candidatura,
  contra a constituição VI); deixar a IA decidir o que é sensível (a regra precisa ser determinística).

## 5. Lembretes

- **Decision**: calculados (`dash/kit.py lembretes(v, hoje)`): Aplicação Enviada → `follow1` aos 7 dias
  e `follow2` aos 14 dias de `etapa_em`; Entrevista → `agradecimento` no dia seguinte a
  `entrevista_em` (campo novo, opcional, editável) ou a `etapa_em`. Estado da pessoa em
  `lembretes: {base: "<etapa>:<data>", follow1|follow2|agradecimento: feito|dispensado, parar: bool}`;
  se `base` não bate com a etapa e a data atuais, o estado antigo é ignorado (a vaga mudou de etapa).
- Card do quadro com etiqueta "Hora do follow-up" / "Agradecer a entrevista" e os botões "feito",
  "dispensar" e "parar lembretes"; contagem no topo do quadro.

## 6. Skills no chat

- gerar-curriculo ganha "Carta de apresentação" (as quatro perguntas, regras, `PY conferir.py --carta
  arquivo.txt --vaga-id ID`) e "Respostas de formulário" (`PY candidatura_ia.py sensiveis
  perguntas.txt` separa as sensíveis); buscar-vagas ganha "o que a candidatura pede" e "follow-ups"
  (`PY dash/banco.py kit <id>` e `PY dash/banco.py lembretes`). Edição em `.agents/skills/` e
  `python sincronizar_skills.py`.

## 7. Testes

- `tests/test_kit.py`: validação dos campos novos, checklist (com e sem análise, estado preservado),
  lembretes (7, 14, dia seguinte, mudança de etapa, parar).
- `tests/test_candidatura.py`: perguntas obrigatórias, sensíveis PT/EN (SC-002, com IA de teste que
  tenta responder), conferência da carta (fato inventado bloqueia, carta correta passa, genérica e
  fora do tamanho viram conferir; SC-003), arquivos gerados, IA falsa local.
