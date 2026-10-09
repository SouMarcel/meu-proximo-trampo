# dash: Acompanhamento de Candidaturas

App local (Python, só biblioteca padrão) que mostra as vagas e o funil de candidaturas.

```
python dash/servidor.py            # abre http://127.0.0.1:8765
python dash/servidor.py --rede     # também acessível de outros aparelhos da sua rede (ex.: celular no Wi-Fi)
```

No Windows dá para dar dois cliques em `abrir-dashboard.bat`; no macOS/Linux, `./dash/abrir-dashboard.sh`.
No VS Code, a tarefa **Dashboard** sobe o servidor ao abrir a pasta, e a página também abre pela
extensão Live Server (`dash/dashboard.html`): aberta assim, ela fala com o servidor em
`127.0.0.1:8765`, que aceita páginas abertas neste computador (`127.0.0.1`/`localhost` em outra
porta) e continua recusando outros sites. O servidor precisa estar no ar: sozinho, o Live Server
só entrega o arquivo.

- **Quadro:** kanban Salva → Aplicação Enviada → Entrevista → Proposta Recebida →
  Encerrada (arraste os cartões ou use o menu ⋯), com anotações, resultado (não
  aprovado, desisti, vaga cancelada, contratado), filtro por plataforma e visão em
  lista.
- **Adicionar Vaga:** cole o link. O servidor lê a vaga (Indeed e LinkedIn pelas APIs
  públicas; Gupy pelo MCP público de candidatos dela; startup.jobs pelo MCP público do
  site; outros sites pelos dados
  estruturados JobPosting da página), grava no Relatório de Vagas e, se houver uma IA ligada
  (botão **IA**), pede a análise em segundo plano (`analise.py`). Se a vaga já está
  no dashboard, mesmo vinda de outro portal (link igual ao de candidatura de um cartão,
  ou mesmo cargo e empresa encontrados nos últimos 60 dias), avisa onde ela está e não
  duplica. Se não der para ler, o formulário abre com o que deu, para completar; dali
  dá para mandar para o relatório ou direto para o quadro.
- **Relatório de Vagas:** o que as buscas trouxeram, em quatro abas: Para decidir,
  Seguidas, Não seguidas e **Fora dos critérios** (vagas que furaram os filtros da
  busca, com o motivo). "Seguir com a vaga" manda para a coluna Salva, inclusive a
  partir de Fora dos critérios; "Não seguir" marca como visitada e a vaga não volta nas
  próximas buscas. Vagas com nota abaixo de 50 ficam recolhidas. Ordem por aderência
  (padrão), plataforma, modo de trabalho ou data de publicação; no empate, maior nota
  primeiro. Filtros por senioridade, modo de trabalho, aderência mínima e dias desde a
  publicação; a página lembra a ordem e os filtros escolhidos. Cada vaga mostra o termo
  de busca que a encontrou.
- **Filtros da busca** (botão no relatório): cargos, localidade, modo de trabalho
  (remoto no país e no exterior, híbrido e presencial na cidade), data de publicação,
  tipo de emprego, senioridade, moedas aceitas para vagas de fora e empresas a excluir. Grava no `config.json` e vale a
  partir da próxima busca.

A página confere o banco a cada poucos segundos, então uma busca gravada aparece
sozinha.

## Arquivos

