# Research: Aba Internacional com o layout do Relatório de Vagas

**Date**: 2026-11-02 | **Spec**: [spec.md](spec.md)

Não há NEEDS CLARIFICATION: as duas decisões da pessoa estão em Clarifications da spec. Esta pesquisa registra o que
o código de hoje dá e as decisões do desenho.

## O que o código já dá

- `TriageReport.tsx` (Relatório de Vagas) já faz tudo o que a spec pede para as vagas do Brasil:
  - as abas internas e os contadores;
  - a busca, Ordenar e os filtros (com a regra da spec 038);
  - Baixa aderência e Marcar todas;
  - o cartão completo e o Forçar verificar.

  Ele recebe as vagas prontas por `props` e não sabe de que área elas são.
- `App.tsx` já separa as listas: `vagasRelatorio` (nacional) vai para o `TriageReport` e `vagasInternacional` para o
  `InternationalHub`. Os botões gravam pelos mesmos `handle…` do App, para as duas áreas:
  - `handleSeguirVaga`, `handleNaoSeguirVaga` e `handleVoltarTriagem`;
  - `handleMarcarTodasNaoSeguidas`, que recebe só os ids;
  - `handleForcarVerificar`.
- `InternationalHub.tsx` só é usado pelo App. Tudo o que ele tem de próprio está nele:
  - os filtros de moeda e visto (regras na própria lista);
  - a contagem do banner;
  - no cartão, o país (`paisDe`), a contratação (`CONTRATACAO`) e os sinais;
  - os botões de filtros e prontidão (por `props`).
- `ScreenPreferencesService` guarda os filtros do Relatório numa chave só (`mpt_pref_triage_filtros`).
- O aviso de "busca internacional desligada" e o `painelBusca` ficam no App, acima do componente da aba, e não mudam.

## Decisões

### D1. Um componente para as duas abas

- **Decision**: o `TriageReport` ganha a prop `area: "nacional" | "internacional"` (padrão `"nacional"`). Com
  `"internacional"`:
  - a linha compacta no topo;
  - os filtros de moeda e visto;
  - os botões Filtros da busca internacional e Prontidão internacional;
  - os extras do cartão;
  - as preferências na chave própria.

  O App passa a usar o `TriageReport` nas duas abas, e o `InternationalHub.tsx` é apagado.
- **Rationale**: a spec pede o "mesmo layout". Com um componente só, uma melhoria futura no Relatório vale para as duas
  abas, e elas não se separam de novo, que é a causa do problema de hoje.
- **Alternatives considered**:
  - copiar o `TriageReport` para o `InternationalHub`: duplica mais de 800 linhas, que voltariam a divergir;
  - extrair cartão, barra e lista em componentes compartilhados: mexe mais no Relatório nacional sem ganho para a
    pessoa (spec, fora do escopo).

### D2. Preferências da Internacional numa chave própria

- **Decision**:
  - `getTriagePreferences(area)` e `saveTriagePreferences(prefs, area)` leem e gravam em
    `mpt_pref_internacional_filtros` quando a área é a internacional;
  - a nacional continua em `mpt_pref_triage_filtros`, como hoje;
  - `ScreenPreferences` ganha `moeda?: "todas" | "usd" | "eur"` e `visto?: boolean`.

  Valor inválido ou ausente volta ao padrão (Maior aderência, sem filtros). O acesso ao armazenamento já está em
  `try/catch`.
- **Rationale**: FR-010 e FR-011. A chave nacional não muda, então quem já usa não perde os filtros do Relatório.
- **Alternatives considered**: uma chave só com um objeto por área (mudaria o formato da chave de hoje).

### D3. Moeda e visto valem para todas as vagas

- **Decision**: na função de filtro, os testes de moeda e visto vêm **antes** da regra da spec 038 ("vaga sem nota
  aparece sempre"). As regras são as de hoje:
  - **Dólar**: o salário cita "usd" ou "$";
  - **Euro**: o salário cita "eur" ou "€";
  - **Visto**: algum sinal fala de "visto" ou "relocation".

  `filtrando` e Limpar filtros incluem os dois.
- **Rationale**: FR-004 e o caso de borda da spec. Os dois filtros não dependem da análise da IA, então a regra da 038
  (que existe porque os outros filtros dependiam da nota) não se aplica a eles.

### D4. Busca no texto inclui local e país na Internacional

- **Decision**: com `area="internacional"`, a busca também procura em `local` e em `paisDe(v)`. A nacional continua
  como está.
- **Rationale**: FR-002. Mantém a busca por país que a Internacional tem hoje, sem mudar a nacional.

### D5. Linha compacta

- **Decision**: no topo do componente, só na Internacional, uma linha com o ícone de globo e três números sobre
  `lista`, a lista filtrada da aba interna ativa (com as de Baixa aderência, mesmo recolhidas):
  - "N vagas";
  - "N remotas", com `modoFiltro(v) === "remoto"`, o mesmo critério do filtro Modo;
  - "N com visto ou relocation", com a regra de D3.
- **Rationale**: FR-008. Contar com o mesmo critério do filtro Modo faz o número bater com o que a pessoa vê ao filtrar
  por Remoto. O banner de hoje usava só a marcação do portal (`remoto`), que a análise pode corrigir.

### D6. Extras do cartão internacional

- **Decision**: com `area="internacional"`, o cartão ganha uma linha abaixo de empresa, local e salário com:
  - a etiqueta do país (`paisDe(v)` ou "Global");
  - "Contratação: …" (`CONTRATACAO`, ou "não informada");
  - os sinais, com o ícone de escudo, como hoje.

  O resto do cartão é o do Relatório. O botão Aplicar sai, e fica o Abrir a vaga (spec, Assumptions).
- **Rationale**: FR-007 e US2 3. Na nacional, o cartão não muda.

### D7. Barra de filtros

- **Decision**: na Internacional, a segunda linha da barra ganha dois grupos depois de Senioridade e Modo:
  - "Moeda:" com Todas, Dólar e Euro, um botão de cada vez, `aria-pressed`;
  - o botão "Visto / relocation", com `aria-pressed`.

  Os botões Filtros da busca internacional e Prontidão internacional ficam na primeira linha, ao lado de Ordenar. O
  placeholder da busca passa a ser "Filtrar por cargo, empresa, país ou habilidades...".
- **Rationale**: FR-004 e FR-009, no mesmo estilo dos filtros do Relatório.

### D8. Textos de lista vazia

- **Decision**: na Internacional, Para decidir vazia diz "Nenhuma vaga de fora esperando decisão. Ligue mais fontes na
  aba Portais internacionais de Filtros da busca, ou peça uma busca." As outras abas internas e a mensagem de filtros
  ("Nenhuma vaga passa nos filtros") são as do Relatório.
- **Rationale**: a mensagem de hoje ("Ative mais fontes internacionais…") cita o caminho que mudou na spec 043.

### D9. Conferência

- **Decision**:
  - `tsc --noEmit` e `vite build`;
  - `python -m unittest` (sem mudança no Python, só para garantir a master);
  - a conferência por CDP com o Edge sem janela, como na spec 043. Ela só lê o DOM, troca as abas internas, a ordem e
    os filtros, e nunca clica em botão que grava (Seguir, Não seguir, Voltar, Marcar todas, Forçar verificar);
  - o teste da pessoa na branch pessoal.
- **Rationale**: a mudança é só de tela; o Python não muda.
