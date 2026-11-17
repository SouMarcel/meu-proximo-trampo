# Delegação: o assistente planeja e valida, um "funcionário" implementa

Este projeto é desenvolvido com assistentes de código. Para economizar os tokens do assistente
principal (o Claude Code, que conversa com a pessoa), ele fica com o **planejamento** (spec, plano,
tarefas) e a **validação** (GO/NO GO), e manda a implementação de cada tarefa para um **funcionário**:
outro assistente de código, rodando sem interação na worktree da feature, que não commita nada.

## Funcionários

| Funcionário | Comando | Como roda | Quando entra |
|---|---|---|---|
| Antigravity CLI | `agy` | `agy --print="<prompt>" --dangerously-skip-permissions --print-timeout 1800s --model <m>` | principal, nas tarefas minor e major |
| Copilot CLI | `copilot` | `copilot -p "<prompt>" --allow-all-tools --allow-all-paths --no-ask-user -s` | reserva: quando o agy falha, está fora ou sem cota |
| Ollama (local) | API em `127.0.0.1:11434` | `POST /api/generate` com o brief; a resposta vai para `<brief>.resposta.md` | só texto puro (rascunho, tradução, resumo) e só se a API já estiver no ar: a ferramenta **nunca inicia o serviço** |

O Gemini CLI fica de fora (exige chave paga). A fila é `agy → copilot`; depois dela, o assistente
principal assume a tarefa e avisa a pessoa de que está gastando os próprios tokens.

Modelos: sempre o mais básico que resolve. O agy começa em `gemini-3.8-flash-medium` (minor) ou
`gemini-4-argon-medium` (major) e só sobe de nível na segunda tentativa, se o NO GO foi por
capacidade do modelo e não por brief mal cortado. O Copilot usa o modelo padrão dele.

## Tamanho da tarefa decide quem faz

Mesma ideia da versão semântica da constituição, aplicada à tarefa:

| Tamanho | O que é | Quem faz |
|---|---|---|
| patch | 1 arquivo, sem lógica nova: texto, docstring, mensagem, rename local, README | o assistente principal (escrever o brief custa mais que fazer) |
| patch de texto puro | rascunho de doc, tradução, mensagem de commit, resumo | Ollama, se já estiver ligado; senão o assistente principal |
| minor | função, endpoint, teste ou ajuste contido em até ~3 arquivos, com critério de aceite testável | funcionário (agy; reserva Copilot) |
| major | spec inteira, fase do tasks.md com vários módulos, portal novo, front React | o assistente quebra em tarefas minor e delega **uma por brief** |

Nunca vai a um funcionário: decisão de produto, emenda da constituição, spec/plan/tasks, commit,
merge, push, e nada que toque `config.json`, `perfil.md`, `.env` ou dados pessoais.

## O ciclo

1. Spec → plan → tasks como sempre, com a aprovação da pessoa. No `tasks.md`, a tarefa delegável
   leva a marca `[D]` e o tamanho (`minor`/`major`).
2. Para cada tarefa `[D]`, o assistente escreve o brief em `specs/NNN-nome/delegacao/T0XX.md` a
   partir de `.specify/templates/delegacao-template.md`: contexto, o que fazer, **arquivos
   permitidos**, regras, critério de aceite, como testar.
3. `PY delegar.py rodar specs/NNN-nome/delegacao/T0XX.md --pasta <worktree>` manda o funcionário
   ler o brief e executar. O transcript inteiro vai para `.cache/delegacao/NNN-nome/` (fora do Git);
   a tela mostra só o resumo: duração, `git diff --stat`, arquivos fora do escopo, se o HEAD mudou,
   resultado da suíte de testes e as últimas linhas do funcionário.
4. **GO/NO GO**, feito pelo assistente principal: testes verdes; só arquivos do escopo; HEAD
   intacto; sem dados pessoais no diff; critério de aceite cumprido (conferido no diff, não no
   relato do funcionário); entrega com interface é rodada de verdade.
5. NO GO: `PY delegar.py resultado <brief> --no-go --nota "<motivo concreto>"` acrescenta
   `## Refazer (tentativa 2)` ao brief, e a rodada repete com `--tentativa 2`. O diff da primeira
   tentativa fica (o funcionário corrige em cima); `--limpar` desfaz antes as mudanças nos arquivos
   permitidos.
6. Segundo NO GO: para. O assistente volta ao plano com a pessoa (tarefa mal cortada, premissa
   errada ou funcionário inadequado) e só troca de funcionário nessa revisão.
7. GO: `PY delegar.py resultado <brief> --go --nota "..."`, `[X]` no `tasks.md` com
   `→ agy, GO na tentativa N`, e o fluxo de sempre: commit na branch da feature, teste da pessoa,
   `master` só com o OK dela.

Códigos de saída de `rodar`: 0 pronto para validar; 2 diff fora do escopo ou HEAD mudou; 3 testes
falharam; 4 funcionário não terminou, não encontrado ou Ollama fora; 5 cota esgotada (o resumo diz
quem é o próximo da fila).

## Quem está fazendo o quê

`PY delegar.py status` mostra uma linha por spec, sem detalhe:

```
051-nome-da-spec · 6/14 tarefas (43%) · agora: T007 → agy (gemini-3.8-flash-medium) há 4 min, tentativa 1
  T006 → agy saiu com 0 (tentativa 1)
  T006 → validação: GO (tentativa 1)
```

A porcentagem vem das marcas `[X]`/`[ ]` do `tasks.md`. O estado fica em
`.cache/delegacao/status.json`, fora do Git. O assistente manda essa mesma linha no chat toda vez
que delega, valida ou troca de funcionário.

## Como ler `specs/NNN/delegacao/`

Um arquivo por tarefa delegada. O brief é a ordem de serviço; o fim do arquivo guarda o histórico:
`## Refazer (tentativa N)` com o motivo de cada NO GO e `## Resultado` com o GO. Quem fez, em
quantas tentativas e por que passou fica registrado junto da spec, sem dados pessoais.
