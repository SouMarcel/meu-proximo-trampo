# Implementation Plan: Limpeza de vagas antigas

**Branch**: `054-limpeza-vagas` | **Date**: 2026-11-23 | **Spec**: [spec.md](spec.md)

## Summary

O trabalho tem quatro partes:

- **Banco:** `dash/banco.py` ganha a regra dos grupos, a prévia e a gravação. A gravação arquiva com ficha curta ou
  encerra com "sem resposta", faz o backup antes e compacta o banco depois.
- **Configuração:** `filtros.py` ganha a chave `limpeza` no `config.json`, com padrões para quem não tem a chave.
- **Servidor:** `dash/servidor.py` ganha quatro rotas `/api/limpeza`.
- **Página:** a branch `frontend-react` ganha a aba Limpeza nos filtros e passa a esconder as arquivadas.

A busca e a sincronia de contas continuam vendo as vagas arquivadas, sem mudança no caminho delas, porque a ficha curta
mantém tudo o que elas usam para reconhecer uma vaga.

## Technical Context

- **Back:** Python com biblioteca padrão, sem dependência nova. SQLite com documento JSON por vaga: campo novo, sem
  migração.
- **Testes:** `unittest`, num arquivo novo `tests/test_limpeza.py`. Seguem o padrão de `tests/test_integridade.py:245`:
  patch de `banco.ARQUIVO`, `banco.BACKUPS` e `filtros.CONFIG` numa pasta temporária.
- **Front:** React e TypeScript na branch `frontend-react` (worktree `../mpt-front-027b`). O build sai pelo PR
  `front/atualizacao` da Action `front.yml`. A validação local é o typecheck e o build.
- **Quem usa a vaga arquivada:**
  - continuam vendo: a dedupe (`IndiceVistas`, `banco.py:216`), a sincronia (`dash/sincronia.py:42`) e o funil
    (`FunnelAnalytics.tsx`);
  - deixam de ver: as listas e os contadores do front, a fila de análise, `lacunas` e o resumo de requisitos.

## Constitution Check

- **I. Local e privado:** nada sai do computador. O backup fica em `dash/dados/backup/`, fora do Git.
- **II. Sem dados pessoais:** os testes e os exemplos usam vagas fictícias. Antes do commit na master, rodar a busca
  de dados pessoais no diff.
- **III. Simples:** biblioteca padrão, sem IA. O comando no terminal deixa a limpeza útil sem a página.
- **IV. Só fatos confirmados:** não se aplica. Nenhum texto é gerado; "sem resposta" é uma marca de situação, não
  um fato no currículo.
- **V. A pessoa decide:**
  - prévia sempre antes de gravar;
  - gravação só com clique ou com `--gravar`;
  - destacadas desmarcadas;
  - a busca nunca limpa sozinha.
- **Restrições técnicas:** o campo novo vai sem migração; o `config.json` sem a chave `limpeza` continua
  funcionando; o servidor mantém a validação de host e origem nas rotas novas, porque elas passam pelo mesmo
  despacho.
- **Delegação:** o banco e os testes ficam comigo, porque a regra é o centro da feature. O front e a documentação
  podem ir a funcionário (`[D]` no tasks).

**Gate:** passa, sem violação.

## Decisões

**D1. Critérios no `config.json`** (`filtros.py`). Chave nova:

```json
"limpeza": {
  "fora":         {"ligado": true, "dias": 30},
  "pendente":     {"ligado": true, "dias": 30, "nota_abaixo_de": null},
  "dispensadas":  {"ligado": true, "dias": 30,
                   "resultados": ["nao_aprovado", "desisti", "cancelada", "sem_resposta", "sem_resultado"]},
  "sem_resposta": {"ligado": true, "dias": 30}
}
```

- `LIMPEZA_PADRAO` (constante) e `_limpeza_cfg(cfg)` completam o que faltar, em `efetivos()`, como os outros grupos.
- `validar_limpeza(e)` aceita:
  - `dias` inteiro de 1 a 365;
  - `nota_abaixo_de` null ou inteiro de 1 a 100;
  - `resultados` só desta lista: `nao_aprovado`, `desisti`, `cancelada`, `sem_resposta`, `sem_resultado`.
- `validar()` só aplica `limpeza` quando o painel a manda, como já faz com `fontes`. Assim o front antigo não apaga a
  chave.
