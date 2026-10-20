# Implementation Plan: Front único

**Branch**: `025-front-unico` (documentos, na `master`) e `frontend-react` (código do front) | **Date**: 2026-10-20 |
**Spec**: [spec.md](spec.md)

## Summary

A página nova (React, em `/novo/`) passa a usar só o servidor local, tela por tela, na ordem das histórias. Telas que
não existem são criadas no visual atual dela: currículo, kit da candidatura, análises do perfil e lembretes. Quando a
[lista de paridade](contracts/paridade.md) estiver toda conferida, o servidor passa a entregar a página nova em `/`,
e o `dashboard.html` sai. O código do front é editado aqui, na `frontend-react`, e chega à `master` pela Action da
spec 022. O servidor só muda na troca.

## Technical Context

- **Front**:
  - React 19, Vite 8, Tailwind 4, TypeScript 5.9 e lucide-react, na `frontend-react` (commit `3a7bc44`);
  - Node 22 e pnpm 10.34.3 (`.mise.toml`), com Node 22.19 já instalado neste computador;
  - install, build e conferência de tipos testados aqui ([research R2](research.md#r2-montagem-e-conferência-local),
    [R3](research.md#r3-conferência-de-tipos)).
- **Servidor**: `dash/servidor.py`, só biblioteca padrão. As rotas do `dash/API.md` cobrem todas as telas; nenhuma
  rota nova prevista.
- **Hoje o front**:
  - usa 5 rotas;
  - o resto vem de `mockData.ts`, `onboardingData.ts` e `setTimeout`;
  - os tipos de `types/job.ts` divergem do servidor ([R11](research.md#r11-divergências-entre-os-tipos-do-front-e-o-servidor-a-corrigir));
  - o `tsc` acusa 10 erros que o build não vê.
- **Testes**:
  - Python: `python -m unittest discover -s tests`, com o `test_front_estatico.py` ajustado na troca;
  - front: `tsc --noEmit`, build, os greps de segurança do [quickstart](quickstart.md) e o roteiro em uso real.
    Sem framework de teste novo ([R3](research.md#r3-conferência-de-tipos)).
- **Plataforma**: Windows primeiro; navegador moderno; página servida em `127.0.0.1:8765` ou pelo Live Server.
- **Escala**: uma pessoa. Algumas centenas de vagas na tela; o JS de hoje tem 436 kB, e a meta é ficar abaixo de
  700 kB.

## Constitution Check

| Princípio | Como o plano cumpre |
|---|---|
| I. Local e privado | A página só fala com `127.0.0.1:8765`, sem CDN nem fonte externa. A chave da IA nunca volta para a tela nem para o navegador. O `localStorage` guarda só preferências de tela. |
| II. Sem dados pessoais na `master` | O `mockData` é reescrito com dados fictícios. A busca de dados pessoais roda antes de cada push da `frontend-react` e antes do merge na `master`. |
| III. Simples e leve | Quem usa não precisa de Node: o build vai pronto. Nenhuma dependência nova, nem no front nem no Python. Sem IA, a página continua com busca, Relatório, quadro e Adicionar vaga. |
| IV. Só fatos confirmados | Saem os campos inventados do perfil (pretensão salarial, anos de experiência). As perguntas sensíveis ficam com campo para a pessoa. A entrevista mostra só os dados da vaga. |
| V. A pessoa decide | Confirmações da seção 4 do `dash/API.md`; a IA só preenche ou propõe; contas só aplicam o que foi marcado ([contrato das telas](contracts/telas.md)). |
| VI. Respeito aos portais | O botão Buscar respeita `proxima_em`, a espera e a busca recente. A leitura das contas só acontece no clique, e o front para no bloqueio que o servidor informa. |
| Fluxo | A spec já foi aprovada. Cada história é testada na `marcel` e só vai à `master` com o OK. |

**Desvio justificado**: o código do front muda na `frontend-react`, e não na `master` por worktree. É o caminho
definido na spec 022: o build entra na `master` só pelo PR da Action, revisado e testado na `marcel`.

Reavaliação depois do desenho: nenhum desvio novo.

## Project Structure

### Documentação

```text
specs/025-front-unico/
├── spec.md, plan.md, research.md, data-model.md, quickstart.md
├── contracts/
│   ├── telas.md            # tela → rotas → regras
│   ├── paridade.md         # lista de paridade (FR-020), marcada a cada entrega
│   └── servidor-troca.md   # rotas de página depois da troca
└── tasks.md                # /speckit-tasks
```

### Código

```text
frontend-react (worktree)            master (worktree 025-front-unico)
src/                                 .github/workflows/front.yml   # + tsc --noEmit (H1)
├── App.tsx                          dash/servidor.py              # troca (H7)
├── contexto/Ferramenta.tsx  (novo)  dash/dashboard.html           # sai (H7)
├── hooks/useConsulta.ts     (novo)  tests/test_front_estatico.py  # troca (H7)
├── services/                        README.md, dash/README.md, dash/API.md, AGENTS.md
│   ├── api.ts               (pedido único)       .agents/skills/buscar-vagas/SKILL.md (+ sincronizar_skills.py)
│   ├── api/{vagas,busca,config,ia,perfil,analises,curriculo,kit,entrevista,contas}.ts (novos)
│   ├── storage.ts           (só preferências)    .vscode/settings.json
│   └── mockData.ts          (só demonstração)
├── types/api.ts             (novo; sai types/job.ts aos poucos)
├── utils/formatters.ts
└── components/
    ├── TextoDaVaga.tsx      (novo)
    ├── Header, NavigationTabs, KanbanBoard, TriageReport, InternationalHub, FunnelAnalytics, JobCard
    ├── InterviewCoach.tsx   (H5, dados reais)
    ├── curriculo/, kit/, analises/ (novos: H3, H4)
    └── modals/ (AddJob, SearchJobs, SearchFilters, AISettings, Profile, CandidateOnboarding, ConnectedAccounts, JobDetail)
```

**Structure Decision**: mantém a estrutura do Figma Make (componentes e modais) para não reescrever o visual, e
acrescenta só a camada de API por área, o contexto, o hook de consulta e as telas que faltam.

## Entregas (uma por história, cada uma com o OK da pessoa)

1. **Base e História 1**:
   - fundação: `api.ts` com o pedido único, `types/api.ts`, contexto `Ferramenta`, `useConsulta`, fila por vaga,
     `TextoDaVaga`, os 10 erros de tipo corrigidos, `typecheck` no `package.json` e `tsc` na Action;
   - telas: Buscar vagas, última busca, Tentar a nota de novo, Completar descrições, Adicionar vaga, Marcar todas
     como não seguidas, Apoie o projeto;
   - modo demonstração com `mockData` no formato novo.
2. **História 2**: Filtros (nacional e internacional, com `opcoes`) e IA. Saem `ConfigIA` e `FiltrosBusca`
   inventados.
3. **História 3**:
   - Meu perfil e Primeiros passos, no lugar do `onboardingData` e do `PerfilUsuario`;
   - Já tenho currículo e Seu currículo;
   - Análises, também no painel Internacional.
4. **História 4**: Currículo (vaga e base), checklist real, carta, respostas, lembretes e os links de arquivos.
5. **História 5**: Entrevista com `GET /api/entrevista/{vid}` e as rotas do §3.10.
6. **História 6**: Contas conectadas.
7. **História 7**: com a paridade completa e uma semana de uso só na página nova, a troca no servidor
   ([contrato](contracts/servidor-troca.md)), a documentação e os testes. Commit na branch `025-front-unico`, teste
   na `marcel`, merge na `master`.

Cada entrega passa pelos portões e pelo roteiro do [quickstart](quickstart.md) e marca as suas linhas na lista de
paridade.

## Riscos

- **O Figma Make voltar a gravar na `frontend-react`**: combinar antes. Os commits daqui ficam no histórico da
  branch, e o Figma precisa partir deles.
- **`JobDetailModal` grande (577 linhas) e currículo e kit dentro dele**: currículo e kit viram componentes próprios
  em `components/curriculo/` e `components/kit/`, abertos do detalhe.
- **Build copiado para `dash/front/` na `marcel` e esquecido**: o `git checkout -- dash/front` é passo fixo antes do
  merge do PR.

## Complexity Tracking

Sem violações além do desvio justificado acima.
