# Data Model: Widgets reorganizáveis no painel Métricas & Funil

Nada muda no servidor nem no banco. Os dados desta spec são a lista fixa de widgets, no código da página, e o layout
guardado no navegador.

## 1. Widget

O id é fixo e é o que fica no layout guardado. A largura (`w`) é em colunas, de 12. A altura (`h`) é em linhas de
4 px e inclui os 16 px de espaço até o widget de baixo.

| Ordem | Id | Título | Tipo | Padrão (x, w) | Largura mín.–máx. | Altura mín.–máx. (px) |
|---|---|---|---|---|---|---|
| 1 | `total` | Total rastreadas | número | 0, 3 | 2–6 | 112–320 |
| 2 | `conversao` | Conversão para entrevista | número | 3, 3 | 2–6 | 112–320 |
| 3 | `aderencia` | Média de aderência (IA) | número | 6, 3 | 2–6 | 112–320 |
| 4 | `ofertas` | Ofertas & propostas | número | 9, 3 | 2–6 | 112–320 |
| 5 | `funil` | Funil de conversão de candidaturas | seção | 0, 12 | 4–12 | 176–640 |
| 6 | `requisitos` | O que as vagas pedem (seletor e leitura) | seção | 0, 12 | 4–12 | 136–640 |
| 7 | `habilidades` | Habilidades mais pedidas | bloco | 0, 8 | 3–12 | 136–2400 |
| 8 | `suas-habilidades` | Suas habilidades | bloco | 8, 4 | 3–12 | 136–2400 |
| 9 | `certificacoes` | Certificações e cursos | bloco | 0, 4 | 3–12 | 136–2400 |
| 10 | `experiencia` | Tempo de experiência | bloco | 4, 4 | 3–12 | 136–1600 |
| 11 | `formacao` | Formação | bloco | 8, 4 | 3–12 | 136–1600 |
| 12 | `idiomas` | Idiomas | bloco | 0, 4 | 3–12 | 136–1600 |
| 13 | `senioridade` | Senioridade | bloco | 4, 4 | 3–12 | 136–1200 |
| 14 | `modelo` | Modelo de trabalho | bloco | 8, 4 | 3–12 | 136–1200 |
| 15 | `contratacao` | Tipo de contratação | bloco | 0, 4 | 3–12 | 136–1200 |
| 16 | `plataformas` | Distribuição por plataforma | bloco | 0, 12 | 3–12 | 136–800 |

- **Linhas do padrão:**
  - os números na linha 1;
  - o funil e a barra, cada um numa linha;
  - Habilidades mais pedidas e Suas habilidades lado a lado;
  - os blocos 9 a 15 de três em três;
  - as plataformas por último.

  O `y` inicial segue essa ordem, com alturas estimadas. A medida (D3) acerta as alturas, e a compactação acerta o `y`.
- **Tipos:** o tipo decide o desenho do título.
  - **número:** rótulo pequeno à esquerda e ícone em quadrado colorido à direita, como hoje;
  - **seção:** título `h3` e subtítulo;
  - **bloco:** título `h4` com ícone à esquerda.
- **Definição no código** (`WidgetDef`, em `painel/layout.ts`): id, título, tipo, ícone, subtítulo (opcional) e corpo.
  O corpo é montado pelo `FunnelAnalytics` e pelo `widgetsRequisitos`.

## 2. Layout guardado

Chave `mpt_pref_metricas_layout` no `localStorage`:

```json
{
  "versao": 1,
  "itens": [
    { "i": "suas-habilidades", "x": 0, "y": 0, "w": 4, "h": 150, "fixa": false },
    { "i": "experiencia", "x": 4, "y": 0, "w": 8, "h": 90, "fixa": true }
  ]
}
```

| Campo | Regra |
|---|---|
| `versao` | 1. Outro valor dá o layout padrão. |
| `i` | Id da tabela §1. Id desconhecido sai, e o id repetido vale só na primeira vez. |
| `x`, `y` | Inteiros, 0 ou mais. `x + w` até 12. |
| `w` | Inteiro entre a largura mínima e a máxima do widget. |
| `h` | Inteiro entre a altura mínima e a máxima do widget, em linhas de 4 px. Com `fixa: false`, é só o ponto de partida até a medida. |
| `fixa` | `true` quando a pessoa mudou a altura; `false` ou ausente é a altura automática. |

- **Gravação:** depois de arrastar, de redimensionar e de Altura do conteúdo. Restaurar o padrão apaga a chave.
- **Leitura:** é tolerante (research D7). O widget que falta entra no fim, no tamanho padrão; o resultado passa pela
  compactação vertical.

## 3. Estados do painel

| Estado | Quando | Grade | Organizar painel |
|---|---|---|---|
| Normal | painel com 768 px ou mais | montada, sem arrastar nem redimensionar | visível |
| Edição | clique em Organizar painel | arrastar pela alça e redimensionar pelo canto; contorno, faixa com Concluir e Restaurar o padrão | vira Concluir |
| Coluna única | painel com menos de 768 px | não é montada: os widgets ficam numa coluna, na ordem do layout (sem layout guardado, a ordem padrão) | não aparece |

- **Transições:**
  - **Normal → Edição:** Organizar painel.
  - **Edição → Normal:** Concluir, ou trocar de aba (o que mudou já está gravado).
  - **Edição → Coluna única:** a tela estreita, e a edição desliga.
  - **Coluna única → Normal:** a tela larga, com o layout guardado.