- `salvar_limpeza(entrada)` grava só essa chave. Ela não depende de `termos` estarem preenchidos, porque a aba
  Limpeza não precisa dos outros filtros.
- A chave entra também no `config.exemplo.json`.

**D2. Grupos** (`banco.grupo_limpeza(v, crit, hoje) -> (grupo, desde, dias) | None`, função pura).

Nunca entram, em nenhum grupo:

- vaga já arquivada (`arquivada_em`);
- `origem == "manual"` (vaga digitada à mão, sem link);
- etapa `entrevista`, `proposta` ou `salva`;
- resultado `contratado`.

A vaga adicionada **por link** (`origem == "link"`) segue os grupos como a da busca. Ela tem os números do portal, a
dedupe se beneficia do arquivamento, e boa parte das candidaturas encerradas vem por link.

| Grupo | Condição | `desde` (a primeira data que existir) |
|---|---|---|
| `fora` | `triagem == "fora"` e sem etapa | `triada_em`, `encontrada_em`, `criada_em` |
| `pendente` | `triagem == "pendente"` e sem etapa; com `nota_abaixo_de`, só `aderencia` int `< N` | `encontrada_em`, `criada_em` |
| `dispensadas` | (`triagem == "visitada"` e sem etapa) ou `etapa == "encerrada"` com `resultado or "sem_resultado"` em `resultados` | visitada: `triada_em`…; encerrada: `etapa_em`, `triada_em`… |
| `sem_resposta` | `etapa == "aplicada"` | `etapa_em`, `triada_em`, `encontrada_em`, `criada_em` |

- `dias = hoje - desde[:10]`. A vaga entra quando `dias >= crit[grupo].dias` e o grupo está ligado.
- Sem nenhuma data, a vaga não entra.
- O `atualizada_em` nunca é usado.

**D3. Destaque** (`banco.destaques(v) -> list[str]`): devolve, nesta ordem, os motivos que se aplicam:

- "tem currículo", quando há `curriculos`;
- "tem carta ou respostas", quando há `documentos`;
- "tem anotação", quando `anotacao` não está vazia.

Lista vazia quer dizer que a vaga não é destacada.

**D4. Prévia** (`banco.prever_limpeza(crit=None, hoje=None) -> dict`): uma leitura só, sem gravar nada. Formato:

```json
{"grupos": {"fora": {"acao": "arquivar", "dias": 30, "ligado": true,
                     "vagas": [{"id", "titulo", "empresa", "plataforma", "dias", "destaques": []}]},
            "pendente": {...}, "dispensadas": {...},
            "sem_resposta": {"acao": "encerrar", ...}},
 "total": 0, "destacadas": 0, "arquivadas": 0, "tamanho_kb": 0}
```

- As vagas de cada grupo saem ordenadas da mais parada para a menos parada.
- `arquivadas` é o número de vagas que já estão arquivadas.
- `crit=None` usa `filtros.efetivos(filtros.ler_config())["limpeza"]`.

**D5. Gravação** (`banco.limpar(ids=None, crit=None, incluir_destacadas=False) -> dict`):

1. `backup_diario()` antes de tudo. Ele já guarda uma cópia por dia e mantém as 10 últimas.
2. Numa única transação `escrita()`, refaz `grupo_limpeza` de cada vaga, porque a situação pode ter mudado depois da
   prévia (FR-009). Quais vagas entram:
   - `ids=None` (terminal): todas as do grupo, menos as destacadas, a não ser que venha `incluir_destacadas`;
   - `ids` vindos da página: só as vagas pedidas que ainda estão num grupo. A pessoa marcou, então a destacada entra.
3. Em cada vaga que entra, faz o que o grupo pede:
   - grupos `fora`, `pendente` e `dispensadas`: `_ficha_curta(doc)` (D6);
   - grupo `sem_resposta`: `doc.update(etapa="encerrada", resultado="sem_resposta", etapa_em=hoje(),
     atualizada_em=agora())`, sem arquivar.
4. Depois do commit, numa conexão nova: `PRAGMA wal_checkpoint(TRUNCATE)` e `VACUUM`, para o arquivo diminuir de
   fato.
5. Devolve `{"arquivadas", "encerradas", "ignoradas", "antes_kb", "depois_kb", "backup"}`. `ignoradas` são os ids
   pedidos que já não estavam em nenhum grupo.

**D6. Ficha curta** (`FICHA_CURTA`, um conjunto de chaves). A vaga fica só com estas chaves e ganha
`arquivada_em = agora()`:

