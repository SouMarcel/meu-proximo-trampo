# Quickstart: validar os portais com login

## 1. Testes automáticos (sem rede e sem navegador)

```powershell
.venv\Scripts\python.exe -m unittest tests.test_sessao tests.test_mygreenhouse tests.test_buscador
.venv\Scripts\python.exe -m unittest discover -s tests
```

O que esperar:

| Caso | Resultado esperado |
|---|---|
| Portal desligado | zero pedidos |
| Fora da página | só o aviso, sem abrir a janela |
| Duas páginas | junta as vagas e para com `moreResultsAvailable: false` |
| Campos da conta | não aparecem na vaga |
| Id | igual ao das empresas acompanhadas |
| 409 | uma recarga só; repetiu, "mudou" |
| 429 | 24 h de espera, sem nenhum pedido depois |
| Login caído | "aguardando_login"; logou, segue; sem login, pulado com aviso; cancelar interrompe |
| Desconectar | apaga as origens; apaga o perfil só sem nenhum portal conectado |

## 2. Teste real na branch pessoal (com a pessoa)

1. Reinicie o dashboard (`dash\servidor.py --sem-navegador`) e abra http://127.0.0.1:8765.
2. Ligue o portal: em Filtros da busca → Portais com login, ligue o MyGreenhouse Jobs. Deve aparecer o aviso de risco;
   ao confirmar, o portal fica "desconectado".
3. Conecte:
   1. clique em Conectar e entre na janela (pode ser pelo LinkedIn);
   2. clique em Pronto. O portal fica "conectado" e a janela volta a minimizar.
4. Clique em Buscar na página. O progresso deve mostrar o MyGreenhouse, e no relatório as vagas aparecem com a etiqueta
   "MyGreenhouse", se houver alguma aberta ao Brasil para os cargos. Pode não vir nenhuma (research R3); confira os
   avisos e o resumo.
5. Simule o login caído:
   1. saia da conta na aba do MyGreenhouse e busque de novo;
   2. a janela deve vir para a frente, e a página mostra "Aguardando login";
   3. entre e veja a busca seguir. Repita sem entrar: depois de 3 minutos, o portal é pulado com aviso.
6. Teste fora da página: `.venv\Scripts\python.exe vagas.py buscar --fontes mygreenhouse` deve mostrar o aviso "só pelo
   botão Buscar da página" e não abrir a janela.
7. Desconecte. O portal volta para "desconectado", e a conexão da Gupy ou do Indeed, se houver, continua.
