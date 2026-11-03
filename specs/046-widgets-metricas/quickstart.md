# Quickstart: conferir os widgets do painel Métricas & Funil

## Antes

- O dashboard roda na branch pessoal, com o build de teste da página.
- Use um navegador no computador, com a janela larga (1280 px ou mais).

## Roteiro

1. **Painel de sempre:** abra Métricas & Funil.
   - O painel é o de antes: os quatro números, o funil, O que as vagas pedem com os nove blocos e as plataformas.
   - No topo, à direita, há o botão **Organizar painel**.
2. **Modo de edição:** clique em Organizar painel.
   - Aparece a faixa "Organizando o painel…", com Restaurar o padrão e Concluir.
   - Cada widget ganha contorno, alça no título e canto de redimensionar.
3. **Trocar de lugar:** arraste Suas habilidades pelo título até o topo do painel.
   - Ela se encaixa na grade.
   - Os outros abrem espaço, sem sobrepor e sem buraco.
4. **Tamanho:** puxe o canto de Tempo de experiência para a direita e para baixo.
   - A largura e a altura mudam em passos.
   - O conteúdo se espalha.
   - Puxe para cima até ficar baixo: a lista rola dentro do widget.
5. **Altura do conteúdo:** no título de Tempo de experiência, clique em Altura do conteúdo.
   - O widget volta a ter a altura da lista.
6. **Conteúdo que se ajusta:**
   - Encolha o funil até a largura mínima: as etapas ficam em 2 colunas.
   - Alargue Habilidades mais pedidas até a largura toda: a lista fica em 2 colunas.
   - Encolha um número até o mínimo: o valor aparece inteiro.
7. **Clique sem arrastar:** ainda no modo de edição, clique numa habilidade.
   - A lista das vagas abre dentro do widget.
   - Nada sai do lugar.
8. **Guardado:** clique em Concluir e recarregue a página.
   - O painel abre como você deixou, sem alça nem canto.
9. **Seletor e leitura:** com o layout mudado, troque o seletor da barra para "Todas as vagas analisadas".
   - Os nove blocos mudam, onde quer que estejam.
   - Volte para "Em Aplicações".
10. **Celular:** estreite a janela até cerca de 360 px.
    - Os widgets ficam numa coluna, na ordem do seu layout, sem rolagem para o lado.
    - Organizar painel não aparece.
    - Alargue de novo: o layout continua o seu.
11. **Restaurar:** em Organizar painel, clique em Restaurar o padrão e confirme.
    - O painel volta ao de antes.
12. **Tema:** troque para o tema escuro e entre em Organizar painel.
    - Alça, canto, contorno e a sombra ao arrastar aparecem bem.

## Conferência automática (antes de entregar para o teste)

- No front, `tsc --noEmit` e `vite build`, sem erro.
- `python -m unittest discover -s tests` continua passando: o servidor não muda.
- CDP sem janela, no build de teste: os dez passos do research D10.
  - Nunca clica em Ler os requisitos nem em Parar.
  - Usa o `localStorage` do perfil temporário do navegador, sem mexer no da pessoa.
