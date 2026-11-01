# Contrato: API do dashboard (empresas acompanhadas)

| Rota | Corpo | Resposta |
|---|---|---|
| `POST /api/empresas/reconhecer` (nova) | `{url*}` (até 1.000) | `{empresa: {sistema, id, nome, url}, rotulo, ia_necessaria: bool, ia_ligada: bool}`; 400 com a mensagem (portal de vagas, link inválido, página fora do ar). Não grava nada. |
| `POST /api/empresas` | `{url*}` | como hoje, mas reconhece por `ats.descobrir` (domínio desconhecido: um pedido à página) |
| `GET /api/empresas` | — | como hoje; `sistema` pode ser `teamtailor`, `ey` ou `pagina` |
| `PUT /api/config` | `empresas: [{sistema, id, nome, url}]` | a empresa com `sistema` é conferida sem pedido (`ats.conferir`); link solto de domínio desconhecido: 400 "use o botão Adicionar" |
| `GET /api/config` | — | `opcoes.fontes_nac` sem a EY; `filtros.empresas` já com a EY migrada |

- `rotulo`: "Greenhouse", "Lever", "Ashby", "Teamtailor", "Site de vagas da EY" ou "Página própria (lida pela IA)".
- `ia_necessaria` é verdadeiro na página própria; com `ia_ligada` falso, o painel avisa que a página só é lida com a
  IA ligada.
- Plataformas novas nas vagas: `Teamtailor` e `Site da empresa`.
