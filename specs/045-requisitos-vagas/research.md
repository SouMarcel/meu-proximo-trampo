# Research: O que as vagas pedem, no painel Métricas & Funil

Decisões do plano, com o motivo e o que ficou de fora.

## D1. De onde vêm os requisitos

- **Decisão:** em dois caminhos, com as mesmas regras.
  - **Na análise:** a análise da IA da página e a do assistente no chat devolvem também o objeto `requisitos`, na mesma
    chamada da nota. Isso vale para as vagas analisadas a partir de agora e para as reanalisadas (Forçar verificar,
    descrição que chegou depois).
  - **Na leitura avulsa:** para as vagas já analisadas, a leitura pede à IA só os requisitos, com um pedido próprio e
    mais curto. Ela grava só o campo `requisitos`.
- **Motivo:**
  - os requisitos saem do mesmo texto que a nota já lê, então na análise eles custam só um pouco mais de resposta;
  - na leitura avulsa, a nota fica intacta (spec FR-005).
- **Alternativas descartadas:**
  - **Reanalisar as vagas antigas:** mudaria notas que a pessoa já viu e decidiu.
  - **Regras sem IA:** a pessoa escolheu a IA. Por regras, só se acham as habilidades que já estão no perfil.

## D2. A forma do campo e a validação

- **Decisão:** o campo `requisitos` vai no documento da vaga (data-model). A validação é tolerante: corta o que não
  vale e grava o resto, sem derrubar a análise inteira.
