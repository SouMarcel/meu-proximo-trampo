# Feature Specification: Front novo em React, montado pelo GitHub Actions

**Feature Branch**: `022-front-react` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-10-20

**Status**: Aprovada para a `master` (2026-10-20); falta validar a Action no GitHub (T006, T007)

**Input**: User description: "O front desta ferramenta está sendo desenvolvido por outro analista usando o Figma
(Figma Make), que publicou a branch `frontend-react`. Vamos pelo processo do GitHub Actions: o Node fica só na nuvem,
quem usa a ferramenta continua só com o Python. Gere também o prompt para o Figma gerar o PR do jeito certo."

## Contexto

O Figma Make trabalha com o projeto React (Vite, TypeScript, Tailwind) na raiz do repositório, numa branch própria
(`frontend-react`) sem histórico em comum com a `master`: não dá para abrir um PR dela. A primeira versão é um
protótipo com dados de exemplo (`mockData.ts`, `localStorage`); do servidor, usa só `GET /api/versao` e
`PATCH`/`DELETE /api/vagas/{id}`.

A ferramenta continua em Python, só com a biblioteca padrão. O código React precisa de uma etapa de montagem
(`pnpm build`) que gera HTML, CSS e JavaScript comuns; esses arquivos funcionam com o `dash/servidor.py` sem Node.

## Clarifications

### Session 2026-10-20

- Q: Converter a ferramenta para Node? → A: Não. O backend continua em Python; o Node fica só na montagem do front.
- Q: Quem monta o front? → A: O GitHub Actions, que abre o PR para a `master` com o resultado. O analista não precisa
  mandar o build.
- Q: O front novo substitui o atual de imediato? → A: Não. Fica em `/novo/`; o `dashboard.html` continua em `/` até o
  front novo ter todas as funções e a pessoa aprovar a troca (tarefa à parte).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Montar o front e abrir o PR (Priority: P1)

O analista termina uma versão no Figma Make e roda a Action **"Front: abrir PR"** no GitHub. A Action monta o front
da `frontend-react`, grava o resultado em `dash/front/` com a origem (`ORIGEM.json`), roda os testes da ferramenta e
abre (ou atualiza) o PR `front/atualizacao` → `master`, com o link da comparação do código-fonte e a lista de commits.

**Acceptance Scenarios**:

1. **Given** um commit novo na `frontend-react`, **When** a Action roda, **Then** o PR é aberto ou atualizado com o
   build e o `ORIGEM.json` desse commit.
2. **Given** nenhum commit novo desde o que está na `master` ou no PR, **When** a Action roda (inclusive pela
   checagem de 6 em 6 horas), **Then** ela termina sem mudar nada.
3. **Given** um build ou um teste que falha, **When** a Action roda, **Then** nenhum PR é aberto ou alterado e o
   erro fica na execução.

### User Story 2 - Usar o front novo sem Node (Priority: P1)

Com o PR na branch da pessoa (teste) ou na `master`, ela abre `http://127.0.0.1:8765/novo/` e usa o front novo,
servido pelo mesmo servidor Python. O dashboard de sempre continua em `/`.

**Acceptance Scenarios**:

1. **Given** `dash/front/index.html` presente, **When** a pessoa abre `/novo/`, **Then** a página e os arquivos de
   `dash/front/` carregam com o tipo certo.
2. **Given** um pedido para fora de `dash/front/` (`/novo/../config.json`, `%2e%2e`, barra invertida) ou de um tipo
   que não é do front, **Then** a resposta é 404.
3. **Given** o front ainda não montado, **When** a pessoa abre `/novo/`, **Then** vê um aviso com o link para `/`.

### User Story 3 - Guiar o Figma Make (Priority: P2)

O analista tem um prompt pronto (`prompt-figma.md`) e o contrato da API (`dash/API.md`) para ligar as telas às rotas
reais, seguindo as regras da ferramenta.

## Requirements *(mandatory)*

- **FR-001**: `dash/servidor.py` entrega `dash/front/` em `/novo/` (só arquivos da pasta, tipos `.html`, `.js`,
  `.css`, `.svg`, `.png`, `.woff2`), redireciona `/novo` para `/novo/` e avisa quando o front não foi montado.
- **FR-002**: `.github/workflows/front.yml` com disparo manual e checagem a cada 6 horas; permissões só de conteúdo e
  PR; Node 22 e pnpm 10.34.3 (os da `frontend-react`); build com `--base ./`; testes Python antes do PR.
- **FR-003**: `dash/front/` é gerado; ninguém edita à mão (marcado como gerado no `.gitattributes`).
- **FR-004**: `dash/API.md` descreve as rotas que o front usa (método, caminho, campos, tela atual).
- **FR-005**: nada muda no dashboard atual nem nas rotas `/api`.

## Success Criteria

- **SC-001**: a pessoa usa o front novo sem instalar Node.
- **SC-002**: cada mudança do analista chega como um PR revisável, com o link do código-fonte.
- **SC-003**: os testes da ferramenta continuam passando.

## Fora do escopo

- Trocar `/` pelo front novo (spec futura, quando as funções estiverem todas no front novo).
- Ligar as telas à API (trabalho do analista, guiado pelo prompt).
