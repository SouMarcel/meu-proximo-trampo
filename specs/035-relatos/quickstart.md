# Quickstart: Relatos

`PY` = `.venv\Scripts\python.exe`; rodar da raiz.

## Testes

```text
PY -m unittest tests.test_relatos -v
PY -m unittest discover -s tests
```

## Na página (branch pessoal, http://127.0.0.1:8765)

1. Numa vaga da Gupy com a candidatura assistida ligada, abra a vaga na janela e avance até as perguntas.
2. **Preencher esta página**:
   - "nome completo da mãe" aparece como dado cadastral ("vai como você escrever");
   - "remuneração atual" aparece como pergunta sensível que fica guardada;
   - pergunta aberta que o perfil não responde aparece com "conte com suas palavras".
3. Escreva um relato maior que o limite do formulário e clique em Preencher. A página recebe a resposta adaptada, dentro
   do limite, e o painel mostra "seu relato (adaptado pela IA)".
4. Em **Meu perfil**, a seção "Seus relatos" mostra o relato. "Levar ao perfil" acrescenta o relato ao `perfil.md`; a
   versão anterior fica em `anexos/perfis-anteriores/`.
5. Na próxima vaga com as mesmas perguntas, mesmo escritas de outro jeito, o nome da mãe e a remuneração atual são
   preenchidos sozinhos, e a pretensão continua perguntada.

`PY relatos.py lista` mostra os relatos guardados.
