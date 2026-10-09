# Feature Specification: Currículo pela página

**Feature Branch**: `007-curriculo-pela-pagina` (pasta da spec; o trabalho acontece na `master` por
worktree, conforme a constituição)

**Created**: 2026-10-09

**Status**: Draft

**Input**: User description: "Fase 6 do roteiro: gerar o currículo pela página, só no clique. No
detalhe de uma vaga, um botão Gerar currículo abre as caixas de marcar das técnicas e as escolhas,
com a sugestão da Fase 5 marcada. Ao confirmar, a IA escolhida escreve o conteúdo em segundo plano,
a partir do perfil, da vaga, do guia de técnicas e do modelo, só com fatos do perfil; a ferramenta
valida, gera o .docx e o PDF na pasta de currículos e roda a conferência sem IA. O detalhe da vaga
lista os currículos gerados (arquivo, técnicas, formato, veredito, data), com links para abrir ou
baixar; com bloquear, a página mostra os pontos e não marca como pronto. Também um Currículo base
(sem vaga), pelo mesmo caminho. Sem IA, explica que precisa de uma IA (ou do chat); sem perfil,
orienta para Meu perfil. Uma geração por vez, com andamento e tentar de novo se a IA falhar. Escrita
só do próprio computador; a página só serve arquivos da pasta de currículos. Nada é gerado sem o
clique. Foco em Windows."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gerar o currículo para uma vaga pela página (Priority: P1)

No detalhe de uma vaga, a pessoa clica em **Gerar currículo**. Aparecem as técnicas como caixas de
marcar e as escolhas de páginas, formato do país e estilo, com a sugestão para aquela vaga marcada e
o motivo dela. Ela confirma; a página mostra o andamento (escrevendo com a IA, gerando os arquivos,
conferindo) e, em poucos minutos, o currículo aparece na lista da vaga, com o veredito da
conferência e os links para o PDF e o .docx.

**Why this priority**: hoje o currículo por vaga só sai pelo chat; quem usa só a página não consegue
adaptar o currículo à vaga que está decidindo.

**Independent Test**: com IA e perfil, abrir uma vaga, gerar o currículo com as técnicas sugeridas e
abrir o PDF pelo link da página.

**Acceptance Scenarios**:

1. **Given** uma vaga, IA e perfil, **When** a pessoa clica em Gerar currículo, **Then** as caixas
   e escolhas aparecem com a sugestão marcada e nada é gerado antes da confirmação.
2. **Given** a confirmação, **When** a geração termina, **Then** o currículo aparece na lista da
   vaga com técnicas, formato, data e veredito, e os links abrem o PDF e o .docx.
3. **Given** uma geração em andamento, **When** a pessoa pede outra, **Then** a página diz que há
   uma geração rodando e não começa a segunda.
4. **Given** a IA falhou, **When** a geração termina, **Then** a página mostra o motivo e oferece
   tentar de novo com as mesmas escolhas.

---

### User Story 2 - Conferência visível e "bloquear" respeitado (Priority: P1)

Cada currículo gerado passa pela conferência sem IA da Fase 5. A lista da vaga mostra o veredito
(ok, conferir, bloquear) e, ao abrir, os pontos: números ou fatos fora do perfil, lacunas da vaga
listadas como competência, problemas de ATS, requisitos tem/sustentado/lacuna e a cobertura das
palavras-chave. Com "bloquear", o currículo fica marcado como **não pronto**, com a explicação do que
resolver (confirmar o fato no perfil, ou gerar de novo).

**Why this priority**: a IA pode errar; a pessoa precisa ver isso antes de enviar o currículo.

**Independent Test**: com uma IA falsa que inventa um número, gerar e ver o currículo marcado como
não pronto, com o número apontado.

**Acceptance Scenarios**:

1. **Given** um currículo com veredito "bloquear", **When** a lista é mostrada, **Then** ele aparece
   como "não pronto" com os pontos que bloqueiam.
2. **Given** um currículo "ok" ou "conferir", **When** a pessoa abre os pontos, **Then** vê os
   requisitos, a cobertura e o que conferir.

---

### User Story 3 - Currículo base pela página (Priority: P2)

Fora de uma vaga (pelo botão Meu perfil ou pelo relatório), a pessoa gera o **currículo base**,
voltado para os cargos-alvo do perfil, pelo mesmo caminho: técnicas, confirmação, andamento,
conferência e links. A versão nova não apaga a anterior.

**Why this priority**: o currículo base é o que a maioria das pessoas envia; mas o currículo por vaga
é o que a página ainda não faz de jeito nenhum.

**Independent Test**: gerar o currículo base pela página e ver os arquivos e o veredito; gerar de novo
e ver as duas versões.

**Acceptance Scenarios**:

1. **Given** perfil e IA, **When** a pessoa gera o currículo base, **Then** ele usa os cargos-alvo do
   perfil e aparece numa lista própria com os mesmos dados da lista da vaga.
2. **Given** um currículo base anterior, **When** um novo é gerado, **Then** os dois continuam
   disponíveis, com datas diferentes.

---

### User Story 4 - Sem IA, sem perfil e acesso pela rede (Priority: P2)

Sem IA configurada, o botão explica que a escrita do currículo precisa de uma IA (com o atalho para o
painel IA) ou pode ser feita pelo chat. Sem perfil, orienta para Meu perfil. De outro aparelho da rede,
a pessoa vê a lista e abre os arquivos, mas não gera.

**Why this priority**: evita cliques que não levam a nada e mantém a escrita só no computador.

