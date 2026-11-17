"""Testes do curriculo.py com técnicas (python -m unittest discover -s tests). Conteúdo fictício do modelo.json."""
import copy
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import curriculo  # noqa: E402
from docx import Document  # noqa: E402
from docx.shared import Cm, Pt  # noqa: E402

MODELO = json.loads((RAIZ / ".agents" / "skills" / "gerar-curriculo" / "modelo.json").read_text(encoding="utf-8"))


def base():
    cv = copy.deepcopy(MODELO)
    cv.pop("tecnicas", None)
    cv.pop("destaques", None)
    return cv


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def gerar(self, cv) -> Document:
        destino = self.tmp / "cv.docx"
        with redirect_stdout(io.StringIO()):
            self.assertEqual(curriculo.validar(cv), [])
        curriculo.Montador(cv).montar().save(destino)
        return Document(str(destino))

    @staticmethod
    def titulos(doc):
        return [p.text for p in doc.paragraphs if p.text.isupper() and len(p.text) > 3]


class TestValidacao(unittest.TestCase):
    def test_tecnicas_invalidas(self):
        with redirect_stdout(io.StringIO()):
            erros = curriculo.validar({**base(), "tecnicas": {"formato": "jp", "paginas": 3, "xyz": "sim", "outra": 1}})
        texto = " ".join(erros)
        for trecho in ("tecnicas.formato", "tecnicas.paginas", "tecnicas.xyz", "'outra'"):
            self.assertIn(trecho, texto)

    def test_destaques_e_dados_pessoais_no_us(self):
        with redirect_stdout(io.StringIO()):
            erros = curriculo.validar({**base(), "destaques": ["a", "b", "c", "d"],
                                       "tecnicas": {"formato": "us"}, "nascimento": "01/01/1990"})
        self.assertTrue(any("destaques" in e for e in erros))
        self.assertTrue(any("nascimento" in e for e in erros))

    def test_ler_tecnicas_preenche_padroes(self):
        self.assertIsNone(curriculo.ler_tecnicas(base()))
        tec = curriculo.ler_tecnicas({"tecnicas": {"xyz": True}})
        self.assertEqual((tec["xyz"], tec["ats"], tec["formato"], tec["estilo"], tec["paginas"]), (True, True, "br", "padrao", 2))
        self.assertFalse(tec["paginas_obrigatorio"])

    def test_ler_tecnicas_sem_paginas_obrigatorio(self):
        tec = curriculo.ler_tecnicas({"tecnicas": {"xyz": True}})
        self.assertFalse(tec["paginas_obrigatorio"])

    def test_validar_completo_e_obrigatorio(self):
        cv = {**base(), "tecnicas": {"paginas": 0, "paginas_obrigatorio": True}}
        with redirect_stdout(io.StringIO()):
            self.assertEqual(curriculo.validar(cv), [])


class TestMotor(Base):
    def test_sem_tecnicas_igual_ao_layout_de_antes(self):
        doc = self.gerar(base())
        sec = doc.sections[0]
        for medida, esperado in ((sec.page_width, Cm(21)), (sec.page_height, Cm(29.7)), (sec.left_margin, Cm(1.9))):
            self.assertAlmostEqual(medida, esperado, delta=Cm(0.01))  # o Word guarda em vinte avos de ponto
        self.assertEqual(doc.styles["Normal"].font.size, Pt(10))
        self.assertIn("EXPERIÊNCIA PROFISSIONAL", self.titulos(doc))
        self.assertNotIn("Técnicas", doc.core_properties.comments or "")

    def test_formato_us_compacto(self):
        doc = self.gerar({**base(), "tecnicas": {"formato": "us", "estilo": "compacto", "paginas": 1}})
        sec = doc.sections[0]
        self.assertAlmostEqual(sec.page_width, Cm(21.59), delta=Cm(0.01))
        self.assertAlmostEqual(sec.page_height, Cm(27.94), delta=Cm(0.01))
        self.assertEqual(doc.styles["Normal"].font.size, Pt(10))
        self.assertIn("PROFESSIONAL EXPERIENCE", self.titulos(doc))
        self.assertIn("formato us; estilo compacto; até 1 página(s)", doc.core_properties.comments)

    def test_formato_eu_executivo(self):
        doc = self.gerar({**base(), "tecnicas": {"formato": "eu", "estilo": "executivo"}})
        self.assertAlmostEqual(doc.sections[0].page_width, Cm(21), delta=Cm(0.01))
        self.assertEqual(doc.styles["Normal"].font.size, Pt(10.5))
        self.assertIn("SUMMARY", self.titulos(doc))

    def test_corpo_nunca_abaixo_de_10(self):
        for estilo in curriculo.ESTILOS.values():
            self.assertGreaterEqual(estilo["corpo"], 10)

    def test_competencias_primeiro_e_destaques(self):
        cv = {**base(), "destaques": ["Destaque um", "Destaque dois"], "tecnicas": {"competencias_primeiro": True}}
        cv.pop("ordem", None)
        t = self.titulos(self.gerar(cv))
        self.assertLess(t.index("COMPETÊNCIAS"), t.index("EXPERIÊNCIA PROFISSIONAL"))
        self.assertEqual(t[t.index("RESUMO") + 1], "DESTAQUES")

    def test_ordem_do_json_vale_mais(self):
        cv = {**base(), "ordem": ["experiencia", "competencias"], "tecnicas": {"competencias_primeiro": True}}
        t = self.titulos(self.gerar(cv))
        self.assertLess(t.index("EXPERIÊNCIA PROFISSIONAL"), t.index("COMPETÊNCIAS"))


