# Quickstart: validar "começar pelo currículo"

Servidor no roteiro, config e banco temporários, currículos fictícios (PDF e DOCX, PT e EN, um com CPF e data de
nascimento), IA falsa local, Chrome sem janela.

| # | Cenário | Esperado |
|---|---|---|
| 1 | Sem perfil: enviar currículo, "Usar este currículo" | proposta com texto, perfil e filtros, sem perguntas da anamnese |
| 2 | Confirmar | perfil (com a origem) e filtros gravados, currículo base marcado, painel de busca aberto; busca não começa (SC-001) |
| 3 | Fechar sem confirmar | nada gravado (SC-003) |
| 4 | Currículo com CPF/RG/nascimento | nada disso no perfil nem no pedido à IA (SC-002) |
| 5 | Sem IA, currículo PT e currículo EN | cargo mais recente nos filtros (SC-005) |
| 6 | Com perfil existente: manter | perfil igual, currículo base marcado |
| 7 | Currículo base PT e EN; vaga PT, vaga EN, vaga EN sem base EN | item com o arquivo certo e "Pronto", ou o aviso e "A fazer" (SC-004); link abre só o arquivo marcado |
| 8 | Meu perfil com perfil do currículo | aviso e "Completar com a anamnese" |
| 9 | PDF escaneado (sem texto) | explicação e opções |
| 10 | Chat: `curriculo_base.py proposta/usar/marcar` | mesmas regras |
| 11 | `python -m unittest discover -s tests` | todos passando |

## Resultados (10/10/2026, Windows 11)

- Referências do `vagas.py` iguais às de antes desta fase.
- Cenários 1 a 9 por um roteiro (servidor no roteiro, config e banco temporários, currículos fictícios em DOCX
  e PDF, Chrome sem janela): **19/19**. Lista de `anexos/`; proposta com perfil e filtros sem gravar nada; sem
  CPF nem data de nascimento; cargo mais recente sem IA em português e em inglês; PDF sem texto explicado;
  arquivo fora de `anexos/` recusado; confirmar grava perfil (com a origem), filtros (idiomas e busca no
  exterior mantidos) e o seu currículo; "manter o perfil" deixa perfil e filtros iguais e só marca o currículo;
  item Currículo com o arquivo do idioma da vaga e "Pronto", ou o aviso; link só para o arquivo marcado; Meu
  perfil com o aviso e "Completar com a anamnese"; botões e tela de confirmação na página (captura conferida).
- Achados na validação: a proposta de filtros dos primeiros passos desligaria a busca no exterior e apagaria os
  idiomas aceitos (por isso os filtros partem dos atuais e só trocam cargos, cidade e modelos); "manter o perfil"
  gravava os filtros (corrigido: manter é só marcar o currículo).
- Cenário 10 (chat): coberto pelos testes da linha de comando.
- Cenário 11: **173 testes passando** (9 novos em `tests/test_curriculo_base.py`).
