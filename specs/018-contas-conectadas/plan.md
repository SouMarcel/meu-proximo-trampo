# Implementation Plan: Contas conectadas

**Branch**: `018-contas-conectadas` (worktree saída da `master`) | **Date**: 2026-10-18 | **Spec**: [spec.md](spec.md)

## Summary

São cinco peças:

1. **Janela da ferramenta (`navegador.py`, pronto na pesquisa).** Abre o Edge ou o Chrome com perfil próprio em
   `.cache/navegador` e conversa com ele pelo DevTools Protocol, com um WebSocket mínimo da biblioteca padrão. Tem
   `abrir`, `Aba.ir`, `Aba.avaliar`, `Aba.frente`, `fechar` e `desconectar`.
2. **Contrato de contas (`contas/`).** Cada portal tem o seu módulo:
   - `contas/gupy.py` e `contas/indeed.py`, ativos;
   - `contas/linkedin.py`, desativado.

   Cada módulo lê as candidaturas **pela API que a própria página usa** (`fetch` de dentro da aba, com a sessão
   dela) e traduz o status de cada uma em etapa do quadro (research §3–§5).
3. **Sincronia (`dash/sincronia.py`).**
   - `proposta(lidas)` é pura: casa pelos ids do banco e, na falta deles, por cargo + empresa no banco inteiro. Nunca
     rebaixa a etapa e não mexe em vaga encerrada.
   - `aplicar(itens)` grava só o que foi marcado: muda a etapa, leva vagas ao quadro ou cria vagas novas, e escreve a
     anotação.
   - `Leitura` roda em segundo plano, porque a Gupy pode esperar o clique de login.
4. **Servidor.** Rotas só deste computador: `/api/contas`, `/api/contas/<portal>/conectar` e `desconectar`,
   `/api/candidaturas/ler`, `/api/candidaturas/estado` e `/api/candidaturas/aplicar`.
5. **Página.** Botão "Atualizar candidaturas" e um diálogo com os portais (Conectar ou Desconectar), "Atualizar
   agora", o progresso ("aguardando o seu login na Gupy…") e a proposta com caixas de marcar.

Mais a documentação: AGENTS.md, README, as skills buscar-vagas e consultar-gupy e a lista de desejos.

## Technical Context

- **Language**: Python 3.10+ (biblioteca padrão); JavaScript ES5 na página.
- **Dependências**: nenhuma nova. Usa o Edge ou o Chrome instalado.
- **Storage**:
  - perfil do navegador em `.cache/navegador`;
  - mapa `applicationId → job.id` da Gupy e a última leitura em `.cache/contas/`;
  - campos novos opcionais na vaga: `conta_status` (último status lido, por portal) e `conta_lida_em`.

  Tudo fora do Git.
- **Testing:** `unittest` com JSON fictício em `tests/dados/contas/`, a `Aba` substituída por uma falsa (sem
  navegador), banco temporário e o codec do WebSocket.
- **Performance:**
  - a Gupy pede 1 página para a lista, mais 1 por candidatura ativa sem id guardado;
  - o Indeed pede 1 página;
  - a leitura típica leva menos de 30 s, mais o tempo do clique de login na Gupy.

## Constitution Check (3.0.0)

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ A sessão, o mapa da Gupy e a última leitura ficam em `.cache/`. O JSON da conta (CPF, celular) nunca é pedido: só as rotas de candidaturas. |
| II. Pública | ✅ Testes com JSON fictício; nada da pessoa no código. |
| III. Simples | ✅ Biblioteca padrão, sem Playwright. Sem conta conectada, a ferramenta segue igual. |
| IV. Só fatos | ✅ A etapa vem do que o portal diz; o que não é reconhecido vira só informação. |
| V. A pessoa decide | ✅ A proposta é marcada pela pessoa; nada grava sozinho. |
| VI. Conta conectada | ✅ Janela da ferramenta, login feito pela pessoa (o clique de login da Gupy é dela), só leitura, só no clique, Gupy e Indeed liberados, LinkedIn desativado, parada no bloqueio. |

## Source Code

```text
navegador.py             # janela da ferramenta (pesquisa)
contas/__init__.py       # contrato, CONTAS (ativos), TODAS, Lida (estrutura comum), PortalErro
contas/gupy.py           # lista + detalhe das ativas; mapa em .cache/contas/gupy.json; tradução por categoria
contas/indeed.py         # appStatusJobs + interviews; tradução por statuses
contas/linkedin.py       # ATIVO = False; leitura da tela do Rastreador de vagas
dash/sincronia.py        # proposta(), aplicar(), Leitura (thread com estado)
dash/servidor.py         # rotas /api/contas e /api/candidaturas
dash/dashboard.html      # botão, diálogo, proposta
tests/test_navegador.py, tests/test_contas.py, tests/dados/contas/*.json|html
README.md, AGENTS.md, .agents/skills/{buscar-vagas,consultar-gupy}/SKILL.md, specs/lista-de-desejos.md
```
