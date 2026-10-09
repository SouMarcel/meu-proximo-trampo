# Quickstart: validar o currículo pela página

Servidor da worktree subido no roteiro (porta 8799), config, banco, perfil e pasta de currículos
temporários; IA falsa local que devolve um currículo no formato do `modelo.json` (fiel ao perfil, ou
com um número inventado, ou inválido); PDF pelo Word.

| # | Cenário | Esperado |
|---|---|---|
| 1 | Catálogo para uma vaga dos EUA e para o base | sugestão `us` com motivo; base `br` |
| 2 | Sem IA / sem perfil: `POST /api/curriculo` | `400` com a orientação; nenhum pedido à IA |
| 3 | Gerar para uma vaga (IA fiel) | andamento; `.json/.docx/.pdf/.meta.json` em `curriculos/` com nome data-empresa-cargo; vaga com `curriculos`; veredito ok ou conferir; links abrem |
| 4 | O pedido à IA | traz perfil sem CPF, vaga, técnicas, guia, modelo e lacunas; nada antes do POST |
| 5 | IA que inventa um número | currículo na lista como **não pronto**, com o número apontado (SC-003) |
| 6 | IA que devolve conteúdo inválido / falha | `falha` com motivo; nada na lista; `tentar` refaz com as mesmas escolhas |
| 7 | Segunda geração durante a primeira | `409` |
| 8 | Currículo base duas vezes | duas versões na lista do base, nenhuma sobrescrita |
| 9 | Arquivo fora da pasta (`../config.json`, nome inválido) | `404` |
| 10 | Pela rede | lista e arquivos sim; gerar → `403` |
| 11 | Página no Chrome sem janela | seção Currículos no detalhe, diálogo de técnicas, lista com veredito |
| 12 | `python -m unittest discover -s tests` | todos passando |

## Resultados (09/10/2026, Windows 11)

- Cenários 1 a 11 por um roteiro (servidor no roteiro, config, banco, perfil e pasta de currículos
  temporários, IA falsa local, PDF pelo Word): **15/15**. Currículo da vaga em 4,7 s com a IA falsa
  (nome `AAAA-MM-DD-empresa-omega-analista-de-dados-pleno`, `.json/.docx/.pdf/.meta.json`, vaga
  ligada); PDF inline e .docx anexo; pedido sem CPF, com técnicas, lacunas, modelo e vaga, e nada
  antes do clique; número inventado → "não pronto"; resposta inválida e IA fora do ar → falha com
  motivo, sem arquivo pela metade, e "tentar de novo" com as mesmas escolhas; segunda geração → 409;
  currículo base duas vezes, duas versões; arquivos fora do padrão → 404; pela rede, ver sim e gerar
  → 403; no Chrome sem janela, a seção Currículos no detalhe da vaga e o diálogo de técnicas com a
  sugestão (captura conferida).
- Cenário 12: ver `python -m unittest discover -s tests` (116 testes, 11 novos em
  `tests/test_curriculo_ia.py`).

