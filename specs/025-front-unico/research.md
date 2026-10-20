# Pesquisa: Front único

Conferido em 2026-10-20 na `frontend-react` (commit `3a7bc44`), na `master` (`920ebd0`) e neste computador.

## R1. Onde o código muda e como chega à `master`

- **Decision**: o React é editado numa worktree da `frontend-react` (branch local que segue `origin/frontend-react`).
  Commits locais, por história. O teste da pessoa é feito com um build local copiado para `dash/front/` na branch pessoal,
  sem commit. Com o OK: `git checkout -- dash/front` na branch pessoal, push da `frontend-react`, Action "Front: abrir PR",
  revisão do PR `front/atualizacao`, merge, `git merge master` na branch pessoal.
- **Rationale**: mantém o caminho da spec 022 (o build só entra na `master` pela Action) e deixa a pessoa testar antes
  de qualquer push. O push da `frontend-react` é público, então só acontece com o OK.
- **Alternatives considered**: commitar o build na branch pessoal (sujaria a branch e entraria em conflito com o PR da
  Action); testar só pelo PR da Action (exige push antes do teste).

## R2. Montagem e conferência local

- **Decision**: `npx -y pnpm@10.34.3 install --frozen-lockfile` e `npx -y pnpm@10.34.3 exec vite build --base ./`
  (as versões do `.mise.toml`). Durante o desenvolvimento, `vite --host 127.0.0.1 --port 5173` com o servidor da
  ferramenta rodando: o CORS do servidor aceita `http://127.0.0.1:<qualquer porta>`, e o `getApiBaseUrl` usa
  `http://127.0.0.1:8765` fora da porta 8765.
- **Verificado**: install em 5 s, build em 1,2 s; `dist/` com `index.html`, um JS (436 kB) e um CSS (77 kB).
- **Rationale**: Node 22 já está instalado; nada muda para quem usa a ferramenta (o build vai pronto no repositório).

## R3. Conferência de tipos

- **Decision**: script `typecheck` (`tsc --noEmit`) no `package.json`, os 10 erros que já existem corrigidos na
  primeira entrega, e o passo `pnpm exec tsc --noEmit` na Action antes do build.
- **Rationale**: o `vite build` não confere tipos. Hoje passam erros como `Vaga` sem `origem` e `formatters.ts` sem
  importar `Vaga`. Com os tipos vindos do `dash/API.md`, campo inventado ou com nome errado vira erro de build.
- **Alternatives considered**: vitest para testes do front. Fica de fora porque é dependência nova sem ganho
  proporcional: as funções puras do front são poucas (formatação, faixa de nota, área). O comportamento é conferido
  pelo quickstart em uso real, como manda a constituição.

## R4. Camada de API

- **Decision**: `src/services/api.ts` com o endereço (`getApiBaseUrl`, já existe) e uma função única de pedido:
  - `Content-Type: application/json` em toda escrita, com corpo `{}` quando vazio;
  - `cache: "no-store"`;
  - erro com `status`, `message` (o `erro` do servidor) e `dados`;
  - erro de rede marcado como "servidor fora do ar".

  Um arquivo por área em `src/services/api/` (`vagas`, `busca`, `config`, `ia`, `perfil`, `analises`, `curriculo`,
  `kit`, `entrevista`, `contas`), com os tipos de resposta em `src/types/api.ts`, copiados do `dash/API.md`.
- **Rationale**: fica um lugar só para as regras gerais (FR-001, FR-005), e cada história mexe só no seu arquivo.

## R5. Consulta periódica (polling)

- **Decision**: um hook `useConsulta(fn, intervaloMs, ativo)` que para com a aba escondida e consulta de novo ao
  voltar. Os intervalos são os do `dash/API.md` §1:
  - versão: 4 s;
  - busca, descrições e currículo: 2 s;
  - contas: 1,5 s, só com o diálogo aberto.

  A regra de parada de cada tarefa fica no componente dela.
- **Rationale**: igual ao dashboard atual, que já foi validado com os portais e com o servidor.

## R6. Estado global

- **Decision**: um contexto `Ferramenta` com:
  - `servidor`: `no_ar`, `fora` ou `demo`;
  - `podeAlterar`: o `pode_alterar` da última resposta que o traz, ou `false` depois de um 403 de rota [local];
  - `ia`: `{disponivel, nome, modelo, cobranca}`, de `GET /api/ia`;
  - `perfilExiste`.

  As vagas continuam no `App`, que já recarrega quando a `versao` muda.
- **Rationale**: as regras "IA só no clique", "sem IA, ir para o painel IA" e "só leitura de outro aparelho" valem em
  todas as telas (FR-004).

