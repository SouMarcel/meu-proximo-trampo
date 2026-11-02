# Research: Abas no painel Filtros da busca

Pesquisa de 2026-11-02, só no código: `SearchFiltersModal.tsx` e `App.tsx` na `frontend-react`, `filtros.py`,
`dash/API.md`, `docs/novo-portal.md` e `specs/lista-de-desejos.md` na `master`. Nenhum pedido a portal.

## O que o código já dá

- O painel é um formulário só (`<form>` com o estado `d` dos filtros), e a gravação é uma só (`PUT /api/config` com o
  objeto inteiro). Pôr as seções em abas não muda o estado nem a gravação: basta mostrar uma parte por vez.
- `App.tsx` monta `<SearchFiltersModal modo={filtrosModo} …>` enquanto `filtrosModo` não é nulo. Trocar entre
  `nacional` e `internacional` muda só a prop, e o componente continua montado, com o estado. Fechar desmonta.
  Por isso o estado da aba dentro do componente cumpre o FR-002 (reabrir volta à Geral) e o FR-011 (ir ao painel
  internacional e voltar mantém o editado e a aba), sem mudar o `App.tsx`.
- As abas do detalhe da vaga (`JobDetailModal.tsx`, `abaBotao`) dão o visual: borda de baixo índigo na ativa,
  `overflow-x-auto` e `whitespace-nowrap`. Elas não têm `role="tab"`.
- Os avisos de filtros sugeridos e de primeira vez já ficam fora das seções. A mensagem de erro fica no fim da área
  que rola.

## Decisões

### D1. A lista de próximos fica em `filtros.py`

- **Decisão**: uma constante `PORTAIS_A_MAPEAR` em `filtros.py`, ao lado de `FONTES_NAC`, enviada em
  `opcoes()["portais_a_mapear"]` (GET /api/config).
- **Por quê**: o roteiro de portal novo já mexe em `filtros.py` (`FONTES_NAC`, `FONTES_PADRAO`). Tirar da lista o
  portal que entra fica no mesmo passo, e um teste confere isso (D2). A página só mostra o que o servidor manda.
- **Alternativas**:
  - ler `specs/lista-de-desejos.md`: texto livre, quebra com qualquer edição, e a pasta `specs/` não é da ferramenta
    em uso;
  - lista fixa no front: duas fontes de verdade, e o roteiro de portal novo teria de lembrar da `frontend-react`.

### D2. Teste de guarda da lista

- **Decisão**: `tests/test_abas_filtros.py` confere:
  - `opcoes()` traz `portais_a_mapear`;
  - cada item tem `nome`, e `situacao` vale `em_estudo` ou `nao_deu`;
  - todo item `nao_deu` tem `motivo`;
  - nenhum nome da lista coincide (sem acento e sem diferença de maiúsculas) com um rótulo de `FONTES_NAC`,
    `FONTES_LOGIN` ou `FONTES_INT`.
- **Por quê**: o último teste falha quando um portal entra na busca e continua na lista (FR-013).
- **Alternativa**: conferir o conteúdo exato (InHire, Catho, Glassdoor). Quebraria a cada atualização da lista. O
  conteúdo da entrega é conferido no quickstart (SC-005).

### D3. Conteúdo da lista na entrega

| Nome | Situação | Motivo |
|---|---|---|
| InHire | em estudo | — |
| Catho | em estudo | — |
| Glassdoor | não deu | "Recusou acesso automatizado em 23/10/2026, e a API de parceiros não está aberta." |

Fonte: `specs/lista-de-desejos.md` ("Mais portais do Brasil" e "Faixa salarial → Glassdoor"). Só fatos registrados,
sem previsão de data (constituição IV).

### D4. Abas no front

- **Decisão**:
  - o estado `aba` (`"geral" | "portais" | "internacionais" | "empresas"`) fica no `SearchFiltersModal` e começa em
    `"geral"`;
  - as abas aparecem só no modo nacional, numa faixa fixa entre o cabeçalho e a área que rola, como no detalhe da vaga;
  - cada seção de hoje vai para a sua aba sem mudar o texto, com duas exceções:
    - o título "Portais" vira "Portais da busca";
    - na aba de empresas, "Empresas que você acompanha" vem antes de "Empresas a excluir".
- **Ida e volta com o painel internacional**: `irPara(aba)` faz `setAba(aba)` e depois `onTrocarModo("nacional")`.
  O link "Filtros da busca" do painel internacional só troca o modo e mantém a aba de onde a pessoa saiu (FR-011).
