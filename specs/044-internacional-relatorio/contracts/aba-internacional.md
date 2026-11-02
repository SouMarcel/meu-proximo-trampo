# Contrato da tela: aba Internacional

A API não muda (`dash/API.md`). Este contrato descreve a tela, de cima para baixo.

## Acima do componente (no App, sem mudança)

1. O painel da busca (Buscar vagas, andamento).
2. O aviso de busca internacional desligada, com o botão Filtros da busca internacional, quando ela está desligada.

## Componente do relatório com `area="internacional"`

1. **Linha compacta**: o ícone de globo, "Vagas de fora" e os três números sobre a lista à vista:
   - "N vagas";
   - "N remotas";
   - "N com visto ou relocation".
2. **Abas internas**: Para decidir (ativa ao abrir), Não seguidas e Fora dos critérios, cada uma com o número de vagas
   de fora.
3. **Barra, primeira linha**:
   - a busca, com o placeholder "Filtrar por cargo, empresa, país ou habilidades...";
   - "Ordenar:" com Maior Aderência, Mais Recentes, Por Plataforma e Modo de Trabalho;
   - os botões Filtros da busca internacional e Prontidão internacional.
4. **Barra, segunda linha**: os filtros do Relatório, nesta ordem:
   1. Senioridade (Jr, Pl, Sr, Não informada);
   2. Modo (Remoto, Híbrido, Presencial, Não informado);
   3. Moeda (Todas, Dólar, Euro), um botão de cada vez;
   4. Visto / relocation (liga e desliga);
   5. Nota mínima;
   6. Publicada há até N dias;
   7. Analisadas.
5. **Marcar todas como não seguidas**: em Para decidir, com o aviso de só leitura quando o servidor está fora do ar.
6. **"Mostrando X de Y vagas" e Limpar filtros**, com qualquer filtro ligado. Limpar filtros também volta a moeda para
   Todas e desliga o visto.
7. **Lista**: um cartão por linha, como no Relatório:
   - em Para decidir, primeiro as de nota 50 ou mais;
   - depois o bloco recolhido Baixa aderência (N), com o próprio Marcar todas.
8. **Cartão**: o do Relatório, com uma linha a mais abaixo de empresa, local e salário:
   - a etiqueta do país, ou "Global";
   - "Contratação: …", ou "Contratação: não informada";
   - os sinais, quando houver.
9. **Lista vazia**:
   - em Para decidir: "Nenhuma vaga de fora esperando decisão. Ligue mais fontes na aba Portais internacionais de
     Filtros da busca, ou peça uma busca.";
   - nas outras abas internas, e com filtros, os textos do Relatório.

## Componente com `area="nacional"` (Relatório de Vagas)

Igual a hoje. Nada da lista acima aparece, a não ser o que o Relatório já tem.
