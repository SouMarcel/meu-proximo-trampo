# Implementation Plan: Empresas acompanhadas em qualquer página de vagas

**Branch**: `042-empresas-sites` (worktree saída da `master`) | **Date**: 2026-11-01 | **Spec**: [spec.md](spec.md)

## Summary

O campo "Empresas que você acompanha" passa a aceitar a página de vagas de qualquer empresa (research D1 a D9):
- **Teamtailor** (`fontes/teamtailor.py`, novo): a lista pública de vagas que o site oferece (feed RSS), uma vez por
  busca;
- **EY**: a leitura de hoje (`fontes/ey.py`), agora como empresa. A EY sai dos portais, e quem a tinha ligada ganha a
  EY na lista (migração em `filtros.efetivos`). Corrige o falso aviso da busca sem resultado;
- **página própria** (`fontes/pagina_empresa.py`, novo): o texto visível da página, depois do filtro de integridade,
  lido pela IA da pessoa só quando muda, com o dia em que cada vaga foi vista primeiro;
- **reconhecer**: sem pedido para os domínios conhecidos; com um pedido (`ats.descobrir`) para os outros, no botão
  Adicionar do painel (rota nova `POST /api/empresas/reconhecer`) e no Acompanhar.

## Technical Context

**Language/Version**: Python 3.10+, só biblioteca padrão (`xml.etree`, `hashlib`, `json`). Front em TypeScript na
`frontend-react`.

**Primary Dependencies**: nenhuma nova. A IA é a de `ia.py`, com a reserva da spec 032.

**Storage**:
- `config.json`: `empresas` aceita os sistemas novos (`teamtailor`, `ey`, `pagina`); `"ey"` sai de `fontes`;
- `.cache/empresas-paginas/<id>.json`: a marca do texto, as vagas separadas e as datas em que foram vistas (fora do
  Git).

**Testing**: `unittest`, sem rede e sem IA de verdade:
- feed fictício do Teamtailor;
- página fictícia no formato da consultoria, com resposta da IA trocada;
- página da EY sem resultado com o CSS de `data-row`;
- config antigo com e sem a EY.

**Target Platform**: Windows primeiro; dashboard local em `127.0.0.1:8765`.

**Project Type**: ferramenta local (CLI + servidor HTTP + página React).

**Constraints**:
- um pedido por empresa por busca;
- pausa entre pedidos ao mesmo site;
- parar no primeiro bloqueio;
- IA só com o texto público da página, nunca com dados da pessoa;
- nada inventado.

**Scale/Scope**: 2 módulos novos, mudanças em `ats.py`, `ey.py`, `filtros.py`, `vagas.py`, `servidor.py`; 1 rota
nova; o painel de empresas no front.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Só o texto público da página vai à IA; a memória fica em `.cache/`. |
| II. Pública, sem dados pessoais | ✅ Feed, página e respostas fictícios nos testes. |
| III. Simples, sem IA obrigatória | ✅ Teamtailor, EY e os sistemas de antes funcionam sem IA; só a página própria precisa dela, com aviso. |
| IV. Só fatos | ✅ A IA só copia: cargo conferido no texto, e-mail e link escritos na página, campo ausente fica vazio. A data é a do dia em que a vaga foi vista, dita como tal. |
| V. A pessoa decide | ✅ A empresa só entra na lista pelo clique dela. |
| VI. Respeito aos portais | ✅ Só páginas públicas, sem login; o feed é o que o site oferece, o robots.txt libera; um pedido por busca; para no primeiro bloqueio. Nenhum termo contrário achado (research R1). |
| Fluxo | ✅ Spec aprovada em 2026-11-01; a pessoa pediu para seguir direto até o merge na branch pessoal. |

Resultado: **passa**, sem emenda.

## Project Structure

```text
specs/042-empresas-sites/  spec.md, plan.md, research.md, data-model.md, contracts/empresas.md, contracts/api.md,
                           quickstart.md, tasks.md, checklists/requirements.md

fontes/teamtailor.py      # novo: feed → vagas no formato comum
fontes/pagina_empresa.py  # novo: texto da página, IA, memória e vagas
fontes/ats.py             # sistemas novos: reconhecer, descobrir, conferir, _lista/normalizar por sistema, bloqueio por host
fontes/ey.py              # busca sem resultado sem aviso; linha de vaga pelo HTML
filtros.py                # EY fora de FONTES_NAC/FONTES_PADRAO; migração em efetivos; _empresas aceita os sistemas novos; acompanhar com descobrir
vagas.py                  # fontes_da_busca pela lista de efetivos
dash/servidor.py          # POST /api/empresas/reconhecer
dash/banco.py             # PLATAFORMAS + "Teamtailor", "Site da empresa"
tests/test_empresas_sites.py, tests/dados/empresas-sites/ (feed, página, EY sem resultado)
README.md, dash/README.md, dash/API.md, AGENTS.md, docs/novo-portal.md, .agents/skills/buscar-vagas/SKILL.md
frontend-react: painel de empresas (Adicionar pelo servidor, rótulo do sistema), etiquetas "Teamtailor" e
  "Site da empresa", texto de ajuda
```

**Structure Decision**: o `fontes/ats.py` continua sendo a única fonte "Empresas acompanhadas" (um item em `fontes`,
acrescentado quando há empresas), e cada sistema novo é um módulo que ele chama. Assim, a busca, o plano, os filtros
e a junção pelo id não mudam.
