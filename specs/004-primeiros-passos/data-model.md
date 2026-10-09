# Data Model: Primeiros passos e anamnese

Tudo local e fora do Git.

## Material (`.cache/primeiros-passos.json` → `materiais[]`; arquivo em `anexos/primeiros-passos/`)

| Campo | Regra |
|---|---|
| `id` | texto curto único (`m1`, `m2`…) |
| `tipo` | `curriculo_pdf`, `curriculo_docx`, `linkedin_pdf`, `linkedin_zip`, `texto` |
| `nome` | nome original saneado (até 120) |
| `arquivo` | caminho relativo em `anexos/primeiros-passos/` (vazio para `texto`) |
| `texto` | texto extraído **já mascarado** (até 60 000 caracteres) |
| `campos` | só `linkedin_zip`: `{perfil, cargos[], formacao[], competencias[], certificacoes[], idiomas[]}` |
| `avisos` | lista (ex.: "PDF digitalizado", "faltou Skills.csv") |
| `contato` | `{emails[], telefones[], linkedin}` reconhecidos (para confirmar) |

Limites: 10 MB por arquivo; formatos aceitos `.pdf`, `.docx`, `.zip`, texto colado.

## Rascunho do perfil (`rascunho`)

```text
objetivo, resumo, formacao, certificacoes, habilidades, idiomas: [{texto, fonte}]
experiencias: [{cargo, empresa, inicio, fim, itens: [{texto, fonte}], fonte}]
conflitos: [{campo, opcoes: [{valor, fonte}], escolha: null | índice}]
contato: {email, telefone, linkedin}   # só depois de confirmados
```

`fonte` = nome do material ou "resposta". Itens sem fonte não entram.

## Respostas da anamnese (`respostas`)

`{id_da_pergunta: valor}`; valor é texto, lista ou booleano conforme o tipo; `null` = pulada
(aparece no diagnóstico). Perguntas por cargo usam id `conquista:<n>` e `medida:<n>`.

## Estado (`etapa`)

`ia → materiais → rascunho → conflitos → anamnese → diagnostico → revisao → filtros → concluido`

## Perfil gravado (`perfil.md`, caminho em `config.json → perfil`)

Markdown no formato do `perfil.exemplo.md` (+ seções opcionais Contato, Trabalho no exterior, Regras
de verbo e atribuição). Versão anterior em `anexos/perfis-anteriores/perfil-AAAA-MM-DD-HHMM.md`.

## Proposta de filtros

Mesmo formato de `filtros.validar` (termos, localidade, modelos, internacional, senioridades…), mais
`mudancas: [{campo, atual, proposto}]` para a página mostrar.