| Arquivo | Para quê |
|---|---|
| `servidor.py` | Servidor local: serve a página e a API (`/api/vagas`, `/api/vagas/link` para adicionar pelo link, `/api/versao` com o aviso de análise em andamento, `/api/buscas/ultima`, `/api/config` para ler e gravar os filtros da busca, `/api/ia` para a IA escolhida e `/api/perfil/…` para os primeiros passos: estado, envio e remoção de materiais, rascunho, progresso, prévia, gravação do perfil e filtros propostos; `/api/busca…` para buscar vagas pela página: plano, andamento, iniciar, cancelar e pedir a nota de novo; `/api/curriculo…` para gerar o currículo pela página: catálogo das técnicas, estado, lista, gerar e tentar de novo; e `/arquivos/curriculos/<nome>.pdf|.docx`, que serve só os arquivos dessa pasta). Só aceita pedidos da própria página; enviar arquivos, gerar o rascunho e gravar, só do próprio computador. |
| `banco.py` | Acesso ao SQLite e comandos `quadro`, `pendentes`, `analisar`, `vaga` (dados completos de uma vaga) e `anotar` (acrescenta uma linha às anotações). |
| `buscador.py` | Busca de vagas pela página: roda a mesma busca do `vagas.py` em segundo plano, com andamento, cancelamento entre consultas, uma busca por vez no computador (trava em `.cache/busca.trava`, compartilhada com o terminal) e intervalo mínimo de 30 minutos entre buscas. Com IA e perfil, as vagas novas ficam para a análise automática. |
| `gerador.py` | Currículo pela página: no clique, pede o currículo à IA escolhida (`curriculo_ia.py`, na raiz), gera os arquivos e a conferência, uma geração por vez, com andamento e "tentar de novo". |
| `analise.py` | Análise automática: manda à IA escolhida (`ia.py`, na raiz) o perfil, as regras de nota da skill e as vagas que esperam nota, em lotes de 10, e grava a resposta com o provedor e o modelo usados. Uma análise por vez; a última falha aparece na página. |
| `dashboard.html` | A página. |
| `abrir-dashboard.bat` / `.sh` | Atalhos para iniciar o servidor. |
| `dados/` | `candidaturas.db` e `backup/` (uma cópia por dia, guarda as 10 últimas). Fora do Git. |

## Dados

### Tabela `vagas` (um registro por vaga)

O ID é o do portal nas vagas da busca e nas do Indeed adicionadas pelo link (o `jk` de 16
caracteres), `gupy-…` nas da Gupy (busca e link),
`startupjobs-…` nas do startup.jobs (busca e link), `li-…` nas do LinkedIn, `web-…` nas de
outros sites e `m-…` nas preenchidas à mão.

