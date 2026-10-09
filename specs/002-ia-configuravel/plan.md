# Implementation Plan: IA configurável

**Branch**: `002-ia-configuravel` (trabalho na `master` por worktree) | **Date**: 2026-10-08 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-ia-configuravel/spec.md`

## Summary

Um módulo `ia.py` (biblioteca padrão) passa a ser a única porta de saída para IA: três adaptadores
(Claude Code por linha de comando, API da Anthropic e API no formato da OpenAI, que cobre OpenAI,
OpenRouter, Groq, DeepSeek, Gemini e "outro compatível"), erros com motivo legível e chaves
mascaradas. As chaves ficam no `.env` por um módulo `segredos.py`; a escolha (sem chave) fica em
`config.json` → `"ia"`. A análise automática passa a usar `ia.responder`, registra provedor e modelo
em cada nota e expõe o último erro para a página. A página ganha o painel "IA" (escolher, modelo,
chave, testar, avisos) com rotas novas no servidor, que só aceitam mudança vinda do próprio
computador. Sem configuração, tudo segue como hoje. Decisões em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.10+; JavaScript ES5 no `dashboard.html` (padrão atual).

**Primary Dependencies**: biblioteca padrão (`urllib`, `json`, `subprocess`, `shutil`); nenhuma
dependência nova.

**Storage**: `config.json` (escolha), `.env` (chaves), SQLite atual (campos novos na análise, sem
migração) — ver [data-model.md](data-model.md).

**Testing**: `unittest` (`tests/test_ia.py`, `tests/test_segredos.py`), com servidor HTTP falso
local para o adaptador compatível; validação manual pelo [quickstart.md](quickstart.md).

**Target Platform**: Windows 10/11 (macOS e Linux na lista de desejos; o código não depende de
plataforma além do comando `claude`).

**Project Type**: aplicação local (servidor Python + página), projeto único.

**Performance Goals**: teste de conexão ≤ 15 s (30 s no Claude Code); nota de vaga nova ≤ 2 min.

**Constraints**: chave nunca na página, no config, em mensagem ou registro; mudança de IA só pelo
próprio computador; sem IA, nenhuma chamada externa; compatível com o comportamento atual.

**Scale/Scope**: um usuário; 2 módulos novos, ajustes em `analise.py`, `servidor.py`, `banco.py`,
`filtros.py`, `startupjobs.py`, `dashboard.html`, README; 2 arquivos de teste.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Chaves só no `.env`; nada é enviado sem escolha salva; avisos de para onde vão os dados; mascaramento em erros e registros; mudança de IA só pelo próprio computador. |
| II. Pública, sem dados pessoais | ✅ Catálogo e exemplos genéricos; nenhuma chave em arquivo versionado. |
| III. Simples, leve, sem IA obrigatória | ✅ É a implementação do próprio princípio: provedor configurável por HTTP com biblioteca padrão, "Sem IA" de primeira classe, sem dependência nova. |
| IV. Só fatos confirmados | ✅ Mesmo pedido e mesma validação da análise atual; resposta torta não é gravada. |
| V. A pessoa decide | ✅ Escolha explícita; teste só no clique; padrão sem configuração = comportamento de hoje. |
| VI. Respeito aos portais | ➖ Não se aplica. |
| Restrições técnicas | ⚠️ Python 3.10+, português, proteções do servidor mantidas e reforçadas; verificação só no Windows (mesmo desvio justificado da spec 001). |
| Fluxo de desenvolvimento | ✅ Spec → plano → tarefas; testes `unittest`; verificação rodando. |

Resultado: **passa**, antes e depois do design, com o desvio de plataforma já registrado.

## Project Structure

### Documentation (this feature)

```text
specs/002-ia-configuravel/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── api-ia.md        # rotas do servidor e interface do ia.py
├── checklists/
│   └── requirements.md
└── tasks.md             # (/speckit-tasks)
```

### Source Code (repository root)

```text
ia.py                    # novo: catálogo, escolha efetiva, adaptadores, erros, mascarar, testar
segredos.py              # novo: ler/gravar/remover chaves no .env preservando linhas
dash/
├── analise.py           # usa ia.responder, lotes de 10, provedor/modelo na análise, ultimo_erro
├── servidor.py          # GET/PUT /api/ia, POST /api/ia/testar, DELETE /api/ia/chave/<p>; ia_erro em /api/versao; existe = há termos
├── banco.py             # validar_analise aceita analise_provedor e analise_modelo
└── dashboard.html       # painel "IA", aviso de falha no Relatório, provedor·modelo no detalhe
filtros.py               # salvar: sem termos, parte do exemplo e preserva "ia"
fontes/startupjobs.py    # _chave via segredos.ler (mesmo comportamento)
tests/
├── test_ia.py           # novo
└── test_segredos.py     # novo
README.md                # seção de IA: provedores, chaves, avisos
```

**Structure Decision**: módulos novos na raiz, como `filtros.py` e `curriculo.py`, porque serão
usados pelo servidor (`dash/`) e pelas próximas features (currículo, carta, anamnese), não só pelo
dashboard.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Só Windows verificado (a constituição pede Windows, macOS e Linux) | Decisão do usuário (foco na experiência web no Windows) | Mesmo motivo da spec 001; o código em si é portável |
