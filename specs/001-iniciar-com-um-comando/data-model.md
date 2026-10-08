# Data Model: Iniciar a ferramenta com um comando

A funcionalidade não cria nem altera dados da pessoa. Só há dois "objetos" de controle, ambos
locais e fora do Git.

## Ambiente do projeto

Pasta `.venv/` na raiz do projeto (já no `.gitignore`).

| Campo | Origem | Regra |
|---|---|---|
| executável | `.venv/Scripts/python.exe` (Windows) ou `.venv/bin/python` | precisa existir |
| `home` | linha `home = …` do `.venv/pyvenv.cfg` | precisa apontar para pasta existente |
| carimbo | `.venv/.requisitos-instalados` (JSON) | `{"requisitos_sha256": "<hash do requirements.txt>", "python": "3.x.y"}`; gravado só depois de instalação ou verificação bem-sucedida |

**Estados e transições** (detalhe em [research.md §3](research.md)):

```text
ausente ──criar+instalar──▶ pronto
inválido ──apagar+recriar──▶ pronto
incompleto ──instalar──▶ pronto
desatualizado ──instalar──▶ pronto        (requirements.txt mudou)
pronto ──requirements.txt mudou──▶ desatualizado
qualquer ──instalação falhou──▶ incompleto (carimbo não é gravado)
```

Toda transição que instala ou apaga passa pela confirmação da pessoa (ou `--sim`).

## Instância em execução

O servidor local já existente (`dash/servidor.py`), identificado pela porta (padrão 8765).
Considerada "em execução" quando `GET http://127.0.0.1:<porta>/api/versao` responde 200 com o
campo `versao` (mesma regra de `servidor.ja_rodando`).

## Configuração (sem mudança)

`config.json` não é criado nem alterado pelo comando. A página consulta `GET /api/config`
(campo `existe`, que o servidor já devolve) para decidir se mostra o aviso de próximo passo.
