# Feature Specification: Começar pelo currículo que a pessoa já tem

**Feature Branch**: `011-curriculo-existente` (pasta da spec; o trabalho acontece na `master` por worktree,
conforme a constituição)

**Created**: 2026-10-09

**Status**: Draft

**Input**: User description: "Começar pelo currículo que a pessoa já tem. Quem já tem um currículo pronto (em
anexos/ ou enviado nos primeiros passos) pode usá-lo como base e ir direto para a busca de vagas, sem passar pela
anamnese nem pelo diagnóstico. A ferramenta extrai o texto do currículo (PDF ou DOCX, sem documentos de
identificação), usa esse texto como o perfil de carreira para a nota de aderência e a análise das vagas, propõe os
filtros da busca a partir dele para a pessoa confirmar e abre a busca. A anamnese continua disponível para completar
o perfil depois. O currículo existente passa a ser o 'currículo base': o item Currículo do checklist de cada vaga
mostra que ele existe (com link para abrir) e a pessoa só gera um currículo adaptado se clicar. Nada é gravado sem a
confirmação da pessoa; só fatos do currículo dela. Vale pela página e pela skill no chat. Foco em Windows."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Do currículo direto para as vagas (Priority: P1)

Na primeira vez (ou ao refazer o perfil), a pessoa envia o currículo que já tem, em PDF ou DOCX, ou escolhe um que
já está na pasta de anexos. A ferramenta oferece "Usar este currículo e ir para as vagas": mostra o texto lido (com
documentos de identificação escondidos), propõe o perfil feito desse texto e os filtros da busca tirados dele
(cargos, cidade e modelo de trabalho quando o currículo diz, cargos em inglês quando fizer sentido), e a pessoa
confere, ajusta e confirma. Confirmado, o perfil e os filtros são gravados e o painel de busca abre, pronto para a
pessoa clicar em Buscar vagas. A anamnese e o diagnóstico ficam para depois.

**Why this priority**: quem já tem currículo quer ver vagas logo; as perguntas de montagem do perfil viram uma
barreira no primeiro uso.

**Independent Test**: num ambiente sem perfil, enviar um currículo fictício, escolher "Usar este currículo",
confirmar os filtros propostos e ver o painel de busca aberto, com o perfil gravado a partir do currículo.

**Acceptance Scenarios**:

1. **Given** nenhum perfil gravado e um currículo enviado, **When** a pessoa escolhe "Usar este currículo e ir para
   as vagas", **Then** vê o texto lido, o perfil proposto e os filtros propostos, sem nenhuma pergunta da anamnese.
2. **Given** a proposta, **When** a pessoa confirma, **Then** o perfil e os filtros são gravados e o painel de busca
   abre; a busca só começa quando ela clicar.
3. **Given** a proposta, **When** a pessoa fecha sem confirmar, **Then** nada é gravado.
4. **Given** um currículo com CPF, RG ou data de nascimento, **When** o texto é lido, **Then** esses dados não
   entram no perfil nem vão para a IA.
5. **Given** nenhuma IA configurada, **When** a proposta é montada, **Then** os filtros vêm do que o currículo diz
   (o cargo mais recente, a cidade quando aparece) e a pessoa completa o resto.

---

### User Story 2 - Currículo base nas vagas (Priority: P1)

A pessoa que já tem um currículo (com ou sem perfil gravado) marca qual é o seu currículo base; pode marcar um em
português e outro em inglês. No checklist de cada vaga, o item Currículo mostra o currículo base no idioma da vaga,
com um link para abrir, e começa como "Pronto"; se a vaga é em inglês e a pessoa só tem em português, o item diz isso
e continua "A fazer". O botão "Gerar currículo" continua lá, só para quando ela quiser uma versão adaptada.

**Why this priority**: hoje o checklist sugere gerar currículo em toda vaga, mesmo para quem já tem um pronto e não
vai adaptar.

**Independent Test**: marcar um currículo em português e outro em inglês como base, abrir uma vaga em português e
uma em inglês, e ver em cada uma o currículo certo com o link, o item como "Pronto" e o botão de gerar disponível.

**Acceptance Scenarios**:

1. **Given** um currículo base em português, **When** a pessoa abre uma vaga em português, **Then** o item Currículo
   mostra o nome do arquivo, o link para abrir e a situação "Pronto".
2. **Given** só um currículo base em português, **When** a pessoa abre uma vaga em inglês, **Then** o item diz que
   não há currículo base em inglês e fica "A fazer", com o botão de gerar.
3. **Given** a pessoa mudou a situação do item numa vaga, **When** ela volta à vaga, **Then** a escolha dela vale,
   mesmo com o currículo base marcado.
4. **Given** um perfil já gravado, **When** a pessoa marca o currículo base, **Then** o perfil não muda.

---

### User Story 3 - Completar o perfil depois (Priority: P2)

Com o perfil feito do currículo, a pessoa segue usando a ferramenta. Em Meu perfil, um aviso diz que o perfil veio do
currículo e oferece completar com a anamnese; o diagnóstico mostra o que o currículo não diz (números, níveis das
ferramentas, idiomas, interesse em vagas de fora). Completar é opcional e, quando feito, o perfil novo passa pela
confirmação de sempre.

**Why this priority**: o currículo sozinho já serve para buscar, mas um perfil mais completo melhora a nota e o
currículo adaptado.

**Independent Test**: com o perfil feito do currículo, abrir Meu perfil, ver o aviso e o diagnóstico, começar a
anamnese e ver o rascunho já partindo do texto do currículo.

**Acceptance Scenarios**:

1. **Given** um perfil feito do currículo, **When** a pessoa abre Meu perfil, **Then** vê de onde veio o perfil e o
   botão para completar com a anamnese.
