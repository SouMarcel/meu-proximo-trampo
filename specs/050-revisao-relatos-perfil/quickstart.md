# Quickstart: validar a revisão do perfil (spec 050)

## Testes automáticos

```powershell
.venv\Scripts\python.exe -m unittest tests.test_revisao_perfil tests.test_reprovacao tests.test_relatos -v
.venv\Scripts\python.exe -m unittest discover -s tests   # não regressão (SC-001)
```

Os testes de `tests/test_revisao_perfil.py` usam IA falsa e perfil, relatos e análise temporários, e cobrem:
- a estrutura do perfil (seções e cargos) e o pedido à IA com os lugares e os relatos (sem os "só neste currículo");
- a conferência: linha atual que não existe, lugar inexistente, número fora das fontes, afirmação de falta,
  assunto sensível, seção não permitida;
- o "sai" das linhas cruas da seção "Relatos";
- as decisões, o bloqueio por discordância sem escolha e a correção escrita;
- `aplicar`: entra no fim do cargo, entra em seção, muda, sai, seção Relatos vazia que sai, ordem de baixo para cima;
- a gravação: só os aceitos, versão anterior guardada, 409 com perfil mudado, relatos `no_perfil` só com item aceito,
  respostas da análise com `revisado_em`;
- sem IA: o caminho de hoje com o aviso;
- o gerador (tipo, alvo `perfil`, tentar) e as rotas (202, 200 sem IA, 400, 404, 409, 403 de fora).

## Teste à mão (na branch de uso pessoal, depois do merge)

1. Reinicie o dashboard (`python iniciar.py --sem-navegador`) e abra uma vaga com análise de reprovação.
2. Responda uma pergunta com **Tenho** e **Levar ao meu perfil** e outra com **Usar só neste currículo**. Clique em
   **Reescrever e gerar o currículo**. Confira:
   - o currículo sai como antes;
   - o `perfil.md` não mudou;
   - a seção mostra "1 resposta para levar ao seu perfil" e o relato aparece em Meu perfil → Seus relatos, fora do
     perfil.
3. Clique em **Revisar e levar ao perfil**. Com a proposta pronta, confira:
   - os itens no cargo certo, com "antes → depois" nos que mudam;
   - a resposta "só neste currículo" não aparece;
   - as discordâncias com os dois trechos, e o Gravar desabilitado até escolher.
4. Recuse um item, escolha nas discordâncias e clique em **Gravar no perfil**. Confira o `perfil.md`, a versão
   anterior em `anexos/perfis-anteriores/` e "levadas ao perfil em …" na seção.
5. Em Meu perfil → Seus relatos, marque um relato antigo já colado na seção "Relatos" e revise. A proposta traz o
   "sai" da linha crua; depois de gravar, a linha some e o fato está no cargo.
6. Mude o `perfil.md` com uma proposta aberta e clique em Gravar: aparece "o seu perfil mudou desde a proposta".
7. Com a IA desligada, Revisar e levar ao perfil leva o relato para a seção "Relatos", com o aviso.
