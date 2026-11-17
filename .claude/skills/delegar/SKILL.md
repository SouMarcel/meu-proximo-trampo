---
name: delegar
description: Delega a implementação de uma tarefa do tasks.md a um "funcionário" (Antigravity CLI, Copilot CLI ou Ollama) por delegar.py, valida a entrega com GO/NO GO e reporta quem está fazendo o quê. Use ao implementar tarefas de uma spec, quando a pessoa pedir para delegar, "manda para o agy/copilot", "quem está fazendo o quê", ou ao decidir se uma tarefa vale um funcionário. Ferramenta de desenvolvimento, só do Claude Code.
---

# Delegar uma tarefa a um funcionário

Você planeja e valida; o funcionário implementa. Processo completo em `docs/delegacao.md`; leia-o
uma vez por sessão. Objetivo: gastar os seus tokens em brief, diff e decisão, nunca em transcript.

## 1. Classificar o tamanho e decidir

- **patch** (1 arquivo, sem lógica nova): faça você. Texto puro (rascunho, tradução, resumo):
  Ollama se `PY delegar.py funcionarios` disser que está ligado; senão você.
- **minor** (até ~3 arquivos, critério testável): delegue (agy e Copilot em rodízio; o script escolhe).
- **major**: quebre em tarefas minor no `tasks.md` e delegue uma por brief. Nunca uma major inteira.
- Nunca delegue: spec/plan/tasks, emenda da constituição, commit, merge, push, qualquer coisa que
  toque `config.json`, `perfil.md`, `.env` ou dados pessoais.

No `tasks.md`, a tarefa delegável leva `[D]` e o tamanho: `- [ ] T007 [D minor] [US1] ...`.

## 2. Escrever o brief

Copie `.specify/templates/delegacao-template.md` para `specs/NNN-nome/delegacao/T0XX.md` e
preencha. O funcionário não conhece o projeto: aponte o que ler (seção da spec, arquivo, teste
que mostra o padrão), diga o que fazer na ordem, liste **todos** os arquivos permitidos (teste
incluído) e escreva um critério de aceite que você consiga conferir no diff. Curto e sem
ambiguidade; se você não sabe explicar em um brief, a tarefa está mal cortada.

## 3. Rodar

```
PY delegar.py rodar specs/NNN-nome/delegacao/T0XX.md --pasta <worktree-da-feature>
```

- Sem `--funcionario`, o script escolhe no rodízio quem está há mais tempo parado (agy ou Copilot),
  para não gastar a cota de um só; o modelo vem do tamanho (agy: `gemini-3.8-flash-medium` para
  minor, `gemini-4-argon-medium` para major; Copilot: o padrão). `--funcionario` e `--modelo` forçam.
- Tempo padrão 1800 s. Rode em background (o Bash foreground para em 10 min) e espere a
  notificação; não fique lendo o log.
- Antes de rodar, mande no chat a linha de status: `NNN-nome · X/Y tarefas (Z%) · agora: T0XX →
  agy (modelo), tentativa N`.

Código de saída:

| Código | Significa | Faça |
|---|---|---|
| 0 | entregou; testes verdes; escopo ok | valide (passo 4) |
| 2 | arquivo fora do escopo ou HEAD mudou | se HEAD mudou, `git reset --soft HEAD~1` na worktree e trate como NO GO; arquivo fora do escopo: veja se o brief esqueceu dele (corrija o brief) ou o funcionário extrapolou (NO GO) |
| 3 | testes falharam | NO GO com o teste que falhou na nota |
| 4 | não terminou, não achou o CLI ou Ollama fora | rode o mesmo brief no outro (`--funcionario <outro>`); Ollama fora: faça você |
| 5 | cota esgotada | **avise a pessoa** e rode o mesmo brief no outro; os dois sem cota: faça você e avise que está gastando tokens do Claude |

## 4. Validar (GO/NO GO)

Leia só o que precisa: `git diff --stat` e depois `git diff -- <arquivos permitidos>`. Nunca o
log inteiro (`.cache/delegacao/...`); as últimas 30 linhas já vêm no resumo.

GO exige tudo isto:
- suíte verde (o resumo mostra; na dúvida, rode `python -m unittest discover -s tests` na worktree);
- só arquivos do escopo, HEAD intacto;
- nada de dados pessoais, nomes de empresa ou números do usuário no diff;
- critério de aceite do brief cumprido, conferido no diff (não confie no relato do funcionário);
- entrega com interface ou comando: rode de verdade (constituição, "Fluxo de desenvolvimento").

Registre:

```
PY delegar.py resultado <brief> --go --nota "o que conferiu"
PY delegar.py resultado <brief> --no-go --nota "motivo concreto, com arquivo e linha" --tentativa 1
```

## 5. Refazer uma vez, depois voltar ao plano

- NO GO na tentativa 1: o `resultado --no-go` já escreveu `## Refazer (tentativa 2)` no brief.
  Complete a seção com o que corrigir e rode de novo com `--tentativa 2`. O diff anterior fica; use
  `--limpar` só quando ele atrapalha. Suba o modelo (`--modelo claude-sonnet-5-5-medium`) só se o
  NO GO foi por capacidade, não por brief ruim.
- NO GO na tentativa 2: pare. Volte ao plano com a pessoa: tarefa mal cortada, premissa errada ou
  funcionário inadequado. Trocar de funcionário é decisão dessa revisão.
- GO: marque `[X]` no `tasks.md` com `→ agy, GO na tentativa N`; mande a linha de status; siga o
  fluxo de entrega de sempre (commit na branch da feature; master só com o OK da pessoa).

## Quem está fazendo o quê

`PY delegar.py status` dá a visão geral (spec, % das tarefas, quem está em qual tarefa há quanto
tempo). Mande essa linha no chat a cada delegação, validação ou troca de funcionário. Sem detalhe:
a pessoa quer saber o quê, quem e quanto já foi.
