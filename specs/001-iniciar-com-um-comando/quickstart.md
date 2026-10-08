# Quickstart: validar "iniciar com um comando"

Pré-requisitos: Python 3.10+ e Git. Rodar num **clone limpo** em pasta temporária (não na pasta
de uso diário), para não mexer em dados reais. Em cada cenário, comparar a lista de arquivos
fora de `.venv/` antes e depois (SC-005).

| # | Cenário | Como | Esperado |
|---|---|---|---|
| 1 | Primeira vez, aceitando | `git clone … && cd … && python iniciar.py` → responder S | instala em `.venv/`, abre a página; aviso "configure a busca" no relatório; nenhum `config.json` criado (US1, SC-001) |
| 2 | Primeira vez, recusando | clone limpo → `python iniciar.py` → responder n | nada instalado; mensagem de como instalar à mão; código 3 |
| 3 | Dia a dia | com o ambiente pronto, `python iniciar.py`; medir o tempo até a página | abre sem perguntas, em até 10 s, sem rede (desligar a internet para conferir) (US2, SC-002) |
| 4 | Já aberta | com a ferramenta rodando, rodar o comando de novo | abre a página existente, sai com 0, sem segunda cópia (SC-003) |
| 5 | Dependência nova | acrescentar uma linha ao `requirements.txt` | avisa, pergunta e instala só o que falta |
| 6 | Ambiente quebrado | apagar o carimbo e uma pasta do pacote em `.venv/`, ou editar o `home` do `pyvenv.cfg` para uma pasta inexistente | detecta, pergunta e refaz (SC-006) |
| 7 | Parar | Ctrl+C, e em outra rodada fechar a janela | a ferramenta para; nenhum processo `servidor.py` sobra; a próxima execução inicia normal |
| 8 | Porta ocupada | ocupar a 8765 com outro programa | mensagem com `--porta`; código 1 |
| 9 | Atalho | dois cliques em `iniciar.bat` | mesmo resultado; em erro, a janela fica aberta (US3) |
| 10 | `--sim` | clone limpo → `python iniciar.py --sim --sem-navegador` | instala sem perguntar e sobe sem abrir navegador |
| 11 | Caminho com espaço e acento | clonar em "Área de Trabalho/teste trampo" | funciona |
| 12 | Jeito antigo | `.venv` criado com os passos manuais do README antigo | reaproveita sem reinstalar (grava o carimbo) |

Testes automáticos: `python -m unittest discover -s tests` (funções puras do `iniciar.py`:
leitura do `requirements.txt`, comparação de versões, estados do ambiente com pastas falsas,
opções do comando).

Plataforma: Windows 10/11 (SC-004). macOS e Linux estão na lista de desejos e não são
verificados nesta feature.
