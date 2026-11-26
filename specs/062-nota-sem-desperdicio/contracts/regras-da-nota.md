# Contrato: arquivo de regras da nota

`.agents/skills/buscar-vagas/regras-da-nota.md`, lido por `dash/analise.py` (`montar_pedido`), pelo
`calibrar_nota.py` e pelo assistente do chat (a skill aponta para ele).

## Estrutura

```markdown
# Regras da nota                       ← ignorado no pedido

## Resposta                            ← o array JSON, um objeto por vaga: campos e o caso "sem_dados"
## Campos                              ← como preencher modelo, senioridade, candidatura, requisitos
## Como dar a nota                     ← pesos, faixas, regras de honestidade
## Vaga do exterior                    ← vai só quando o grupo tem vaga da área internacional
## Portais                             ← não vai inteiro
### Gupy                               ← vai só quando o grupo tem vaga com plataforma "Gupy"
### Nerdin
...
```

## Regras

- O nome de cada `### ` é exatamente o `PLATAFORMA` da fonte (`fontes/*.py`), como fica em `vaga["plataforma"]`.
- O texto é para a IA: sem comandos, sem "no chat", sem o que a página mostra, sem nomes nem dados de uma pessoa.
- Os campos de `## Resposta` são os mesmos de hoje (o formato gravado não muda); `banco.aplicar_analises` continua a
  validação.
- O código procura as seções pelo título `## <nome>`; um título renomeado quebra o teste
  `tests/test_nota_regras.py`.
- Parte fixa (tudo menos `## Vaga do exterior` e `## Portais`, as seções de `analise.CONDICIONAIS`): no máximo 5,5
  mil caracteres. As seções condicionais vão depois de `## Vagas`, para não mudar o começo do pedido.
- No pedido, as linhas quebradas do arquivo são juntadas (`analise._compactar`); listas e títulos ficam.
- `dash/requisitos.py` lê do mesmo arquivo o item `` - `requisitos`: `` (até `## Como dar a nota`) para a leitura
  avulsa dos requisitos.
- Mudou o arquivo → `python sincronizar_skills.py` e `PY calibrar_nota.py` antes de levar à `master`.
