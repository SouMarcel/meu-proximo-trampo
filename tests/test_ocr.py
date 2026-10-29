"""Testes do ocr.py (spec 037): o OCR do Windows chamado pelo PowerShell, aqui sempre simulado (sem rodar o
PowerShell): disponibilidade, leitura do JSON do script, páginas a mais e falhas, que nunca viram exceção."""
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ocr  # noqa: E402


def saida(dados, codigo=0):
    bruto = dados if isinstance(dados, bytes) else json.dumps(dados, ensure_ascii=False).encode("utf-8")
    return subprocess.CompletedProcess(args=[], returncode=codigo, stdout=bruto, stderr=b"")


class TestOcr(unittest.TestCase):
    def setUp(self):
        for alvo in (mock.patch.object(ocr.sys, "platform", "win32"),
                     mock.patch.object(ocr.shutil, "which", return_value="C:/Windows/powershell.exe")):
            alvo.start()
            self.addCleanup(alvo.stop)

    def test_disponivel(self):
        self.assertTrue(ocr.disponivel())
        with mock.patch.object(ocr.sys, "platform", "darwin"):
            self.assertFalse(ocr.disponivel())
            with mock.patch.object(ocr.subprocess, "run") as run:
                self.assertEqual(ocr.ler_pdf("a.pdf"), ("", []))  # fora do Windows: nada, sem aviso
            run.assert_not_called()
        with mock.patch.object(ocr.shutil, "which", return_value=None):
            self.assertFalse(ocr.disponivel())

    def test_le_as_paginas(self):
        dados = {"paginas": 2, "lidas": 2, "textos": ["Certificado de Conclusão\nAna Exemplo", "  ", "Página 3"],
                 "idioma": "pt-BR"}
        with mock.patch.object(ocr.subprocess, "run", return_value=saida(dados)) as run:
            texto, avisos = ocr.ler_pdf("anexos/cert.pdf")
        self.assertEqual(texto, "Certificado de Conclusão\nAna Exemplo\n\nPágina 3")
        self.assertEqual(avisos, [])
        cmd = run.call_args.args[0]
        self.assertIn("-File", cmd)
        self.assertIn(str(ocr.SCRIPT), cmd)
        self.assertEqual(cmd[cmd.index("-MaxPaginas") + 1], str(ocr.MAX_PAGINAS))
        self.assertEqual(run.call_args.kwargs["timeout"], ocr.TEMPO_LIMITE)
        self.assertNotIn("shell", run.call_args.kwargs)

    def test_um_texto_so_e_paginas_a_mais(self):
        with mock.patch.object(ocr.subprocess, "run", return_value=saida({"paginas": 9, "lidas": 5, "textos": "Só uma"})):
            texto, avisos = ocr.ler_pdf("a.pdf")
        self.assertEqual(texto, "Só uma")
        self.assertEqual(avisos, ["OCR só nas 5 primeiras páginas."])

    def test_falhas_viram_aviso(self):
        casos = [
            (saida({"erro": "sem OCR neste Windows"}), "sem OCR neste Windows"),
            (saida(b"isto nao e json"), "resposta inválida"),
            (saida(b"", 1), "resposta inválida"),
            (subprocess.TimeoutExpired("powershell", 30), "demorou mais de 30 s"),
            (OSError("sem powershell"), "OSError"),
        ]
        for retorno, motivo in casos:
            efeito = {"side_effect": retorno} if isinstance(retorno, BaseException) else {"return_value": retorno}
            with mock.patch.object(ocr.subprocess, "run", **efeito):
                texto, avisos = ocr.ler_pdf("a.pdf")
            self.assertEqual(texto, "", motivo)
            self.assertEqual(len(avisos), 1, motivo)
            self.assertIn(motivo, avisos[0])
            self.assertTrue(avisos[0].startswith("OCR do Windows não leu o arquivo"), avisos[0])


class TestScript(unittest.TestCase):
    def test_script_existe_e_e_ascii(self):
        """O PowerShell 5.1 lê .ps1 sem BOM como ANSI: o script fica só com ASCII."""
        bruto = ocr.SCRIPT.read_bytes()
        self.assertTrue(bruto)
        bruto.decode("ascii")


if __name__ == "__main__":
    unittest.main()
