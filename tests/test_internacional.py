"""Testes da área internacional e dos idiomas aceitos (filtros.py, vagas.py, banco.py), com a fonte falsa."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash"), str(Path(__file__).resolve().parent)]
import banco  # noqa: E402
import filtros  # noqa: E402
import fonte_falsa  # noqa: E402
import vagas  # noqa: E402

BASE = {"termos": ["analista"], "localidade": {"pais": "Brasil", "estado": "PR", "cidade": "Curitiba", "raio_km": 25},
        "modelos": {"remoto": False, "hibrido": True, "presencial": False}}
PT = ("Estamos buscando uma pessoa analista para a nossa equipe. Você vai trabalhar com dados e com a área de vendas, "
      "e também com o time de produto. Não é preciso ter experiência em todas as ferramentas, mas é bom conhecer SQL. "
      "Os benefícios incluem plano de saúde e vale refeição para você e sua família, com trabalho remoto.")
EN = ("We are looking for an analyst to join our team. You will work with the data and the sales team, and you are "
      "expected to have experience with SQL. This is a remote role and we will support your growth with our team "
      "and the company. You will be part of a team that is about building great products for our customers.")
ES = ("Buscamos una persona analista para nuestro equipo. El trabajo es con los datos y con el equipo de ventas, y "
      "con las personas del producto. Somos una empresa que valora el conocimiento y tu experiencia es muy importante "
      "para el puesto. Los beneficios incluyen seguro y trabajo remoto para ti y tus compañeros del equipo.")
FR = ("Nous recherchons un analyste pour notre équipe. Vous travaillerez avec les données et les équipes des ventes, "
      "et vous serez au coeur du poste dans une entreprise qui valorise le travail et votre expérience. Le poste est "
      "pour une personne avec des connaissances et des compétences sur les outils des données de notre entreprise.")


def efet(**mud):
    return filtros.efetivos({**BASE, **mud})


class TestConfig(unittest.TestCase):
    def test_padroes_neutros_e_formato_antigo(self):
        f = efet()
        self.assertEqual(f["idiomas_aceitos"], [])
        i = f["internacional"]
        self.assertEqual((i["ativo"], i["aceita_mudar"], i["passaporte"], i["salario_min_anual_usd"], i["fuso_horas"]),
                         (False, False, False, 0, 0))
        antigo = filtros.efetivos({**BASE, "internacional": {"ativo": True, "paises": ["Portugal"], "termos": ["x"]}})
        self.assertEqual(antigo["internacional"]["paises"], ["Portugal"])

    def test_validar(self):
        cfg = {**efet(), "idiomas_aceitos": ["pt", "en"],
               "internacional": {"ativo": True, "paises": ["Portugal"], "termos": ["data analyst"], "regioes": ["latam"],
                                 "salario_min_anual_usd": 60000, "fuso_horas": 3, "contratacao": ["eor"],
                                 "aceita_mudar": True, "paises_mudanca": ["Irlanda"], "passaporte": True,
                                 "autorizacao_trabalho": ["Portugal"], "precisa_sponsor": False}}
        v = filtros.validar(cfg)
        self.assertTrue(v["internacional"]["ativo"])  # sem remoto no Brasil
        self.assertEqual(v["idiomas_aceitos"], ["pt", "en"])
        self.assertEqual(v["internacional"]["paises_mudanca"], ["Irlanda"])
        for ruim, msg in (({"paises": []}, "país"), ({"termos": []}, "cargo"), ({"regioes": ["lua"]}, "região"),
                          ({"fuso_horas": 20}, "fuso"), ({"paises_mudanca": ["Atlântida"]}, "país desconhecido")):
            with self.assertRaises(ValueError, msg=msg):
                filtros.validar({**cfg, "internacional": {**cfg["internacional"], **ruim}})
        with self.assertRaises(ValueError):
            filtros.validar({**cfg, "idiomas_aceitos": ["xx"]})


class TestAreaEPais(unittest.TestCase):
    def test_pais_do_local(self):
        for local, esperado in (("Remote - United States", "Estados Unidos"), ("Lisboa, Portugal", "Portugal"),
                                ("London, UK", "Reino Unido"), ("Worldwide", "mundo todo"), ("LATAM", "América Latina"),
                                ("Curitiba, PR", None), ("São Paulo, Brasil", "Brasil"), ("", None),
                                ("Porto Alegre, RS", None)):
            self.assertEqual(filtros.pais_do_local(local), esperado, local)

    def test_area_da_vaga(self):
        f = efet()
        self.assertEqual(filtros.area_da_vaga({"grupos": ["internacional:Portugal"]}, f), ("internacional", "Portugal"))
        self.assertEqual(filtros.area_da_vaga({"grupos": ["remoto", "internacional:Portugal"]}, f), ("nacional", None))
        self.assertEqual(filtros.area_da_vaga({"grupos": ["mudanca:Irlanda"]}, f), ("internacional", "Irlanda"))
        self.assertEqual(filtros.area_da_vaga({"local": "Remote - US"}, f), ("internacional", "Estados Unidos"))
        self.assertEqual(filtros.area_da_vaga({"local": "Curitiba"}, f), ("nacional", None))
        self.assertEqual(filtros.area_da_vaga({"area": "internacional", "pais_vaga": "Chile", "local": "Curitiba"}, f),
                         ("internacional", "Chile"))


class TestConsultas(unittest.TestCase):
    def test_internacional_sem_remoto_e_mudanca(self):
        f = efet(internacional={"ativo": True, "paises": ["Portugal"], "termos": ["data analyst"],
                                "aceita_mudar": True, "paises_mudanca": ["Irlanda"]})
        cs = filtros.consultas(f)
        grupos = [(c["grupo"], c["area"], c["remoto"]) for c in cs]
        self.assertIn(("local", "nacional", False), grupos)
        self.assertIn(("internacional:Portugal", "internacional", True), grupos)
        self.assertIn(("mudanca:Irlanda", "internacional", False), grupos)
        self.assertIn("presencial ou híbrido em: Irlanda", filtros.resumo(f))
        desligada = filtros.consultas(efet())
        self.assertTrue(all(c["area"] == "nacional" for c in desligada))


class TestIdiomaESalario(unittest.TestCase):
    def test_idioma_texto(self):
        self.assertEqual(filtros.idioma_texto(PT), "pt")
        self.assertEqual(filtros.idioma_texto(EN), "en")
        self.assertEqual(filtros.idioma_texto(ES), "es")
        self.assertEqual(filtros.idioma_texto(FR), "fr")
        self.assertIsNone(filtros.idioma_texto("Data Analyst"))
        self.assertIsNone(filtros.idioma_texto("você não com uma the and with you " * 5))  # empate: não decide
        self.assertEqual(filtros.idioma_da_vaga({"descricao": PT, "idioma": "en"}), "en")  # o da análise vale mais

    def test_corte_por_idioma(self):
        f = efet(idiomas_aceitos=["pt", "en"])
        self.assertEqual(filtros.criterios({"titulo": "Analista", "descricao": ES}, f),
                         ["Vaga em espanhol; você aceita português e inglês"])
        for texto in (PT, EN, "curta"):
            self.assertEqual(filtros.criterios({"titulo": "Analista", "descricao": texto}, f), [])
        self.assertEqual(filtros.criterios({"titulo": "Analista", "descricao": ES}, efet()), [])  # vazio = todos

    def test_salario_anual(self):
        casos = {"USD 100,000 - 120,000 per year": 120000, "$60k-$80k": 80000, "US$ 5,000/month": 60000,
                 "$50/hour": 104000, "R$ 8.000 por mês": None, "EUR 60.000": None, "": None, "a combinar": None}
        for texto, esperado in casos.items():
            self.assertEqual(filtros.salario_anual_usd({"salario": texto}), esperado, texto)
        f = efet(internacional={"salario_min_anual_usd": 90000})
        vaga = {"titulo": "Data Analyst", "local": "Remote - US", "salario": "$60k-$80k"}
        self.assertEqual(filtros.criterios(vaga, f), ["Paga até US$ 80,000 por ano; seu mínimo é US$ 90,000"])
        self.assertEqual(filtros.criterios({**vaga, "local": "Curitiba"}, f), [])  # só para vaga internacional
        self.assertEqual(filtros.criterios({**vaga, "salario": None}, f), [])  # sem salário, não corta


class TestBuscaPorArea(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.patches = [mock.patch.object(vagas, "CACHE", self.tmp / ".cache"),
                        mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db"),
                        mock.patch.object(filtros, "CONFIG", self.tmp / "config.json"),
                        mock.patch.dict(vagas.FONTES, {"falsa": fonte_falsa})]
        for p in self.patches:
            p.start()
        fonte_falsa.CHAMADAS.clear()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        if hasattr(fonte_falsa, "AREAS"):
            del fonte_falsa.AREAS
        shutil.rmtree(self.tmp, ignore_errors=True)

    def config(self):
        return {**BASE, "fontes": ["falsa"], "internacional": {"ativo": True, "paises": ["Portugal"], "termos": ["data analyst"]}}

    def test_area_gravada_e_fonte_por_area(self):
        cfg = self.config()
        f = filtros.efetivos(cfg)
        r = vagas.executar(cfg, f, ["falsa"], 10, pausa=0)
        vagas.gravar_resultado(r, sem_avaliacao=True)
        areas = {v["id"]: (v["area"], v["pais_vaga"]) for v in banco.listar_vagas()}
        self.assertEqual(areas["falsa-data-analyst-internacional-portugal-2"], ("internacional", "Portugal"))
        self.assertEqual(areas["falsa-analista-local-2"], ("nacional", None))
        self.assertEqual(len(fonte_falsa.CHAMADAS), 2)
        fonte_falsa.CHAMADAS.clear()
        fonte_falsa.AREAS = ("nacional",)
        r = vagas.executar(cfg, f, ["falsa"], 10, pausa=0)
        self.assertEqual([c["grupo"] for c in fonte_falsa.CHAMADAS], ["local"])
        self.assertEqual(r["parametros"]["consultas"], 2)

    def test_analise_com_idioma_e_vaga_por_link(self):
        (self.tmp / "config.json").write_text(json.dumps({**self.config(), "idiomas_aceitos": ["pt", "en"]}), encoding="utf-8")
        self.assertEqual(banco.validar_analise({"aderencia": 70, "idioma": "ES"})["idioma"], "es")
        with self.assertRaises(ValueError):
            banco.validar_analise({"aderencia": 70, "idioma": "espanhol"})
        doc, nova = banco.criar_de_link({"id": "x-1", "titulo": "Data Analyst", "empresa": "Acme",
                                         "local": "Remote - United States", "descricao": EN})
        self.assertTrue(nova)
        self.assertEqual((doc["area"], doc["pais_vaga"]), ("internacional", "Estados Unidos"))
        doc = banco.criar_manual({"titulo": "Analista", "empresa": "Beta", "local": "Curitiba", "etapa": "relatorio",
                                  "area": "internacional", "pais_vaga": "Chile", "descricao": ES})
        self.assertEqual((doc["area"], doc["pais_vaga"]), ("internacional", "Chile"))
        self.assertEqual(doc["triagem"], "fora")
        self.assertIn("espanhol", doc["motivo_fora"][0])


if __name__ == "__main__":
    unittest.main()