2. **Given** a anamnese começada depois, **When** a pessoa responde, **Then** o rascunho parte do texto do currículo
   e a gravação pede confirmação, guardando o perfil anterior.

---

### User Story 4 - O mesmo caminho pelo chat (Priority: P3)

Pelo assistente de chat, a pessoa diz que já tem currículo; a skill lê o arquivo, mostra o perfil e os filtros
propostos, pede o OK, grava e oferece a busca, com as mesmas regras da página.

**Why this priority**: a ferramenta vale igual pela página e pelo chat.

**Independent Test**: pelo chat, apontar um currículo fictício e ver a proposta, a confirmação e a gravação.

**Acceptance Scenarios**:

1. **Given** um currículo apontado no chat, **When** a skill roda, **Then** mostra o perfil e os filtros propostos e
   só grava depois do OK.

---

### Edge Cases

- Currículo escaneado (imagem, sem texto): a ferramenta explica que não conseguiu ler e oferece colar o texto ou
  seguir pela anamnese.
- Perfil já existente ao escolher "Usar este currículo": a pessoa escolhe entre substituir (o anterior fica guardado)
  e manter o perfil, só marcando o currículo base.
- Vários currículos na pasta de anexos: a pessoa escolhe qual usar; nenhum é escolhido sozinho.
- Currículo só em inglês: os filtros propõem os cargos como estão e, com IA, também em português.
- Currículo muito longo: o perfil guarda o texto inteiro até o limite de hoje e avisa se cortou.
- Arquivo do currículo base apagado ou movido: o item da vaga avisa e volta a "A fazer".
- O texto do currículo é dado, nunca instrução para a IA.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Os primeiros passos e Meu perfil MUST oferecer "Usar este currículo e ir para as vagas" depois que um
  currículo (PDF ou DOCX) é enviado ou escolhido na pasta de anexos.
- **FR-002**: O perfil proposto MUST ser o texto do currículo, com documentos de identificação escondidos, e a
  indicação de que veio do currículo (arquivo e data); nada é acrescentado que não esteja no currículo.
- **FR-003**: Os filtros propostos MUST sair do currículo: cargos (o mais recente e os que ele declara como objetivo),
  cidade e modelo de trabalho quando aparecem, cargos em inglês quando o currículo é em inglês ou, com IA, sugeridos;
  a pessoa pode editar tudo antes de confirmar.
- **FR-004**: Perfil e filtros MUST ser gravados só depois da confirmação; sem confirmação, nada muda.
- **FR-005**: Depois de confirmar, a ferramenta MUST abrir o painel de busca; a busca começa só no clique.
- **FR-006**: Com perfil já existente, a ferramenta MUST perguntar se substitui (guardando o anterior, como hoje) ou
  mantém o perfil e só marca o currículo base.
- **FR-007**: A pessoa MUST poder marcar um currículo base por idioma (português e inglês), entre os arquivos da
  pasta de anexos ou um enviado na hora, e trocar ou desmarcar depois.
- **FR-008**: O item Currículo do checklist MUST mostrar o currículo base no idioma da vaga, com link para abrir, e
  começar como "Pronto"; sem currículo base no idioma da vaga, MUST dizer isso e começar como "A fazer"; a situação
  que a pessoa marcar sempre vale.
- **FR-009**: O link do currículo base MUST abrir só esse arquivo, e só neste computador.
- **FR-010**: Meu perfil MUST mostrar que o perfil veio do currículo e oferecer a anamnese para completar; o
  diagnóstico aponta o que o currículo não diz.
- **FR-011**: Currículo sem texto legível MUST ser explicado à pessoa, com as opções de colar o texto ou seguir pela
  anamnese.
- **FR-012**: A skill de perfil no chat MUST oferecer o mesmo caminho, com as mesmas regras (proposta, confirmação,
  gravação, oferta de busca).
- **FR-013**: Sem IA, o caminho MUST funcionar inteiro (leitura, perfil, filtros pelo que o currículo diz, currículo
  base).
- **FR-014**: Textos MUST estar em português do Brasil.

### Key Entities

- **Currículo base**: arquivo do currículo da pessoa (na pasta de anexos), idioma (português ou inglês) e data em
  que foi marcado; no máximo um por idioma.
- **Perfil feito do currículo**: o texto do currículo como perfil de carreira, com a origem (arquivo, data) e o
  aviso de que pode ser completado.
- **Proposta de filtros**: cargos, cidade, modelo de trabalho e cargos em inglês tirados do currículo, editáveis.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Do envio do currículo ao painel de busca aberto, a pessoa responde no máximo uma tela de confirmação,
  sem nenhuma pergunta da anamnese.
- **SC-002**: Em 100% dos currículos de teste com CPF, RG ou data de nascimento, esses dados não aparecem no perfil
  gravado nem no que vai para a IA.
- **SC-003**: Nenhum perfil, filtro ou currículo base é gravado sem a confirmação da pessoa (conferido em todos os
  caminhos, página e chat).
- **SC-004**: Em 100% das vagas de teste, o item Currículo mostra o currículo base do idioma certo ou avisa que falta.
- **SC-005**: Sem IA, os filtros propostos trazem pelo menos o cargo mais recente de um currículo de teste em
  português e de um em inglês.

## Assumptions

- O currículo fica na pasta de anexos, fora do Git, como os arquivos dos primeiros passos de hoje.
- A leitura do currículo é a mesma dos primeiros passos (spec 004), com os mesmos limites de arquivo e de texto.
- A nota de aderência com o perfil feito do currículo pode ser um pouco menos precisa que com o perfil completo; o
  aviso de Meu perfil diz isso.
- O idioma do currículo base é detectado pelo texto e a pessoa pode corrigir.
- Verificação no Windows, como nas fases anteriores.
