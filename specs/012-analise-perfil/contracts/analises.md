# Contrato: análises do perfil

## Rotas (as que gravam, só deste computador)

| Rota | O que faz |
|---|---|
| `GET /api/analises-perfil` | as análises salvas, a prontidão calculada agora e se há IA |
| `POST /api/analises-perfil/lacunas` | `{visao}` → calcula, salva e devolve o ranking (ou `{faltam: N}`) |
| `POST /api/analises-perfil/plano` | IA: plano de estudo para as lacunas do topo da última análise |
| `POST /api/analises-perfil/cargos` | IA: cargos-alvo |
| `POST /api/analises-perfil/cargos/filtros` | `{cargos: [{titulo, titulo_en}], confirmar}` → sem `confirmar`, a proposta (`filtros`, `mudancas`); com, grava |
| `PUT /api/analises-perfil/marcas` | `{linkedin_en: bool}` |

## Módulo `analise_perfil.py`

```text
lacunas(vagas, perfil, visao) -> {vagas, faltam?, itens}     prontidao(perfil, cfg) -> [Item]
cargos_alvo(perfil) -> [Cargo]                               plano_estudo(perfil, lacunas) -> [..]
filtros_com_cargos(cargos) -> {filtros, mudancas}           carregar() / salvar(tipo, resultado) / marcar(chave, valor)
```

## Linha de comando

```text
PY analise_perfil.py lacunas [--seguidas]
PY analise_perfil.py prontidao
PY analise_perfil.py cargos            # precisa de IA
PY analise_perfil.py plano             # precisa de IA; usa a última análise de lacunas
```
