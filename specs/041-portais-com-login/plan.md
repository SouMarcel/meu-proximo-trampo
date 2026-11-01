# Implementation Plan: Portais com login na busca (primeiro: MyGreenhouse Jobs)

**Branch**: `041-portais-com-login` (worktree saída da `master`) | **Date**: 2026-11-01 | **Spec**: [spec.md](spec.md)

## Summary

**A área comum fica em `fontes/_sessao.py`** e serve a todo portal que só mostra a busca depois do login:
- o contexto "busca da página" (`na_pagina`), que só o buscador do dashboard abre;
- a aba em segundo plano na janela da ferramenta;
- o pedido JSON de dentro da aba (os cookies não saem do navegador);
- a espera pelo login (só pelo endereço da aba);
- o estado da conexão (`.cache/portais-login.json`).

Fora da página (terminal, chat), um portal com login só devolve o aviso "só pelo botão Buscar da página".

**O primeiro portal é `fontes/mygreenhouse.py`**, no contrato de `fontes/__init__.py` (research D1 a D11):
- **Lista:** é o JSON que a própria página pede (`my.greenhouse.io/jobs/search?query=<cargo>&work_type[]=remote` com
  os cabeçalhos do Inertia).
  - Na área nacional, vai com o local do país da pessoa (só o Brasil é conhecido) e `date_posted=past_five_days`
    quando a janela for de até 120 h.
  - Lê até 3 páginas de 12 vagas por cargo.
- **Vaga:**
  - id `greenhouse-<empresa>-<id>`, o mesmo das empresas acompanhadas, então não duplica;
  - plataforma "MyGreenhouse", `ats: "greenhouse"`, link público da vaga;
  - os dados da conta (vista, salva, candidatura) ficam de fora.
- **Descrição:** vem pela API pública do quadro da empresa, sem a sessão, só das vagas do relatório.
- **Parada:**
  - login caído: espera de 3 minutos com a janela na frente;
  - captcha: para nesta busca;
  - 403, 429, 503 ou desafio: 24 h de espera;
  - formato desconhecido: "o portal mudou".
- **Ligar:** `"mygreenhouse"` na lista `fontes`, em `filtros.FONTES_LOGIN`, desligado por padrão, com o aviso de risco
  confirmado na página.

**Painel**: seção "Portais com login" em Filtros da busca, com liga/desliga, Conectar, Pronto, Desconectar e a
situação. O estado da busca ganha "aguardando login" (front na `frontend-react`).

**Constituição**: emenda 5.2.0 → 5.3.0, com a seção nova "Busca com login" no princípio VI (texto abaixo). **A pessoa
precisa aprovar o texto antes da implementação.**

## Technical Context

**Language/Version**: Python 3.10+, só biblioteca padrão (`json`, `urllib`, `threading`). Front em TypeScript na
`frontend-react`.

**Primary Dependencies**: nenhuma nova. O navegador é o Edge ou o Chrome da pessoa, pelo `navegador.py` que já existe.

**Storage**:
- `.cache/portais-login.json`, a conexão de cada portal;
- `.cache/mygreenhouse-espera.json`;
- o perfil da janela em `.cache/navegador`, já existente;

todos fora do Git. O formato do `config.json` não muda: `"mygreenhouse"` entra na lista `fontes`. As vagas têm
`plataforma = "MyGreenhouse"`.

**Testing**: `unittest`, sem rede e sem navegador:
- `Aba` falsa com respostas do Inertia fictícias em `tests/dados/mygreenhouse/` (página 1 e página 2,
  `moreResultsAvailable`, uma resposta 409, uma página de login e uma de desafio);
- testes de `_sessao`: fora da página, espera de login com relógio e `sleep` trocados, conectar e desconectar;
- testes do buscador: o estado "aguardando_login" e o cancelamento durante a espera;
- não regressão: contas, FullStack, empresas acompanhadas, integridade e busca.

No fim, uma busca real pela página na branch pessoal, com a pessoa conectada.

**Target Platform**: Windows primeiro, com o Edge ou o Chrome. O dashboard local fica em `127.0.0.1:8765`.