- `jk`, `ids_relacionados`, `url`, `url_candidatura`, `titulo`, `empresa`;
- `plataforma`, `outras_plataformas`, `origem`, `area`, `local`, `modelo_trabalho`, `remoto`;
- `encontrada_em`, `criada_em`, `publicada_em`, `triada_em`, `etapa_em`, `analisada_em`, `atualizada_em`,
  `busca_id`;
- `triagem`, `etapa`, `resultado`, `aderencia`, `salario`, `anotacao`, `curriculos`, `documentos`, `kit`.

Saem `analise_status` e `descricao_pendente`. Com isso, `precisa_analise`, `analise.precisa`, `lacunas` e
`pendentes_de_descricao` já deixam a vaga arquivada de fora sem mudar o código deles. A exceção é o
`requisitos.selecionar` (D8).

**D7. Desarquivar** (`banco.atualizar_usuario`, `banco.py:653`): quando `etapa` chega diferente da atual numa vaga
arquivada, `doc.pop("arquivada_em")`. Isso cobre a sincronia de contas (`sincronia.aplicar` chama
`atualizar_usuario`) e qualquer mudança de etapa pela página, num ponto só (FR-015).

**D8. Quem ignora as arquivadas:**

- `banco.arquivada(v) -> bool`;
- `_cmd_quadro` (`banco.py:845`): o quadro e as contagens de Aplicações;
- `requisitos.selecionar` (`dash/requisitos.py:254`): sem isso, a vaga arquivada como encerrada contaria como "sem
  leitura" em Aplicações;
- `procurar` (`banco.py:131`) continua achando a arquivada, porque é consulta pelo nome. A saída de `_cmd_vaga`
  mostra "(arquivada em …)".

**D9. "Sem resposta"**: `RESULTADOS` (`banco.py:45`) ganha `"sem_resposta"`. Isso já basta para
`_validar_usuario`, e a pessoa pode escolher o resultado à mão.

**D10. Rotas** (`dash/servidor.py`). Seguem o mesmo despacho das outras, então passam pela validação de host e de
origem.

| Rota | O que faz |
|---|---|
| `GET /api/limpeza` | `{"criterios": efetivos[limpeza], "arquivadas": N, "tamanho_kb": N}` |
| `PUT /api/limpeza` | corpo `{"criterios": {...}}` → `filtros.salvar_limpeza` → devolve o mesmo que o `GET` |
| `GET /api/limpeza/previa` | `banco.prever_limpeza()`, com os critérios gravados |
| `POST /api/limpeza/aplicar` | corpo `{"ids": [...]}`, até 2000 ids, cada um validado por `ID_VALIDO` → `banco.limpar(ids)` → resultado do D5 |

Na página, o botão "Ver o que seria limpo" grava os critérios da aba (`PUT`) e depois pede a prévia. Assim a prévia
sempre usa o que está na tela e o que está gravado, os dois iguais.

**D11. Comando** (`dash/banco.py limpar [--gravar] [--incluir-destacadas]`):

- Sem opção, mostra por grupo o total, as destacadas com o motivo e até 10 exemplos. Termina com "Nada foi gravado.
  Para gravar: python dash/banco.py limpar --gravar".
- Com `--gravar`, mostra o resultado do D5.
- Entra no docstring do `banco.py`, no `AGENTS.md` (lista de comandos) e na skill `buscar-vagas` (só mostrar a
  prévia, gravar só com o OK). A skill é editada em `.agents/skills/` e copiada com `sincronizar_skills.py`.

**D12. Front** (branch `frontend-react`):

- `types/api.ts`:
  - `Resultado` ganha `"sem_resposta"`;
  - `Vaga` ganha `arquivada_em?: string | null`;
  - tipos novos `CriteriosLimpeza` e `PreviaLimpeza`.
- `utils/rotulos.ts`: `sem_resposta: "Sem resposta"`. O select do `JobDetailModal` já lê esse mapa.
- `utils/formatters.ts`: `noQuadro` e `noRelatorio` passam a exigir `!vaga.arquivada_em`. Conferir em `App.tsx` todo
  `vagas.filter`/contador que não passa por elas. `FunnelAnalytics` continua recebendo todas.
