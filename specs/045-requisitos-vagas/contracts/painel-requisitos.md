# Contrato de tela: O que as vagas pedem (Métricas & Funil)

## Ordem do painel

1. Os quatro números (sem mudança).
2. O funil (sem mudança).
3. **O que as vagas pedem** (novo).
4. Distribuição por plataforma, na largura toda (antes dividia a linha com o quadro antigo).

O quadro "Habilidades Mais Valorizadas nas Vagas" sai (FR-022).

## Cabeçalho da seção

- **Título:** "O que as vagas pedem". **Subtítulo:** "Habilidades, certificações, experiência e outros requisitos das
  vagas escolhidas abaixo."
- **Seletor:** dois grupos de botões, cada um com `aria-pressed`, no estilo dos filtros de Vagas Nacionais:
  - **Vagas:** "Em Aplicações" | "Todas as vagas analisadas";
  - **Área:** "As duas" | "Nacionais" | "Internacionais".
- **Linha de contagem:** "Contando 30 vagas com requisitos lidos, de 40 nesta seleção". Os complementos aparecem só
  quando existem: "· 2 a ler · 7 sem o texto do anúncio · 1 esperando análise".
- **Leitura:**
  - **Botão:** com `a_ler` > 0 e sem leitura rodando, aparece "Ler os requisitos das N vagas desta seleção", com a IA
    escolhida em letra pequena ("com Gemini · gemini-2.5-flash; a nota das vagas não muda").
  - **Sem IA:** o botão fica desligado, com "Escolha uma IA no botão IA ou peça no chat: ler os requisitos das vagas".
    "botão IA" abre o painel da IA (`onAbrirIA`).
  - **Rodando:** uma barra "Lendo 40 de 120 vagas…" e o botão "Parar".
  - **Parada:** "Leitura parada: 40 de 120 vagas lidas. Clique de novo para continuar."
  - **Erro:** "A leitura parou: <motivo>. O que foi lido ficou gravado; clique de novo para continuar."
- **Poucas vagas:** o aviso "Poucas vagas para tirar conclusão (N)". Com `poucas`, ele aparece acima das listas.
- **Nenhuma vaga com requisitos:** no lugar das listas, "Ainda não há requisitos lidos nestas vagas." e o botão. Os
  indicadores que já existem nas vagas e o quadro Suas habilidades continuam aparecendo.

## Blocos (grade: 1 coluna no celular, 2 a partir de `md`, 3 a partir de `lg` nos blocos menores)

1. **Habilidades mais pedidas** (largura de 2 colunas a partir de `lg`):
   - abas internas "Técnicas e ferramentas" e "Comportamentais", cada uma com o seu número;
   - cada linha mostra:
     - o nome;
     - a etiqueta do perfil ("✓ nas suas habilidades", "• citada no seu perfil" ou "não está no seu perfil", com
       texto além da cor);
     - "12 de 30 vagas (40%)" e "exigida em 9";
     - a barra proporcional.
   - aparecem 15 linhas, com "Ver todas (N)" e "Ver menos".
2. **Suas habilidades:**
   - o resumo "8 das suas 14 habilidades aparecem nestas vagas";
   - as linhas: o nome como está no perfil, o nível em letra menor e "20 vagas";
   - as cinco em destaque têm a borda e o fundo de destaque, e as de zero ficam apagadas, com "nenhuma vaga desta
     seleção";
   - abaixo, "Suas certificações", no mesmo formato;
   - sem a seção: "Seu perfil não tem a seção Habilidades e ferramentas. Abra Meu perfil para montar." com o botão
     "Meu perfil" (`onAbrirPerfil`).
3. **Certificações e cursos:** as linhas como em Habilidades, com a etiqueta "Certificação" ou "Curso".
4. **Tempo de experiência:** as seis faixas em barras, com o número de vagas. A faixa de `destaque` vem marcada como "a
   mais pedida".
5. **Formação:** os níveis em barras e, abaixo, "Áreas mais citadas" em etiquetas com o número.
6. **Idiomas:** cada idioma com o número de vagas e os níveis em etiquetas ("Fluente 9 · Intermediário 6").
7. **Senioridade e modelo:** dois grupos de barras.
8. **Tipo de contratação:** barras.

Cada bloco diz a base no rodapé ("em 30 vagas com requisitos lidos" ou "em 35 vagas analisadas").

## Clique num item

- **Abrir:** clicar no nome de um item (linha, faixa, nível, área, idioma ou habilidade dela) abre, logo abaixo, a
  lista "Vagas que pedem <item> (N)", com cargo · empresa. Um segundo clique fecha.
- **Ir à vaga:** clicar numa vaga abre o detalhe dela (`onSelectVaga`), como nas listas de vagas.
- **Contagem:** a lista vem dos `ids` do resumo e casa com a lista de vagas carregada. Por isso, o número é o mesmo da
  linha (SC-005).

## Acessibilidade e largura

- **Etiquetas:** as do perfil têm texto, além da cor.
- **Botões:** os do seletor e das abas internas têm `aria-pressed`, e os itens clicáveis são `button`.
- **Largura:** a 360 px, uma coluna, sem rolagem horizontal. Os nomes longos quebram a linha (`break-words`).
- **Tema:** claro e escuro, com as classes `dark:` já usadas no painel.
