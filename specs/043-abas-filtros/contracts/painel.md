# Contrato de tela: painel Filtros da busca com abas

## Modo nacional ("Filtros da busca")

```text
┌ Filtros da busca ─────────────────────────────────────────── X ┐
│ O que procurar nos portais. …                                   │
├─────────────────────────────────────────────────────────────────┤
│ Geral │ Portais (6) │ Portais internacionais (0) │ Empresas acompanhadas/excluídas (3) │  ← fixa, rola na horizontal
├─────────────────────────────────────────────────────────────────┤
│ [aviso de filtros sugeridos | primeira vez]   ← em qualquer aba │
│ (conteúdo da aba ativa; esta área rola)                         │
├─────────────────────────────────────────────────────────────────┤
│ [mensagem de erro]                            ← em qualquer aba │
│ Esta busca fará N consultas por portal…                         │
│                         [Somente leitura]  Cancelar  Salvar filtros │
└─────────────────────────────────────────────────────────────────┘
```

| Aba | Seções, nesta ordem |
|---|---|
| Geral | Cargos · Localidade · Modo de trabalho · Data de publicação · Tipo de emprego · Senioridade · Moedas aceitas (vagas fora do seu país) · Idiomas aceitos |
| Portais | Portais da busca · Portais com login (se houver) · Próximos a mapear (se houver) |
| Portais internacionais | [aviso + link, se a busca internacional está desligada] · Fontes do exterior |
| Empresas acompanhadas/excluídas | Empresas que você acompanha · Empresas a excluir |

**Próximos a mapear**: lista só para leitura, um portal por linha:

```text
InHire       Em estudo
Catho        Em estudo
Glassdoor    Não deu · Recusou acesso automatizado em 23/10/2026, e a API de parceiros não está aberta.
```

A dica do bloco diz: "Portais que a ferramenta estuda para entrar na busca, e os que não deram, com o motivo."

**Contadores**:
- Portais: os portais ligados, os da busca e os com login;
- Portais internacionais: as fontes do exterior ligadas;
- Empresas acompanhadas/excluídas: as empresas acompanhadas mais as excluídas.

Eles mudam junto com o formulário, antes de salvar. Para o leitor de tela: "6 ligados", "3 empresas".

**Teclado**: Tab chega à aba ativa; ← e → trocam de aba e levam o foco; Home e End vão à primeira e à última.

## Modo internacional ("Filtros da busca internacional")

- Sem abas e sem a seção "Fontes do exterior".
- O resto como hoje.
- O texto do fim: "Cargos, portais e localidade ficam em **Filtros da busca**; as fontes do exterior, na aba
  **Portais internacionais**."
  - O primeiro link volta à aba de onde a pessoa saiu.
  - O segundo abre a aba Portais internacionais.
