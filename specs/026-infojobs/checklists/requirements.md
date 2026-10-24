# Specification Quality Checklist: InfoJobs na busca de vagas e pausa por portal

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-10-23
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Decisões da pessoa antes da spec:
  - leitura própria da busca pública (Apify e Google Jobs descartados);
  - InfoJobs ligado por padrão;
  - pausa `<PORTAL>_PAUSA` por portal, com o padrão e o mínimo de 3 s comentados no exemplo do `.env`;
  - espera de horas depois do bloqueio, como o LinkedIn.
- Nomes de variável (`<PORTAL>_PAUSA`) e do arquivo `.env` aparecem na spec porque são a interface que a pessoa usa,
  não detalhe interno.
- Esclarecimentos de 23/10/2026:
  - FR-010: espera de 24 horas;
  - FR-012: pausa ajustável só nos portais sem API que leem páginas (LinkedIn, Nerdin, InfoJobs);
  - FR-014: pausa do InfoJobs sorteada de 3 a 7 s (N a N+4 com `INFOJOBS_PAUSA`).
- Sondagem do site (23/10/2026) registrada nas Assumptions; termos de uso, paginação e códigos dos filtros ficam
  para o research.md do plano.
