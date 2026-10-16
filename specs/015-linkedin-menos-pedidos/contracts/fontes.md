# Contrato das fontes: atributos novos (opcionais)

Acréscimo ao contrato de `fontes/__init__.py`. Uma fonte sem esses atributos se comporta exatamente como hoje.

```text
AGRUPAR = True        # opcional: o vagas.py junta as consultas de um mesmo grupo numa só; a consulta chega com
                      # "termos" (lista dos cargos desta parte), "termo" (a expressão de filtros.expressao_or) e
                      # "agrupada": True. A fonte monta a busca a partir de "termo" sem tirar aspas.

MAX_DESCRICOES = 20   # opcional: no máximo N chamadas a descrever() por busca (contando as que falham). A fila
                      # começa pelas vagas do banco com descricao_pendente desta plataforma; candidatas que ficarem
                      # sem texto saem com descricao_pendente = True.

def espera() -> dict | None:
    '''Opcional: {"ate": ISO, "motivo": texto} enquanto a fonte está em espera depois de um bloqueio; None fora
    dela. Durante a espera, buscar() devolve ([], [aviso]) na primeira consulta da busca e ([], []) nas outras, e
    descrever() devolve a descrição que a vaga já tinha, sem nenhum pedido.'''

def parada() -> bool:
    '''Opcional: verdadeiro se a fonte bloqueou nesta busca ou está em espera. O vagas.py usa para decidir se uma
    vaga sem texto fica pendente (fonte parada) ou se o erro é da vaga (marca sai).'''
```

## LinkedIn (`fontes/linkedin.py`)

| Constante | Valor |
|---|---|
| `AGRUPAR` | `True` (plano B da pesquisa R1: `False`) |
| `MAX_PAGINAS` | 1 (consulta de um cargo) |
| `MAX_PAGINAS_AGRUPADA` | 3 |
| `MAX_DESCRICOES` | 20 |
| `ESPERA` | `timedelta(hours=6)` |
| `ARQ_ESPERA` | `RAIZ/.cache/linkedin-espera.json` (trocável nos testes) |

Aviso de bloqueio: `f"{BLOQUEIO} ({motivo}); em espera até {HH:MM}"`, com `motivo` conforme o research R10.

Aviso de espera (na primeira consulta de uma busca durante a espera): `"LinkedIn em espera até HH:MM ({motivo});
ficou de fora desta busca"`.
