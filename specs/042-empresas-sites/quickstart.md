# Quickstart: validar as empresas acompanhadas em qualquer página

## 1. Testes automáticos (sem rede e sem IA)

```powershell
.venv\Scripts\python.exe -m unittest tests.test_empresas_sites tests.test_empresas_acompanhadas tests.test_ey
.venv\Scripts\python.exe -m unittest discover -s tests
```

| Caso | Esperado |
|---|---|
| Feed do Teamtailor | vagas com título, local, modelo, data, link e descrição; id `teamtailor-<host>-<n>` |
| Página própria | uma vaga por bloco; cargo fora do texto descartado; e-mail só se escrito; mesma marca sem IA; sem IA, aviso |
| EY sem resultado | zero vagas, sem aviso |
| Migração | EY ligada → EY em empresas e fora de `fontes`; EY desligada ou config novo → nada |
| Reconhecer | Varejista (página com o feed) → teamtailor; consultoria → pagina; LinkedIn → recusado |
| Bloqueio | 429 no host: sem nova tentativa, as outras empresas seguem |

## 2. Teste na branch pessoal (com a pessoa)

1. Reinicie o dashboard (`dash\servidor.py --sem-navegador`) e abra http://127.0.0.1:8765.
2. Em Filtros da busca, confira:
   - a EY sumiu da lista de portais;
   - a EY está em Empresas que você acompanha.
3. Adicione os dois links e confira o rótulo de cada um:
   - `https://carreiras.varejista.com.br/jobs` deve aparecer como "Teamtailor";
   - `https://consultoria.com.br/carreira/#vagas` deve aparecer como "Página própria (lida pela IA)".
4. Salve e clique em Buscar. No relatório devem aparecer:
   - as vagas da varejista que batem com os cargos e o local;
   - as da consultoria que batem com os cargos, com a etiqueta "Site da empresa".
5. Busque de novo depois do intervalo: a consultoria não deve chamar a IA (a página não mudou), e nada volta como novo.