**Independent Test**: sem IA, clicar em Gerar currículo e ver a explicação; sem perfil, ver a
orientação; pela rede, ver a lista sem poder gerar.

**Acceptance Scenarios**:

1. **Given** sem IA, **When** a pessoa clica, **Then** a página explica e oferece o painel IA, sem
   gerar nada.
2. **Given** sem perfil, **When** a pessoa clica, **Then** a página oferece Meu perfil.
3. **Given** acesso por outro aparelho, **When** a pessoa abre a vaga, **Then** vê os currículos e
   abre os arquivos, mas o botão de gerar fica indisponível com a explicação.

---

### Edge Cases

- A IA devolve um conteúdo que não segue o modelo do currículo: a geração falha com o motivo e a
  opção de tentar de novo; nada pela metade fica na lista.
- O PDF não pode ser gerado (sem Word nem LibreOffice): o .docx aparece na lista, o PDF fica como
  indisponível e as páginas como não medidas.
- O currículo passou do limite de páginas: aparece na lista com o aviso e as sugestões de corte.
- Arquivo do currículo apagado da pasta à mão: a lista mostra o item como indisponível.
- Vaga removida do dashboard: os arquivos continuam na pasta; só o vínculo some.
- Duas versões para a mesma vaga no mesmo dia: os nomes não colidem (a segunda ganha um sufixo).
- Pedido para abrir um arquivo fora da pasta de currículos (caminho manipulado): recusado.
- A página é fechada durante a geração: a geração continua; ao reabrir, aparece o andamento ou o
  resultado.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O detalhe da vaga MUST ter o botão **Gerar currículo**, que abre as técnicas e
  escolhas do catálogo da Fase 5, com a sugestão para a vaga marcada e o motivo.
- **FR-002**: Nada MUST ser gerado nem enviado à IA antes da confirmação da pessoa.
- **FR-003**: Ao confirmar, a IA escolhida MUST escrever o conteúdo do currículo em segundo plano a
  partir do perfil, da vaga, das técnicas escolhidas, do guia de técnicas e do modelo do currículo,
  com a instrução de usar só fatos do perfil.
- **FR-004**: A ferramenta MUST validar o conteúdo devolvido pela IA, gerar o .docx e o PDF na pasta
  de currículos com nome de data, empresa e cargo (sem sobrescrever outro arquivo) e rodar a
  conferência sem IA.
- **FR-005**: A vaga MUST guardar a lista dos currículos gerados para ela (arquivos, técnicas,
  formato, estilo, páginas, veredito, pontos da conferência e data), mostrada no detalhe.
- **FR-006**: Com veredito "bloquear", o currículo MUST aparecer como não pronto, com os pontos e o
  que fazer.
- **FR-007**: A página MUST permitir abrir ou baixar o PDF e o .docx de cada currículo, servindo
  apenas arquivos da pasta de currículos.
- **FR-008**: O currículo base MUST poder ser gerado pela página pelo mesmo caminho, a partir dos
  cargos-alvo do perfil, sem apagar versões anteriores, com uma lista própria.
- **FR-009**: MUST haver no máximo uma geração por vez, com andamento visível e retomado ao reabrir a
  página.
- **FR-010**: Se a IA falhar ou devolver conteúdo inválido, a página MUST mostrar o motivo e oferecer
  tentar de novo com as mesmas escolhas, sem deixar item pela metade na lista.
- **FR-011**: Sem IA, o botão MUST explicar que precisa de uma IA (com atalho para o painel IA) ou do
  chat; sem perfil, MUST orientar para Meu perfil.
- **FR-012**: Gerar MUST ser aceito só no computador onde a ferramenta roda; de outro aparelho, só ver
  e abrir os arquivos.
- **FR-013**: O que é enviado à IA MUST ser só o perfil, a vaga, as técnicas e os guias, nunca
  arquivos de outras pastas.
- **FR-014**: Textos MUST estar em português do Brasil.

### Key Entities *(include if feature involves data)*

- **Currículo gerado**: arquivos (.json, .docx, .pdf), alvo (vaga ou base), técnicas e escolhas,
  páginas, veredito e pontos da conferência, data, IA que escreveu.
- **Geração em andamento**: alvo, escolhas, etapa (escrevendo, gerando, conferindo), resultado ou
  motivo da falha.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com IA e perfil, a pessoa gera o currículo de uma vaga e abre o PDF sem sair da página,
  em até 3 minutos do clique.
- **SC-002**: 100% dos currículos gerados pela página passam pela conferência e mostram o veredito.
- **SC-003**: 0 currículos com "bloquear" aparecem como prontos.
- **SC-004**: 0 pedidos à IA sem a confirmação da pessoa; 0 arquivos servidos de fora da pasta de
  currículos.
- **SC-005**: Uma falha da IA nunca deixa item pela metade na lista; a pessoa tenta de novo com um
  clique.

## Assumptions

- A escrita usa a IA do painel IA (spec 002) e o mesmo pedido para todas as IAs; com a assinatura do
  Claude Code, sem custo por uso; com chave, o custo de uma chamada por currículo (avisado antes).
- O currículo base gerado pela página vai para um arquivo novo com data (não substitui o
  `base.json` do chat); a pessoa escolhe qual usar.
- A lista de currículos de uma vaga fica junto da vaga; a do currículo base, num registro próprio
  local.
- O motor, o catálogo e a conferência são os da Fase 5; esta fase não muda as regras de escrita.
- Verificação só no Windows.
