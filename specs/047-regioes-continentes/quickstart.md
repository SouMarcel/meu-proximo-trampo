# Quickstart: conferir as regiões

Pré-requisito: a branch da spec mesclada na branch pessoal e o dashboard reiniciado (`python iniciar.py
--sem-navegador`).

1. **Testes, sem rede**: `python -m unittest discover -s tests`. Cobrem:
   - o catálogo (cada país num continente);
   - a leitura do texto;
   - a sobreposição;
   - a autorização por região;
   - as consultas por região;
   - a validação do config;
   - o perfil;
   - a revisão.
2. **Painel**: Filtros da busca → modo internacional.
   - Regiões aceitas mostra "Seu país (Brasil)" e as dez regiões, sem "Mundo todo".
   - Marque Américas, Europa e Oceania e salve.
   - Reabra o painel: as marcas continuam.
3. **Países de interesse**: a linha Regiões aparece acima dos países.
   - Marque União Europeia: a contagem do LinkedIn sobe 1 e a dos outros portais não muda.
   - Desligue o LinkedIn: aparece o aviso "nenhum portal ligado procura por região".
   - Desmarque a região antes de seguir, se não quiser a consulta.
4. **Autorização de trabalho**: escreva "Portugal, União Europeia" e salve.
   - Um nome inventado ("Atlântida") dá o erro "país ou região desconhecido".
5. **Revisão**: `.venv\Scripts\python.exe dash\banco.py regioes` lista as vagas que voltariam (as da América Latina,
   com Américas marcada) e não grava. Grave com `--gravar` só com o OK da pessoa.
6. **Busca real** (a pessoa, quando quiser): com uma região em Países de interesse, depois da busca:
   - o resumo mostra a consulta do LinkedIn pela região;
   - as vagas mostram a etiqueta com o país do local ou com a região.

   Se as vagas vierem de lugares fora da região, o LinkedIn não reconheceu o nome. Nesse caso, anote o nome para
   ajustar `REGIAO_EN`.