- **Alternativa**: guardar a aba no `App.tsx` ou no `localStorage`. Não é preciso: a spec quer abrir sempre na Geral.

### D5. Acessibilidade das abas

- **Decisão**: o padrão de abas do WAI-ARIA:
  - `role="tablist"` com `aria-label="Grupos de filtros"`;
  - cada botão com `role="tab"`, `aria-selected`, `aria-controls` e `tabIndex` 0 na ativa e -1 nas outras;
  - as setas ← e → e as teclas Home e End trocam de aba e levam o foco;
  - a área da aba com `role="tabpanel"` e `aria-labelledby`.
- **Por quê**: FR-015. Com `role="tab"`, o leitor de tela anuncia "use as setas", e por isso as setas precisam
  funcionar.
- **Alternativa**: botões com `aria-pressed`, como no `InterviewCoach`. Funciona pelo teclado, mas o leitor de tela
  não diz que são abas.

### D6. Contadores

- **Decisão**: o número aparece numa pílula depois do nome da aba e é calculado do formulário, antes de salvar:
  - **Portais**: os nomes de `d.fontes` que estão em `opcoes.fontes_nac` ou `opcoes.fontes_login`;
  - **Portais internacionais**: os de `d.internacional.fontes` que estão em `opcoes.fontes_int`;
  - **Empresas acompanhadas/excluídas**: `d.empresas.length + d.empresas_excluir.length`.

  Nome desconhecido, de um config antigo, não conta. Para o leitor de tela, a pílula tem o texto completo (ex.: "6
  ligados", "3 empresas").
- **Por quê**: FR-014. A pessoa vê sem abrir a aba, inclusive o zero.

### D7. Erro no rodapé

- **Decisão**: a mensagem de erro (leitura ou gravação) sai do fim da área que rola e vai para o rodapé, acima da
  conta de consultas.
- **Por quê**: FR-009. Com as abas, o erro precisa ficar à vista em qualquer aba, sem rolar. Por exemplo, "marque
  pelo menos um portal" aparece mesmo com a pessoa na Geral.

### D8. Aba Portais internacionais

- **Decisão**: a seção "Fontes do exterior" sai do painel internacional e vai para a aba, com o texto de hoje.
  - Com `d.internacional.ativo` falso, um aviso âmbar no topo da aba: "A busca internacional está desligada: estas
    fontes só rodam com ela ligada." O link "Ligar em Filtros da busca internacional" chama
    `onTrocarModo("internacional")`.
  - Marcar continua possível.
  - O texto do fim do painel internacional passa a ser: "Cargos, portais e localidade ficam em Filtros da busca; as
    fontes do exterior, na aba Portais internacionais", com dois links.

### D9. Compatibilidade

- Página nova com um servidor antigo: `portais_a_mapear` é opcional no tipo `Opcoes`. Sem ele, o bloco não aparece.
- Servidor novo com uma página antiga: o campo a mais é ignorado.
- O `config.json` e a busca não mudam (FR-016).

### D10. Textos de ajuda e documentos (FR-017)

- `dash/API.md` §3.4: `opcoes.portais_a_mapear` e as abas do painel.
- `dash/README.md`: o painel com as quatro abas.
- `.agents/skills/buscar-vagas/SKILL.md`, depois `python sincronizar_skills.py`. Os caminhos ficam:
  - "Filtros da busca → aba Portais";
  - "aba Portais → Portais com login";
  - "aba Empresas acompanhadas/excluídas";
  - "aba Portais internacionais".
- `docs/novo-portal.md`, na tabela de arquivos (`filtros.py`): tirar o portal de `PORTAIS_A_MAPEAR` quando ele entra.
  Na pesquisa que barra um portal, registrá-lo como `nao_deu`, com o motivo.
- `specs/lista-de-desejos.md`: a lista do painel (`filtros.PORTAIS_A_MAPEAR`) acompanha "Mais portais do Brasil".

### D11. Onde mexer no front

- **Decisão**: a worktree da `frontend-react` que já existe, ao lado da pasta do projeto.
  - Ela está na `frontend-react`, igual à do GitHub, sem mudanças e com o `node_modules` instalado.
  - O commit fica local até o OK da pessoa.
- **Por quê**: economia (constituição, "Economia"). Não é preciso uma worktree nova nem instalar de novo.