- `services/api/limpeza.ts`: `ler`, `gravar`, `previa` e `aplicar`.
- `components/modals/LimpezaAba.tsx` (componente novo, para não engordar o modal de 970 linhas):
  - os 4 grupos, cada um com interruptor e dias;
  - o campo "só com nota abaixo de" no grupo Pendentes;
  - as caixas de resultados no grupo Visitadas e encerradas;
  - o botão "Ver o que seria limpo";
  - a lista por grupo, com caixa de seleção, recolhível, as destacadas em âmbar com o motivo e desmarcadas;
  - "Arquivar N vagas" com confirmação, e a frase "Já arquivadas: N".
- `SearchFiltersModal.tsx`: `Aba` ganha `"limpeza"`, rótulo "Limpeza". A aba não passa pelo Salvar geral do modal;
  ela tem o próprio fluxo.
- Depois de aplicar, recarregar as vagas: a versão do banco muda, e a página já recarrega por ela.

**D13. Documentação:**

- `dash/API.md`: as rotas novas, `sem_resposta` na tabela de resultados (L118), `arquivada_em` no modelo da vaga e a
  chave `limpeza` em §3.4;
- `dash/README.md`;
- `specs/lista-de-desejos.md`: "ver e restaurar vagas arquivadas", que ficou fora do escopo.

## Testes (`tests/test_limpeza.py`)

- **Grupos e datas:**
  - fora com 40 e com 10 dias, com prazo de 30;
  - grupo desligado;
  - pendente com `nota_abaixo_de`, inclusive a vaga sem nota;
  - encerrada com resultado fora da lista;
  - `sem_resultado`;
  - fallback de data;
  - vaga sem data;
  - `atualizada_em` recente não muda nada.
- **Exclusões:** manual, entrevista, proposta, salva e contratado.
- **Destaques:** cada motivo; terminal sem `--incluir-destacadas`; ids vindos da página incluem a destacada.
- **Ficha curta:** só as chaves de `FICHA_CURTA` e `arquivada_em`; descrição e análise fora.
- **Dedupe:** depois de arquivar, `IndiceVistas().achar()` acha a vaga pelo id, pelo jk do link e pela chave
  cargo+empresa.
- **Sem resposta:** etapa encerrada, resultado `sem_resposta`, descrição mantida.
- **Recontagem:** id pedido que saiu do grupo depois da prévia vai para `ignoradas`.
- **Backup e tamanho:** o backup é criado; `depois_kb < antes_kb` num banco com descrições grandes (SC-004).
- **Desarquivar:** `atualizar_usuario` com etapa nova tira `arquivada_em`.
- **Configuração:** padrões sem a chave; `validar_limpeza` recusa dias fora de 1 a 365 e resultado desconhecido;
  `validar()` sem `limpeza` mantém a chave gravada.
- **Rotas** (com o servidor de teste, se já houver o padrão em `tests/`): GET, PUT, prévia e aplicar.

## Verificação (quickstart)

1. `python -m unittest discover -s tests`: tudo passando.
2. Na worktree, com uma cópia do banco da branch pessoal em `TRAMPO_BANCO` (pasta temporária, fora do Git):
   - `PY dash/banco.py limpar` mostra a prévia com números;
   - `--gravar` arquiva e mostra o antes e o depois.
3. `PY vagas.py buscar` contra essa cópia não recria nenhuma vaga arquivada (SC-003). Fica opcional, porque toca os
   portais. A alternativa é testar a dedupe com `IndiceVistas` em cima dos documentos arquivados.
4. Merge na branch pessoal e reinício do dashboard. Junto com o PR do front, testar na página: aba Limpeza → prévia →
   arquivar algumas → conferir que:
   - os contadores e as listas diminuem;
   - o funil fica igual;
   - existe um backup novo.

## Project Structure

```text
filtros.py                      # D1
config.exemplo.json             # D1
dash/banco.py                   # D2–D9, D11
dash/requisitos.py              # D8
dash/servidor.py                # D10
dash/API.md, dash/README.md     # D13
AGENTS.md, .agents/skills/buscar-vagas/SKILL.md (+ sincronizar_skills.py)
tests/test_limpeza.py
frontend-react: src/types/api.ts, src/utils/{rotulos,formatters}.ts, src/services/api/limpeza.ts,
                src/components/modals/{LimpezaAba,SearchFiltersModal}.tsx, src/App.tsx
```

Não há `research.md`, `data-model.md` nem `contracts/` separados. As decisões, o modelo (D1, D6) e o contrato (D4,
D5, D10) ficam aqui, como nas specs anteriores.

## Complexity Tracking

Sem violações da constituição.
