# Contrato: pergunta de idiomas (`GET /api/perfil`, `perguntas[]`)

Muda só o item `id: "idiomas"` da lista `perguntas` do estado do perfil (dash/API.md §3.6). A rota é a mesma.

```text
{id: "idiomas", tipo: "lista",
 texto: "Quais idiomas você fala e em que nível?",
 idiomas: ["Inglês", "Português (BR)", "Francês", "Alemão", "Espanhol"],   // "Outro" é da página
 niveis: [{valor: "A1"|…|"C2"|"Nativo", rotulo: "B2 (Intermediário superior)"|"Nativo", descricao}],
 linhas: [{idioma: "Inglês"|…|"Outro", outro: string, nivel: "A1"|…|"Nativo"|"", original: string}]}
```

- **`linhas`**: as respostas já gravadas em `respostas.idiomas`, convertidas por `ler_idiomas`.
  - Sem resposta, as linhas vêm dos idiomas do rascunho, tirados do currículo ou do LinkedIn (decisão 5 da spec).
  - Sem nenhum dos dois, vem `[]`, e a página mostra uma linha vazia.
- **Na montagem do perfil**, a linha do rascunho com um idioma que está na resposta sai do perfil (decisão 5).
- **Resposta** (sem mudança): `POST /api/perfil/progresso` com `{respostas: {idiomas: string[] | null}}`. Cada texto
  é `"{nome} — {rotulo}"`; `null` quer dizer pulada.
- **Página antiga**: ela ignora `idiomas`, `niveis` e `linhas` e mostra a caixa de texto "um por linha", que grava a
  mesma lista de textos.
- **Pergunta `ingles`**: deixa de vir em `perguntas`. A resposta `{respostas: {ingles: …}}` ainda é aceita, por
  compatibilidade.
