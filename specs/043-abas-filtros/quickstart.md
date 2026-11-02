# Quickstart: conferir as abas do painel Filtros da busca

## Pré-requisitos

- O servidor da branch da feature mesclado na branch pessoal (pasta principal) e o dashboard reiniciado com
  `--sem-navegador`.
- O build da `frontend-react` (`vite build --base ./`) copiado para `dash/front/` da branch pessoal, só para o teste e
  sem commit.

## Verificação automática

```text
PY -m unittest discover -s tests                  # inclui tests/test_abas_filtros.py
npx -y pnpm@10.34.3 exec tsc --noEmit             # na worktree da frontend-react
npx -y pnpm@10.34.3 exec vite build --base ./
python sincronizar_skills.py --conferir
```

Esperado: tudo passa, e `GET /api/config` traz `opcoes.portais_a_mapear` com InHire, Catho e Glassdoor
([contracts/api.md](contracts/api.md)).

## Roteiro na página (`http://127.0.0.1:8765`)

1. **Abre na Geral**: em Filtros da busca, a aba Geral está ativa, com Cargos até Idiomas aceitos (US1-1).
2. **Portais**: a aba mostra Portais da busca, Portais com login e Próximos a mapear, com InHire e Catho "Em estudo"
   e Glassdoor "Não deu", com o motivo (US1-2, US3, SC-005). O contador bate com os portais marcados.
3. **Empresas**: a aba mostra "Empresas que você acompanha" e "Empresas a excluir". Colar um link e Adicionar
   funciona como antes (US1-3).
4. **Um formulário só**: mude um cargo (Geral), desmarque um portal (Portais) e remova uma empresa excluída
   (Empresas), trocando de aba no meio. Volte a cada aba: as mudanças continuam. A conta de consultas no rodapé muda
   junto. Salve, reabra o painel e confira as três mudanças; desfaça-as e salve de novo (US1-4 a 6, SC-002).
5. **Cancelar**: mude algo, clique em Cancelar e reabra. Nada foi gravado, e o painel abre na Geral.
6. **Erro em outra aba**: desmarque todos os portais da busca, vá para a Geral e salve. A mensagem "marque pelo menos
   um portal" aparece no rodapé. Cancele.
7. **Portais internacionais**:
   - com a busca internacional desligada, a aba mostra o aviso e o link;
   - o link abre Filtros da busca internacional, que não tem mais Fontes do exterior;
   - o link "Portais internacionais", no fim do painel internacional, volta para a aba certa, com o que foi editado
     ainda ali;
   - o link "Filtros da busca" volta à aba de onde a pessoa saiu (US2, FR-011).
8. **Teclado**: com o foco numa aba, ← e → trocam de aba, e Home e End vão à primeira e à última.
9. **Celular e temas**: na largura de 360 px, as quatro abas rolam na horizontal, sem a página rolar de lado; os
   temas claro e escuro ficam legíveis (SC-004).
10. **Inventário** (SC-003): cada uma das 12 seções de hoje e as 10 do painel internacional está num lugar. O painel
    internacional fica com 9, porque Fontes do exterior foi para a aba.

## Antes da entrega

Na branch pessoal: `git checkout -- dash/front` e apagar os arquivos novos em `dash/front/assets/`.