class TestSugestaoECortes(unittest.TestCase):
    def test_sugerir(self):
        self.assertEqual(curriculo.sugerir()["formato"], "br")
        br = {"titulo": "Analista de Dados", "local": "São Paulo, SP", "descricao": "Vaga para a nossa equipe de dados em São Paulo."}
        self.assertEqual(curriculo.sugerir(br)["formato"], "br")
        us = {"titulo": "Data Analyst", "local": "Remote - United States", "descricao": "You will join our team."}
        self.assertEqual(curriculo.sugerir(us)["formato"], "us")
        eu = {"titulo": "Data Analyst", "local": "Lisbon, Portugal", "descricao": "You will join our team in Lisbon."}
        self.assertEqual(curriculo.sugerir(eu)["formato"], "eu")

    def test_catalogo(self):
        c = curriculo.catalogo()
        self.assertEqual(set(c["tecnicas"]), {"ats", "foco", "xyz", "resultado_primeiro",
                                              "competencias_primeiro", "paginas_obrigatorio"})
        self.assertEqual(set(c["escolhas"]["paginas"]["opcoes"]), {"0", "1", "2"})
        json.dumps(c)  # serializável para a skill e a página

    def test_catalogo_com_vaga(self):
        c = curriculo.catalogo({"titulo": "Analista de Dados"})
        self.assertEqual(set(c["escolhas"]["paginas"]["opcoes"]), {"1", "2"})
        # Não altera o dicionário global ESCOLHAS
        self.assertIn(0, curriculo.ESCOLHAS["paginas"]["opcoes"])

    def test_descrever_tecnicas_sem_limite(self):
        tec = {"formato": "br", "estilo": "padrao", "paginas": 0}
        self.assertIn("sem limite de páginas", curriculo.descrever_tecnicas(tec))

    def test_sugestoes_corte(self):
        cv = base()
        cv["experiencia"] = [{"empresa": f"Empresa {i}", "cargos": [{"cargo": "Analista", "itens": list("abcdefg")}]}
                             for i in range(4)]
        cv["resumo"] = "x" * 500
        texto = " ".join(curriculo.sugestoes_corte(cv))
        self.assertIn("Empresa 2, Empresa 3", texto)
        self.assertIn("até 5 itens", texto)
        self.assertIn("resumo", texto)


class TestMain(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_main_paginas_zero_nunca_acima_do_limite(self):
        cv = {**base(), "tecnicas": {"paginas": 0}}
        arquivo = self.tmp / "cv.json"
        arquivo.write_text(json.dumps(cv), encoding="utf-8")
        out = io.StringIO()
        with mock.patch("sys.argv", ["curriculo.py", str(arquivo)]), \
             mock.patch.object(curriculo, "para_pdf", return_value=(self.tmp / "cv.pdf", "")), \
             mock.patch.object(curriculo, "paginas", return_value=5), \
             mock.patch.object(curriculo, "rodar_conferencia", return_value=0), \
             redirect_stdout(out):
            codigo = curriculo.main()
        self.assertEqual(codigo, 0)
        self.assertNotIn("acima do limite", out.getvalue())

    def test_main_paginas_com_limite_acima_sai_com_3(self):
        cv = {**base(), "tecnicas": {"paginas": 2}}
        arquivo = self.tmp / "cv.json"
        arquivo.write_text(json.dumps(cv), encoding="utf-8")
        out = io.StringIO()
        with mock.patch("sys.argv", ["curriculo.py", str(arquivo)]), \
             mock.patch.object(curriculo, "para_pdf", return_value=(self.tmp / "cv.pdf", "")), \
             mock.patch.object(curriculo, "paginas", return_value=5), \
             mock.patch.object(curriculo, "rodar_conferencia", return_value=0), \
             redirect_stdout(out):
            codigo = curriculo.main()
        self.assertEqual(codigo, 3)
        self.assertIn("acima do limite", out.getvalue())


if __name__ == "__main__":
    unittest.main()