| Campo | Valores |
|---|---|
| `origem` | `busca` (veio de `vagas.py`), `link` (Adicionar Vaga pelo link; fica no relatório como as da busca) ou `manual` (formulário, direto no quadro) |
| `plataforma` | `Indeed`, `LinkedIn`, `Gupy`, `InHire`, `Catho`, `Startup Jobs`, `Outra` |
| `outras_plataformas` | outros portais onde a mesma vaga apareceu (na mesma busca, numa busca seguinte ou pelo Adicionar Vaga). O dashboard mostra uma etiqueta por plataforma, inclusive a do link de candidatura (vaga do Indeed com candidatura na Gupy também leva a etiqueta Gupy), e o filtro de plataforma acha a vaga por qualquer uma |
| `titulo`, `empresa`, `local`, `url`, `descricao` | dados da vaga |
| `publicada_em`, `encontrada_em` | `AAAA-MM-DD` |
| `salario`, `tipo`, `remoto`, `url_candidatura` | quando o portal informa |
| `termos`, `grupos`, `ids_relacionados`, `busca_id`, `jk` | controle da busca: termos que acharam a vaga, de qual grupo de consultas veio (`remoto`, `local` = cidade, `internacional:<país>`), anúncios repetidos e ids da mesma vaga em outros portais, de qual busca veio |
| `area`, `pais_vaga` | `nacional` ou `internacional` e o país (ou região) da vaga: pela consulta que achou a vaga ou pelo local; nas vagas antigas, deduzidos pelos grupos da busca |
| `idioma` | idioma da vaga (`pt`, `en`, `es`…), detectado sem IA ou lido pela análise; base do filtro `idiomas_aceitos` |
| `restricao_local` | onde a vaga aceita candidatos, como o portal informa (ex.: `USA, Canada`, `Worldwide`); base da elegibilidade |
| `ats` | sistema de candidatura (`greenhouse`, `lever`, `ashby`), quando conhecido; o detalhe mostra o botão "Candidatar no …" |
| `autorizacao`, `contratacao[]`, `ingles`, `fuso`, `sistema_candidatura`, `pede[]`, `riscos[]` | o que a análise leu sobre a candidatura, cada um com a `frase` do anúncio (opções em `dash/kit.py`) |
| `kit` | o que a pessoa marcou no checklist: `estados` por item (`a_fazer`, `pronto`, `nao_se_aplica`), `extras` e `removidos` |
| `lembretes`, `entrevista_em` | lembretes de follow-up marcados (`feito`, `dispensado`, `parar`, valem para a etapa e a data em `base`) e a data da entrevista |
| `documentos[]` | cartas e respostas de formulário geradas pela página (`tipo`, `nome` dos arquivos em `curriculos/`) |
| `checklist`, `lembretes_pendentes` | calculados pelo servidor a cada leitura (não gravados) |
| `sinais` | sinais positivos lidos no anúncio sem IA ("Oferece patrocínio de visto", "Oferece relocation" e as suas frases positivas); etiqueta verde na listagem, no card e no detalhe |
| `triagem` | `pendente` (no relatório), `seguir` (foi para o quadro), `visitada` (não seguir), `fora` (furou os filtros da busca) |
| `motivo_fora[]` | por que a vaga ficou fora dos critérios |
| `etapa` | `salva`, `aplicada`, `entrevista`, `proposta`, `encerrada` ou `null` (fora do quadro) |
| `etapa_em`, `triada_em` | `AAAA-MM-DD` da última mudança |
| `resultado` | só em `encerrada`: `nao_aprovado`, `desisti`, `cancelada`, `contratado` |
| `analise_status` | `feita`, `sem_analise` (gravada sem IA), `pendente` (adicionada no dashboard, esperando a IA), `sem_dados` |
| `aderencia` | 0–100 (só com IA); faixas: ≥80 forte, 65–79 boa, 50–64 parcial, <50 baixa |
| `resumo`, `encaixe[]`, `lacunas[]`, `alertas[]`, `modelo_trabalho` | análise da IA |
| `senioridade[]`, `senioridade_origem` | análise da IA: `junior`, `pleno`, `senior` (pode ter mais de um; `[]` = não informada), `declarada` pelo anúncio ou `sugerida` pela IA quando o anúncio não diz. Sem esse campo, o dashboard deduz pelo título (Jr, Pl, Sr, Pleno, Sênior, Snr, Mid-level, Intermediate, Semi Senior/SSr como pleno, II, III, Principal). O relatório mostra os níveis abreviados: Jr, Pl, Sr |
| `tipo_emprego[]` | análise da IA: `tempo_integral`, `pj`, `meio_periodo`, `estagio`, `temporario` |
| `moeda` | análise da IA: código da moeda em que a vaga paga (`BRL`, `USD`, `EUR`…), quando a vaga diz |
| `fora_dos_criterios` | análise da IA: motivo que os outros campos não pegam (ex.: exige residência em outro país) |
| `anotacao` | suas anotações |
| `criada_em`, `atualizada_em`, `analisada_em` | carimbos de data |

Uma vaga aparece no quadro quando tem `etapa` e é `manual` ou tem `triagem: "seguir"`.

### Tabela `buscas` (um registro por busca)

ID `AAAAMMDD-HHMMSS`. Campos: `data`, `fontes`, `termos`, `janela_horas`, `resumo`
(filtros usados), `consultas`, `brutas`, `excluidas_titulo`, `ja_vistas`, `candidatas`,
`avaliadas`, `fora_criterios`, `com_nota`, `fortes`, `boas`, `parciais`, `baixas`
(buscas antigas têm `somente_remoto`). O relatório mostra a mais recente.
