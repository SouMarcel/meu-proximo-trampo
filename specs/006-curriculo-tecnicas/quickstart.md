# Quickstart: validar o currículo com técnicas

Materiais **fictícios**: o `modelo.json` da skill, um perfil e uma vaga de exemplo gerados no teste.
Pasta temporária; PDF pelo Word do Windows (ou LibreOffice).

| # | Cenário | Esperado |
|---|---|---|
| 1 | `curriculo.py modelo.json` sem `tecnicas` | igual ao de antes desta fase (mesmo documento) |
| 2 | `--tecnicas` sem vaga e com vaga em inglês dos EUA | catálogo; sugestão `br` e depois `us` |
| 3 | `formato: us`, `estilo: compacto`, `paginas: 1` | Letter, títulos em inglês, corpo 10 pt; aviso e código 3 se passar de 1 página, com sugestões |
| 4 | `formato: eu`, `estilo: executivo` | A4, inglês, corpo 10,5 pt |
| 5 | `competencias_primeiro` e `destaques` | Competências antes de Experiência; Destaques depois do Resumo |
| 6 | `us` com `nascimento` no JSON | erro de validação |
| 7 | `conferir.py` com número inventado, empresa a mais e lacuna em Competências | veredito bloquear com os três pontos e os trechos (SC-002, SC-003) |
| 8 | `conferir.py` de um currículo fiel ao perfil, com vaga | ok, requisitos tem/sustentado/lacuna e cobertura de palavras-chave |
| 9 | Números escritos de outro jeito ("1,5 mil" × "1.500") | contam como o mesmo fato |
| 10 | `.docx` com tabela e contato no cabeçalho | conferência de ATS aponta os dois |
| 11 | Tempo da conferência | ≤ 5 s (SC-005) |
| 12 | Skill no Claude Code | pergunta as técnicas com caixas de marcar e roda a conferência antes de entregar |
| 13 | `python -m unittest discover -s tests` | todos passando |

## Resultados (09/10/2026, Windows 11)

- Antes de mexer no motor, o `.docx` do `modelo.json` foi guardado; depois das técnicas, o mesmo JSON
  sem `tecnicas` gera `document.xml` e `styles.xml` **idênticos byte a byte** (SC-006).
- Cenários 1 a 11 por um roteiro (pasta temporária, perfil e vaga fictícios, PDF pelo Word):
  **13/13**. Formato americano compacto em Letter; acima de 1 página → código 3 com sugestões de
  corte; dentro do limite, sem aviso; Destaques depois do Resumo e Competências antes da
  Experiência; dado pessoal no formato americano recusado; número inventado, empresa a mais e
  lacuna em Competências → "bloquear"; currículo fiel ao perfil → "ok" com tem/sustentado/lacuna e
  palavras-chave; "1500" × "1.500" e "trinta por cento" × "30%" como o mesmo fato; tabela e contato
  no cabeçalho apontados; conferência em 0,2 s.
- Cenário 12 (skill no Claude Code, com as caixas de marcar): a conferir pela pessoa numa conversa.
- Cenário 13: **105 testes passando** (22 novos em `tests/test_curriculo.py` e `tests/test_conferir.py`).
