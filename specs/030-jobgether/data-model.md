# Data Model: JobGether na busca de vagas

Não há tabela nova nem mudança de formato no banco nem no `config.json`.

## Vaga do JobGether

É uma vaga no formato comum de `fontes/__init__.py`. De onde vem cada campo:

| Campo | Origem na API | Regra |
|---|---|---|
| `id` | `url` (`/offer/<24 hex>-<slug>`) | `jobgether-<24 hex>`, em minúsculas; sem id na URL, `jobgether-<id da API>` |
| `plataforma` | — | `"JobGether"` |
| `titulo` | `title` | como veio, sem espaços sobrando |
| `empresa` | `company` | "Empresa não informada" se vier vazio |
| `local` | `location` | `"Remoto (<location curto>)"`, ou `"Remoto"` |
| `remoto` | — | `true` (a API traz remotas por padrão) |
| `modelo_trabalho` | `remote` | `"hibrido"` se falar em hybrid; senão `"remoto"` |
| `publicada_em` | `postedAt` | AAAA-MM-DD (`_comum.data_iso`) |
| `url` | `url` | a página no JobGether |
| `url_candidatura` | — | `null` |
| `salario` | `salaryRange` | "US$ 65.000–70.000", sem período; `null` sem valor |
| `moeda` | `salaryRange` | código de 3 letras do fim do texto (ex.: `USD`) |
| `tipo` | `contractType` | "Tempo integral", "Meio período", "Temporário", "Freelance", "Estágio" |
| `tipo_emprego` | `contractType` | `meio_periodo`, `temporario`, `pj` ou `estagio`; "Full time" fica sem código |
| `restricao_local` | `location` | o texto curto (até 200 caracteres) |
| `descricao` | — | vazia; a nota da IA fica provisória (`nota_sem_descricao`, spec 021) |

**Validação**:
- item sem `title` ou sem id fica de fora;
- item com campo fora do formato fica de fora, sem derrubar a lista (`_comum.filtrar`);
- a mesma vaga numa segunda página aparece uma vez.

## Espera do JobGether

O arquivo `.cache/jobgether-espera.json` (fora do Git) traz `{"desde": ISO, "motivo": "código 403"}`. Ele é gravado
por `_comum.gravar_espera` no primeiro 403 ou 429. A espera vale por 24 horas a partir de `desde`
(`_comum.ler_espera`).

## Estado da busca (memória)

O `_estado` do módulo é zerado a cada busca (`_comum.AO_ESQUECER`) e guarda:
- `bloqueado`: bloqueou nesta busca;
- `ultimo`: hora do último pedido, para a pausa;
- `pausa`: a faixa em uso;
- `listas`: as consultas já lidas (cargo, local, híbrido) e o resultado de cada uma;
- `avisos`: os avisos já dados (espera, local não reconhecido), para cada um sair uma vez.

## Vaga manual com link do JobGether

O `banco.criar_manual` recebe o `url` de um link `jobgether.com/offer/<id>-…`:
- o id da vaga passa a ser `jobgether-<id>`;
- se esse id já existe (a busca já trouxe), devolve a vaga que existe, sem gravar (`nova = false`);
- os outros links continuam com o id `m-…` de hoje.
