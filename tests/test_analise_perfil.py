"""Análises do perfil (analise_perfil.py) com perfil e vagas fictícios e uma IA falsa: lacunas das vagas (SC-001,
SC-002), cargos-alvo (SC-003), filtros só com confirmação (SC-004) e prontidão internacional (SC-005)."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import analise_perfil as ap  # noqa: E402
import banco  # noqa: E402
import filtros  # noqa: E402

PERFIL = (Path(__file__).resolve().parent / "dados" / "kit" / "perfil-ficticio.md").read_text(encoding="utf-8")


def vaga(i, lacunas, aderencia=70, seguida=False, triagem="pendente", descricao=""):
    return {"id": f"v{i}", "titulo": f"Analista {i}", "empresa": f"Empresa {i}", "analise_status": "feita",
            "aderencia": aderencia, "lacunas": lacunas, "triagem": "seguir" if seguida else triagem,
            "etapa": "salva" if seguida else None, "descricao": descricao}


VAGAS = [
    vaga(1, ["Tableau avançado"], 90, seguida=True),
    vaga(2, ["Experiência com Tableau"], 85, seguida=True),
    vaga(3, ["Tableau"], 80, seguida=True),
    vaga(4, ["Certificação AWS"], 40),
    vaga(5, ["Certificação AWS", "dbt"], 35),
    vaga(6, ["dbt (data build tool)"], 60, triagem="visitada"),
    vaga(7, ["Inglês fluente"], 75),
    vaga(8, [], 50, descricao="Requisitos:\n- Snowflake\n- Airflow"),
]


class ComDados(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.cfg = self.tmp / "config.json"
        self.cfg.write_text(json.dumps({"termos": ["analista", '"analista de dados"'], "localidade": {"pais": "Brasil"},
                                        "modelos": {"remoto": True}, "idiomas_aceitos": ["pt", "en"]}), encoding="utf-8")
        for alvo, nome, valor in ((banco, "DADOS", self.tmp), (filtros, "CONFIG", self.cfg)):
            p = mock.patch.object(alvo, nome, valor)
            p.start()
            self.addCleanup(p.stop)


class TestGuardar(ComDados):
    def test_salvar_carregar_marcar(self):
        self.assertEqual(ap.carregar(), {})
        r = ap.salvar("lacunas", {"itens": [1]})
        self.assertTrue(r["data"])
        self.assertEqual(ap.carregar()["lacunas"]["itens"], [1])
        self.assertEqual(ap.marcar("linkedin_en", True), {"linkedin_en": True})
        with self.assertRaises(ap.AnaliseErro):
            ap.marcar("outra", True)


class TestLacunas(unittest.TestCase):
    def test_ranking_agrupado_e_pesado(self):
        r = ap.lacunas(VAGAS, PERFIL, "todas")
        self.assertEqual(r["vagas"], 8)
        topo = r["itens"][0]
        self.assertIn("tableau", topo["termos"])  # SC-001: a mais frequente nas de maior aderência
        self.assertEqual(topo["vagas"], 3)  # as três variações juntas
        self.assertEqual(topo["nivel"], "critica")
        self.assertEqual([e["id"] for e in topo["exemplos"]], ["v1", "v2", "v3"])  # as de maior peso
        rotulos = {i["rotulo"] for i in r["itens"]}
        self.assertTrue(any("AWS" in x for x in rotulos) and any("dbt" in x for x in rotulos))
        self.assertIn("Snowflake", ap._frases(VAGAS[7], PERFIL))  # requisito do anúncio que o perfil não mostra entra
        self.assertFalse(any("snowflake" in i["termos"] for i in r["itens"]))  # mas, numa vaga só e de peso baixo, fica abaixo de 10%
        aws = next(i for i in r["itens"] if "AWS" in i["rotulo"])
        self.assertLess(aws["peso"], topo["peso"])
        self.assertTrue(all(i["nivel"] in ("critica", "alta", "media") for i in r["itens"]))

    def test_minimo_e_visoes(self):
        r = ap.lacunas(VAGAS, PERFIL, "seguidas")
        self.assertEqual((r["vagas"], r["faltam"], r["itens"]), (3, 2, []))  # SC-002
        self.assertEqual(ap.lacunas(VAGAS[:4], PERFIL)["faltam"], 1)
        with self.assertRaises(ap.AnaliseErro):
            ap.lacunas(VAGAS, PERFIL, "outra")

    def test_plano_com_ia_falsa(self):
        itens = ap.lacunas(VAGAS, PERFIL)["itens"]
        resposta = json.dumps([{"lacuna": "Tableau", "passos": ["Curso introdutório", "Refazer um painel do Power BI no Tableau",
                                                                  "Publicar", "Quarto passo"], "semanas": 4}])
        pedidos = []
        with mock.patch("ia.disponivel", return_value=True), mock.patch("ia.responder", side_effect=lambda p, **k: pedidos.append(p) or resposta), \
                mock.patch.object(ap, "_marca_ia", return_value={}):
            r = ap.plano_estudo(PERFIL, itens)
        self.assertEqual(len(r["itens"][0]["passos"]), 3)
        self.assertIn("nunca afirme", pedidos[0])
        with mock.patch("ia.disponivel", return_value=False), self.assertRaisesRegex(ap.AnaliseErro, "precisa de uma IA"):
            ap.plano_estudo(PERFIL, itens)


class TestCargos(ComDados):
    def test_cargos_com_evidencia(self):
        resposta = json.dumps([
            {"titulo": "Analista de BI", "titulo_en": "BI Analyst", "tipo": "lateral", "evidencia": "Painéis em Power BI usados por 1.500 pessoas", "lacuna": "Tableau"},
            {"titulo": "Analista de Dados Sênior", "titulo_en": "Senior Data Analyst", "tipo": "degrau", "evidencia": "Automatizei o relatório mensal", "lacuna": "liderança"},
            {"titulo": "Cientista de Dados", "titulo_en": "Data Scientist", "tipo": "vizinho", "evidencia": "Liderei time de machine learning na NASA", "lacuna": "ML"},
            {"titulo": "Analista de BI", "titulo_en": "BI Analyst", "tipo": "lateral", "evidencia": "repetido", "lacuna": ""},
            {"titulo": "Gerente", "tipo": "chefe", "evidencia": "x", "lacuna": ""}])
        with mock.patch("ia.disponivel", return_value=True), mock.patch("ia.responder", return_value=resposta), \
                mock.patch.object(ap, "_marca_ia", return_value={}):
            r = ap.cargos_alvo(PERFIL)
        self.assertEqual([c["titulo"] for c in r["itens"]], ["Analista de BI", "Analista de Dados Sênior", "Cientista de Dados"])
        self.assertEqual([c["conferir"] for c in r["itens"]], [False, False, True])  # SC-003: evidência inventada
        self.assertTrue(r["avisos"])  # menos de 5

    def test_filtros_so_com_confirmacao(self):
        antes = self.cfg.read_text(encoding="utf-8")
        cargos = [{"titulo": "Analista de BI", "titulo_en": "BI Analyst"}, {"titulo": "Analista de Dados", "titulo_en": ""}]
        r = ap.filtros_com_cargos(cargos)
        self.assertEqual(r["filtros"]["termos"], ["analista", '"analista de dados"', '"Analista de BI"', '"BI Analyst"'])
        self.assertEqual(self.cfg.read_text(encoding="utf-8"), antes)  # SC-004
        ap.filtros_com_cargos(cargos, confirmar=True)
        cfg = json.loads(self.cfg.read_text(encoding="utf-8"))
        self.assertIn('"Analista de BI"', cfg["termos"])
        self.assertEqual(cfg["idiomas_aceitos"], ["pt", "en"])  # o resto fica
        with self.assertRaises(ap.AnaliseErro):
            ap.filtros_com_cargos([{"titulo": "analista"}])  # nada novo


class TestProntidao(ComDados):
    def test_itens(self):
        cfg = {"termos": ["x"], "localidade": {"pais": "Brasil"}, "modelos": {"remoto": True},
               "internacional": {"ativo": False, "contratacao": ["contractor"], "passaporte": True, "autorizacao_trabalho": ["Portugal"]}}
        with mock.patch("curriculo_base.marcados", return_value={"pt": None, "en": "anexos/resume.pdf"}):
            itens = {i["item"]: i for i in ap.prontidao(PERFIL, cfg)}
        self.assertEqual(itens["ingles"]["situacao"], "pronto")  # "Inglês — avançado" no perfil
        self.assertEqual(itens["fuso"]["situacao"], "nao_informado")
        self.assertEqual(itens["contratacao"]["situacao"], "pronto")
        self.assertIn("Portugal", itens["passaporte"]["detalhe"])
        self.assertEqual((itens["curriculo_en"]["situacao"], itens["curriculo_en"]["detalhe"]), ("pronto", "resume.pdf"))
        self.assertEqual(itens["linkedin_en"]["situacao"], "nao_informado")
        ap.marcar("linkedin_en", True)
        with mock.patch("curriculo_base.marcados", return_value={"pt": None, "en": None}), mock.patch("curriculo_ia.listar", return_value=[]):
            itens = {i["item"]: i for i in ap.prontidao("# Perfil sem idiomas", cfg)}
        self.assertEqual((itens["linkedin_en"]["situacao"], itens["ingles"]["situacao"], itens["curriculo_en"]["situacao"]),
                         ("pronto", "nao_informado", "falta"))  # SC-005


class TestLinhaDeComando(ComDados):
    def test_comandos(self):
        with mock.patch.object(ap, "vagas_do_banco", return_value=VAGAS), mock.patch.object(ap, "perfil_texto", return_value=PERFIL), \
                mock.patch("sys.stdout"):
            self.assertEqual(ap.main(["lacunas"]), 0)
            self.assertEqual(ap.main(["lacunas", "--seguidas"]), 0)
            self.assertEqual(ap.main(["prontidao"]), 0)
        self.assertEqual(ap.carregar()["lacunas"]["visao"], "todas")  # a análise ficou salva
        with mock.patch("ia.disponivel", return_value=False), mock.patch("sys.stderr"):
            self.assertEqual(ap.main(["cargos"]), 2)


if __name__ == "__main__":
    unittest.main()
