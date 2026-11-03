# Quickstart: conferir O que as vagas pedem

## Antes

- O dashboard roda na branch pessoal, com o build de teste da página.
- A pessoa tem vagas analisadas, um perfil com a seção de habilidades e, para os passos 3 a 6, uma IA escolhida no
  botão IA.
- Antes do passo 3, uma cópia de conferência: `PY dash/requisitos.py resumo --json > .cache/antes.json` e a lista de
  notas (`PY dash/banco.py quadro`).

## Roteiro

1. **Painel sem leitura:** abra Métricas & Funil.
   - Depois do funil vem **O que as vagas pedem**, com o seletor em "Em Aplicações" e "As duas".
   - A linha diz quantas vagas há para ler e quantas estão sem o texto do anúncio.
   - Senioridade, modelo, contratação e o inglês já aparecem.
   - Suas habilidades mostra o perfil, sem contagens.
   - O quadro antigo "Habilidades Mais Valorizadas" não aparece mais.
2. **Seletor:** troque para "Todas as vagas analisadas" e "Internacionais".
   - Os números mudam.
   - Recarregue a página: a seleção continua a mesma.
   - Volte para "Em Aplicações" e "As duas".
3. **Leitura:** clique em **Ler os requisitos das N vagas desta seleção**.
   - Aparece "Lendo X de N vagas…" com o botão Parar.
   - No fim, as listas se enchem.
4. **Parar e continuar:** em "Todas as vagas analisadas", comece a leitura e clique em Parar depois do primeiro lote.
   - A mensagem diz quantas foram lidas.
   - Clique de novo: a contagem "a ler" continua de onde parou, sem voltar ao total.
5. **A nota não mudou:** compare `PY dash/banco.py quadro` e algumas vagas abertas no detalhe com o que era antes da
   leitura. A nota, o resumo, o Encaixe e as Lacunas são os mesmos.
6. **Experiência não é habilidade:** percorra as listas de habilidades e certificações.
   - Nenhum item fala de anos ou de experiência.
   - O tempo de experiência mostra as faixas, com a mais pedida em destaque.
7. **Suas habilidades:**
   - as suas mais pedidas estão no topo, em destaque, e as de zero estão no fim, apagadas;
   - nas listas, as etiquetas "nas suas habilidades", "citada no seu perfil" e "não está no seu perfil" batem com o seu
     perfil.
8. **De onde vem o número:** clique num item, por exemplo "SQL — 12 de 30 vagas".
   - Aparecem 12 vagas.
   - Clique numa delas: o detalhe da vaga abre.
9. **Terminal:** rode `PY dash/requisitos.py resumo` com a mesma seleção da página. As contagens são as mesmas.
10. **Largura e tema:** estreite a janela até cerca de 360 px e troque o tema.
    - Tudo cabe numa coluna, sem rolagem para o lado, nos dois temas.

## Conferência automática (antes de entregar para o teste)

- `python -m unittest discover -s tests` passando (com `tests/test_requisitos.py`).
- No front, `tsc --noEmit` e `vite build`, sem erro.
- CDP sem janela, no build de teste:
  - abre Métricas & Funil;
  - confere a seção, o seletor (troca e lembra) e a largura de 360 px;
  - abre e fecha a lista de um item.

  Nunca clica em Ler os requisitos nem em Parar, porque isso gasta a IA e grava nas vagas da pessoa.
