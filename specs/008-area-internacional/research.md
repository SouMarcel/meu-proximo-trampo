# Research: Área de vagas internacionais

## 1. Área da vaga (nacional ou internacional)

- **Decision**: campos novos na vaga `area` (`nacional` | `internacional`) e `pais_vaga` (país em
  português, ou região: "mundo todo", "América Latina", "Europa"…). Calculados ao gravar: consulta do
  grupo `internacional:<país>` → internacional com aquele país; senão, local reconhecido fora do país
  da pessoa (`filtros.pais_do_local`) → internacional; senão nacional. Vagas antigas sem `area`: a
  página e o servidor deduzem pelo mesmo critério (grupo da consulta), sem migração.
- "Nacional" é o país da pessoa (`localidade.pais`, padrão Brasil): a aba mostra o nome do país; a
  ferramenta continua servindo a quem mora em outro país.
- **Vaga de fora mesmo sem a busca ligada** (ex.: startup.jobs, link colado): vai para a aba
  Internacional, com a etiqueta. Para quem não usa nada disso, nada muda (FR-013).

## 2. Configuração

- **Decision**: `internacional` (objeto que já existe) ganha: `regioes` (`brasil`, `latam`,
  `americas`, `mundo`), `salario_min_anual_usd` (número ou 0), `fuso_horas` (0–12, horas de
  sobreposição aceitas; 0 = não informado), `contratacao` (`contractor`, `eor`, `pj`, `clt`),
  `aceita_mudar` + `paises_mudanca`, `passaporte`, `autorizacao_trabalho` (países), `precisa_sponsor`.
  Topo: `idiomas_aceitos` (`pt`, `en`, `es`, `fr`, `de`, `it`; vazio = todos). Validação em
  `filtros.validar` (formato antigo continua lido por `efetivos`). `moedas_aceitas` continua no topo
  (já valia para vaga de fora).
- `ativo` deixa de exigir `modelos.remoto` (FR-006); exige países e cargos.

## 3. Consultas por área

- **Decision**: cada consulta ganha `area`. A internacional roda com remoto em cada país de interesse;
  com `aceita_mudar`, roda também sem o filtro de remoto em cada país de `paises_mudanca` (ou dos
  países de interesse, se a lista estiver vazia). Fontes ganham `AREAS` (Indeed: nacional e
  internacional; Gupy: nacional; startup.jobs: nacional e internacional, como hoje); `vagas.executar`
  pula a fonte nas consultas de área que ela não atende (FR-011, SC-004). Sem `AREAS`, vale para as
  duas (fontes futuras).

## 4. Idioma da vaga

- **Decision**: `filtros.idioma_da_vaga(v)`: campo do portal (`idioma`/`lang`) se houver; senão,
  contagem de palavras comuns de PT, EN, ES, FR, DE e IT no título + descrição; só decide com pelo
  menos 25 palavras reconhecidas e o primeiro com folga de 1,5× sobre o segundo; senão, `None` (não
  corta). Com IA, a análise devolve `idioma` (2 letras), validado por `banco.validar_analise`, e ele
  vale mais que a detecção. `criterios()` corta quando `idiomas_aceitos` não está vazio, o idioma é
  conhecido e não está na lista: "Vaga em espanhol; você aceita português e inglês".
- Detecção antes da IA (no `vagas.executar`, junto com empresa e senioridade) e de novo depois da
  análise (como já acontece com os outros critérios).

## 5. Moeda e salário

- **Decision**: moeda: regra que já existe (`moedas_aceitas`). Salário: `filtros.salario_anual_usd(v)`
  lê o texto de salário do portal (números, "k", período: ano, mês ×12, hora ×2080) quando a moeda é
  USD; vaga internacional com o máximo abaixo de `salario_min_anual_usd` → Fora dos critérios. Sem
  número ou em outra moeda: não corta. Sem câmbio.

## 6. Análise com IA

- **Decision**: `criterios_extra(f)` ganha, com a busca internacional ligada, uma linha com regiões,
  contratação, fuso e as caixas (passaporte, autorização nos países, precisa de sponsor, aceita mudar
  para os países), para a análise apontar nos alertas (FR-010); e a linha de idiomas aceitos. A skill
  `buscar-vagas` (que dá as regras de nota usadas pela análise automática) ganha o campo `idioma` e a
  instrução de alertar sobre autorização/sponsor/fuso nas vagas internacionais.

## 7. Página

- **Abas**: Quadro, Relatório de Vagas (`nacional`), **Internacional** (`internacional`). O relatório
  é o mesmo componente, filtrado por área; a aba Internacional mostra, sem busca ligada e sem vagas,
  a explicação e o botão "Filtros da busca internacional".
- **Painel Filtros da busca internacional** (`dlg-filtros-int`): ligar, países (lista com busca como
  hoje), cargos em inglês, regiões, moedas, salário mínimo anual (USD), fuso, contratação e as caixas;
  grava pelo `PUT /api/config` existente (mesmo `config.json`). O trecho "também vagas remotas no
  exterior" sai do painel de filtros nacional, que ganha "Idiomas aceitos".
- **Etiqueta** `Internacional · país · moeda` (`intTag(v)`) em `relItemHTML`, `cardHTML`,
  `renderLista`, `renderDetalhe` e no aviso de vaga repetida do Adicionar Vaga.
- **Quadro**: filtro por área (todas, nacional, internacional), lembrado como os outros filtros.
- **Adicionar Vaga**: campo Área (nacional/internacional) com palpite pelo local lido do link
  (`filtros.pais_do_local`), editável; grava `area` e `pais_vaga`.

## 8. Testes

- `tests/test_internacional.py`: validação dos filtros novos e formato antigo; consultas (internacional
  sem remoto nacional, aceita mudar, `area`); fontes por área com fonte falsa; área e país ao gravar;
  idioma (PT, EN, ES, curto → None) e corte; salário anual; `pais_do_local`; SC-002 pela saída de
  referência do `vagas.py` (a mesma da spec 005) com a internacional desligada e sem idiomas.
