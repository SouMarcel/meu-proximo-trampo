# Quickstart: validar a spec 038

## Pré-requisitos

O build da `front-038-vagas-analisadas` copiado para `dash/front/` da branch pessoal, sem commit. A página precisa ser
recarregada (sem reiniciar o servidor, porque o backend não muda).

## Automático

```text
(frontend-react) pnpm exec tsc --noEmit && pnpm exec vite build --base ./
python -m unittest discover -s tests
```

## Na página (Relatório de Vagas)

1. **Caixa "Analisadas" desmarcada**:
   - com Nota mínima 70, as vagas sem nota (aguardando a IA, descrição pendente, falha) continuam em Para decidir;
   - o mesmo vale com Senioridade, Modo e "Publicada há até";
   - a busca por texto continua filtrando todas.
2. **Caixa marcada**:
   - as vagas sem nota somem de Para decidir, de Não seguidas e de Fora dos critérios;
   - os números das abas caem;
   - a vaga com nota provisória continua.
3. **"Mostrando X de Y (N sem análise ocultas)"** aparece com a caixa marcada.
4. **"Marcar todas como não seguidas"**, com a caixa marcada: o número no botão de confirmar é o das vagas visíveis.
5. **Persistência**: recarregar a página mantém a caixa. "Limpar filtros" a desmarca.
6. **Tema escuro e celular**: a caixa aparece e quebra a linha sem rolagem lateral.

## Antes da entrega

- `git checkout -- dash/front` na branch pessoal e apagar os assets novos.
