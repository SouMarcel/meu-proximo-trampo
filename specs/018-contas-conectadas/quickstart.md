# Quickstart: verificar as contas conectadas

## Pré-requisitos

- Windows com o Edge;
- dashboard da branch pessoal reiniciado com `--sem-navegador`;
- contas da Gupy e do Indeed.

## Testes automáticos

```text
.venv\Scripts\python.exe -m unittest discover -s tests
```

Esperado: todos passam, incluindo `tests/test_navegador.py` e `tests/test_contas.py`.

## Na página

1. **Painel:** "Atualizar candidaturas" mostra Gupy e Indeed com o ícone e o estado. O LinkedIn não aparece.
2. **Conectar o Indeed:** a janela abre no login → logar → "Pronto" → "Conectado".
3. **Conectar a Gupy:** a mesma coisa, com "Entrar com LinkedIn".
4. **Atualizar agora:**
   - aparece "Lendo suas candidaturas…" e a janela fica minimizada;
   - se a Gupy pedir login, a janela vem para a frente e a tela diz "Faça o login na Gupy na janela que abriu"; um
     clique em "Entrar com LinkedIn" e a leitura segue sozinha;
   - no fim, a janela fica minimizada (aberta); uma segunda leitura logo depois não pede login de novo.
5. **Proposta:** agrupada por portal. As mudanças e as idas ao quadro vêm marcadas; as novas finalizadas vêm
   desmarcadas. Conferir com o que a Gupy e o Indeed mostram.
6. **Aplicar marcadas:** o quadro muda só no que foi marcado. O cartão tem a linha "Etapa atualizada pela …", e os
   lembretes de follow-up usam a data do portal.
7. **Atualizar agora de novo:** o que foi aplicado aparece como "sem mudança".
8. **Desconectar o Indeed:** a próxima leitura pede login de novo no Indeed.
9. **Portal com problema:** desconectar a Gupy e atualizar. O Indeed é lido e a Gupy aparece com o aviso.
