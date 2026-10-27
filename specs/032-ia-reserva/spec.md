# Feature Specification: IA com reserva e aviso de indisponibilidade

**Feature Branch**: `032-ia-reserva` (worktree `../meu-proximo-trampo-032`, saída da `master`)

**Created**: 2026-10-27

**Status**: Aprovada em 2026-10-27

**Input**: User description: "podemos então contornar esse problema da IA estando fora. 1. avisar quando a IA não
estiver disponível, com o motivo de estar fora. 2. podemos cadastrar mais de 1 provedor como sequência de fallback. no
meu caso quero o google e como fallback o openrouter modelos gratuitos".

## Contexto

Hoje a ferramenta usa uma IA só. Quando ela cai (ex.: o Gemini com erro 503, sobrecarga do Google), todas as funções
com IA param: a candidatura assistida, o currículo, a carta, a análise do relatório e a do perfil. A pessoa só fica
sabendo quando tenta usar alguma delas (research R2). Com uma sequência de reservas, a ferramenta passa para a próxima
IA e avisa por quê.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reserva quando a IA principal cai (Priority: P1)

A pessoa escolhe a IA principal e, em ordem, uma ou mais reservas. Se a principal falhar, a ferramenta tenta a
próxima, até uma responder.

**Independent Test**: provedores simulados; a principal responde 503, e a reserva responde.

**Acceptance Scenarios**:

1. **Given** o Gemini como principal e o OpenRouter gratuito como reserva, **When** o Gemini responde 503, **Then** a
   ferramenta usa o OpenRouter, e a tarefa (currículo, respostas, análise) segue normalmente.
2. **Given** a principal funcionando, **When** a pessoa usa uma função com IA, **Then** a reserva não é chamada.
3. **Given** um documento gerado pela reserva, **When** a pessoa vê de onde ele veio, **Then** aparece a IA que
   respondeu de fato (ex.: "OpenRouter · openrouter/free"), não a principal.

### User Story 2 - Aviso com o motivo (Priority: P1)

Quando uma IA da sequência falha, a pessoa vê qual falhou e por quê. Se todas falharem, vê o motivo de cada uma.

**Acceptance Scenarios**:

1. **Given** a principal fora, **When** a reserva responde, **Then** a função mostra: "Gemini (Google) fora: o
   provedor está com problema agora (erro 503). Respondeu o OpenRouter (gratuito)."
2. **Given** todas fora, **When** a pessoa usa uma função com IA, **Then** a mensagem lista cada uma com o seu motivo
   (ex.: "Gemini: erro 503 (sobrecarga); OpenRouter: limite de uso atingido").
3. **Given** uma falha recente da principal, **When** a pessoa abre a página, **Then** o botão IA mostra um alerta,
   e o painel IA mostra a situação de cada IA da sequência: a última falha (com hora e motivo) ou o último sucesso.

### User Story 3 - Configurar e testar a sequência no painel IA (Priority: P1)

No painel IA, a pessoa escolhe a principal e adiciona, remove e ordena as reservas, cada uma com provedor e modelo e
com a chave cadastrada como hoje. O botão "Testar" testa a sequência inteira e mostra o resultado de cada uma.

**Acceptance Scenarios**:

1. **Given** o painel IA, **When** a pessoa adiciona o OpenRouter com `openrouter/free` como reserva e salva, **Then**
   a sequência fica gravada, sem nenhuma chave no `config.json`.
2. **Given** uma reserva sem chave cadastrada, **When** a pessoa salva, **Then** o painel avisa que ela será pulada
   até a chave existir.
3. **Given** a sequência, **When** a pessoa clica em Testar, **Then** vê uma linha por IA: funcionando ou o motivo da
   falha.

### Edge Cases

- **Configuração antiga** (só `ia` com uma escolha): continua igual, sem reserva.
- **Reserva repetida** (mesmo provedor e modelo da principal ou de outra reserva): não é aceita.
- **Reserva sem chave**: é pulada, com o motivo "falta a chave", e a próxima é tentada.
- **Principal "Sem IA"**: não há sequência. A IA fica desligada e as reservas não são usadas.
- **Erro que não é do provedor** (ex.: a IA respondeu, mas o texto veio fora do formato que a função espera): não
  troca de provedor. A função trata como hoje.
