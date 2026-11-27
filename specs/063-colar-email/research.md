# Research: Colar e-mail (spec 063)

## R1. Onde a leitura mora e como a proposta chega ao Aplicar

- **Decision**: módulo novo `dash/colar_email.py`, com um objeto `LEITURA_EMAIL` na memória do servidor que guarda a
  última leitura (as propostas, com o trecho e o tipo). O Aplicar manda só as chaves marcadas e as escolhas (vaga e tipo
  quando a pessoa escolheu); o conteúdo (trecho, tipo lido) vem do servidor, não da página.
- **Rationale**: é o mesmo desenho da `sincronia.Leitura` (spec 018): a página não consegue mandar um trecho que não
  estava no e-mail. Não guarda nada em disco (FR-010).
- **Alternatives**: mandar a proposta inteira da página no Aplicar (a página poderia forjar o trecho); juntar à
  `sincronia.LEITURA.resultado` (a leitura dos portais apaga o resultado a cada Atualizar agora e roda em segundo
  plano; o e-mail é síncrono).

## R2. Limpeza do texto colado

- **Decision**: tirar linhas de cabeçalho (De/From/Para/To/Cc/Cco/Bcc/Assunto/Subject/Data/Date/Enviado/Sent/Enviada
  em/Responder a/Reply-To, com ":" no começo da linha), endereços de e-mail (regex) e links (http/https), juntar espaços;
  depois `integridade.verificar` (caracteres invisíveis, instruções à IA). O achado vai na proposta como `alerta`.
- **Rationale**: o aviso pede só o corpo, mas a pessoa pode colar tudo; endereços e links não ajudam a reconhecer e não
  devem ir à IA.

## R3. Reconhecimento do tipo sem IA

- **Decision**: lista de padrões por tipo (PT, EN, ES), testada na ordem de prioridade contratado → proposta → negativa →
  cancelada → desistência → entrevista → recebida; o primeiro que casa decide. O trecho é a frase (entre pontos ou
  quebras de linha) em que o padrão casou, cortada em 240 caracteres.
- **Rationale**: uma negativa costuma agradecer a candidatura ("recebemos sua candidatura… infelizmente"), e um
  convite de entrevista costuma citar a candidatura recebida; a ordem evita que "recebida" ganhe. "Proposta" antes de
  "negativa" é arriscado ("não temos uma proposta"), então os padrões de proposta exigem frase de oferta ("temos o
  prazer de lhe oferecer", "proposta de trabalho/contratação", "job offer", "offer letter", "pleased to offer").
- **Alternatives**: pontuação por quantidade de padrões (mais difícil de explicar e testar).

## R4. Achar a candidatura

- **Decision**: candidatas = vagas com etapa (Aplicações), inclusive as arquivadas com etapa, sem as juntadas a outra.
  Empresa citada: o nome-base (`banco.empresa_base`) de cada vaga aparece no texto sem acento e sem espaços/pontuação,
  ou cada palavra do nome (sem sufixo societário, ≥ 3 letras) aparece como palavra. Cargo: proporção das palavras do
  cargo (≥ 3 letras) presentes no texto.
  1. Uma vaga só com a empresa citada → ela.
  2. Mais de uma com a empresa citada → a de maior proporção de cargo se for ≥ 0,6 e a segunda ficar pelo menos 0,2
     abaixo; senão, "escolher" entre elas.
  3. Nenhuma empresa citada → cargo com proporção 1,0 em uma vaga só → ela; senão "escolher" (lista de busca do quadro).
- **Rationale**: e-mails de recrutadores citam a empresa quase sempre; os de portais (Gupy, LinkedIn) citam cargo e
  empresa. Empresa genérica (`empresa_base` == "") nunca casa pela empresa.

## R5. Mudança proposta e "só anotar"

- **Decision**: tipo → etapa/resultado pela tabela da US1. `contas.avancou(etapa_atual, etapa_nova)`: verdadeiro →
  `mudar`; falso → `anotar` (etapa igual ou anterior, ou card encerrado). Vaga sem etapa (escolhida pela pessoa em
  Vagas Nacionais/Internacionais) → `quadro` (entra em Aplicações com `triagem=seguir`, como na sincronia). A mudança é
  recalculada no Aplicar com o card como estiver naquela hora.
- **Data da anotação**: a da confirmação, `dd/mm/aaaa`. Texto: `26/11/2026 — e-mail de negativa: "seguimos com outros
  candidatos"` (até 500 caracteres, limite do `banco.anotar`). `etapa_em` = hoje.

## R6. IA no não reconhecido

- **Decision**: depois das regras, se `ia.disponivel()` e houver e-mails sem tipo ou sem candidatura, um pedido só
  (`ia.responder`, `tempo=180`) com: as regras do que é cada tipo, os e-mails numerados (corpo limpo, cada um até
  6.000 caracteres) e a lista de candidaturas (id, empresa, cargo, etapa; até 300). Resposta: array JSON
  `[{email, tipo, vaga_id, trecho}]`, lido com `analise.lista_json`. Vale só se: `tipo` está na lista; `vaga_id` é
  vazio ou está na lista enviada; `trecho` aparece no e-mail (comparação sem acento e espaços). Senão o e-mail fica "não
  reconhecido". `IAErro` (inclusive limite de uso): fica "não reconhecido", com o aviso na resposta.
- **Rationale**: um pedido só respeita a economia da spec 062; validar o trecho impede que a IA invente o que vai às
  Anotações (constituição IV).

## R7. Escolha da vaga na página

- **Decision**: `GET /api/candidaturas/email/vagas?q=` devolve até 30 vagas `{id, titulo, empresa, etapa}`: sem `q`,
  as de Aplicações; com `q`, `banco.procurar(q)` sem arquivadas nem juntadas. Para "escolher" entre poucas (R4.2), a
  proposta já traz as `opcoes`.
- **Rationale**: o quadro pode ter milhares de vagas; a busca evita mandar tudo à página.

## R8. Front

- **Decision**: componente novo `ColarEmail.tsx`, mostrado no diálogo Atualizar candidaturas mesmo sem portal
  conectado; as propostas do e-mail aparecem num grupo "E-mail" com o mesmo cartão das dos portais, e o botão Aplicar
  conta e aplica as duas origens (duas chamadas). Delegado a um funcionário na `frontend-react` (worktree
  `../mpt-front-027b`).
