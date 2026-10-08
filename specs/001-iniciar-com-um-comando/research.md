# Research: Iniciar a ferramenta com um comando

Sem agentes de pesquisa: as incógnitas se resolvem com o código atual (`dash/servidor.py`,
`dash/abrir-dashboard.bat`, `README.md`) e com o comportamento conhecido da biblioteca padrão.

## 1. Ambiente isolado e instalação das dependências

- **Decision**: `iniciar.py` (biblioteca padrão) cria `.venv/` com `venv.EnvBuilder(with_pip=True)`
  usando o próprio interpretador que rodou o comando e instala com
  `<.venv python> -m pip install -r requirements.txt --disable-pip-version-check --no-cache-dir`,
  mostrando a saída do pip (andamento, FR-005).
- **Rationale**: `.venv/` já é o caminho documentado e já está no `.gitignore`; `with_pip` usa o
  pip embutido (sem internet); `--no-cache-dir` evita gravar cache fora da pasta do projeto
  (FR-004); `--disable-pip-version-check` tira um aviso que confunde quem não é técnico.
- **Alternatives considered**: instalar no Python do sistema (fere FR-004); `uv`/`pipx` (exigem
  ferramenta extra, fere o princípio III); Docker (pesado e fora da proposta).

## 2. Saber se o ambiente está pronto sem rede e em segundos

- **Decision**: depois de cada instalação bem-sucedida, gravar o carimbo
  `.venv/.requisitos-instalados` com o SHA-256 do `requirements.txt` e a versão do Python. Na
  partida, o ambiente está **pronto** quando: o executável do `.venv` existe, o `home` do
  `pyvenv.cfg` aponta para uma pasta existente e o carimbo bate com o `requirements.txt` atual.
  Nenhum processo extra nem acesso à rede (FR-008, SC-002).
- **Ambiente do jeito antigo (sem carimbo)**: roda uma vez o Python do `.venv` com um verificador
  que usa `importlib.metadata` para conferir cada linha do `requirements.txt` (`nome` ou
  `nome>=versão`); se tudo está instalado, grava o carimbo e segue sem reinstalar. Especificador
  diferente de `>=` ou nome ausente → trata como faltando.
- **Rationale**: comparar arquivo é instantâneo; o verificador só roda na transição.
- **Alternatives considered**: `pip check`/`pip install --dry-run` (lento, o segundo precisa de
  rede); comparar data de modificação (frágil com `git pull`).

## 3. Estados do ambiente e o que o comando faz em cada um

| Estado | Como detecta | Ação (com confirmação, salvo `--sim`) |
|---|---|---|
| ausente | sem `.venv/` | criar e instalar |
| inválido | executável ausente ou `home` do `pyvenv.cfg` inexistente (pasta copiada de outra máquina) | apagar `.venv/` e recriar |
| incompleto | executável ok, sem carimbo e o verificador acusa falta | instalar o que falta |
| desatualizado | carimbo diferente do `requirements.txt` | instalar o que falta |
| pronto | carimbo bate | iniciar direto |

Instalação interrompida deixa o carimbo ausente ou antigo, então cai em "incompleto" e se refaz
(SC-006).

## 4. Rodar o servidor e parar sem sobrar processo

- **Decision**: se o próprio `iniciar.py` já está rodando no Python do `.venv`, importa
  `dash/servidor.py` e chama `servidor.main()`. Senão, `subprocess.run([<.venv python>,
  "dash/servidor.py", ...opções])` na mesma janela, esperando o fim; `KeyboardInterrupt` no
  processo pai só espera o filho terminar e sai com o código dele.
- **Rationale**: o servidor já trata Ctrl+C, imprime o endereço e "Feche esta janela (ou Ctrl+C)
  para parar" (FR-006, FR-012). Na mesma janela, Ctrl+C chega aos dois processos; fechar a janela
  encerra os dois (evento de fechamento do console no Windows, SIGHUP no macOS/Linux), sem órfão.
- **Alternatives considered**: `os.execv` (no Windows não substitui o processo de verdade e a
  janela volta ao prompt com o servidor ainda escrevendo); segundo plano (descartado na
  clarificação).

## 5. Ferramenta já aberta

- **Decision**: antes de olhar o ambiente, `iniciar.py` consulta
  `http://127.0.0.1:<porta>/api/versao` (a mesma checagem de `servidor.ja_rodando`, reescrita com
  `urllib` para rodar com o Python do sistema). Se responder, abre a página (salvo
  `--sem-navegador`) e sai com 0 (FR-007), em menos de 2 s.
- **Rationale**: evita qualquer trabalho de ambiente e não depende do `.venv`.

## 6. Pré-requisitos e versões

- **Decision**: versão mínima 3.10 (a do README), verificada na primeira linha útil do
  `iniciar.py`. O arquivo é escrito com sintaxe aceita desde o Python 3.6 (sem `match`, sem
  operador `:=`, sem anotações `X | Y`), para que um Python antigo mostre a mensagem em vez de um
  erro de sintaxe.
- **Debian/Ubuntu sem `ensurepip`**: a criação do `.venv` falha; a mensagem manda instalar o
  pacote `python3-venv` (com o comando de exemplo).
- **Rationale**: FR-002 e o caso-limite "pré-requisito ausente ou antigo".

## 7. Atalhos de duplo clique

- **Decision** (só Windows nesta feature; macOS/Linux na lista de desejos):
  - `iniciar.bat` (Windows): vai para a pasta do arquivo, procura `py -3` (o lançador oficial,
    que não cai no atalho da Microsoft Store) e depois `python`; sem Python, mensagem com o link
    de download; roda `iniciar.py %*` **na mesma janela**; se sair com erro, `pause`.
  - Adiados para a lista de desejos: `iniciar.command` (macOS) e `iniciar.sh` (Linux).
- **Janela minimizada**: não aplicada. O servidor roda na própria janela do atalho e a janela
  precisa ficar visível quando há erro (FR-013); minimizar esconderia o erro. O
  `dash/abrir-dashboard.bat` atual, que abre minimizado, continua existindo como alternativa.
  O FR-013 foi ajustado para refletir isso.
- **Alternatives considered**: reabrir o `.bat` minimizado e restaurar a janela no erro (exige
  PowerShell, frágil).

## 8. Opções do comando

- **Decision**: `--sim` (aceita a instalação sem perguntar, FR-011), e repassa ao servidor
  `--sem-navegador`, `--rede`, `--porta N` (FR-010). Ajuda e mensagens em português (FR-015).
- **Porta ocupada por outro programa**: o servidor já responde "Não foi possível usar a porta…
  Tente --porta 8766." e sai com 1; o comando só repassa o código.

## 9. Configuração ausente

- **Decision**: o comando não toca em `config.json` (FR-009). Comportamento atual mantido: a página
  abre com os filtros padrão (`filtros.efetivos({})`) e a primeira gravação no painel Filtros da
  busca cria o arquivo a partir do exemplo (`filtros.salvar`).
