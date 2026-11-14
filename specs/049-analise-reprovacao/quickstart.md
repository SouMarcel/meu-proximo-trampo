# Quickstart: validar a análise de reprovação (spec 049)

## Testes automáticos

```powershell
.venv\Scripts\python.exe -m unittest tests.test_reprovacao -v
.venv\Scripts\python.exe -m unittest discover -s tests   # não regressão (SC-001)
```

Os testes de `tests/test_reprovacao.py` usam uma IA falsa, banco, perfil e pasta de currículos temporários, e
cobrem:
- a escolha do currículo analisado: vaga → arquivo base → base gerado → perfil, com os avisos;
- a leitura tolerante e a conferência: grupos, trecho achado ou não, negação que vira pergunta, sensíveis, limite de
  10;
- a guarda de uma análise por vaga: a nova substitui a anterior, e as outras vagas não mudam;
- a validação das respostas e o cálculo de estado, resumo e pronta para gerar;
- o destino `perfil` (vai ao `perfil.md` e a Seus relatos, sem duplicar no Tentar de novo) e o destino `so_aqui`
  (não vai a nenhum dos dois);
- o pedido do currículo com os ⚠️, os trechos reescritos e os ❌, e o meta `reprovacao: true`;
- a conferência da reescrita (número inventado ganha aviso);
- o gerador: tipos, situações, fila e tentar;
- as rotas: 202, 400, 404, 409 e 403 fora deste computador.

## Teste à mão (na branch de uso pessoal, depois do merge)

1. Reinicie o dashboard (`python iniciar.py --sem-navegador`) e abra uma vaga com descrição.
2. Clique em **Gerar currículo**, marque **Análise de reprovação** e clique em **Gerar**. A seção mostra "Analisando
   como um recrutador…", e nenhum currículo novo aparece.
3. Com a análise pronta, abaixo da lista de currículos devem aparecer:
   - os motivos agrupados, com o trecho do currículo e a frase da vaga;
   - qual currículo foi analisado;
   - as perguntas.
4. Responda:
   - uma pergunta com **Não tenho** (❌);
   - uma com **Tenho**, relato e **Levar ao meu perfil** (⚠️);
   - uma com **Tenho** e **Usar só neste currículo**;
   - pule as demais.

   Feche e reabra a janela: as respostas continuam lá.
5. Clique em **Reescrever e gerar o currículo**. Confira:
   - os trechos aparecem como "antes → depois";
   - o currículo novo entra na lista com "com análise de reprovação";
   - o relato "Levar ao meu perfil" aparece em Meu perfil → Seus relatos ("no perfil") e no `perfil.md`;
   - o relato "só neste currículo" não aparece em nenhum dos dois;
   - o item ❌ não aparece como competência no currículo.
6. Rode a análise de novo na mesma vaga. O diálogo avisa a substituição, e só a nova análise fica na janela.
7. Gere um currículo com o checkbox desmarcado: tudo sai como antes.
