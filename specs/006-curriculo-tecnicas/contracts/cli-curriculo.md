# Contrato: linha de comando do currículo

```text
PY curriculo.py <arquivo.json> [--sem-pdf]
    gera .docx (e .pdf); com "tecnicas" no JSON, aplica formato, estilo, ordem e limite de páginas;
    com perfil, roda a conferência no fim e mostra o veredito
    códigos: 0 ok · 1 erro de geração · 2 JSON inválido · 3 acima do limite de páginas ou conferência "bloquear"

PY curriculo.py --tecnicas [--vaga-id ID | --vaga arquivo.txt]
    catálogo das técnicas e escolhas, com a sugestão para o alvo, em JSON

PY conferir.py <arquivo.json> [--vaga arquivo.txt | --vaga-id ID] [--perfil caminho] [--json]
    conferência sem IA (ATS, requisitos × perfil, fatos)
    códigos: 0 ok · 1 conferir · 3 bloquear · 2 erro de uso
```

O `.docx` conferido é o que está ao lado do JSON (mesmo nome); sem ele, só as conferências que
dependem do conteúdo rodam e a de ATS do documento fica como "não conferida".
