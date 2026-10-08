# Implementation Plan: Iniciar a ferramenta com um comando

**Branch**: `001-iniciar-com-um-comando` (trabalho na `master` por worktree) | **Date**: 2026-10-07 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-iniciar-com-um-comando/spec.md`

## Summary

Um `iniciar.py` na raiz, só com biblioteca padrão, leva a pessoa do clone à página aberta: confere
a versão do Python, vê se a ferramenta já está aberta (e só mostra a página), detecta o estado do
ambiente `.venv/` por um carimbo do `requirements.txt` (sem rede e em segundos), pede confirmação
antes de criar/instalar e sobe o servidor atual na mesma janela, que para com Ctrl+C ou ao ser
fechada. Atalho de duplo clique para Windows. A página ganha um aviso de próximo
passo quando ainda não há configuração. README passa a "clonar e rodar um comando". **Só
Windows** nesta feature (decisão do usuário, foco na experiência web); macOS e Linux na
[lista de desejos](../lista-de-desejos.md). Decisões em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.10+ (o `iniciar.py` tem sintaxe aceita desde 3.6, para mostrar a
mensagem de versão em Python antigo); Batch no atalho.

**Primary Dependencies**: biblioteca padrão (`venv`, `subprocess`, `hashlib`, `urllib`,
`argparse`, `importlib.metadata` no verificador); as do projeto vêm do `requirements.txt`, sem
dependência nova.

**Storage**: arquivos locais: `.venv/` e o carimbo `.venv/.requisitos-instalados`
([data-model.md](data-model.md)). Nenhum dado da pessoa.

**Testing**: `unittest` (biblioteca padrão), `tests/test_iniciar.py`; validação manual pelo
[quickstart.md](quickstart.md).

**Target Platform**: Windows 10/11 com Python 3.10+ (macOS e Linux na lista de desejos).

**Project Type**: aplicação local (servidor Python + página no navegador), projeto único.

**Performance Goals**: página aberta em até 10 s com o ambiente pronto; detecção de "já aberta"
em menos de 2 s; primeira vez em até 5 min (com internet).

**Constraints**: sem rede e sem perguntas com o ambiente pronto; nada escrito fora de `.venv/`
(pip com `--no-cache-dir`); mensagens em português; Ctrl+C ou fechar a janela encerram tudo.

**Scale/Scope**: uma pessoa por computador; 1 arquivo Python novo, 1 atalho, ajustes em
`dashboard.html` e `README.md`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Tudo dentro da pasta do projeto; nenhum dado da pessoa lido ou escrito; a única saída de rede é o download das dependências na instalação, com confirmação. |
| II. Pública, sem dados pessoais | ✅ Nada específico de um usuário; exemplos genéricos. |
| III. Simples, leve, sem IA obrigatória | ✅ Só biblioteca padrão; nenhuma dependência nova; instalação vira um comando; não envolve IA. |
| IV. Só fatos confirmados | ➖ Não se aplica (não gera conteúdo). |
| V. A pessoa decide | ✅ Pede confirmação antes de instalar ou recriar; `--sim` é escolha explícita; não cria configuração. |
| VI. Respeito aos portais | ➖ Não se aplica. |
| Restrições técnicas | ⚠️ Python 3.10+, português, proteções do servidor intocadas. A constituição pede Windows, macOS e Linux; esta feature entrega só Windows por decisão do usuário (ver Complexity Tracking). |
| Fluxo de desenvolvimento | ✅ Spec → plano → tarefas; master por worktree; testes `unittest` nas funções puras; verificação rodando. |

Resultado: **passa**, antes e depois do design, com um desvio justificado (plataformas).

## Project Structure

### Documentation (this feature)

```text
specs/001-iniciar-com-um-comando/
├── plan.md              # este arquivo
├── research.md          # decisões (Phase 0)
├── data-model.md        # ambiente e instância (Phase 1)
├── quickstart.md        # roteiro de validação (Phase 1)
├── contracts/
│   └── comando-iniciar.md   # opções, sequência, códigos de saída, aviso da página
├── checklists/
│   └── requirements.md
└── tasks.md             # (Phase 2: /speckit-tasks)
```

### Source Code (repository root)

```text
iniciar.py               # novo: o comando
iniciar.bat              # novo: atalho Windows (py -3 / python; pause em erro)
tests/
└── test_iniciar.py      # novo: unittest das funções puras
dash/
├── servidor.py          # sem mudança (reaproveitado: main(), ja_rodando, mensagens)
├── dashboard.html       # aviso de próximo passo quando /api/config devolve existe=false
└── abrir-dashboard.bat  # sem mudança (alternativa minimizada)
README.md                # "Instalação" = clonar + comando; passos manuais como alternativa
specs/lista-de-desejos.md  # novo: macOS e Linux (e o que mais for adiado)
```

**Structure Decision**: projeto único na raiz, seguindo o padrão atual (scripts na raiz como
`vagas.py` e `curriculo.py`, servidor em `dash/`). O `iniciar.py` concentra a lógica em funções
puras testáveis (ler requisitos, comparar versões, estado do ambiente, opções) e uma `main()` com
os efeitos (perguntar, instalar, iniciar).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Só Windows (a constituição pede Windows, macOS e Linux) | O usuário priorizou a experiência web no Windows; macOS e Linux entram quando o Windows rodar sem problemas | Cobrir os três agora triplicaria atalhos e verificação sem máquina para testar macOS/Linux |

O `iniciar.py` usa `pathlib` e caminhos do `.venv` dos dois tipos (`Scripts/` e `bin/`) porque
custa uma linha, mas só o Windows é prometido e verificado nesta feature.
