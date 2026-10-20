# Feature Specification: Registro dos pedidos ao LinkedIn

**Feature Branch**: `024-registro-linkedin` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-10-20

**Status**: Em teste

**Input**: User description: análise de sugestões para o LinkedIn bloquear menos as buscas; das cinco, a única que
vale agora é registrar os pedidos de cada execução, para saber o que provoca o bloqueio.

## Contexto

Uma busca típica faz uma consulta ao LinkedIn (os cargos ligados por OR): no máximo 3 páginas e 20 descrições.
Num caso real, o bloqueio (429) veio na primeira ou na segunda página, 20 horas depois da busca anterior. Isso sugere
um limite por rede, e não pelo volume de uma busca. Mas hoje só o motivo do bloqueio fica gravado. Não ficam gravados
o pedido em que ele veio, o intervalo desde o pedido anterior nem o que mais pediu ao LinkedIn antes: Completar
descrições, Forçar verificar, link ou post colados.

Reduzir páginas ou descrições fica para depois, se os registros mostrarem que o volume pesa. Contornar o bloqueio
(VPN, troca de IP ou de identificação do navegador) não entra, por regra da ferramenta.

## Requirements

- **FR-001**: cada pedido ao LinkedIn entra em `.cache/linkedin-pedidos.json` (fora do Git), com os últimos 300.
  - Campos: quando, origem (`busca`, `completar`, `forcar`, `adicionar` ou `outro`), tipo (`pagina`, `descricao`,
    `link` ou `post`), a resposta (código HTTP ou `rede`) e os segundos desde o pedido anterior.
  - Nada de cargos, endereços ou dados da vaga.
- **FR-002**: a origem vale por thread, porque no servidor a busca e o Forçar verificar podem rodar juntos.
- **FR-003**: o registro passa por todos os caminhos que pedem ao LinkedIn:
  - `fontes/linkedin.py` (páginas da busca e descrições);
  - `fontes/link.py` (link de vaga colado);
  - `fontes/post.py` (link de post colado).
- **FR-004**: `vagas.py pedidos-linkedin [--horas N]` resume o registro, dividido em rodadas (pedidos com menos de
  30 minutos entre si).
  - Por rodada: pedidos por tipo e as respostas.
  - Em cada bloqueio: em que pedido da rodada ele veio, quantos segundos depois do anterior e quantos pedidos houve
    nas 24 horas antes.
- **FR-005**: se não der para gravar o registro, nada muda no resto: a busca, a pausa e a espera de 6 horas seguem
  iguais.

## Success Criteria

- **SC-001**: depois de alguns bloqueios, o resumo responde se eles vêm com poucos pedidos (rede) ou depois de
  muitos (volume).
- **SC-002**: nenhum dado pessoal nem termo de busca no registro.
- **SC-003**: `python -m unittest discover -s tests` passa, sem gravar no `.cache/` de verdade.

## Fora do escopo

- Menos páginas por consulta ou menos descrições por busca (decisão depois dos registros).
- Contornar o bloqueio de qualquer forma.
