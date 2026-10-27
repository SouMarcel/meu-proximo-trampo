# Quickstart: verificação dos dados de contato (Windows)

Rode tudo na raiz da worktree (`..\meu-proximo-trampo-033`), com `PY` = `..\meu-proximo-trampo\.venv\Scripts\python.exe`.

## 1. Testes sem rede

```powershell
PY -m unittest tests.test_dados_contato -v
PY -m unittest discover -s tests
```

Esperado: tudo passa. Cenários (contratos em [contracts/contato.md](contracts/contato.md)):
- proposta a partir de um texto de currículo fictício, da memória e dos filtros, sem gravar;
- gravar com validação (e-mail, LinkedIn, documento recusado);
- reconhecimento por `autocomplete`, tipo e sinônimos;
- "Nome da empresa anterior" não reconhecido;
- campo sensível (cidadania) não preenchido;
- país e estado numa lista;
- "Preencher esta página" com "Full name", "E-mail", "Celular" e "LinkedIn profile" preenchidos sem chamar a IA, e com a
  IA fora do ar;
- não pisa em valor existente;
- as rotas `GET`, `PUT` e `DELETE /api/candidatura/contato` e a proposta.

## 2. Na branch pessoal de teste

1. Merge na branch de teste e reinício do dashboard (`--sem-navegador`).
2. Painel da candidatura assistida: "Propor a partir do currículo" traz nome, e-mail, telefone e LinkedIn do currículo
   base (SC-004). Conferir, corrigir e salvar.
3. Numa vaga com a candidatura assistida ligada, "Preencher esta página" num formulário novo: os campos de contato vêm
   com "seus dados de contato".
