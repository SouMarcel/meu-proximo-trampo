"""Testes do sincronizar_skills.py: a cópia em .claude/skills/ precisa bater com a fonte em .agents/skills/."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sincronizar_skills as sinc  # noqa: E402


class CopiasDoRepositorio(unittest.TestCase):
    def test_copias_em_dia(self):
        self.assertEqual(sinc.diferencas(), [], "rode: python sincronizar_skills.py (e edite em .agents/skills/)")

    def test_skills_de_desenvolvimento_ficam_fora_da_fonte(self):
        self.assertFalse(any(p.name.startswith("speckit-") for p in sinc.FONTE.iterdir()))


class Conferencia(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        raiz = Path(self.tmp.name)
        self.fonte, self.destino = raiz / "fonte", raiz / "destino"
        (self.fonte / "a").mkdir(parents=True)
        (self.fonte / "a" / "SKILL.md").write_text("---\nname: a\ndescription: teste\n---\n# A\ntexto\n", encoding="utf-8")
        (self.fonte / "a" / "modelo.json").write_text('{"x": 1}\n', encoding="utf-8")
        (self.destino / "outra").mkdir(parents=True)
        (self.destino / "outra" / "SKILL.md").write_text("não mexer", encoding="utf-8")
        self.skills = ("a",)

    def tearDown(self):
        self.tmp.cleanup()

    def dif(self):
        return sinc.diferencas(self.fonte, self.destino, self.skills)

    def test_gera_com_aviso_depois_do_frontmatter(self):
        sinc.gerar(self.fonte, self.destino, self.skills)
        texto = (self.destino / "a" / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(texto.startswith("---\nname: a\n"))
        self.assertIn("---\n<!-- Cópia gerada de .agents/skills/a/", texto)
        self.assertEqual(self.dif(), [])
        self.assertEqual((self.destino / "outra" / "SKILL.md").read_text(encoding="utf-8"), "não mexer")

    def test_acusa_editada_faltando_e_sobrando(self):
        sinc.gerar(self.fonte, self.destino, self.skills)
        (self.destino / "a" / "SKILL.md").write_text("editada à mão", encoding="utf-8")
        (self.destino / "a" / "modelo.json").unlink()
        (self.destino / "a" / "extra.txt").write_text("sobra", encoding="utf-8")
        problemas = " | ".join(self.dif())
        self.assertIn("diferente da fonte: .claude/skills/a/SKILL.md", problemas)
        self.assertIn("falta na cópia: .claude/skills/a/modelo.json", problemas)
        self.assertIn("sobrando na cópia: .claude/skills/a/extra.txt", problemas)
        sinc.gerar(self.fonte, self.destino, self.skills)
        self.assertEqual(self.dif(), [])

    def test_fim_de_linha_crlf_nao_conta_como_diferenca(self):
        sinc.gerar(self.fonte, self.destino, self.skills)
        arq = self.destino / "a" / "modelo.json"
        arq.write_bytes(arq.read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(self.dif(), [])

    def test_fonte_ausente(self):
        shutil.rmtree(self.fonte / "a")
        with self.assertRaises(FileNotFoundError):
            sinc.gerar(self.fonte, self.destino, self.skills)


if __name__ == "__main__":
    unittest.main()
