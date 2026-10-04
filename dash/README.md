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
  lista. **Adicionar Vaga** registra vagas de qualquer site.
- **Relatório de Vagas:** o que as buscas trouxeram. "Seguir com a vaga" manda para a
  coluna Salva; "Não seguir" marca como visitada e a vaga não volta nas próximas
  buscas. Vagas com nota abaixo de 50 ficam recolhidas.

A página confere o banco a cada poucos segundos, então uma busca gravada aparece
sozinha.

## Arquivos

| Arquivo | Para quê |
|---|---|
| `servidor.py` | Servidor local: serve a página e a API (`/api/vagas`, `/api/versao`, `/api/buscas/ultima`). Só aceita pedidos da própria página. |
| `banco.py` | Acesso ao SQLite e comandos `quadro`, `pendentes`, `analisar`. |
| `dashboard.html` | A página. |
| `abrir-dashboard.bat` / `.sh` | Atalhos para iniciar o servidor. |
| `dados/` | `candidaturas.db` e `backup/` (uma cópia por dia, guarda as 10 últimas). Fora do Git. |

## Dados

### Tabela `vagas` (um registro por vaga)

O ID é o do portal (no Indeed, o `jk` de 16 caracteres) nas vagas da busca, e `m-…`
nas adicionadas à mão.

| Campo | Valores |
|---|---|
| `origem` | `busca` (veio de `vagas.py`) ou `manual` (botão Adicionar Vaga) |
| `plataforma` | `Indeed`, `LinkedIn`, `Gupy`, `InHire`, `Catho`, `Outra` |
| `titulo`, `empresa`, `local`, `url`, `descricao` | dados da vaga |
| `publicada_em`, `encontrada_em` | `AAAA-MM-DD` |
| `salario`, `tipo`, `remoto`, `url_candidatura` | quando o portal informa |
| `termos`, `ids_relacionados`, `busca_id`, `jk` | controle da busca (anúncios repetidos, de qual busca veio) |
| `triagem` | `pendente` (no relatório), `seguir` (foi para o quadro), `visitada` (não seguir) |
| `etapa` | `salva`, `aplicada`, `entrevista`, `proposta`, `encerrada` ou `null` (fora do quadro) |
| `etapa_em`, `triada_em` | `AAAA-MM-DD` da última mudança |
| `resultado` | só em `encerrada`: `nao_aprovado`, `desisti`, `cancelada`, `contratado` |
| `analise_status` | `feita`, `sem_analise` (gravada sem IA), `pendente` (adicionada à mão, esperando a IA), `sem_dados` |
| `aderencia` | 0–100 (só com IA); faixas: ≥80 forte, 65–79 boa, 50–64 parcial, <50 baixa |
| `resumo`, `encaixe[]`, `lacunas[]`, `alertas[]`, `modelo_trabalho` | análise da IA |
| `anotacao` | suas anotações |
| `criada_em`, `atualizada_em`, `analisada_em` | carimbos de data |

Uma vaga aparece no quadro quando tem `etapa` e é `manual` ou tem `triagem: "seguir"`.

### Tabela `buscas` (um registro por busca)

ID `AAAAMMDD-HHMMSS`. Campos: `data`, `fontes`, `termos`, `janela_horas`,
`somente_remoto`, `brutas`, `excluidas_titulo`, `ja_vistas`, `candidatas`, `avaliadas`,
`com_nota`, `fortes`, `boas`, `parciais`, `baixas`. O relatório mostra a mais recente.
