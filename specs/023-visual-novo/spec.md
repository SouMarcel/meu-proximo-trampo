# Feature Specification: Visual do front novo no dashboard atual

**Feature Branch**: `023-visual-novo` (worktree saída da `master`; testada na branch pessoal antes da `master`)

**Created**: 2026-10-20

**Status**: Concluída (2026-10-20): testada e aprovada pela pessoa

**Input**: User description: "Aplique o estilo novo à dash antiga para eu testar."

## Contexto

O front novo em React (spec 022, em `/novo/`) tem o visual aprovado, mas só o Relatório de Vagas está ligado ao
servidor. O dashboard atual (`dash/dashboard.html`, em `/`) tem todas as funções. Esta spec leva o visual do front
novo para o dashboard atual, sem mudar a lógica, as rotas nem os ids.

## Requirements

- **FR-001**: paleta do front novo (cinza-azulado e índigo; verde, âmbar, rosa e azul para os estados) nas
  variáveis do `:root`, que o CSS inteiro já usa.
- **FR-002**: tema claro por padrão, escuro pelo sistema (`prefers-color-scheme`) e um botão no cabeçalho
  (sistema → claro → escuro). A escolha fica só no navegador (`localStorage`, chave `tema`) e é aplicada antes de
  pintar a página; sem ela, vale o do sistema.
- **FR-003**: fontes do sistema; sai o Google Fonts (nenhum pedido para fora do computador).
- **FR-004**: componentes no estilo do front novo:
  - abas em pílula e botões com cantos de 12 px;
  - cartões e Relatório com cantos de 16 px e sombras leves;
  - selos e plataformas arredondados;
  - nota em destaque, diálogos com fundo desfocado, foco dos campos com anel índigo.
- **FR-005**: nada muda no comportamento: o mesmo HTML gerado, as mesmas rotas e os mesmos testes.

## Success Criteria

- **SC-001**: as telas do dashboard (Quadro, Relatório, Internacional e as caixas de diálogo) ficam legíveis nos
  dois temas.
- **SC-002**: a página não faz nenhum pedido para fora de `127.0.0.1`.
- **SC-003**: `python -m unittest discover -s tests` continua passando.

## Fora do escopo

As abas que só existem no front novo (Métricas e Funil, Preparador de Entrevistas como aba) e o cabeçalho com marca:
são mudanças de função ou de estrutura, não de visual.
