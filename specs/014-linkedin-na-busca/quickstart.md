# Quickstart: validar o LinkedIn na busca

Testes sem rede (HTML fictício e `_baixar` substituído), servidor no roteiro com config e banco temporários, Chrome
sem janela, e uma busca real pequena só com o OK do usuário.

| # | Cenário | Esperado |
|---|---|---|
| 1 | Parâmetros para os seis grupos (remoto, país, cidade, país de fora, mudança, global) | local e `f_WT` certos; `f_JT` e `f_TPR` pelos filtros (SC-001) |
| 2 | Lista fictícia com 3 cards (um sem empresa, um sem data) | 3 vagas `li-<id>` com os campos do data-model |
| 3 | Vaga já no banco pelo link + mesma vaga em dois grupos | aparece uma vez (SC-002) |
| 4 | Vaga presencial em país fora da mudança; vaga de estágio sem estágio marcado | Fora dos critérios com o motivo |
| 5 | Bloqueio (429) na 2ª consulta | nenhum pedido depois; aviso uma vez; vagas das outras fontes no relatório (SC-004) |
| 6 | Redirecionamento para login | tratado como bloqueio |
| 7 | Descrição só das candidatas | `descrever` chamado só para elas (SC-005) |
| 8 | LinkedIn desligado | saída igual às referências da spec 013 (SC-003) |
| 9 | Página: seção Portais, marcar o LinkedIn, salvar | config com `linkedin`; contador mostra as consultas dele; sem portal nenhum, pede um |
| 10 | Busca real pequena (1 termo, remoto no país + 1 país de fora), com OK | vagas reais com etiqueta, área e modelo; pausa entre as consultas |
| 11 | `python -m unittest discover -s tests` | todos passando |

## Resultado (12/10/2026, Windows 11)

Sem rede: testes com HTML fictício e um roteiro com a fonte falsa, o LinkedIn simulado (bloqueio na 2ª consulta),
servidor na porta 8799 e Chrome sem janela.

- 1: parâmetros certos nos seis tipos de grupo, cobertos por dois configs (com cidade: remoto, cidade, país de fora,
  mudança e mundo todo; sem cidade: país inteiro com remoto e híbrido); `f_JT` e `f_TPR` pelos filtros; países em
  inglês ("United States", "United Kingdom", "Germany").
- 2: três cards (um sem empresa, um sem data, um sem o urn) lidos com o id `li-<n>` igual ao do link.
- 3: a vaga já adicionada pelo link não volta; a mesma vaga em dois grupos aparece uma vez.
- 4: vaga presencial na França (mudança só para a Alemanha) e vaga de estágio vão para Fora dos critérios com o motivo.
- 5: no bloqueio da 2ª consulta, nenhum pedido depois (2 de 6 consultas), o aviso sai uma vez, as vagas da outra
  fonte seguem e nenhuma descrição é pedida ao LinkedIn depois do bloqueio.
- 6: redirecionamento (login) e 999 contam como bloqueio; erro 500 não bloqueia.
- 7: descrição só das candidatas, com o tipo de emprego lido dos critérios.
- 8: com o LinkedIn desligado, saída idêntica às referências da spec 013.
- 9: a seção Portais mostra os quatro portais com os termos do LinkedIn e a chave do startup.jobs; o LinkedIn vem
  desmarcado; ao marcar, o contador mostra as consultas dele; salvar grava `fontes`; sem portal nenhum, pede um
  (captura `tela-014-portais.png` no scratchpad).
- 10: busca real com o OK do usuário ("scrum master", remoto no Brasil + Portugal; 4 pedidos em 15 s, sem bloqueio):
  10 vagas por consulta (a busca pública devolve 10 por página), título, empresa, local e data lidos; modelo remoto;
  área nacional nas do Brasil e "internacional Portugal" nas de lá; descrição com os critérios e o tipo de emprego
  (Tempo integral → tempo_integral). Nada gravado.
- 11: `python -m unittest discover -s tests` → 218 testes OK.
