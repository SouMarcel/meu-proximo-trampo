"""Começar pelo currículo que a pessoa já tem (curriculo_base.py): currículos fictícios gerados aqui (DOCX em
português e PDF em inglês), máscara de documentos, perfil feito do currículo, filtros propostos com e sem IA,
confirmação e o seu currículo no checklist das vagas."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import curriculo_base as cb  # noqa: E402
import filtros  # noqa: E402
import kit  # noqa: E402
import primeiros_passos as pp  # noqa: E402

LINHAS_PT = ["Ana Exemplo", "Curitiba, PR · ana@exemplo.com", "CPF: 123.456.789-09 · Data de nascimento: 01/02/1990",
             "Resumo", "Analista de dados com foco em relatórios comerciais.", "Experiência",
             "Analista de Dados Pleno — Empresa Alfa", "03/2021 – atual",
             "Automatizei o relatório mensal, reduzindo o fechamento de 10 para 6 dias.",
             "Assistente de Dados — Empresa Beta", "01/2018 – 06/2020", "Formação", "Estatística — Universidade Gama (2017)"]
LINHAS_EN = ["John Sample", "Austin, Texas · john@example.com", "Summary",
             "Data analyst who builds sales reporting for the team and works fully remote with the whole company.",
             "Experience", "Senior Data Analyst at Acme Corp (2022 - Present)",
             "Built Power BI dashboards used by the sales team every day.", "Data Analyst at Beta Inc (2019 - 2022)",
             "Education", "BSc Statistics (2018)"]


def criar_docx(destino: Path, linhas: list[str]) -> Path:
    import docx
    d = docx.Document()
    for linha in linhas:
        d.add_paragraph(linha)
    d.save(destino)
    return destino


def criar_pdf(destino: Path, linhas: list[str]) -> Path:
    """Um PDF de texto simples (Helvetica), montado à mão para o teste."""
    esc = lambda s: s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    fluxo = "BT /F1 11 Tf 50 780 Td 14 TL " + " ".join(f"({esc(l)}) Tj T*" for l in linhas) + " ET"
    objetos = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
               f"<< /Length {len(fluxo)} >>\nstream\n{fluxo}\nendstream",
               "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    corpo, offsets = "%PDF-1.4\n", []
    for i, o in enumerate(objetos, 1):
        offsets.append(len(corpo.encode("latin-1")))
        corpo += f"{i} 0 obj\n{o}\nendobj\n"
    xref = len(corpo.encode("latin-1"))
    corpo += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n" + "".join(f"{o:010d} 00000 n \n" for o in offsets)
    corpo += f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
    destino.write_bytes(corpo.encode("latin-1"))
    return destino


class ComPasta(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "anexos" / "cv").mkdir(parents=True)
        (self.tmp / "anexos" / "perfis-anteriores").mkdir()
        self.cfg = self.tmp / "config.json"
        self.cfg.write_text(json.dumps({"termos": ["analista"], "localidade": {"pais": "Brasil"}, "modelos": {"remoto": True},
                                        "idiomas_aceitos": ["pt", "en"], "perfil": "perfil.md",
                                        "internacional": {"ativo": True, "fontes": ["remotive"], "termos": ["data analyst"]}}), encoding="utf-8")
        for alvo, nome, valor in ((cb, "RAIZ", self.tmp), (cb, "ANEXOS", self.tmp / "anexos"), (pp, "RAIZ", self.tmp),
                                  (pp, "ANEXOS", self.tmp / "anexos" / "primeiros-passos"),
                                  (pp, "ANTERIORES", self.tmp / "anexos" / "perfis-anteriores"),
                                  (pp, "PROGRESSO", self.tmp / ".cache" / "pp.json"), (filtros, "CONFIG", self.cfg)):
            p = mock.patch.object(alvo, nome, valor)
            p.start()
            self.addCleanup(p.stop)
        self.pt = criar_docx(self.tmp / "anexos" / "cv" / "curriculo.docx", LINHAS_PT)
        self.en = criar_pdf(self.tmp / "anexos" / "resume.pdf", LINHAS_EN)
        criar_docx(self.tmp / "anexos" / "perfis-anteriores" / "velho.docx", ["velho"])
        self.sem_ia = mock.patch("ia.disponivel", return_value=False)
        self.sem_ia.start()
        self.addCleanup(self.sem_ia.stop)



class TestBase(ComPasta):
    def test_candidatos_e_marcar(self):
        nomes = {c["arquivo"]: c["idioma"] for c in cb.candidatos()}
        self.assertEqual(nomes, {"anexos/cv/curriculo.docx": "pt", "anexos/resume.pdf": "en"})  # sem perfis-anteriores
        self.assertEqual(cb.marcar("en", "anexos/resume.pdf"), {"pt": None, "en": "anexos/resume.pdf"})
        cb.marcar("pt", "anexos/cv/curriculo.docx")
        cfg = json.loads(self.cfg.read_text(encoding="utf-8"))
        self.assertEqual(cfg["curriculo_base"], {"en": "anexos/resume.pdf", "pt": "anexos/cv/curriculo.docx"})
        self.assertEqual(cfg["idiomas_aceitos"], ["pt", "en"])  # o resto do config fica
        self.assertEqual(cb.desmarcar("en"), {"pt": "anexos/cv/curriculo.docx", "en": None})
        for ruim in ("../config.json", "anexos/perfis-anteriores/velho.docx", "anexos/nao-existe.pdf", "config.json"):
            with self.assertRaises(cb.CurriculoErro, msg=ruim):
                cb.marcar("pt", ruim)
        self.pt.unlink()
        self.assertEqual(cb.marcados()["pt"], None)  # arquivo sumido conta como não marcado

    def test_perfil_mascarado_com_origem(self):
        lido = cb.ler("anexos/cv/curriculo.docx")
        perfil = cb.perfil_do_curriculo(lido["texto"], lido["arquivo"], "2026-10-10")
        self.assertNotIn("123.456.789-09", perfil)  # SC-002
        self.assertNotIn("01/02/1990", perfil)
        self.assertIn("Analista de Dados Pleno — Empresa Alfa", perfil)
        self.assertEqual(pp.origem_do_perfil(perfil), {"arquivo": "anexos/cv/curriculo.docx", "data": "2026-10-10"})
        self.assertIsNone(pp.origem_do_perfil("# Meu perfil"))
        self.assertEqual(cb.ler("anexos/resume.pdf")["idioma"], "en")


class TestProposta(ComPasta):
    def test_dados_sem_ia(self):
        pt = cb.dados_sem_ia(cb.ler("anexos/cv/curriculo.docx")["texto"])
        self.assertEqual((pt["cargos_alvo"], pt["cidade"], pt["estado"]), (["Analista de Dados Pleno"], "Curitiba", "PR"))
        en = cb.dados_sem_ia(cb.ler("anexos/resume.pdf")["texto"])
        self.assertEqual((en["cargos_alvo_en"], en["modelos"]), (["Senior Data Analyst"], ["remoto"]))  # SC-005
        objetivo = cb.dados_sem_ia("Objetivo: Product Owner\nExperiência\nAnalista — X\n2020 - atual")
        self.assertEqual(objetivo["cargos_alvo"], ["Product Owner"])

    def test_dados_com_ia_e_falha(self):
        resposta = json.dumps({"cargos_alvo": ["Analista de Dados"], "cargos_alvo_en": ["Data Analyst"], "cidade": "Curitiba",
                               "estado": "PR", "modelos": ["remoto", "talvez"]})
        pedidos = []
        with mock.patch("ia.responder", side_effect=lambda p, **k: pedidos.append(p) or resposta):
            d = cb.dados_do_curriculo(cb.ler("anexos/cv/curriculo.docx")["texto"], com_ia=True)
        self.assertEqual((d["origem"], d["cargos_alvo_en"], d["modelos"]), ("ia", ["Data Analyst"], ["remoto"]))
        self.assertNotIn("123.456.789-09", pedidos[0])  # SC-002: documentos não vão para a IA
        with mock.patch("ia.responder", side_effect=RuntimeError("fora do ar")):
            self.assertEqual(cb.dados_do_curriculo(cb.ler("anexos/cv/curriculo.docx")["texto"], com_ia=True)["origem"], "texto")

    def test_proposta_nao_grava_e_confirmar_grava(self):
        antes = self.cfg.read_text(encoding="utf-8")
        r = cb.proposta("anexos/cv/curriculo.docx")
        self.assertEqual(r["filtros"]["termos"], ['"Analista de Dados Pleno"'])
        self.assertEqual(r["filtros"]["localidade"]["cidade"], "Curitiba")
        self.assertTrue(r["filtros"]["internacional"]["ativo"])  # a busca no exterior que a pessoa já tinha fica
        self.assertEqual(self.cfg.read_text(encoding="utf-8"), antes)  # SC-003: a proposta não grava nada
        self.assertFalse((self.tmp / "perfil.md").exists())
        g = cb.confirmar({"arquivo": r["arquivo"], "perfil": r["perfil"], "edicao": {**r["edicao"], "cargos_en": ["Data Analyst"]},
                          "idioma": r["idioma"]})
        self.assertEqual(g["perfil"], "perfil.md")
        cfg = json.loads(self.cfg.read_text(encoding="utf-8"))
        self.assertEqual(cfg["termos"], ['"Analista de Dados Pleno"', '"Data Analyst"'])
        self.assertEqual((cfg["idiomas_aceitos"], cfg["internacional"]["fontes"], cfg["internacional"]["termos"]),
                         (["pt", "en"], ["remotive"], ["data analyst"]))  # os cargos do exterior que já havia ficam
        self.assertEqual(cfg["curriculo_base"], {"pt": "anexos/cv/curriculo.docx"})
        self.assertIsNotNone(pp.origem_do_perfil((self.tmp / "perfil.md").read_text(encoding="utf-8")))
        self.assertEqual(pp.carregar()["etapa"], "concluido")

    def test_manter_perfil(self):
        (self.tmp / "perfil.md").write_text("# Meu perfil de verdade\n", encoding="utf-8")
        r = cb.proposta("anexos/resume.pdf")
        self.assertTrue(r["existe_perfil"])
        g = cb.confirmar({"arquivo": r["arquivo"], "perfil": r["perfil"], "manter_perfil": True, "idioma": "en"})
        self.assertIsNone(g["perfil"])
        self.assertEqual((self.tmp / "perfil.md").read_text(encoding="utf-8"), "# Meu perfil de verdade\n")
        self.assertEqual(g["curriculo_base"]["en"], "anexos/resume.pdf")
        self.assertEqual(json.loads(self.cfg.read_text(encoding="utf-8"))["termos"], ["analista"])  # filtros também ficam
        # substituir guarda o anterior
        g2 = cb.confirmar({"arquivo": r["arquivo"], "perfil": r["perfil"], "idioma": "en"})
        self.assertTrue(g2["anterior"].startswith("anexos/perfis-anteriores/"))

    def test_curriculo_sem_texto(self):
        criar_pdf(self.tmp / "anexos" / "escaneado.pdf", [])
        r = cb.proposta("anexos/escaneado.pdf")
        self.assertEqual(r["perfil"], "")
        self.assertTrue(any("escaneado" in a for a in r["avisos"]))


class TestChecklist(unittest.TestCase):
    BASE = {"pt": {"nome": "curriculo.docx", "url": "/arquivos/curriculo-base/pt"}, "en": None}

    def test_item_por_idioma(self):
        pt = kit.checklist({"idioma": "pt", "descricao": ""}, self.BASE)[0]
        self.assertEqual((pt["estado"], pt["base"]["nome"]), ("pronto", "curriculo.docx"))
        en = kit.checklist({"idioma": "en", "descricao": ""}, self.BASE)[0]
        self.assertEqual((en["estado"], en["falta_base"]), ("a_fazer", "en"))
        escolha = kit.checklist({"idioma": "pt", "kit": {"estados": {"curriculo": "a_fazer"}}}, self.BASE)[0]
        self.assertEqual(escolha["estado"], "a_fazer")  # a escolha da pessoa vale (SC-004)
        self.assertNotIn("base", kit.checklist({"idioma": "pt"})[0])  # sem currículo marcado, como antes


class TestLinhaDeComando(ComPasta):
    def test_lista_proposta_usar_marcar(self):
        with mock.patch("sys.stdout") as saida:
            self.assertEqual(cb.main(["lista"]), 0)
            self.assertEqual(cb.main(["proposta", "anexos/cv/curriculo.docx", "--sem-ia"]), 0)
        self.assertFalse((self.tmp / "perfil.md").exists())
        with mock.patch("sys.stdout"):
            self.assertEqual(cb.main(["marcar", "anexos/resume.pdf"]), 0)
            self.assertEqual(cb.main(["usar", "anexos/cv/curriculo.docx", "--sem-ia", "--manter-perfil"]), 0)
        self.assertEqual(cb.marcados(), {"pt": "anexos/cv/curriculo.docx", "en": "anexos/resume.pdf"})
        self.assertFalse((self.tmp / "perfil.md").exists())
        with mock.patch("sys.stderr"):
            self.assertEqual(cb.main(["marcar", "../config.json"]), 2)


if __name__ == "__main__":
    unittest.main()
