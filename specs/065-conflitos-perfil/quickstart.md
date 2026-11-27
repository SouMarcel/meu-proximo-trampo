# Quickstart: validar a spec 065

Pré-requisito: `python iniciar.py` com a página em http://127.0.0.1:8765 e uma IA ligada (para o refazer).
Use um perfil de teste (copie o `perfil.md` antes, ou teste numa pasta com dados de demonstração).

## Testes automáticos

```text
python -m unittest tests.test_primeiros_passos
python -m unittest discover -s tests
```

Na `frontend-react`: `npm run typecheck` e `npm run build`.

## US1: perfil mudou depois do rascunho

1. Meu perfil → Atualizar o perfil → envie um material → Gerar rascunho com IA.
2. Fora do assistente, acrescente um item numa experiência do `perfil.md` (ou incorpore um relato).
3. Volte ao assistente, vá até a Revisão: aparece o aviso com as duas datas e o item novo em "sairiam".
4. "Ver o que muda" → o botão diz "Gravar mesmo assim (substitui o perfil)"; nada grava antes desse clique.
5. "Refazer o rascunho": o rascunho novo traz o item; as escolhas de conflito que continuam valendo já vêm marcadas.
6. Com a Revisão aberta, mude o `perfil.md` de novo e clique em gravar: recusa com "O perfil mudou…".

## US2: nota separada

1. Com fontes que discordam numa data, gere o rascunho.
2. Na aba Conflitos, cada opção mostra o valor e, abaixo, a nota em letra menor.
3. Escolha e grave: o perfil tem só o valor.
4. Num rascunho antigo com valor "04/2018 (comentário)" escolhido no fim de uma experiência, o Diagnóstico aponta
   "A data escolhida em … traz texto a mais".

## US3: recolher resolvidos

1. Escolha todos os conflitos e clique em Continuar.
2. Volte à aba Conflitos: aparece "Todos os conflitos estão resolvidos." e o resumo "N resolvidos (mudar)" fechado.
3. Abra o resumo, mude uma escolha, saia e volte: a escolha nova ficou.
