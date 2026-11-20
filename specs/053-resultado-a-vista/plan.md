# Implementation Plan: Currículo e carta com resultado à vista

**Branch**: `053-resultado-a-vista` | **Date**: 2026-11-20 | **Spec**: [spec.md](spec.md)

## Summary

Só backend e instruções, sem mudança na página: o guia de técnicas (que entra em todo pedido de currículo e é lido
pela skill no chat) passa a pedir resultado primeiro; a conferência sem IA ganha os avisos de contato incompleto, de
itens só de tarefa e de confissão de lacuna; a classificação de requisitos para de contar "em preparação" como "tem" e
de dar "sustentado" a requisito de vários idiomas com um faltando; o pedido da carta e das respostas proíbe confessar
diferencial.

## Technical Context

Python com biblioteca padrão (`conferir.py`, `candidatura_ia.py`), instruções em Markdown/JSON
(`.agents/skills/gerar-curriculo/tecnicas.md` e `modelo.json`, copiadas para `.claude/skills/` por
`sincronizar_skills.py`); testes com `unittest` em `tests/test_conferir.py`. A página junta `conferencia.fatos` e
`conferencia.ats` numa lista só e mostra a mensagem de cada ponto; a carta e as respostas já mostram os pontos da
conferência delas. Por isso, nenhum ponto novo precisa de mudança no front.

## Constitution Check

- **IV. Só fatos confirmados**: nada acrescenta fato. O guia só muda a ordem; a conferência só avisa; a
  classificação fica mais conservadora (menos "tem"). A regra da carta tira texto (a confissão), não põe.
- **V. Indicar, não sair fazendo**: todos os avisos são "conferir"; a pessoa decide.
- **II. Ferramenta pública, sem dados pessoais**: testes e exemplos fictícios; nada do perfil real.
- **III. Simples e sem dependência nova**: listas curtas de expressões, `re` da biblioteca padrão.
- **Delegação** (constituição 5.4.0, `docs/delegacao.md`): tarefas minor vão a funcionário, uma por brief; as de
  texto (patch) ficam com o assistente principal.

## Decisões

**D1. Resultado primeiro no guia** (`tecnicas.md`, seção "Bullet bem feito (base de todas)", que vai em todo pedido):
"Em cada experiência, os itens com resultado confirmado (número, percentual, valor ou efeito escrito no perfil) vêm
primeiro, depois os de tarefa; só a ordem muda, o texto do fato não." Em "Foco": "Destaques: prefira os itens com
número ligados ao alvo." Em "XYZ": a mesma ordem. O exemplo do `modelo.json` deixa de usar "Responsável pelo
backlog…" (expressão vaga que o próprio guia proíbe) e ganha a ordem nova (item com resultado primeiro), sempre
fictício. Depois, `python sincronizar_skills.py`.

**D2. Contato** (`conferir.conferir_ats`): no lugar do aviso de contato vazio, que continua igual, três verificações
sobre os itens de `cv["contato"]`:
- sem e-mail (nenhum item casa com `[^@\s]+@[^@\s]+\.[A-Za-z]{2,}`) → `{"nivel": "conferir", "tipo": "contato",
  "trecho": "", "mensagem": "o contato não tem e-mail: recrutadores respondem por e-mail"}`;
- formato `br` sem telefone (nenhum item com 8 ou mais dígitos) → aviso equivalente, "o contato não tem telefone";
- contato vazio → só o aviso de hoje (sem repetir os dois de cima).

**D3. Itens só de tarefa** (`conferir.itens_de_tarefa(cv) -> list[dict]`, chamado por `conferir()`, pontos em
`fatos`): percorre só os itens das experiências (`experiencia[].cargos[].itens` ou `experiencia[].itens`, como
`trechos`). Um item é "só de tarefa" quando começa por expressão vaga (VAGAS: "responsável por", "responsável pelo",
"responsável pela", "atua", "atuou", "atuando", "auxiliou", "auxílio", "apoiou", "participou", "participação",
"suporte a", "responsible for", "assisted", "helped", "participated", "worked on", "involved in") **ou** não tem
número (`\d`) nem marca de efeito (EFEITO: "o que permitiu", "permitindo", "reduzindo", "reduziu", "aumentando",
"aumentou", "resultando", "resultou", "garantindo", "garantiu", "o que levou", "evitando", "viabilizando",
"which enabled", "resulting in", "reducing", "increasing", "leading to", "enabling"). Comparação com `norm()`.
Saída, só se houver algum: um ponto resumo `{"tipo": "tarefa", "nivel": "conferir", "valor": "N de M", "trecho": "",
"mensagem": "N de M itens das experiências descrevem tarefa, sem resultado: se houver um resultado, conte-o (vira
relato)"}` e até 8 pontos `{"tipo": "tarefa_item", "nivel": "conferir", "valor": <item[:160]>, "trecho": <item[:160]>,
"mensagem": "item só de tarefa"}`. Item com número sempre conta como resultado (spec, Edge Cases), salvo se começar
por expressão vaga.

