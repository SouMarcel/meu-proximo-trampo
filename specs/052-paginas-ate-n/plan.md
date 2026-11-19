# Implementation Plan: Páginas em duas opções (Completo ou Até N) e apagar currículo gerado

**Branch**: `052-paginas-ate-n` | **Date**: 2026-11-19 | **Spec**: [spec.md](spec.md)

## Summary

Backend: a escolha `paginas` passa a aceitar 0 (Completo, só no base) e de 1 a 5, com um orçamento de conteúdo para
cada N; uma rota nova apaga um currículo gerado (arquivos, ligação com a vaga e com a análise de reprovação). Front
(branch `frontend-react`): a área Páginas vira "Completo" ou "Até [N] páginas", com a caixa do limite obrigatório
junto, e cada currículo da lista ganha a lixeira.

## Technical Context

Python com biblioteca padrão (`curriculo.py`, `curriculo_ia.py`, `dash/banco.py`, `dash/servidor.py`,
`reprovacao.py`); testes com `unittest`. Front React 19 + TypeScript + Tailwind, ícones `lucide-react`, sem testes
automatizados: valida com `npm run typecheck` e `npm run build`.

## Constitution Check

- Fatos confirmados: o orçamento só limita conteúdo; o encurtar continua "só tirar ou condensar".
- Indicar, não sair fazendo: apagar só no clique e com confirmação; a rota é só local, como as outras do currículo.
- Dados pessoais fora do Git: nada de `curriculos/` nem `dash/dados/` em commit; testes com dados fictícios.
- Front: código na `frontend-react`, montado pela Action; `dash/front/` nunca à mão na `master`.

## Decisões

**D1. Opções de páginas** (`curriculo.ESCOLHAS["paginas"]`): `{0: "Completo (sem limite, tudo do perfil)", 1: "Até
1 página", 2: "Até 2 páginas", 3: "Até 3 páginas", 4: "Até 4 páginas", 5: "Até 5 páginas"}`, padrão 2. O catálogo
continua tirando o 0 com vaga. `validar` e `validar_tecnicas` já recusam valores fora das opções. A técnica
`paginas_obrigatorio` continua em `TECNICAS` (contrato da API intacto); quem a muda de lugar é o front.

**D2. Orçamento de 3 a 5** (`curriculo_ia.ORCAMENTO`), cerca de 400 palavras por página, ponto de partida:

| N | Resumo | Recentes completas | Itens | Anteriores | Cursos | Palavras |
|---|---|---|---|---|---|---|
| 3 | até 4 linhas | 4 | até 5 | até 2 itens | até 4 | ~1200 |
| 4 | até 5 linhas | 5 | até 6 | até 2 itens | até 5 | ~1600 |
| 5 | até 5 linhas | 6 | até 6 | até 3 itens | até 6 | ~2000 |

1 e 2 ficam como estão. `montar_pedido_encurtar` já usa `ORCAMENTO.get(limite)`.

**D3. Apagar** (`curriculo_ia.apagar(nome) -> dict`): valida o nome com `NOME_VALIDO`; lê `<nome>.meta.json`
(sem ele, ou com `tipo` carta/respostas, recusa com `GeracaoErro`; inexistente, `FileNotFoundError`). Apaga em duas
fases para não ficar pela metade: renomeia cada arquivo existente (`.json`, `.docx`, `.pdf`, `.meta.json`) para
`<arquivo>.apagando`; se um renomear falhar (`OSError`, arquivo aberto no Word), desfaz os já renomeados e levanta
`GeracaoErro("um arquivo do currículo está aberto em outro programa; feche e tente de novo")`. Depois apaga os
renomeados. Devolve o `alvo` do meta.

**D4. Ligações**: `banco.desligar_curriculo(vid, nome)` tira o nome de `doc["curriculos"]` (vaga inexistente:
ignora). `reprovacao.esquecer_curriculo(vid, nome)` zera `curriculo_gerado` quando é aquele nome (sem análise:
ignora).

**D5. Rota**: `DELETE /api/curriculo/<nome>` [local], em `_curriculo` do `dash/servidor.py`. 200 `{apagado: nome}`;
400 nome inválido ou não é currículo gerado; 404 não existe; 409 arquivo aberto. Com alvo de vaga, chama D4.

**D6. Front, área Páginas** (`Curriculos.tsx`, `GerarCurriculo`): a escolha `paginas` deixa o laço genérico e ganha
um bloco próprio: rádio "Completo" (só se a opção "0" vier no catálogo) e rádio "Até [select 1–5] página(s)"; o
select guarda o último N, para voltar a ele ao sair do Completo. Logo abaixo, a caixa `paginas_obrigatorio`, com a
explicação do catálogo, desabilitada com Completo; a lista de Técnicas não a mostra. No gerar, com Completo,
`paginas_obrigatorio` vai `false`. Sem opção "0" (vaga), só o "Até [N]".

**D7. Front, lixeira** (`ItemCurriculo`): botão com o ícone `Trash2` depois de PDF e .docx, `title="Apagar este
currículo"`, `window.confirm("Apagar este currículo de vez? O PDF, o .docx e os dados dele somem da pasta.")`;
chama `curriculoApi.apagar(nome)` (`DELETE`), e a lista recarrega. Erro aparece numa linha do item.

## Estrutura

Backend na worktree `../mpt-052` (branch `052-paginas-ate-n`); front na worktree `../mpt-front-027b` (branch
`frontend-react`). Teste do usuário: backend mesclado na branch pessoal e o `dist/` do front copiado para `dash/front/`
dela, sem commit.