- **Garantia do FR-002, sem depender só da IA:** a validação tira das habilidades e das certificações:
  - os nomes que começam por tempo ou por experiência ("5 anos", "anos de", "experiência", "vivência", "conhecimento
    em", "years", "experience");
  - os nomes de idioma ("Inglês", "English", "Espanhol"), que vão em `idiomas`.
- **Motivo:** a resposta da IA pode vir com um item fora do formato. Uma habilidade estranha não pode custar a nota da
  vaga, e o SC-002 passa a valer por construção.
- **Alternativa descartada:** rejeitar a análise inteira, como faz o `validar_analise` com campos obrigatórios. Seria
  rígido demais para uma lista longa e opcional.

## D3. Uma regra só, na skill

- **Decisão:** as regras dos requisitos ficam na skill `buscar-vagas`, no passo 3, num item `requisitos` entre os campos
  da análise. Os dois pedidos usam a mesma fonte:
  - a análise da página já copia o trecho que vai de `modelo_trabalho` até "4. **Gravar.**" (`analise._secao`), então
    pega as regras novas sem mudança;
  - a leitura avulsa copia só o item `requisitos` (`_secao` do início do item até o próximo campo).

  A linha de formato do pedido (`analise.montar_pedido`) ganha `"requisitos" {…}` entre os opcionais.
- **Motivo:** página e chat seguem a mesma regra, e mudar a regra é mudar um lugar só. As skills já são a fonte das
  regras da nota.

## D4. A leitura avulsa em segundo plano

- **Decisão:** uma classe `Leitura` em `dash/requisitos.py`, no molde da `Fila` da análise:
  - **Vagas:** a seleção que a pessoa vê no painel (Em Aplicações ou Todas as vagas analisadas, mais a área). Entra a
    vaga com `analise_status` "feita", texto do anúncio, sem `descricao_pendente` e sem `requisitos`.
  - **Lotes:** de `analise.LOTE` vagas, separados por `analise.lotes()`. A vaga com o texto suspeito (spec 034) vai num
    lote só dela, e o texto passa por `integridade.limpar`.
  - **O que vai à IA:** só o cargo, a empresa e o texto do anúncio, mais os nomes da lista de habilidades e
    certificações do perfil (FR-006).
  - **Andamento:** guarda lidas, total, rodando, parado e erro. A página lê esse estado em `GET /api/requisitos`.
  - **Parar:** a marca é conferida entre um lote e outro, e o lote em andamento termina.
  - **Falha:** a leitura para e guarda o motivo, já mascarado, como a `Fila` (`ia.mascarar`). O que foi lido fica
    gravado.
  - **Retomar:** cada clique recalcula as vagas sem `requisitos`, então nenhuma é lida duas vezes. A vaga que a IA não
    devolveu fica para o próximo clique.
  - **Com a análise automática rodando:** a leitura espera ela terminar antes do próximo lote, para não fazer dois
    pedidos à mesma IA ao mesmo tempo.
  - **Gravação:** com `banco.aplicar_requisitos`, que só troca `requisitos` e `atualizada_em`.
- **Motivo:** algumas centenas de vagas levam vários minutos. A página não pode ficar presa num pedido só, e a IA gratuita
  pode parar no meio.
- **Alternativa descartada:** a página mandar um lote por vez e esperar cada resposta. A leitura dependeria da aba
  aberta e ficaria espalhada entre o front e o servidor.

## D5. As contas no servidor, uma vez só

- **Decisão:** `requisitos.resumo(vagas, perfil, selecao)` monta tudo o que a seção mostra: as contagens, as listas, as
  faixas, os indicadores e o quadro Suas habilidades, com os ids das vagas de cada item.
  - A página pede `GET /api/requisitos?vagas=…&area=…`.
  - O comando `PY dash/requisitos.py resumo` imprime o mesmo resumo.
- **Motivo:**
  - o SC-005 pede o mesmo número na página e no terminal, e uma implementação só garante isso;
  - a comparação com o perfil usa o `conferir.norm` e o `conferir._contem` (D7), que já estão em Python;
  - os testes ficam no `unittest`.
- **Alternativa descartada:** contar no front com a lista de vagas que ele já tem. Seriam duas implementações, que
  poderiam divergir, e o front teria de receber o perfil.

## D6. A seleção

- **Em Aplicações:** a regra do front (`noQuadro`): `etapa` preenchida e (`origem` "manual" ou `triagem` "seguir").
  Inclui Encerrada.
- **Todas as vagas analisadas:** `analise_status` "feita", de qualquer triagem (Para decidir, Seguidas, Não seguidas,
  Fora dos critérios).
- **Área:** a regra do front (`areaDe`):
  - vale a `area` gravada;
  - sem ela, a vaga é internacional quando todos os `grupos` são `internacional:` ou `mudanca:`;
  - nos outros casos, é nacional.

  O `filtros.area_da_vaga` não serve aqui porque também olha o local, e o painel precisa contar como as listas de
  vagas mostram.
- **Bases das contagens:** cada bloco diz em quantas vagas se apoia.
  - Habilidades, certificações, tempo de experiência e formação contam as vagas com `requisitos`.
  - Senioridade, modelo e contratação contam as vagas da seleção com análise feita.
  - Idiomas conta as vagas com `requisitos` ou com o nível de inglês da análise (FR-013).

## D7. Juntar nomes e comparar com o perfil (sem IA)

- **A mesma habilidade:** a chave é o nome pelo `conferir.norm` (minúsculas, sem acento), sem espaços e sem pontuação,
  mas mantendo `+` e `#`. Assim "Power BI", "PowerBI" e "power bi" dão a mesma chave, e "C#" e "C++" ficam diferentes.
  O nome mostrado é a grafia mais frequente.
- **A habilidade do perfil e a pedida são a mesma quando:**
  - a chave é igual;
  - ou o nome menor, com 3 letras ou mais, está inteiro, em palavras completas, dentro do outro (`conferir._contem`).
    O mínimo de 3 letras evita que "C" combine com "C#" ou "R" com "R&D";

  Os grupos de `conferir.FAMILIAS` ficam de fora. Eles juntam ferramentas parecidas (Jira e Trello, Power BI e
  Looker, SQL e MySQL), que servem para a conferência do currículo apontar um equivalente, mas não para dizer "nas
  suas habilidades" (princípio IV).
- **Nomes do perfil com barra** ("Python/Pandas", "SQL/MySQL"): cada parte vale como um nome para comparar, e o quadro
  mostra a linha como está no perfil.
- **"Citada no seu perfil":** o nome pedido, com 3 letras ou mais, aparece em palavras completas no texto do perfil com
  os relatos (`analise_perfil.perfil_texto`), fora das seções de habilidades e certificações.
- **Motivo:** é uma regra que se explica e se testa, sem custo de IA. O FR-003 (a IA usa o nome do perfil quando é a
  mesma habilidade) cobre boa parte das grafias diferentes.

## D8. As habilidades e certificações do perfil

- **As seções:** títulos de nível 2 que começam com "Habilidades", "Competências" ou "Skills" (habilidades) e com
  "Certificações", "Cursos" ou "Certifications" (certificações).
- **Linhas lidas:** só as de lista (`-`, `*`, `•`). Cada linha é lida assim:
  - "Rótulo: a, b, c" (dois-pontos e vírgulas, como "Stack geral: Jira, Confluence") dá um item por nome da lista,
    sem nível;
  - "Nome — nível" (travessão, meia-risca ou " - ") dá o nome e o nível, cortado em 80 caracteres;
  - "Nome (detalhe)" dá o nome, e o detalhe vira o nível. Isso vale para certificações como "PSM I (em preparação)";
  - a linha de exemplo do modelo (com "ex.:") é ignorada.
- **Motivo:** cobre o modelo do `perfil.exemplo.md` e os formatos que a ferramenta grava (spec 001 e spec 035), sem
  pedir à pessoa que reescreva o perfil.

## D9. O tempo de experiência, a formação e os idiomas

- **Tempo:** `experiencia.anos` é o mínimo inteiro de anos na atividade principal do cargo. As faixas são até 1 ano,
  2 a 3 anos, 4 a 5 anos, 6 a 9 anos e 10 anos ou mais. Sem número, ou sem o campo, a vaga entra em Não diz.
- **Formação:** `formacao.nivel` é o mínimo pedido: `tecnico`, `graduacao`, `pos` (pós ou MBA), `mestrado` ou
  `doutorado`. Sem o campo, a vaga entra em Não diz. As `areas` são contadas como as habilidades (D7, sem o perfil).
- **Idiomas:** cada idioma tem o nome em português e o nível na mesma escala do campo `ingles` (`basico`,
  `intermediario`, `fluente`, `nativo`; "avançado" conta como `fluente`). Na vaga sem `requisitos`, o inglês conta
  pelo campo `ingles` da análise (o `nao_pede` não conta).
- **Contratação:** junta `tipo_emprego` e `contratacao`, cada valor uma vez por vaga, com os rótulos de `kit.py`. Os
  dois "CLT" (`tempo_integral` e `clt`) viram um só, e os dois "PJ" também.

## D10. A página

- **Componente:** um novo, `src/components/RequisitosVagas.tsx`, dentro do `FunnelAnalytics`. Ele fica depois do funil
  e substitui o quadro antigo (FR-022). A Distribuição por plataforma vai para o fim, na largura toda.
- **Dados:**
  - `src/services/api/requisitos.ts`, com `resumo`, `ler` e `parar`;
  - o resumo é pedido de novo quando a seleção muda e quando a `versao` do banco muda;
  - durante a leitura, o resumo é pedido a cada 3 s.
- **Seletor:** dois grupos de botões (Vagas e Área), guardados em `mpt_pref_metricas_requisitos` (`storage.ts`).
- **Listas:** barras no estilo da Distribuição por plataforma. Cada item tem o nome, "N de M (x%)", "exigida em K" e a
  etiqueta do perfil. Clicar abre, logo abaixo, a lista das vagas (cargo · empresa), e clicar numa vaga chama
  `onSelectVaga`, que abre o detalhe como nas outras abas.
- **Props novas do `FunnelAnalytics`:** `versao`, `onSelectVaga`, `onAbrirIA` e `onAbrirPerfil`, passadas pelo App.
- **Largura:** uma coluna no celular, duas ou três no computador, e nomes longos quebram a linha (SC-007).

## D11. Chat e terminal

- **Comandos do `dash/requisitos.py`:**
  - `resumo [--vagas aplicacoes|todas] [--area todas|nacional|internacional] [--json]`: o resumo em texto (ou em JSON);
  - `pendentes [mesma seleção] [--limite N]`: em JSON, as vagas da seleção sem `requisitos`, com o texto já limpo e a
    marca `atencao` da integridade, para o assistente ler;
  - `gravar <arquivo.json>`: grava `[{"id", "requisitos"}]` pelo mesmo `banco.aplicar_requisitos`, sem mexer na nota.
- **Skill `buscar-vagas`:** o item `requisitos` nos campos (D3), um fluxo curto "ler os requisitos das vagas já
  analisadas" com esses comandos, e a pergunta "o que as vagas pedem?" respondida pelo `resumo`.
- **`AGENTS.md`:** os comandos novos na lista de comandos.

## D12. Conferência

- **`unittest`:** em `tests/test_requisitos.py`, com banco temporário e IA falsa, no molde de `test_forcar.py`:
  - a validação e o FR-002;
  - as chaves e a comparação com o perfil;
  - a leitura do perfil;
  - a seleção e as faixas;
  - o resumo;
  - `aplicar_requisitos` sem mexer na nota;
  - a análise que grava `requisitos`;
  - a `Leitura`: lotes, parar, falha, retomar e a vaga suspeita sozinha;
  - as rotas;
  - o comando do terminal.
- **Front:** `tsc --noEmit` e `vite build`.
- **CDP sem janela:** só leituras e trocas no seletor. Nunca clica em Ler os requisitos, que gasta a IA e grava nas
  vagas da pessoa: essa parte é dela, no teste.
- **Na branch pessoal:** o roteiro do quickstart.
