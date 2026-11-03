# Contrato: rotas e comandos dos requisitos

## Rotas do servidor (`dash/servidor.py`)

| Rota | Quem pode | Corpo | Resposta |
|---|---|---|---|
| `GET /api/requisitos?vagas=aplicacoes\|todas&area=todas\|nacional\|internacional` | quem abre o dashboard (como `GET /api/vagas`) | — | 200: o resumo (data-model §3). Um parâmetro inválido volta ao padrão. |
| `POST /api/requisitos/ler` | só deste computador (403 com `SO_LOCAL_PERFIL`) | `{"vagas", "area"}` | 202 `{"leitura": estado}` quando começa. 200 `{"leitura": estado}` quando já está rodando, sem abrir outra. 409 `{"erro": "escolha uma IA no botão IA ou peça a leitura ao assistente no chat"}` sem IA. 200 com `total: 0` quando não há o que ler. |
| `POST /api/requisitos/parar` | só deste computador | `{}` | 200 `{"leitura": estado}` com `parada: true` quando havia leitura; sem leitura, o estado atual. |

- **Seleção:** a leitura lê as vagas da seleção recebida (research D4), na hora do clique.
- **Andamento:** a página acompanha pelo `leitura` do `GET /api/requisitos`. A `versao` do banco muda a cada lote
  gravado, e a página recarrega as vagas como já faz.
- **Erros:** o motivo de uma falha da IA vem em `leitura.erro.motivo`, já sem chave (`ia.mascarar`).

## Pedido à IA da leitura avulsa (`requisitos.montar_pedido`)

- **Abertura:** "Você lê os requisitos de anúncios de vagas para o usuário da ferramenta meu-proximo-trampo. Responda
  SOMENTE com um array JSON `[{"id", "requisitos": {…}}]`."
- **Regras:** o item `requisitos` da skill `buscar-vagas`, copiado da fonte (research D3).
- **Nomes do perfil:** "Nomes que o usuário usa para as habilidades e certificações dele (use o mesmo nome quando for a
  mesma coisa): …". Só os nomes, sem nível e sem o resto do perfil (FR-006).
- **Vagas:** o mesmo aviso de texto da internet de `analise.montar_pedido`. Cada vaga traz:
  - `### id:`;
  - Cargo;
  - Empresa;
  - Descrição, depois do `integridade.limpar`, cortada em `analise.LIMITE_DESCRICAO`.
- **Resposta:** o array entre o primeiro `[` e o último `]`. Um id que não estava no lote é ignorado.

## Pedido da análise (`analise.montar_pedido`)

- **Linha de formato:** ganha, entre os opcionais, `"requisitos" {"habilidades" [{"nome", "tipo", "exigida"}],
  "certificacoes" [{"nome", "tipo", "exigida"}], "experiencia" {"anos", "em", "frase"}, "formacao" {"nivel", "areas",
  "frase"}, "idiomas" [{"idioma", "nivel", "frase"}]}`.
- **Regras:** vêm no trecho da skill que o pedido já copia (D3).
- **Nomes do perfil:** não precisam ir à parte, porque o perfil inteiro já vai no pedido.

## Comandos (`PY dash/requisitos.py`)

| Comando | O que faz |
|---|---|
| `resumo [--vagas aplicacoes\|todas] [--area todas\|nacional\|internacional] [--json]` | Imprime o resumo da seleção. Sem `--json`, em texto: as contagens, as 15 primeiras de cada lista, as faixas, os indicadores e Suas habilidades. Sem IA. Sai com 0. |
| `pendentes [--vagas …] [--area …] [--limite N]` | Imprime em JSON, até N vagas (padrão 10), as vagas da seleção que o botão leria: `id`, `titulo`, `empresa`, `atencao` (texto suspeito, spec 034) e `descricao` já limpa e cortada. Também traz `restam` (quantas faltam depois dessas). |
| `gravar <arquivo.json>` | Lê `[{"id", "requisitos"}]` (ou `{"requisitos": [...]}`) e grava com `banco.aplicar_requisitos`. Imprime "N vaga(s) com os requisitos gravados" e os problemas. Sai com 1 se nada foi gravado e havia itens. |

O texto do `resumo` usa os mesmos nomes da página, como "Habilidades mais pedidas", "Suas habilidades" e "N de M
vagas (x%)".
