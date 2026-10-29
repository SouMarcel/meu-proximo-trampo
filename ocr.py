#!/usr/bin/env python3
"""OCR de PDF que é só imagem (spec 037): certificado gerado como figura, documento escaneado.

Usa o que o Windows 10/11 já traz, sem instalar nada e sem rede: o script `ocr_windows.ps1` transforma cada página
em imagem (Windows.Data.Pdf) e lê o texto com o OCR do sistema (Windows.Media.Ocr, em português do Brasil ou no
primeiro idioma disponível). Fora do Windows, ou sem o OCR, devolve vazio e quem chama mantém o aviso de PDF
digitalizado.

  disponivel()        True no Windows com o PowerShell
  ler_pdf(caminho)    (texto, avisos); falha nunca vira exceção, vira aviso

O texto lido sai como está: quem chama mascara os documentos (CPF, RG) e marca o texto como lido por OCR.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
SCRIPT = RAIZ / "ocr_windows.ps1"
TEMPO_LIMITE = 30  # segundos por arquivo
MAX_PAGINAS = 5


def disponivel() -> bool:
    return sys.platform == "win32" and bool(shutil.which("powershell"))


def _falha(motivo: str) -> str:
    return f"OCR do Windows não leu o arquivo ({motivo})."


def ler_pdf(caminho) -> tuple[str, list[str]]:
    """O texto das páginas (até MAX_PAGINAS), separadas por linha em branco, e os avisos."""
    if not disponivel():
        return "", []
    comando = [shutil.which("powershell") or "powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy",
               "Bypass", "-File", str(SCRIPT), "-Caminho", str(Path(caminho).resolve()), "-MaxPaginas", str(MAX_PAGINAS)]
    try:
        r = subprocess.run(comando, capture_output=True, timeout=TEMPO_LIMITE,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        return "", [_falha(f"demorou mais de {TEMPO_LIMITE} s")]
    except OSError as e:
        return "", [_falha(e.__class__.__name__)]
    try:
        dados = json.loads((r.stdout or b"").decode("utf-8-sig", errors="replace").strip())
    except ValueError:
        dados = None
    if not isinstance(dados, dict):
        return "", [_falha("resposta inválida")]
    if dados.get("erro"):
        return "", [_falha(str(dados["erro"])[:160])]
    textos = dados.get("textos") or []
    if isinstance(textos, str):  # o ConvertTo-Json do PowerShell 5.1 desfaz a lista de um item só
        textos = [textos]
    texto = "\n\n".join(t.strip() for t in textos if isinstance(t, str) and t.strip())
    lidas, paginas = int(dados.get("lidas") or 0), int(dados.get("paginas") or 0)
    avisos = [f"OCR só nas {lidas} primeiras páginas."] if lidas and paginas > lidas else []
    return texto, avisos