**Project Type**: ferramenta local (CLI + servidor HTTP + página React).

**Performance Goals**: com 4 cargos, cerca de 13 pedidos ao MyGreenhouse por busca, perto de 1 minuto de pausa. O login
caído soma no máximo 3 minutos.

**Constraints**:
- desligado por padrão; desligado, nenhum pedido;
- só no clique da página;
- nenhum clique, senha ou cookie fora do navegador;
- nenhuma leitura de página de outro domínio durante o login;
- parar no primeiro bloqueio;
- nada da conta guardado.

**Scale/Scope**: 1 portal novo, cerca de 2 módulos Python novos, 4 rotas e 1 seção do painel.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ A sessão fica no perfil local da janela; o pedido sai de dentro da aba (os cookies não saem). Só o cargo, o país e os filtros vão ao portal. `viewed`, `appliedAt` e `saved` são descartados. Estado e espera ficam em `.cache/`. |
| II. Pública, sem dados pessoais | ✅ JSON de teste fictício: empresas, títulos e ids trocados, sem `currentUserEmail`. |
| III. Simples | ✅ Biblioteca padrão e o `navegador.py` existente; funciona sem IA. |
| IV. Só fatos | ✅ Local, modelo e data como o portal informa. A faixa salarial (`payRanges`) fica de fora enquanto vier nula. |
| V. A pessoa decide | ✅ Desligado por padrão, aviso de risco confirmado, só no clique dela. A espera pergunta antes de seguir sem o portal. |
| VI. Respeito aos portais | ⚠️ **Precisa de emenda.** Hoje a regra é "só a busca pública, sem login", e a conta conectada cobre só a área da própria pessoa. A emenda proposta abaixo cria a seção "Busca com login". Além disso, os termos do MyGreenhouse proíbem automação (research R1), então vale "Termos contrários": decisão da pessoa de 2026-11-01, termos e risco no painel, desligado por padrão. |
| Restrições técnicas | ✅ Contrato de `fontes/__init__.py` mantido; id prefixado (o das empresas acompanhadas). |
| Fluxo | ✅ Spec aprovada em 2026-11-01 → plano (este) → tarefas, com aprovação em cada etapa. |

Resultado: **passa com a emenda**, que é aprovada pela pessoa e aplicada como primeira tarefa da implementação.

### Emenda proposta (5.2.0 → 5.3.0, MINOR: seção nova no princípio VI)

1. **No 1º parágrafo do princípio VI**, depois de "…sem nova tentativa nem forma de contornar.", entra: "A exceção é a
   busca com login (abaixo)."
2. **Seção nova, depois de "Conta conectada"**:

> **Busca com login.** Um portal que só mostra a busca de vagas depois do login pode entrar numa área própria da
> ferramenta ("Portais com login"), só nestas condições:
>
> - **Portal por portal:** cada um entra em spec própria, com análise de risco e a decisão da pessoa registrada. Vem
>   desligado por padrão, e a pessoa liga confirmando o aviso de risco da conta. A busca do LinkedIn fica de fora.
> - **Login da pessoa, na janela da ferramenta:** valem as regras da conta conectada:
>   - perfil só da ferramenta;
>   - nunca pedir, ler ou digitar senha;
>   - os cookies não saem do navegador;
>   - nenhum clique em botão do portal.
>
>   O login por outro serviço (ex.: LinkedIn) é permitido, com aviso; a ferramenta não lê nem age nas páginas dele.
> - **Só no clique da página:** a leitura roda só na busca iniciada pelo botão da página. A busca pelo terminal ou pelo
>   chat não usa a sessão, e o assistente nunca a usa.
> - **Só leitura, só a busca:** a ferramenta lê só os resultados da busca e os dados públicos da vaga. Nada da conta
>   (vagas vistas, salvas, candidaturas) é guardado.
> - **Pouco e parando:**
>   - pausa e limite de páginas;
>   - no primeiro bloqueio, para e fica em espera;
>   - captcha ou verificação param o portal, e quem resolve é a pessoa;
>   - com o login caído, a janela espera a pessoa por pouco tempo, e a busca segue sem o portal se ela não entrar.
> - **Termos contrários:** se os termos do portal proíbem automação, vale também a regra de "Termos contrários".
>   Exemplo: MyGreenhouse Jobs (spec 041), desligado por padrão, por decisão de 2026-11-01.

