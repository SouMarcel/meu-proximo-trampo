# Implementation Plan: Front novo em React, montado pelo GitHub Actions

**Branch**: `022-front-react` | **Date**: 2026-10-20 | **Spec**: [spec.md](spec.md)

## Summary

O Figma Make segue gravando na `frontend-react`. Uma Action na `master` monta esse front (Node só na nuvem), copia o
`dist/` para `dash/front/` e abre o PR `front/atualizacao`. O servidor Python entrega o front em `/novo/`.

## Technical Context

- **Servidor**: `dash/servidor.py` (biblioteca padrão). Hoje entrega só `dashboard.html` em `/`. O CORS só aceita
  `http://127.0.0.1` e `localhost`, então o preview do Figma (https, na nuvem) não alcança o servidor: lá o front
  fica em modo demonstração.
- **Endereço da API no front**: a mesma regra de `dash/dashboard.html` (`var BASE`): caminho relativo quando a página
  vem do servidor; `http://127.0.0.1:8765` quando aberta pelo Live Server.
- **Front**: React 19, Vite 8, Tailwind 4, `pnpm-lock.yaml`, `.mise.toml` (Node 22, pnpm 10.34.3). Build local de
  conferência (2026-10-20, commit `ae682e0`): `pnpm install --frozen-lockfile` e `vite build --base ./` passam;
  `dist/` com `index.html`, um JS (~436 kB) e um CSS (~76 kB); nenhuma CDN, fonte externa ou telemetria.
- **GitHub**: repositório público, `master` sem proteção; o Actions está com permissão só de leitura e sem poder
  criar PR. A Action declara `contents: write` e `pull-requests: write`, e a opção "Allow GitHub Actions to create and
  approve pull requests" precisa ser ligada uma vez (com o OK da pessoa).

## Constitution Check

- Dados pessoais fora do Git: o build só tem dados de exemplo fictícios; `dash/front/` não lê nada da pessoa.
- Python com biblioteca padrão: nenhuma dependência Python nova; o Node fica no GitHub Actions.
- Indique, não saia fazendo: a Action só abre o PR; o merge é da pessoa, depois do teste na branch pessoal.
- Texto da internet é dado: o prompt exige mostrar descrições como texto (sem `dangerouslySetInnerHTML`).

## Design

1. **Rota `/novo/`** (`Handler._front`): resolve o caminho dentro de `FRONT.resolve()` (`is_relative_to`), recusa
   tipos fora de `TIPOS_FRONT`, usa `_enviar` (mesmos cabeçalhos de segurança). `/novo` → 308 para `/novo/`, porque o
   build usa caminhos relativos. Sem `index.html`, 404 com aviso em HTML.
2. **Action** (`.github/workflows/front.yml`):
   - descobre o commit da `frontend-react` (`git ls-remote`) e compara com o `ORIGEM.json` da `master` e do PR
     aberto; sem novidade, para (a entrada `forcar` monta de novo);
   - `pnpm install --frozen-lockfile`, `pnpm exec vite build --base ./` (a base relativa não depende do analista);
   - copia `dist/` para `dash/front/` e grava `ORIGEM.json` (branch, commit, data, execução);
   - `pip install -r requirements.txt` e `python -m unittest discover -s tests`;
   - commit do bot na branch `front/atualizacao` (forçada a partir da `master`), `gh pr create` ou `gh pr edit` com a
     comparação do código-fonte, os commits e uma lista de conferência.
3. **`.gitattributes`**: `dash/front/** linguist-generated=true` (o GitHub recolhe o diff do build).
4. **`dash/API.md`**: contrato das rotas a partir do `servidor.py` e do uso no `dashboard.html`.
5. **`prompt-figma.md`**: as regras para o Figma Make.

## Fluxo de teste e entrega

Commit na worktree → `git merge` na branch pessoal → testes e `/novo/` com um build local → com o OK: dados pessoais
conferidos, merge na `master`, push, opção do Actions ligada, `gh workflow run front.yml` → o PR de teste é revisado
na branch pessoal (`git merge origin/front/atualizacao`) → com o OK, merge do PR e `git merge master` na branch pessoal.
