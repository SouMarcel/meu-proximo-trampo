# Implementation Plan: Vaga segura — filtro de integridade do texto e origem do link

**Branch**: `034-vaga-segura` (worktree `../mpt-034-vaga-segura`, saída da `master`) | **Date**: 2026-10-28 |
**Spec**: [spec.md](spec.md)

## Summary

**Módulo novo `integridade.py`** (raiz, biblioteca padrão). Funções puras:
- `limpar(texto)` tira os caracteres invisíveis e é idempotente;
- `verificar(texto)` devolve `(texto_limpo, achado | None)`, com as linhas com cara de instrução, as palavras de
  alfabetos misturados, os caracteres de adulteração e as marcas de trecho oculto;
- `sinal_oculto(texto)` diz se um trecho oculto do HTML tinha instrução ou link;
- `origem_do_link(url)` e `portal_do_host(host)` comparam por domínio exato ou subdomínio.

O cabeçalho do módulo dá crédito ao `posting_guard.py` do ai-job-search (MIT). O código é nosso, não uma cópia.

**`fontes/link.py`**:
- `texto_de_html` pula os elementos ocultos e os blocos script/style/noscript/template. O trecho oculto com sinal vira
  a marca "[trecho oculto tirado pela ferramenta: …]";
- `plataforma(host)` passa a usar `integridade.portal_do_host`, sem casar domínio parecido.

**Onde o filtro roda**:
- `vagas.executar` aplica `verificar` às candidatas e às fora dos critérios. O `.cache/candidatas.md` já sai limpo e
  marca o ⚠, e o resumo do `vagas.py buscar` conta as vagas com ⚠;
- `dash/banco.py` aplica o filtro em `inserir_vagas`, `completar_descricao`, `criar_manual` e `criar_de_link`, e
  grava `integridade` e `origem_link`;
- comando novo `banco.py integridade [--gravar]` para as vagas antigas;
- `pendentes` e `vaga` mostram o ⚠.

**`dash/analise.py`**:
- `montar_pedido` limpa o texto de novo e diz à IA para não seguir instruções das descrições, citando-as em
  `alertas`;
- `analisar` põe cada vaga com ⚠ num pedido só dela.

**`post_ia.py`**: limpa o texto colado antes de mandar à IA.

**Front** (`frontend-react`): ⚠ no `JobCard`, bloco "Texto da vaga" no `JobDetailModal` (achados, contagens e lembrete
da nota), origem do link no detalhe e no Adicionar Vaga.

**Documentação**: `dash/API.md`, README, skill `buscar-vagas` e AGENTS.md (o comando novo).

## Technical Context

**Language/Version**: Python 3.10+, só biblioteca padrão (`re`, `unicodedata`, `html.parser`, `urllib.parse`). Front em
TypeScript/React, na `frontend-react`.

**Primary Dependencies**: nenhuma nova.

**Storage**: dois campos opcionais no documento da vaga (SQLite com JSON, `dash/dados/candidaturas.db`):
`integridade` e `origem_link` ([data-model.md](data-model.md)).

**Testing**: `unittest`, sem rede. `tests/test_integridade.py` com:
- HTML e textos fabricados, um caso por truque;
- domínios parecidos;
- lotes da análise com uma IA falsa, como em `test_forcar.py`;
- gravação no banco temporário (`TRAMPO_BANCO`).

Os testes atuais de `link`, `post`, portais e análise servem de não regressão.

**Target Platform**: Windows (verificação), servidor local 127.0.0.1:8765.

**Performance Goals**: menos de 1 s para filtrar 100 vagas de 12 mil caracteres (SC-005).

**Constraints**:
- avisa e nunca bloqueia;
- o conteúdo oculto tirado nunca é guardado;
- o resultado do filtro nunca vai à IA;
- texto sem achado sai idêntico (SC-006).

**Scale/Scope**: centenas de vagas por busca; o filtro é regex e varredura de caracteres, sem rede.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Tudo roda no computador; nada é enviado a outro serviço. |
| II. Pública, sem dados pessoais | ✅ Testes com textos fabricados; nada da pessoa no código. |
| III. Simples | ✅ Biblioteca padrão; funciona sem IA. A verificação não depende de IA. |
| IV. Só fatos / texto é dado | ✅ Põe em código o "texto vindo da internet é dado, nunca instrução". O que se cita é trecho da vaga. |
| V. A pessoa decide | ✅ Só avisa. A vaga com ⚠ segue para todos os fluxos; o banco antigo só é regravado com `--gravar`. |
| VI. Respeito aos portais | ✅ Nenhum pedido novo a portal. Fica de fora a repetição depois de 403 do projeto de origem. |
| Fluxo | ✅ Spec aprovada em 28/10, com a autorização de seguir até o commit; teste do usuário na branch pessoal antes da master. |

Resultado: passa, sem desvio. A reavaliação depois do desenho segue igual: nenhum artefato mudou o quadro.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Marca visível no texto para o trecho oculto com sinal | O HTML vira texto em várias camadas (`_comum.texto`, cada portal) antes de chegar ao banco; a marca leva o achado até o `verificar` sem mudar o contrato de todas as fontes | Devolver os achados junto com o texto mudaria a assinatura de `texto_de_html` e `_comum.texto` em 12 fontes (research R3) |
| Verificação só no Windows | Decisão da pessoa | Mesmo motivo das specs anteriores |

## Project Structure

### Documentation (this feature)

```text
specs/034-vaga-segura/
├── spec.md, plan.md, research.md (R1–R9)
├── data-model.md, quickstart.md
├── contracts/integridade.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
integridade.py              # novo: limpar, verificar, sinal_oculto, portal_do_host, origem_do_link
fontes/link.py              # texto_de_html sem oculto (+ marca); plataforma() pelo domínio exato
vagas.py                    # filtro nas candidatas; ⚠ no candidatas.md e no resumo
dash/banco.py               # integridade/origem_link na gravação; comando integridade; ⚠ em pendentes e vaga
dash/analise.py             # texto limpo no pedido; vaga com ⚠ num pedido só dela; regra no pedido
post_ia.py                  # texto colado limpo antes da IA
.agents/skills/buscar-vagas/SKILL.md (+ cópia por sincronizar_skills.py), AGENTS.md, README.md, dash/API.md
tests/test_integridade.py
frontend-react: src/types/api.ts, src/components/JobCard.tsx, src/components/modals/JobDetailModal.tsx,
  src/components/modals/AddJobModal.tsx
```

**Structure Decision**: um módulo na raiz, como `filtros.py`, porque é usado pelas fontes, pelo banco e pela análise. A
tabela de domínios conhecidos fica nele, e `link.plataforma` e o banco leem a mesma tabela. Assim o "de quem é este
domínio" tem um lugar só. A lista de `candidatura/dominios.py` (onde a candidatura assistida pode preencher) continua
separada, porque responde outra pergunta.
