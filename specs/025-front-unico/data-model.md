# Modelo de dados: Front único

O servidor e o banco não mudam. Este documento descreve o que o front guarda **na tela** e de onde cada coisa vem. Os
formatos completos estão no `dash/API.md`; `src/types/api.ts` (na `frontend-react`) é a cópia deles em TypeScript.

## Tipos (src/types/api.ts)

| Tipo | Origem no `dash/API.md` | Usado em |
|---|---|---|
| `Vaga` (com `checklist` e `lembretes_pendentes` calculados) | §2 | quadro, Relatório, Internacional, detalhe, funil |
| `Versao` | §3.13 | `App` (a cada 4 s) |
| `UltimaBusca`, `PlanoBusca`, `EstadoBusca`, `EstadoPendentes` | §3.1, §3.3 | Relatório, diálogo Buscar vagas |
| `RespostaLink`, `CamposExtraidos`, `NovaVaga` | §3.2 | Adicionar vaga |
| `Config` = `{filtros: Filtros, consultas, opcoes: Opcoes, existe}` | §3.4 | Filtros da busca, Internacional |
| `EstadoIA`, `Provedor` | §3.5 | painel IA, contexto `Ferramenta` |
| `EstadoPerfil`, `Material`, `Rascunho`, `Pergunta`, `Previa`, `FiltrosPropostos`, `CurriculosDaPasta`, `PropostaDoCurriculo` | §3.6 | Meu perfil / Primeiros passos |
| `Analises`, `ItemLacuna`, `Prontidao`, `ItemPlano`, `Cargo` | §3.7 | Meu perfil → Análises, Internacional |
| `Catalogo`, `EstadoGeracao`, `MetaCurriculo` | §3.8 | detalhe da vaga, currículo base |
| `DocumentoCarta`, `DocumentoRespostas` | §3.9 | detalhe da vaga (kit) |
| `Entrevista`, `Historia`, `PerguntaProvavel`, `Rodada`, `RetornoSimulacao` | §3.10 | Preparar entrevista |
| `Contas`, `Portal`, `EstadoCandidaturas`, `ItemCandidatura` | §3.11 | Atualizar candidaturas |
| `ErroApi` = `{status, message, dados}` | §1 | todas as telas |

Regra: nenhum campo em `src/types/api.ts` que não esteja no `dash/API.md`. Campos só de tela (ex.: "verificando")
ficam em tipos separados, derivados.

## Estado derivado (só na tela, nunca gravado)

- **Situação da nota** da vaga, para os selos:
  1. `verificando`, quando o id está em `versao.verificando`;
  2. `falha`, quando está em `versao.falhas`;
  3. senão, o `analise_status` da vaga, com o selo "nota provisória" quando `nota_sem_descricao`.
- **Área** da vaga: o campo `area`; sem ele, deduzida por `grupos`, como no `dashboard.html`.
- **No quadro**: `etapa != null` e (`origem == "manual"` ou `triagem == "seguir"`).
- **No Relatório**: `origem != "manual"`, separado por área.
- **Faixa da nota**: ≥80 forte, ≥65 boa, ≥50 parcial, abaixo disso baixa; sem número, "sem nota".

## Contexto `Ferramenta`

| Campo | Valores | Atualizado por |
|---|---|---|
| `servidor` | `no_ar` \| `fora` \| `demo` | `GET /api/versao` (falha de rede → `fora`; sem resposta na abertura → `demo`) |
| `podeAlterar` | boolean | `pode_alterar` das respostas que o trazem; 403 numa rota [local] → `false` |
| `ia` | `{disponivel, nome, modelo, cobranca}` | `GET /api/ia` na abertura e depois de salvar a IA |
| `perfilExiste` | boolean | `GET /api/perfil/estado` |

## Preferências de tela (localStorage, chaves `mpt_pref_*`)

Só aba aberta, sub-aba e ordem do Relatório, filtros visuais e tema. Toda leitura e escrita com `try/catch`, e a tela
funciona sem elas (FR-002).

## Transições que o front dispara (resumo do §3.1)

| Ação | Corpo do `PATCH /api/vagas/{id}` |
|---|---|
| Seguir com a vaga | `{triagem: "seguir", etapa: "salva", etapa_em: hoje, triada_em: hoje}` |
| Não seguir | `{triagem: "visitada", etapa: null, triada_em: hoje}` |
| Voltar para triagem | `{triagem: "pendente", etapa: null, resultado: null, triada_em: null}` |
| Mover de coluna | `{etapa, etapa_em: hoje}` + `resultado: null` fora de `encerrada` |
| Resultado | `{resultado}` |
| Salvar no detalhe | `{anotacao, email_candidatura, assunto_candidatura}` |
| Data da entrevista | `{entrevista_em}` |
| Checklist | `{kit}` |
| Lembrete Feito, Dispensar ou Parar | `{lembretes}` |

Uma escrita por vez por vaga (fila); a vaga local é trocada pela devolvida.