**D4. "Em preparação" na classificação** (`conferir.avaliar_requisitos`): ANDAMENTO = ("em preparacao", "em
andamento", "cursando", "estudando", "nao concluid", "in progress", "preparing", "ongoing"), comparado em `norm()`.
Para cada termo achado, ver se **todas** as linhas do perfil que o contêm têm marca de andamento. Se algum termo
achado só aparece em linha com marca, e a situação seria "tem", ela vira "sustentado", e a evidência passa a ser
`"em preparação: " + <essa linha[:140]>`. Assim, "Certificação X ou equivalente" contra um perfil que cita a área de
X em vários cargos e "Certificação X (em preparação)" sai "sustentado" (o "x" só existe na linha em preparação).

**D5. Vários idiomas** (`conferir.avaliar_requisitos`): IDIOMAS = {"Inglês": ("ingles", "english"), "Espanhol":
("espanhol", "spanish"), "Francês": ("frances", "french"), "Alemão": ("alemao", "german"), "Italiano": ("italiano",
"italian"), "Mandarim": ("mandarim", "chines", "mandarin", "chinese"), "Japonês": ("japones", "japanese")}. Se o
requisito cita 2 ou mais idiomas e o perfil não cita algum deles, a situação é "lacuna" e a evidência,
`"falta: Espanhol"` (os que faltam, separados por vírgula). Com todos, segue a regra de hoje. Português fica de fora
(língua de quem usa a ferramenta).

**D6. Confissão de lacuna** (`conferir.py`): CONFISSOES = ("nao tenho", "nao possuo", "ainda nao tenho", "ainda nao
possuo", "nao sou certificad", "nao conto com", "i don't have", "i do not have", "i lack", "i am not certified",
"i'm not certified"), comparadas em `norm()`. `conferir_carta` acrescenta `{"tipo": "confissao", "valor": <frase>,
"nivel": "conferir", "mensagem": "a carta confessa uma falta: tire, a menos que a vaga exija esse ponto"}` para cada
frase (dividida em `.`, `!`, `?`) que contém uma confissão. `conferir_respostas` acrescenta à lista `conferir` de cada
resposta da IA (não às da pessoa) a mensagem "confessa uma falta: tire, a menos que a pergunta peça".

**D7. Regra no pedido** (`candidatura_ia.py`): uma constante `REGRA_FALTAS` com o texto "Diferencial da vaga
(desejável, diferencial, nice to have) que o perfil não tem: não cite, nem para dizer que falta. O que o perfil marca
como em preparação ou em andamento só pode ser dito assim. Nunca escreva confissão de falta (\"não tenho\", \"não
possuo\")." entra nas regras de `montar_pedido_carta`, `montar_pedido_verificar` e `montar_pedido_respostas`.

**D8. Documentação**: `dash/API.md` (os tipos novos de ponto em `conferencia.fatos`/`ats`, na carta e nas
respostas); `specs/lista-de-desejos.md` ganha a "caça de números" (FR-014).

## Tarefas e quem faz

| Tarefa | Decisão | Tamanho | Quem |
|---|---|---|---|
| Guia e exemplo do modelo, sincronizar | D1 | patch | assistente principal |
| Avisos de contato | D2 | minor | funcionário |
| Itens só de tarefa | D3 | minor | funcionário |
| "Em preparação" e vários idiomas | D4, D5 | minor | funcionário |
| Confissão na carta e nas respostas | D6 | minor | funcionário |
| Regra no pedido | D7 | patch | assistente principal |
| API.md e lista de desejos | D8 | patch | assistente principal |

As quatro tarefas de funcionário mexem em `conferir.py` e `tests/test_conferir.py`: rodam uma depois da outra, cada
uma com o seu brief em `delegacao/`, em rodízio agy/Copilot.

## Estrutura

Worktree `../mpt-053` (branch `053-resultado-a-vista`, saída da `master`). Teste do usuário: merge na branch pessoal,
dashboard reiniciado, currículo e carta gerados pela página. A branch `requisitos-texto-achatado` (leitura de
requisitos de texto achatado) é independente; as duas tocam `conferir.py` em funções diferentes.

## Verificação

- `python -m unittest discover -s tests` verde; testes novos por decisão (D2 a D6), com textos fictícios. D3 com um
  conjunto de 20 itens marcados à mão (SC-003: pelo menos 90% de acerto).
- `python sincronizar_skills.py --conferir` sem diferença.
- `PY conferir.py <currículo.json>` mostra os avisos novos no texto e no `--json`.
- Na página (branch pessoal): gerar o currículo base e conferir a ordem (itens com resultado no topo de cada
  experiência) e os avisos; gerar a carta de uma vaga com diferencial que o perfil não tem e ver que ela não o cita.
