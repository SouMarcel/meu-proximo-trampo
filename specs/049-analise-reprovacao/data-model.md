# Data Model: Análise de reprovação (spec 049)

Arquivo `dash/dados/reprovacao.json` (fora do Git): `{ "<vaga_id>": Analise }`. Há uma análise por vaga, e a nova
substitui a anterior.

## Analise

| Campo | Tipo | Regra |
|---|---|---|
| `vaga` | `{id, titulo, empresa}` | Cópia curta, para mostrar |
| `criada_em` | ISO | Hora em que a análise ficou pronta |
| `tecnicas` | objeto | As técnicas escolhidas no diálogo, validadas por `curriculo_ia.validar_tecnicas`; usadas no currículo da etapa 3 |
| `curriculo_analisado` | `{tipo: vaga\|base_arquivo\|base_gerado\|perfil, nome, rotulo}` | Qual texto foi analisado (R2). `rotulo` é o que a página mostra, como "currículo desta vaga de 12/11 14:30" |
| `texto_analisado` | str (≤ 40000) | O texto do currículo analisado, com documentos mascarados. É usado na reescrita e na conferência dos trechos, mesmo se o arquivo sumir depois, e não vai para a página |
| `avisos` | `[str]` | Fonte que falhou, alerta de integridade (spec 034) |
| `motivos` | `[Motivo]` | Até 30 |
| `perguntas` | `[Pergunta]` | Até 10, na ordem de peso |
| `respostas` | `{<n da pergunta>: Resposta}` | Gravadas pela pessoa |
| `respostas_em` | ISO \| null | Hora da última gravação de respostas |
| `reescritos` | `[Reescrito]` | Preenchido na etapa 3 |
| `curriculo_gerado` | str \| null | Nome do currículo gerado pela etapa 3 (em `curriculos/`) |
| `gerado_em` | ISO \| null | Hora em que esse currículo saiu |
| `levados` | `[str]` | Ids dos relatos levados ao perfil por esta análise |

## Motivo

| Campo | Tipo | Regra |
|---|---|---|
| `i` | int | Índice estável dentro da análise |
| `grupo` | enum | `requisito_nao_comprovado` · `experiencia_generica` · `competencia_sem_evidencia` · `resultado_pouco_claro` · `informacao_ausente`. Fora disso, o motivo é descartado |
| `motivo` | str (≤ 400) | Sem afirmação de falta da pessoa (R4) |
| `trecho_cv` | str (≤ 500) \| null | null = não aparece no currículo |
| `trecho_ok` | bool | O trecho foi achado no currículo analisado (R5); para null, `true` |
| `trecho_vaga` | str (≤ 500) | A frase da vaga que o sustenta |
| `perguntas` | `[int]` | O `n` das perguntas ligadas |
| `sensivel` | bool | Assunto de autorização de trabalho, visto, salário, deficiência ou relocação: sem pergunta, com a nota "responda na candidatura" |

**Estado do motivo** (calculado, não guardado):
- `nao_tenho` (❌): alguma pergunta ligada tem a resposta `nao`;
- `tenho` (⚠️): alguma pergunta ligada tem `tenho` com relato;
- `sem_resposta`: não há resposta ou a resposta foi `pular`;
- `sem_pergunta`: o motivo não tem pergunta ligada.

Quando há ❌ e ⚠️ no mesmo motivo, vale ⚠️.

## Pergunta

| Campo | Tipo | Regra |
|---|---|---|
| `n` | int | 1..10 |
| `texto` | str (≤ 300) | Não sensível (`candidatura_ia.sensivel`) |

## Resposta

| Campo | Tipo | Regra |
|---|---|---|
| `resposta` | `nao` \| `tenho` \| `pular` | Obrigatória |
| `relato` | str (≤ 4000) | Obrigatório e não vazio quando `tenho`; documentos mascarados |
| `destino` | `perfil` \| `so_aqui` | Obrigatório quando `tenho`; padrão `so_aqui` |
| `levado` | str \| null | Id do relato quando já foi para o perfil; nesse caso a resposta não pode voltar a mudar de destino (R7) |

**Pronta para gerar**: toda pergunta tem `nao`, `pular`, ou `tenho` com relato.

## Reescrito

| Campo | Tipo | Regra |
|---|---|---|
| `original` | str (≤ 600) | Trecho do currículo analisado |
| `novo` | str (≤ 800) | Só com fatos do currículo, do perfil e dos ⚠️ |
| `motivos` | `[int]` | Índices dos motivos ligados |
| `avisos` | `[str]` | Número ou nome que não está nas fontes (conferência sem IA) |

## Transições

```text
(nenhuma) --Gerar com o checkbox--> analisando --ok--> aguardando_respostas
analisando --falha--> (a análise anterior continua; o estado do gerador mostra a falha e "Tentar de novo")
aguardando_respostas --gravar respostas--> aguardando_respostas
aguardando_respostas --Reescrever e gerar--> reescrevendo → escrevendo → gerando → conferindo --ok--> pronta
pronta --mudar respostas--> pronta (com "respostas mudaram"), e Reescrever e gerar de novo é possível
```

A situação (`aguardando_respostas`/`pronta`) é calculada pelo `curriculo_gerado`. O andamento vem do estado do
gerador.