- **Pergunta sensível** (salário, visto, deficiência): continua nunca indo a nenhuma IA, principal ou reserva.
- **Privacidade**: a reserva recebe os mesmos pedidos que a principal. O painel diz isso ao adicionar uma reserva,
  principalmente quando a principal é local (Claude Code ou um endereço deste computador) e a reserva é na nuvem.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A configuração de IA MUST aceitar, além da principal, uma lista ordenada de até 3 reservas, cada uma com
  provedor, modelo e endereço (para "outro compatível"). O formato antigo continua valendo.
- **FR-002**: Quando a IA em uso falhar por motivo do provedor, a ferramenta MUST tentar a próxima da sequência, sem
  nova tentativa na que falhou. Motivos do provedor: indisponível (5xx), limite (429), sem crédito, chave recusada,
  modelo inexistente, tempo esgotado, sem conexão ou falta de chave.
- **FR-003**: Toda resposta que veio de uma reserva MUST trazer o aviso de qual IA falhou, com o motivo, e de qual
  respondeu. Ele aparece onde a função já mostra avisos (painel da candidatura, currículo, carta, análise).
- **FR-004**: Quando todas falharem, a mensagem de erro MUST listar cada IA com o seu motivo.
- **FR-005**: A situação de cada IA da sequência (último sucesso, ou última falha com hora e motivo) MUST ficar
  guardada fora do Git (`.cache/ia-estado.json`) e aparecer no painel IA. O botão IA mostra um alerta quando a última
  tentativa com a principal falhou.
- **FR-006**: O documento gerado (currículo, carta, respostas, análise do perfil) MUST registrar a IA que respondeu
  de fato.
- **FR-007**: O painel IA MUST permitir adicionar, remover e ordenar as reservas. O "Testar" testa cada IA da sequência,
  e o painel avisa da reserva sem chave e de que a reserva recebe os mesmos pedidos.
- **FR-008**: As regras de hoje não mudam: nenhuma chave no `config.json` nem na página, mensagens sem chave, pergunta
  sensível nunca vai à IA.
- **FR-009**: Documentação: `dash/API.md` (rotas da IA), README (seção da IA) e `.env.exemplo` (sem mudança de
  variáveis).

### Key Entities

- **Sequência de IA**: a principal mais até 3 reservas, em ordem. Cada uma é `{provedor, modelo, url_base}`.
- **Situação da IA**: por provedor e modelo, o último sucesso ou a última falha (hora e motivo), em
  `.cache/ia-estado.json`.

## Success Criteria *(mandatory)*

- **SC-001**: Com a principal respondendo 503 e a reserva funcionando, a função com IA termina normalmente, com o aviso
  do motivo.
- **SC-002**: Com a principal funcionando, zero chamadas à reserva.
- **SC-003**: Com todas fora, a mensagem traz o motivo de cada uma.
- **SC-004**: A configuração do usuário fica: Gemini (`gemini-3.8-flash`) como principal e OpenRouter (`openrouter/free`)
  como reserva.

## Assumptions

- **Até 3 reservas**: o pedido foi "mais de 1 provedor". Com 3, cabem por exemplo dois gratuitos e um pago, sem lista
  longa de esperas.
- **Sem nova tentativa no mesmo provedor**: com a reserva configurada, passar para ela é mais rápido do que esperar a
  principal voltar. Sem reserva, a função falha na hora, com o motivo, como hoje.
- **A situação vem das chamadas reais**: o painel mostra o que aconteceu na última tentativa. A ferramenta não testa os
  provedores sozinha, para não gastar o limite dos planos gratuitos. O "Testar" é no clique.
- **Constituição**: sem emenda. A IA continua opcional (princípio III), e as regras de privacidade e de pergunta
  sensível valem para a principal e para as reservas.
- **Front**: na branch `frontend-react` (painel IA e botão IA).
- **Verificação**: só no Windows.
