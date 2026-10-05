# dash: Acompanhamento de Candidaturas

App local (Python, só biblioteca padrão) que mostra as vagas e o funil de candidaturas.

```
python dash/servidor.py            # abre http://127.0.0.1:8765
python dash/servidor.py --rede     # também acessível de outros aparelhos da sua rede (ex.: celular no Wi-Fi)
```

No Windows dá para dar dois cliques em `abrir-dashboard.bat`; no macOS/Linux, `./dash/abrir-dashboard.sh`.

- **Quadro:** kanban Salva → Aplicação Enviada → Entrevista → Proposta Recebida →
  Encerrada (arraste os cartões ou use o menu ⋯), com anotações, resultado (não
  aprovado, desisti, vaga cancelada, contratado), filtro por plataforma e visão em
  lista.
- **Adicionar Vaga:** cole o link. O servidor lê a vaga (Indeed e LinkedIn pelas APIs
  públicas; Gupy pelo MCP público de candidatos dela; outros sites pelos dados
  estruturados JobPosting da página), grava no
  Relatório de Vagas e, se o Claude Code estiver instalado, pede a análise em segundo
  plano (`analise.py`). Se não der para ler, o formulário abre com o que deu, para
  completar; dali dá para mandar para o relatório ou direto para o quadro.
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
| `servidor.py` | Servidor local: serve a página e a API (`/api/vagas`, `/api/vagas/link` para adicionar pelo link, `/api/versao` com o aviso de análise em andamento, `/api/buscas/ultima`, `/api/config` para ler e gravar os filtros da busca). Só aceita pedidos da própria página. |
| `banco.py` | Acesso ao SQLite e comandos `quadro`, `pendentes`, `analisar`, `vaga` (dados completos de uma vaga) e `anotar` (acrescenta uma linha às anotações). |
| `analise.py` | Análise automática: roda `claude -p` sem ferramentas com o perfil, as regras de nota da skill e as vagas que esperam nota, e grava a resposta. Uma análise por vez. |
| `dashboard.html` | A página. |
| `abrir-dashboard.bat` / `.sh` | Atalhos para iniciar o servidor. |
| `dados/` | `candidaturas.db` e `backup/` (uma cópia por dia, guarda as 10 últimas). Fora do Git. |

## Dados

### Tabela `vagas` (um registro por vaga)

O ID é o do portal nas vagas da busca e nas do Indeed adicionadas pelo link (o `jk` de 16
caracteres), `gupy-…` nas da Gupy (busca e link), `li-…` nas do LinkedIn, `web-…` nas de
outros sites e `m-…` nas preenchidas à mão.

| Campo | Valores |
|---|---|
| `origem` | `busca` (veio de `vagas.py`), `link` (Adicionar Vaga pelo link; fica no relatório como as da busca) ou `manual` (formulário, direto no quadro) |
| `plataforma` | `Indeed`, `LinkedIn`, `Gupy`, `InHire`, `Catho`, `Outra` |
| `titulo`, `empresa`, `local`, `url`, `descricao` | dados da vaga |
| `publicada_em`, `encontrada_em` | `AAAA-MM-DD` |
| `salario`, `tipo`, `remoto`, `url_candidatura` | quando o portal informa |
| `termos`, `grupos`, `ids_relacionados`, `busca_id`, `jk` | controle da busca: termos que acharam a vaga, de qual grupo de consultas veio (`remoto`, `local` = cidade, `internacional:<país>`), anúncios repetidos, de qual busca veio |
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
