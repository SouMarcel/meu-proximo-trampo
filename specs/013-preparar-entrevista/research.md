# Research: Preparação para entrevista

## 1. Onde fica

- **Decision**: pasta `entrevistas/` na raiz (nova no `.gitignore`, citada no AGENTS.md entre os dados pessoais):
  `entrevistas/historias.json` (banco de histórias, para todas as vagas) e `entrevistas/vaga-<id>.json` (a preparação
  de cada vaga: texto colado sobre a empresa, resumo do dossiê, perguntas geradas pela IA, simulação, anotações de
  depois da entrevista). Gravação atômica, como nas análises do perfil.
- **Rationale**: histórias e respostas têm dados da pessoa; ficam fora do Git como `curriculos/`.

## 2. Dossiê

- **Sem IA**: cargo, empresa, local, plataforma, salário, link; da análise: resumo, encaixe, lacunas, alertas, e os
  campos do kit (autorização, contratação, inglês, fuso, riscos); anotações; o texto colado sobre a empresa (até 20.000
  caracteres).
- **Com IA** (no clique): `[{ponto, origem: vaga|texto|deducao, trecho}]`. Ponto com origem vaga ou texto precisa de um
  trecho que aparece naquele texto (comparação sem acento, por termos, ≥ 60%); se não, vira "dedução". Nada de
  pesquisa: a IA só recebe a vaga e o texto colado.

## 3. Perguntas prováveis

- **Lista padrão** (sem IA), cada uma com o porquê:
  - comportamentais: desafio difícil, conflito, erro e aprendizado, prioridades, influência sem autoridade, por que
    esta empresa/vaga;
  - técnicas: uma por requisito do anúncio (`conferir.requisitos_da_vaga`, até 6) — "Conte uma situação em que você
    usou/fez X" — com o porquê "a vaga pede: X";
  - lacunas da análise (até 3) — "A vaga pede X e o seu perfil não mostra: como você responderia?";
  - perguntas que caíram em entrevistas anteriores desta vaga (anotações de depois).
- **Com IA** (no clique): até 10 perguntas `[{texto, tipo, porque}]` a partir da vaga, da análise e do perfil, somadas
  à lista (sem repetir).
- Idioma: as da lista padrão em português e em inglês (escolha na simulação).

## 4. Histórias STAR

- **Com IA**: até 5 rascunhos `[{titulo, situacao, tarefa, acao, resultado, reflexao, conquista, perguntas}]` a partir
  das conquistas do perfil, escolhendo as que respondem às perguntas prováveis. Cada rascunho passa por
  `conferir._fatos_do_texto` (número e data fora do perfil → conferir) e pela checagem de nomes próprios da carta
  (empresa fora do perfil → conferir).
- **Sem IA**: formulário vazio no mesmo formato.
- Salvar só na confirmação; editar e remover depois. As histórias aparecem em qualquer vaga, com as perguntas que
  respondem.

## 5. Simulação

- Uma pergunta por vez, das perguntas prováveis, no idioma escolhido (pt/en). Resposta por escrito.
- **Com IA**: `{funcionou, faltou, mais_forte}` com regras: honesto, sem elogio vazio, sem nota; a resposta mais forte
  só com fatos do perfil e das histórias salvas — conferida por `_fatos_do_texto` contra perfil + histórias (fora →
  aviso "conferir").
- Pular, repetir, encerrar; as respostas ficam salvas na preparação da vaga. Resumo no fim, sem IA: os pontos "faltou"
  juntos.
- **Sem IA**: só as perguntas, uma por vez.

## 6. Salário

- Faixa da vaga (`salario`, `moeda`), pretensão do perfil (linha "Pretensão"/"pretensão salarial"/"expected salary"),
  e pontos fixos de conversa (deixar a empresa falar primeiro, responder com a faixa da vaga ou a sua pretensão, olhar
  benefícios, contratação e moeda, pedir tempo para pensar). Nenhum valor que não venha da vaga ou do perfil.

## 7. Depois da entrevista

- `{data, etapa, perguntas: [..], bem, mal, proximos}` acrescentado à preparação; as perguntas entram nas próximas
  perguntas prováveis com o porquê "caiu na entrevista de <data>".

## 8. Página, chat e testes

- Botão "Preparar entrevista" no card da coluna Entrevista e no detalhe da vaga; diálogo com as seções Dossiê,
  Perguntas, Histórias, Simular, Salário e Depois.
- Skill nova `preparar-entrevista` (`.agents/skills/`, sincronizada) e `entrevista.py` com linha de comando.
- `tests/test_entrevista.py`: dossiê e perguntas sem IA (SC-001), origem do resumo, histórias com fato fora do perfil
  (SC-002), salvar só com confirmação (SC-003), salário (SC-004), retorno da simulação (SC-005), anotações alimentando
  as perguntas.
