# Implementation Plan: Perfil como base, relato só na vaga dele, e relatos incorporados com conflitos

**Branch**: `060-relatos-por-vaga` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

## Summary

Os relatos pendentes saem dos pedidos gerais e ficam só nos pedidos da vaga deles; "Incorporar" reaproveita a revisão
da spec 050 aplicando direto o que não diverge e deixando as divergências para a aba Conflitos; a aba Seus relatos
vira caixa de entrada; a aba "Currículo base" vira "Extração perfil - currículo", e o currículo da vaga passa a ser o
currículo geral mais recente do idioma.

## Technical Context

Python 3 só com biblioteca padrão; front React na `frontend-react`. Esta branch recebe antes o merge da
`061-apagar-documentos` (as duas mexem em `curriculo_ia.py` e `dash/servidor.py`). Constituição emendada para 5.6.0
(princípio IV) nesta branch.

## Constitution Check

- IV: a regra nova é a da emenda 5.6.0; nada inventado; Incorporar só aplica o que a conferência sem IA validou.
- V: Incorporar é um clique da pessoa; o que entrou fica à vista com Desfazer; divergências esperam a escolha dela.
- III: sem IA, nada muda no perfil (o relato espera), e o resto da ferramenta funciona.

## Decisões

**D1. Relatos por vaga** (`relatos.py`): `com_relatos(perfil, vaga=None)` — `vaga` é um dict de vaga (ou um id); sem
vaga devolve o perfil como está; com vaga acrescenta o bloco (`bloco`) só dos relatos pendentes cujo `vaga.id` é o id
da vaga ou está em `vaga["ids_relacionados"]`. `pendentes()` (sem `no_perfil`), `desmarcar_no_perfil(ids)`.
`relatos.py lista [--vaga ID]`. Fora isso, `bloco()`/`levar_ao_perfil` continuam (o CLI antigo), mas a página não
usa mais `levar_ao_perfil`.

**D2. Pedidos gerais só com o perfil**: `dash/analise.py` `montar_pedido` (~150) lê o perfil sem relatos;
`analise_perfil.perfil_texto` (~91) idem (vale para `dash/requisitos.py`); `conferir._com_relatos(perfil_txt,
vaga=None)` (~787) com a vaga quando há `--vaga-id`; `curriculo_ia.COMPLETO` (~66) sem "e dos relatos".

**D3. Pedidos da vaga** — `curriculo_ia.perfil_texto(vaga=None)` (~106) e `entrevista.perfil_texto(vaga=None)` (~137)
repassam a vaga a `relatos.com_relatos`. Chamadas: `curriculo_ia.gerar` (~317, com a vaga; `None` no geral);
`candidatura_ia` `gerar_carta` (~346), `verificar_carta` (~533, vaga pela meta da carta: `alvo.id` →
`banco.obter`), `gerar_respostas` (~610), `propor_respostas` (~731), `adaptar_relatos` (~805); `entrevista`
`preparacao`/`perguntas_ia`/`historias_ia` (vid → vaga), `retorno_ia` (~350) ganha `vid=None`; `reprovacao` (~175,
~459, ~654) com a vaga.

**D4. Incorporar** (`revisao_perfil.incorporar(ids, progresso=None) -> dict`): chama `revisar("relatos", ids)`; depois,
com `TRAVA`: `diretos` = itens aceitos e válidos da proposta; se houver, `aplicar(perfil, diretos)` +
`primeiros_passos.gravar_perfil` (anterior guardada); a proposta fica só com as discordâncias (`itens = []`,
`perfil_sha` do perfil novo; sem discordância → `gravada_em`). Relatos sem discordância aberta (inclusive `sem_fato`)
→ `relatos.marcar_no_perfil`. Guarda em `revisao_perfil.json` a chave `"ultima_incorporacao"`: `{anterior,
sha_depois, relatos, entrou: [{tipo, secao, cargo, novo}], em}`. Devolve `{entrou, conflitos, incorporados,
anterior}`. `desfazer() -> dict`: só se `perfil_sha(perfil atual) == sha_depois`; regrava o texto de
`ANTERIORES/<anterior>` com `gravar_perfil`, `relatos.desmarcar_no_perfil(relatos)`, descarta a proposta "relatos" e
apaga a `ultima_incorporacao`; senão `RevisaoErro("o perfil mudou depois da incorporação", 409)`.
`ultima_incorporacao()` para a página. O `gravar("relatos")` de hoje resolve os conflitos (marca os relatos deles).