## R7. Escritas na mesma vaga

- **Decision**: fila por id de vaga (uma promessa encadeada por id). Depois de cada escrita, a vaga local é trocada
  pela que o servidor devolve.
- **Rationale**: `dash/API.md` §3.1. Hoje o `App` chama `patchVaga` sem fila.

## R8. Texto da internet

- **Decision**: o componente `TextoDaVaga` monta elementos React a partir de um markdown mínimo: parágrafos, quebras,
  `**negrito**`, listas com `-`/`*`, links só `http`/`https` com `target="_blank" rel="noopener noreferrer"`.
  `dangerouslySetInnerHTML` é proibido em `src/`, e a regra é conferida com grep em cada entrega. O ícone SVG dos
  portais (`/api/contas`) vira `<img src="data:image/svg+xml,...">`, que não executa script.
- **Rationale**: o React já escapa o texto; o risco está em `innerHTML`, que o dashboard antigo usa com escape à mão.

## R9. Modo demonstração

- **Decision**: o `mockData.ts` fica só para o modo demonstração, reescrito no formato de `src/types/api.ts`, com
  nomes fictícios. Em demonstração, todos os botões que gravam ficam desligados com o aviso. Saem o
  `onboardingData.ts` e o `JobStorageService`, que fazia exportar, importar e "restaurar padrões".
- **Rationale**: FR-001, FR-002, constituição II (exemplos fictícios).

## R10. Telas que só existem na página nova

- **Decision**:
  - **Métricas e Funil** fica: só calcula a partir das vagas.
  - **Internacional** fica, com as vagas de `area` internacional, o painel de prontidão (`GET /api/analises-perfil`)
    e os filtros internacionais.
  - **Preparador de Entrevistas** passa a ser a tela da entrevista da História 5, com seletor de vaga.

  Some o que não tem fonte real: `perguntas_frequentes` e `historias_star` dentro da vaga, dicas fixas e números
  inventados.
- **Rationale**: FR-016.

## R11. Divergências entre os tipos do front e o servidor (a corrigir)

| No front hoje | No servidor (`dash/API.md`) |
|---|---|
| `Vaga` sem `origem`, `formato`, `nota_sem_descricao`, `lembretes_pendentes`, `kit`, `lembretes`, `autorizacao`, `ingles`, `contratacao`, `fuso`, `riscos`, `pede` | existem (§2) |
| `checklist: {id, texto, estado, obrigatorio, categoria}` | `{item, rotulo, origem, estado, frase, acao, extra?, base?, falta_base?}` |
| `analise_status` com `verificando` e `falha` | `pendente, feita, sem_dados, sem_analise`; "verificando" e "falha" vêm de `/api/versao` |
| `FiltrosBusca.internacional.empresas: string[]`, `analise_automatica` | `empresas: [{sistema, id, nome, url}]`; não há `analise_automatica` |
| `ConfigIA.provedor` com `claude` e `ollama`, `chave_api` | ids `claude_code, anthropic, openai, openrouter, groq, deepseek, gemini, compativel, nenhum`; a chave nunca volta |
| `PerfilUsuario` (nome, anos de experiência, pretensão salarial…) | o perfil é o `perfil.md` montado pelos primeiros passos (§3.6) |
| `PortalConectado.id` com `linkedin` | só `gupy` e `indeed` |

## R12. A troca (História 7)

- **Decision**:
  - `dash/servidor.py`: `/` e `/index.html` passam a entregar `dash/front/index.html`, e os arquivos do front saem da
    raiz (`/assets/...`, `/favicon.svg`), com a mesma checagem de pasta e tipo de hoje;
  - `/novo` e `/novo/...` respondem 308 para `/` (ou para o mesmo arquivo na raiz);
  - sem build, `/` mostra o aviso de front não montado;
  - sai a constante `PAGINA` e o `dash/dashboard.html`.

  Também são ajustados:
  - `tests/test_front_estatico.py`;
  - `README.md`, `dash/README.md`, `dash/API.md` (§1 e §3.12), `AGENTS.md`;
  - `.agents/skills/buscar-vagas/SKILL.md` e a cópia com `sincronizar_skills.py`;
  - `.vscode/settings.json` (Live Server em `dash/front/index.html`);
  - o docstring do servidor e o `front.yml` (texto do PR).
- **Rationale**: o build usa caminhos relativos (`./assets/...`), então funciona na raiz e no Live Server sem
  mudança. `iniciar.py` e `abrir-dashboard.*` já abrem `http://127.0.0.1:8765` e não mudam.
