# Specification Quality Checklist: Informações básicas e idiomas com nível

**Created**: 2026-10-29 · **Feature**: [spec.md](../spec.md)

## Content Quality

- [x] Sem detalhe de implementação além do costume das specs do projeto (arquivos de dados e documentos citados)
- [x] Foco no valor para a pessoa: dados dela onde ela procura, nível de idioma padronizado
- [x] Escrita para quem usa a ferramenta
- [x] Seções obrigatórias completas

## Requirement Completeness

- [x] Sem [NEEDS CLARIFICATION]: as quatro decisões foram tomadas pelo usuário em 29/10
- [x] Requisitos testáveis e sem ambiguidade (FR-001 a FR-016)
- [x] Critérios de sucesso mensuráveis (cliques, blocos, % de linhas com nível reconhecido)
- [x] Critérios de sucesso sem tecnologia
- [x] Cenários de aceitação em todas as histórias
- [x] Casos de borda: outro aparelho, Outro sem nome, repetição, resposta antiga irreconhecível, pergunta pulada
- [x] Escopo delimitado: contato do `perfil.md` e login no Conectar ficam fora
- [x] Dependências e premissas descritas (reconhecimento de nível atual, rotas e arquivos sem mudança, front pela Action)

## Feature Readiness

- [x] Todo requisito tem critério de aceite
- [x] As histórias cobrem os fluxos principais (aba nova, diálogo enxuto, idiomas, respostas antigas, avisos)
- [x] Resultados mensuráveis definidos
- [x] Sem vazamento de implementação

## Notes

- Nível de respostas antigas: só sigla do CEFR ou "nativo" viram nível; o resto a pessoa escolhe (constituição: só
  fatos confirmados, nada de estimar níveis).
