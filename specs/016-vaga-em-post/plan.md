# Implementation Plan: Vaga publicada em post

**Branch**: `016-vaga-em-post` (worktree saída da `master`) | **Date**: 2026-10-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/016-vaga-em-post/spec.md`

## Summary

São cinco peças, todas encaixadas no Adicionar Vaga de hoje:

1. **Leitura do post.** O módulo novo `fontes/post.py` reconhece links de post (activity, posts, share, ugcPost) e
   pede uma vez a versão pública de incorporação do LinkedIn, sem cookies e sem seguir redirecionamento. Dela tira o
   texto, o autor (empresa ou pessoa) e o link canônico. Bloqueios usam os motivos de `fontes/linkedin` sem gravar
   espera.
2. **Extração com IA.** O módulo novo `post_ia.py` pede à IA configurada um JSON fixo (cargo, empresa, local, link,
   e-mail, assunto, se parece vaga, quantas). O texto vai como dado. O e-mail e o link só valem se estiverem
   escritos no texto.
3. **Servidor.**
   - `POST /api/vagas/link` passa a responder ao link de post com os dados para o formulário, sem gravar.
   - A rota nova `POST /api/vagas/extrair` (só deste computador) roda a extração.
   - `POST /api/vagas` e `PATCH` aceitam os campos novos.
4. **Página.**
   - Com IA, a página mostra "Em análise pela IA, aguarde…" e abre o formulário já preenchido. Sem IA, ou com erro
     da IA, o formulário abre direto com o que a leitura trouxe.
   - Entra a opção "Colar texto de post ou mensagem".
   - Vagas de post ganham a etiqueta "Post".
   - O cartão expandido ganha "E-mail de candidatura", "Assunto" e "Enviar por e-mail" (`mailto:`).
   - O kit mostra a candidatura por e-mail.
5. **Documentação**: README, AGENTS.md e a skill buscar-vagas.

Decisões em [research.md](research.md); dados em [data-model.md](data-model.md); interfaces em
[contracts/](contracts/); roteiro em [quickstart.md](quickstart.md).

## Technical Context

**Language/Version**: Python 3.10+ (biblioteca padrão); JavaScript ES5 no `dash/dashboard.html`.

**Primary Dependencies**: nenhuma nova.

**Storage**: SQLite com documentos JSON. Campos novos e opcionais na vaga (`formato`, `email_candidatura`,
`assunto_candidatura`), sem migração. Id `lip-…` para vaga de link de post.

**Testing**:
- `unittest`, com abridor falso para o LinkedIn (como em `tests/test_linkedin.py`) e `ia.responder` falso;
- HTML de post fictício em `tests/dados/linkedin/`;
- a página e um post real pelo roteiro.

**Target Platform**: Windows 10/11.

**Project Type**: aplicação local (servidor + página).

**Performance Goals**:
- sem IA, formulário aberto em até 5 s depois de Buscar dados;
- com IA, formulário preenchido em até 1 minuto, com limite de 120 s antes de cair no caminho de reserva.

**Constraints**:
- um pedido ao LinkedIn por link, sem login, cookies ou redirecionamento, e sem nova tentativa;
- nada gravado sem o clique em Adicionar;
- funciona sem IA;
- links de vaga de hoje sem mudança.

**Scale/Scope**:
- novos: `fontes/post.py`, `post_ia.py`, `tests/test_post.py`, `tests/dados/linkedin/post*.html`;
- alterados: `dash/servidor.py`, `dash/banco.py`, `dash/dashboard.html`, `fontes/link.py` (só para não tratar post
  como vaga), README, AGENTS.md e a skill buscar-vagas (com `sincronizar_skills.py`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Só o texto do post vai ao provedor de IA escolhido, sem o perfil, e a tela diz qual provedor lê. A extração é só deste computador. Nada é guardado além da vaga que a pessoa salvar. |
| II. Pública, sem dados pessoais | ✅ O post real fica descrito sem nome nem e-mail. Os dados de teste são fictícios. |
| III. Simples, sem IA obrigatória | ✅ Biblioteca padrão. Sem IA, o formulário abre com descrição, link e empresa. |
| IV. Só fatos confirmados | ✅ A IA só copia do texto. E-mail e link precisam estar escritos no texto. Tudo passa pelo formulário que a pessoa confere. O texto é dado, nunca instrução. |
| V. A pessoa decide | ✅ Nada é gravado sem o clique em Adicionar. O `mailto:` só abre o programa de e-mail, e nada é enviado. |
| VI. Respeito aos portais | ✅ Página pública, um pedido por clique da pessoa, sem login, cookies ou redirecionamento, parando no primeiro bloqueio. Não grava a espera da busca, por decisão da pessoa (clarificação de 2026-10-16), o mesmo tratamento do link de vaga na 015. |
| Restrições técnicas | ✅ Campos novos sem migração; id `lip-` estável e prefixado. A rota nova segue a validação de host e origem. ⚠️ Verificação só no Windows. |
| Fluxo de desenvolvimento | ✅ Spec → plano → tarefas, com aprovação; testes de funções puras; verificação rodando a página. |

Resultado: **passa**, sem emenda. Re-checado depois do desenho: sem mudança.

## Project Structure

### Documentation (this feature)

```text
specs/016-vaga-em-post/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api.md             # /api/vagas/link (post), /api/vagas/extrair, /api/vagas e PATCH com campos novos
│   └── extracao-ia.md     # pedido e resposta da extração com IA
├── checklists/
│   └── requirements.md
└── tasks.md               # (/speckit-tasks)
```

### Source Code (repository root)

```text
fontes/post.py          # id_do_post(url), ler(url) → {id, url, texto, autor, autor_tipo}; PostErro(motivo)
                        # pedido único ao embed, sem cookies e sem redirecionamento; motivos de linkedin._motivo
