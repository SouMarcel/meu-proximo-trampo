# Implementation Plan: Limite de páginas que vale e currículo completo

**Branch**: `051-paginas-e-completo` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: a spec aprovada em 17/11. O usuário pediu para seguir direto até o merge na `marcel`.

## Summary

O pedido à IA ganha um limite concreto de conteúdo para 1 e 2 páginas, o currículo que passa do limite ganha um aviso
na conferência e há uma técnica nova, "Limite de páginas obrigatório". Com ela, a ferramenta faz uma segunda chamada à
IA para encurtar o currículo, em até 2 tentativas, e mede de novo. A escolha "Páginas" ganha o valor 0 (Completo), que
só aparece no catálogo sem vaga. Tudo fica no backend (`curriculo.py`, `curriculo_ia.py`, `dash/gerador.py`). O front
não muda, porque desenha o catálogo e o estado da geração de forma genérica.

## Technical Context

**Language/Version**: Python 3 (biblioteca padrão + python-docx, que o projeto já usa)

**Primary Dependencies**: as de sempre; nenhuma nova

**Storage**: `curriculos/*.json`, `.docx`, `.pdf` e `.meta.json`, todos fora do Git

**Testing**: `python -m unittest discover -s tests`, com a IA e o PDF substituídos (padrão de
`tests/test_curriculo_ia.py`)

**Target Platform**: o servidor local do dashboard (Windows primeiro)

**Constraints**:
- a geração já leva até 10 min de IA; o encurtamento acrescenta no máximo 2 chamadas;
- medir as páginas depende do LibreOffice ou do Word; sem um deles, não há medida nem encurtamento.

## Constitution Check

- **I e II (local; sem dados pessoais na `master`)**: os testes usam o perfil fictício de `tests/test_conferir.py`.
  Os números do limite são genéricos.
- **III (IA não obrigatória)**: o caminho do chat (`curriculo.py`) continua sem IA. O encurtamento só existe na
  geração pela página, que já usa IA.
- **IV (só fatos confirmados)**: o pedido para encurtar só permite tirar ou condensar. A ferramenta descarta a versão
  que cresce, e a conferência roda na versão final. O currículo completo usa só o perfil e os relatos.
- **V (a pessoa decide)**: o encurtamento só acontece com a caixa marcada pela pessoa. O aviso indica o que fazer, sem
  agir sozinho.
- **Fluxo de desenvolvimento**: Spec Kit; worktree saída da `master`; delegação (constituição 5.4.0,
  `docs/delegacao.md`), com GO/NO GO meu em cada entrega; merge na `marcel` para o teste do usuário; a `master` só com
  o OK dele.

Resultado: sem violações.

## Decisões

- **D1, limite de conteúdo** (constante `ORCAMENTO` em `curriculo_ia.py`, um texto por limite):

  | Limite | Resumo | Experiências | Cursos | Palavras | Outros |
  |---|---|---|---|---|---|
  | 2 páginas | até 4 linhas, cerca de 450 caracteres | as 3 mais recentes com até 5 itens; as anteriores com no máximo 1 item ou só a linha de empresa, cargo e período | até 3 | cerca de 800 | — |
  | 1 página | até 3 linhas | as 2 mais recentes com até 4 itens; as anteriores só com a linha | até 2 | cerca de 450 | sem projetos |

  O estilo "executivo" ganha "a fonte é maior: conte com menos espaço". O ajuste fino fica para a T006.
- **D2, Completo = `paginas: 0`**: o front converte `paginas` com `Number()`, então o valor precisa ser numérico. No
  catálogo, a chave vira "0". `catalogo(vaga)` tira a opção quando há vaga. `validar_tecnicas(dados, vaga)` recusa 0
  com vaga.
- **D3, encurtar dentro de `curriculo_ia.gerar`**:
  - depois de medir, com `paginas_obrigatorio` e `0 < limite < paginas`, a ferramenta monta o pedido para encurtar
    (JSON atual, páginas medidas, limite e as regras);
  - a resposta passa por `ler_resposta`, e a ferramenta monta e mede de novo, nos mesmos arquivos desta geração;
  - a resposta que crescer (mais caracteres de JSON ou mais experiências) é descartada;
  - erro de IA ou `GeracaoErro` encerra as tentativas e fica a melhor versão;
  - o resultado vai para `meta.encurtado = {de, para, tentativas}`.
- **D4, aviso**: ponto `{"nivel": "conferir", "trecho": "N páginas", "mensagem": …}` acrescentado a
  `conferencia["ats"]` antes de o meta ser gravado. O veredito é recalculado: "ok" passa a "conferir". O meta guarda
  `veredito` e `pronto` coerentes.
- **D5, etapa**: `dash/gerador.ETAPAS["encurtando"]`. O progresso já é repassado pelo `avisar`.
- **D6, nome**: `nome_arquivo(vaga, data, pasta, completo=False)`. Sem vaga e com `completo`, o nome fica
  `AAAA-MM-DD-base-completo`.

## Project Structure

```text
curriculo.py                 TECNICAS, ESCOLHAS, catalogo, descrever_tecnicas, main (T001)
curriculo_ia.py              ORCAMENTO, montar_pedido, validar_tecnicas, nome_arquivo (T002); encurtar (T003)
dash/gerador.py              validar_tecnicas com a vaga (T002); ETAPAS (T003)
tests/test_curriculo.py      T001
tests/test_curriculo_ia.py   T002, T003
.agents/skills/gerar-curriculo/{tecnicas.md,SKILL.md}, dash/API.md   T005
specs/051-paginas-e-completo/delegacao/T00X.md                        briefs
```
