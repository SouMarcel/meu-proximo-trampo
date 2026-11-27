# Contrato: Colar e-mail (dash/API.md 3.11)

Todas **[local]** (403 de outro aparelho da rede), dentro das rotas de contas/candidaturas.

## `POST /api/candidaturas/email/ler`

Corpo: `{emails: string[]}`. Até 20 itens, cada um até 20.000 caracteres; itens vazios são ignorados.

Resposta 200:

```json
{
  "itens": [/* Proposta de e-mail (data-model.md) */],
  "ia": {"usada": true, "nome": "Gemini", "erro": null},
  "lidas_em": "2026-11-26T21:00:00"
}
```

`ia.usada` = algum e-mail foi à IA; `ia.erro` = mensagem quando a IA falhou (os e-mails ficam "não reconhecido").
Sem IA ligada: `ia = {usada: false, nome: null, erro: null}`.

Erros: 400 "cole pelo menos um e-mail"; 400 corpo inválido.

Nada é gravado. A leitura substitui a anterior na memória do servidor.

## `POST /api/candidaturas/email/aplicar`

Corpo: `{itens: [{chave: string, vaga_id?: string, tipo_email?: string}]}` (até 20).

Resposta 200: `{aplicados: number, anotados: number, erros: string[]}`. `aplicados` conta as propostas gravadas
(mudança de etapa ou só anotação); `anotados` quantas delas foram só anotação. Os itens aplicados saem da leitura.

Erros: 400 "não há leitura de e-mail; clique em Ler"; erro por item (vaga inexistente, tipo inválido, falta escolher)
vai em `erros`, sem parar os outros.

## `GET /api/candidaturas/email/vagas?q=texto`

Resposta 200: `{vagas: [{id, titulo, empresa, etapa}]}`, até 30. Sem `q`: as de Aplicações (com etapa, sem juntadas),
as mais recentes primeiro. Com `q`: `banco.procurar(q)` sem arquivadas e sem juntadas.