fontes/link.py          # plataforma(): sem mudança; ler(): link de post não é tratado como vaga (o servidor
                        # chama post antes)
post_ia.py              # extrair(texto, autor, autor_tipo) → campos limpos; ExtracaoErro; pedido com o texto como dado
dash/banco.py           # criar_manual aceita formato, post_id (id lip-, repetido devolve a existente),
                        # email/assunto, publicado_por → anotacao; _validar_usuario aceita email/assunto
dash/servidor.py        # /api/vagas/link: post → {post, parcial, ia} ou 422 com sugestão; /api/vagas/extrair (só local)
dash/dashboard.html     # com IA: "Em análise pela IA, aguarde…" e formulário preenchido; sem IA ou erro: formulário
                        # direto com o parcial; "Colar texto de post ou mensagem";
                        # campos E-mail/Assunto no formulário e no cartão; "Enviar por e-mail"; etiqueta Post; kit
README.md, AGENTS.md, .agents/skills/buscar-vagas/SKILL.md (+ python sincronizar_skills.py)
tests/test_post.py, tests/dados/linkedin/post.html, tests/dados/linkedin/post-pessoa.html
```

**Structure Decision**:
- **Leitura do post (`fontes/post.py`):** fica separada de `fontes/link.py`, porque o post não é vaga, não tem dados
  estruturados e segue regras próprias (sem redirecionamento, motivos do LinkedIn).
- **Extração com IA (`post_ia.py`):** fica na raiz, como os outros módulos que chamam a IA (`candidatura_ia.py`,
  `curriculo_ia.py`), e não dentro de `fontes/`, que só fala com portais.
- **Gravação:** reutiliza o caminho do Adicionar Vaga à mão (`criar_manual`), porque a vaga só é gravada depois que a
  pessoa confere o formulário.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Verificação só no Windows | Decisão do usuário | Mesmo motivo das specs anteriores |
| Formatos share/ugcPost verificados com um pedido real só na verificação | Só o formato activity foi testado na pesquisa | Testar todos os formatos agora pediria mais pedidos ao LinkedIn sem necessidade |
