# Contrato: `GET /api/config` → `opcoes.portais_a_mapear`

Acréscimo em `dash/API.md` §3.4. O resto da resposta e o `PUT /api/config` não mudam.

```json
{
  "opcoes": {
    "…": "as opções de hoje",
    "portais_a_mapear": [
      {"nome": "InHire", "situacao": "em_estudo", "motivo": ""},
      {"nome": "Catho", "situacao": "em_estudo", "motivo": ""},
      {"nome": "Glassdoor", "situacao": "nao_deu",
       "motivo": "Recusou acesso automatizado em 23/10/2026, e a API de parceiros não está aberta."}
    ]
  }
}
```

- `situacao`: `em_estudo` ou `nao_deu`.
- `motivo`: preenchido só quando `nao_deu`.
- Lista vazia, ou o campo ausente (servidor antigo): a página não mostra o bloco "Próximos a mapear".
- O campo é só para leitura: a página não grava nada dele.

Tipo no front (`src/services/api/config.ts`):

```ts
export interface PortalAMapear {
  nome: string
  situacao: "em_estudo" | "nao_deu"
  motivo: string
}
// em Opcoes:
portais_a_mapear?: PortalAMapear[]
```
