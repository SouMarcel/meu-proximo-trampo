# Data Model: Fontes internacionais e elegibilidade

## Configuração (`config.json → internacional`, campos novos)

```text
fontes: [remotive|himalayas|remoteok|jobicy|weworkremotely|getonboard]   # vazio por padrão
empresas: [{sistema: greenhouse|lever|ashby, id, nome, url}]             # normalizadas pelo link
frases_restricao: [texto]      # cada uma corta a vaga que a contém (vaga internacional)
frases_positivas: [texto]      # cada uma vira sinal positivo
```

Validação: fontes do catálogo; empresas reconhecidas por `ats.reconhecer(url)` (link de outro
sistema → erro com a explicação); até 50 empresas e 30 frases de cada tipo, 120 caracteres cada.

## Fonte (`fontes/<nome>.py`)

Contrato de hoje + `AREAS = ("internacional",)` e `POR_PAIS = False`; `TERMOS` (texto curto sobre os
termos de uso, para o painel e o README).

## Consulta

Grupo novo `internacional:global` (um por cargo em inglês), `area: internacional`, `global: True`.

## Vaga (campos novos)

| Campo | Regra |
|---|---|
| `restricao_local` | texto de restrição de local ou região do portal (até 200) |
| `ats` | sistema de candidatura (`greenhouse`, `lever`, `ashby`) quando conhecido |
| `sinais` | lista: "Oferece patrocínio de visto", "Oferece relocation", frases positivas próprias |
| `moeda`, `salario`, `url_candidatura` | já existem; preenchidos pela fonte quando ela informa |

## Elegibilidade (`filtros.elegibilidade(v, f) -> {motivos, sinais}`)

`motivos` entram em `criterios()` (Fora dos critérios); `sinais` são gravados na vaga.