3. **Relatório de impacto** no topo do arquivo, data 2026-11-01. Arquivos atualizados: AGENTS.md (Respeite os
   portais), README.md, dash/API.md, docs/novo-portal.md e a skill buscar-vagas.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Busca com a sessão da pessoa (fora da regra "sem login") | O MyGreenhouse Jobs, a única busca do Greenhouse entre empresas, exige login. A pessoa quer uma área para portais assim (decisão de 2026-11-01). | As empresas acompanhadas (API pública) cobrem só as empresas que a pessoa já conhece. Colar a lista no chat a cada vez foi oferecido, e ela preferiu a área. |
| Termos do MyGreenhouse contra automação, com risco na conta | Decisão da pessoa em 2026-11-01, depois de ler os trechos (research R1). | Parar a spec foi oferecido e recusado. |
| API interna (Inertia), não documentada | É o pedido que a própria página faz. Ler a tela daria o mesmo dado com mais fragilidade. | Ler o HTML: a lista não vem no HTML (deferred prop). |
| Resultado hoje pequeno para o perfil de teste (research R3) | A área serve a portais futuros, e o MyGreenhouse ganha valor se vagas ágeis abertas ao Brasil aparecerem ou se a busca internacional for ligada. | Pausar a spec e só acompanhar empresas foi oferecido; a pessoa escolheu os dois caminhos. |

## Project Structure

### Documentation (this feature)

```text
specs/041-portais-com-login/
├── spec.md, plan.md
├── research.md (R1–R4 + decisões técnicas D1–D11)
├── data-model.md
├── contracts/sessao.md, contracts/mygreenhouse.md, contracts/api.md
├── quickstart.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
fontes/_sessao.py         # novo: na_pagina, conectados/marcar, aba, pedir_json, esperar_login, PortalComLoginErro
fontes/mygreenhouse.py    # novo: buscar, descrever, logado, pausa, aviso_pausa, espera, parada
fontes/__init__.py        # registro em FONTES; docstring: atributos de portal com login (COM_LOGIN…)
filtros.py                # FONTES_LOGIN (aceitas em "fontes", fora de FONTES_PADRAO)
vagas.py                  # fontes_em_espera ignora portal com login fora da página; aviso no terminal
dash/buscador.py          # executar dentro de _sessao.na_pagina; situação "aguardando_login"; plano conta o portal
dash/servidor.py          # /api/portais-login (GET) e /{portal}/conectar|pronto|desconectar; o Desconectar das contas soma os portais com login
dash/banco.py             # PLATAFORMAS + "MyGreenhouse"
integridade.py            # PORTAIS: "MyGreenhouse": ("my.greenhouse.io",)
.env.exemplo              # MYGREENHOUSE_PAUSA comentada
.specify/memory/constitution.md   # emenda 5.3.0 (primeira tarefa, depois do OK)
README.md, dash/README.md, dash/API.md, AGENTS.md, docs/novo-portal.md (seção "Portal com login"),
specs/lista-de-desejos.md (Greenhouse como portal: feito na spec 041)
.agents/skills/buscar-vagas/SKILL.md (+ python sincronizar_skills.py)
tests/test_sessao.py, tests/test_mygreenhouse.py, tests/dados/mygreenhouse/*.json, tests/test_buscador.py (casos novos)
frontend-react: src/types/api.ts, src/services/api/ (portais-login), src/components/modals/SearchFiltersModal.tsx
  (seção nova), progresso da busca ("aguardando login"), src/utils/formatters.ts (etiqueta e domínio)
```

**Structure Decision**: a fonte segue o molde da FullStack e do JobGether (pausa, espera, `parada`), com a leitura por
uma `Aba` em vez de `urllib`. Tudo que vale para qualquer portal com login fica em `_sessao.py`, para que o próximo
portal seja só um módulo novo. O buscador da página é o único que abre o contexto; `vagas.executar` não muda de
assinatura.
