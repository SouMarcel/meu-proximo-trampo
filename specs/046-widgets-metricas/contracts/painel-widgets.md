# Contrato de tela: widgets no painel Métricas & Funil

## Topo do painel

- **Fora do modo de edição:** um botão discreto à direita, **Organizar painel**, com o ícone de layout
  (`LayoutDashboard`).
- **No modo de edição:** no lugar do botão, uma faixa em índigo claro (escuro no tema escuro) com:
  - o texto "Organizando o painel: arraste pelo título e puxe o canto para mudar o tamanho";
  - o botão **Restaurar o padrão** (contorno);
  - o botão **Concluir** (cheio, índigo).
- **Restaurar o padrão** pergunta "Voltar o painel ao layout padrão? A posição e o tamanho que você escolheu serão
  perdidos." Com OK, o padrão volta, e o modo de edição continua.
- **Abaixo de 768 px de largura do painel:** nem o botão nem a faixa aparecem.

## Widget

- **Atributos:** o elemento de cada widget tem `data-widget="<id>"`, com o id do data-model §1, para a conferência e a
  acessibilidade.
- **Moldura:** a mesma de hoje: fundo branco (`slate-900` no escuro), borda, cantos de 16 px e sombra leve.
  - O título fica no alto, e o corpo ocupa o resto.
  - O corpo é um contêiner (`@container`) com a barra de rolagem fina do projeto (`rolagem-fina`).
- **Título por tipo:**
  - **número:** rótulo à esquerda e ícone em quadrado colorido à direita;
  - **seção:** `h3` e subtítulo;
  - **bloco:** `h4` com ícone.
- **No modo de edição:**
  - o título ganha a classe `alca-widget`, o ícone `GripVertical` à esquerda, o cursor de mover e o
    `title="Arraste para mudar de lugar"`;
  - a moldura ganha um contorno tracejado índigo;
  - o canto inferior direito mostra a marca de redimensionar, visível nos dois temas, a 16 px do pé do item (o espaço
    até o widget de baixo);
  - o widget de altura fixa mostra no título o botão **Altura do conteúdo** (ícone `ArrowUpDown`), que volta a altura
    automática.
- **Ao arrastar:** a sombra do lugar novo é um retângulo tracejado índigo com fundo índigo bem claro, sem o vermelho
  da biblioteca.
- **Rolagem:** com a altura fixa, o conteúdo que passar rola dentro do corpo. Com a altura automática, o widget cresce
  e os de baixo descem.

## Conteúdo por largura do widget

| Widget | Estreito | Médio | Largo |
|---|---|---|---|
| Números | valor `text-2xl` | `text-3xl` a partir de 160 px | igual |
| Funil | 2 colunas | 3 colunas a partir de 448 px | 6 colunas a partir de 896 px |
| Habilidades mais pedidas, Certificações e cursos, Suas habilidades | 1 coluna | 1 coluna | 2 colunas a partir de 768 px |
| Demais blocos | 1 coluna, rótulos quebram a linha | igual | igual |
| Barra de O que as vagas pedem | seletor e botões quebram a linha | igual | igual |

## O que não muda

- **Textos e números:** os de dentro dos widgets são os da spec 045 e do painel de antes. O título "Habilidades mais
  pedidas", por exemplo, continua igual.
- **Barra de O que as vagas pedem:** continua com o seletor, a contagem, a leitura com andamento e Parar, os avisos e o
  erro.
  - O seletor vale para os nove blocos, onde quer que eles estejam.
  - A leitura continua rodando durante a edição.
- **Blocos que dependem de requisitos lidos** (Habilidades mais pedidas, Certificações e cursos, Tempo de experiência e
  Formação):
  - aparecem sempre, com "Ainda não há requisitos lidos nestas vagas." quando não há;
  - enquanto o resumo carrega, mostram "Montando o resumo…".
- **Clique:** o clique num item abre a lista das vagas dentro do widget, e o clique numa vaga abre o detalhe, nos dois
  modos.
