# Quickstart: verificação das empresas acompanhadas (Windows)

Rode tudo na raiz da worktree (`..\meu-proximo-trampo-031`), com `PY` = `..\meu-proximo-trampo\.venv\Scripts\python.exe`.

## 1. Testes sem rede

```powershell
PY -m unittest tests.test_empresas_acompanhadas -v
PY -m unittest discover -s tests
```

Esperado: tudo passa. Cenários (contratos em [contracts/empresas.md](contracts/empresas.md)):
- "Remote, Brazil", "Latin America" e "Anywhere" entram na nacional;
- "Remote, United States" e "Remote" sozinho ficam de fora;
- presencial na cidade da pessoa entra na consulta da cidade;
- uma lista por empresa para as duas áreas;
- 429 no Greenhouse para as outras empresas dele, e as do Lever seguem;
- 404 com o aviso de empresa que saiu do sistema;
- config antigo com `internacional.empresas` continua valendo, e o salvar passa a lista para cima;
- `POST /api/empresas` acompanha, deduplica e respeita o máximo;
- `POST /api/vagas/link` traz `empresa` com `acompanhada`.

## 2. Na branch pessoal de teste

1. Merge na branch de teste e reinício do dashboard (`--sem-navegador`).
2. Com a busca internacional desligada e uma empresa acompanhada que tenha vaga remota aberta ao Brasil:
   `PY vagas.py buscar --fontes ats`. As vagas dela aparecem com a busca "remoto".
3. Com o front novo (depois do push e do PR): a seção "Empresas que você acompanha" aparece em "Filtros da busca", com
   a lista que já existia.
4. Cole no Adicionar Vaga um link de vaga do Greenhouse, do Lever ou do Ashby: aparece "Acompanhar <empresa>".
5. No detalhe de uma vaga com candidatura num desses sistemas: aparece "Acompanhar empresa", ou "Acompanhando".

## 3. Ordem de entrega

1. O back-end vai para a master (o PR #14 do JobGether pode ser mesclado antes).
2. Depois, o push do front para a `frontend-react` e o PR novo.