**D5. Rotas e geração**: `gerador._rodar_revisao` chama `rv.incorporar(ids, …)` quando a origem é "relatos" (a origem
"vaga:<id>" da spec 049 continua com `revisar`). `POST /api/perfil/revisao` sem IA: 400 "Ligue uma IA para
incorporar os relatos" (sai o `levar_sem_ia` da página). `GET /api/perfil/revisao?origem=relatos` devolve também
`incorporacao` (a `ultima_incorporacao`, sem o sha). `POST /api/perfil/revisao/desfazer` → `desfazer()`. Tudo
`[local]`, com `TRAVA_PERFIL` como as outras escritas do perfil.

**D6. Currículo geral** (`curriculo_ia.geral_atual(idioma) -> dict | None`): entre os metas de currículo com
`alvo.tipo == "base"` e idioma (`curriculo.FORMATOS[tecnicas.formato].idioma`) igual, o mais recente com
`tecnicas.paginas != 0`; sem ele, o Completo mais recente; sem nenhum, `None`. `curriculo_ia.perfil_mudou_depois(meta)`
compara a data de modificação do perfil.md com `meta.criado_em`. Usos: `banco.curriculos_base()` (~833, item
Currículo da vaga: `{pt, en: {nome, url}}`, `nome` = arquivo PDF ou .docx do geral; sem geral, o marcado antigo como
reserva); rota do arquivo (`dash/servidor.py` ~829, `/arquivos/curriculo-base/<idioma>`) serve o PDF (ou .docx) do
geral, com o marcado antigo como reserva; `analise_perfil` (~350) "tem currículo em inglês" = `geral_atual("en")` ou
o marcado antigo; `reprovacao.curriculo_atual` (~142) usa `geral_atual(idioma)` no lugar do marcado. A lista de
currículos gerais da página (`GET /api/curriculo?…` sem vaga) ganha `perfil_mais_novo: bool` (perfil gravado depois do
geral mais recente).

**D7. Candidatura assistida** (`candidatura/contato.py` `_do_curriculo`, ~158): lê o perfil.md
(`primeiros_passos.caminho_perfil()`), e-mail, telefone e LinkedIn por `pp.reconhecer_contato(texto)`; fonte
"perfil"; sem perfil, aviso "sem perfil: a proposta usa as respostas já dadas e os filtros da busca". Não tenta o
nome pela primeira linha (o perfil começa com o título).

**D8. Front, Seus relatos** (`src/components/perfil/Relatos.tsx`): topo com os pendentes (marcar, editar, Excluir,
botão Incorporar que chama o mesmo `revisarPerfil("relatos", ids)` e acompanha a geração); depois da geração, lê
`GET /api/perfil/revisao?origem=relatos` e mostra "Entrou no perfil:" com a lista `incorporacao.entrou` e o botão
Desfazer (`POST /api/perfil/revisao/desfazer`); com conflitos, "N ponto(s) para decidir em Conflitos" com botão que
leva à aba. No fim, `<details>` "Relatos incorporados (N)" fechado, só leitura + Apagar. Sem `SecaoRevisaoPerfil`
aqui (vai para Conflitos).

**D9. Front, Meu perfil** (`src/components/perfil/MeuPerfil.tsx`): ícone de aviso (`AlertTriangle`, âmbar) na aba Seus
relatos quando há pendentes e na aba Conflitos quando a proposta "relatos" tem discordância sem escolha e não foi
gravada (carregar relatos e a revisão ao abrir e quando o perfil muda). Em Conflitos, abaixo dos conflitos das
fontes, `<SecaoRevisaoPerfil origem="relatos" />` quando houver proposta aberta; "As fontes não discordam em nada" só
sem os dois. Aba "Currículo base" → "Extração perfil - currículo"; sai `SeuCurriculo` (aba e tela final); frase nova;
aviso "Seu perfil mudou depois do último currículo geral: gere de novo o Completo e o de até 2 páginas" quando
`perfil_mais_novo`. `src/components/curriculo/Curriculos.tsx`: rótulos da seção sem vaga ("Currículos do perfil",
"Gerar currículo").

## Estrutura

Backend: `relatos.py`, `dash/analise.py`, `analise_perfil.py`, `conferir.py`, `curriculo_ia.py`, `candidatura_ia.py`,
`entrevista.py`, `reprovacao.py`, `revisao_perfil.py`, `dash/gerador.py`, `dash/servidor.py`, `dash/banco.py`,
`candidatura/contato.py`; testes em `tests/`. Front: `Relatos.tsx`, `MeuPerfil.tsx`, `Curriculos.tsx`,
`src/services/api/perfil.ts`, `src/services/api/curriculo.ts`. Docs: `dash/API.md`, `README.md`, `AGENTS.md`, skills.
