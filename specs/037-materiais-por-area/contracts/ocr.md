# Contrato: OCR do Windows (`ocr.py` ↔ `ocr_windows.ps1`)

## Chamada

```text
powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File <raiz>/ocr_windows.ps1 -Caminho <pdf> [-MaxPaginas 5]
```

- `subprocess.run([...], capture_output=True, timeout=30, creationflags=CREATE_NO_WINDOW)`, sem shell.
- O caminho é um arquivo de `anexos/`, já conferido por quem chama.

## Saída (stdout, UTF-8, uma linha JSON)

```text
{"paginas": 3, "lidas": 3, "textos": ["texto da página 1", "…"], "idioma": "pt-BR"}
{"erro": "sem OCR em português neste Windows"}
```

## `ocr.ler_pdf(caminho) -> (texto, avisos)`

| Situação | Retorno |
|---|---|
| leu algo | `("pág. 1\n\npág. 2", [])` (quem chama acrescenta o aviso de OCR) |
| mais de 5 páginas | texto das 5 primeiras, com o aviso "OCR só nas 5 primeiras páginas" |
| fora do Windows | `("", [])` (o OCR não está disponível) |
| erro, tempo esgotado ou JSON inválido | `("", ["OCR do Windows não leu o arquivo (<motivo>)"])` |

`ocr.disponivel()` é `True` só no Windows com `powershell` no PATH. O idioma é conferido pelo script.
