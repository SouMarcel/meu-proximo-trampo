"""Faixa salarial (spec 028), sem rede e sem IA: leitura dos textos de salário (formatos do Brasil e de fora, benefício
não conta), vagas parecidas (cargo, senioridade e moeda), resumo, links que só a pessoa abre, anotações e as rotas."""
import http.client
import json
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock
from urllib.parse import unquote_plus

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import banco  # noqa: E402
import entrevista  # noqa: E402
import salarios  # noqa: E402


def vaga(vid, titulo, salario=None, **campos):
    return {"id": vid, "origem": "busca", "plataforma": "Gupy", "titulo": titulo, "empresa": f"Empresa {vid}",
            "url": f"https://exemplo.invalid/{vid}", "triagem": "seguir", "etapa": "salva", "salario": salario, **campos}


def gravar(*docs):
    with banco.escrita() as con:
        for d in docs:
            banco._gravar(con, d["id"], d)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        p = mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db")
        p.start()
        self.addCleanup(p.stop)


class TestLerValor(unittest.TestCase):
    def v(self, texto, moeda=None):
        r = salarios.ler_valor(texto, moeda)
        return r and (r["min"], r["max"], r["moeda"], r["periodo"], r["mensal_min"], r["mensal_max"])

    def test_formatos_do_brasil(self):
        self.assertEqual(self.v("R$ 5.000 - R$ 7.000"), (5000, 7000, "BRL", "mes", 5000, 7000))
        self.assertEqual(self.v("R$ 5.000,00 a R$ 7.500,50 por mês"), (5000, 7500.5, "BRL", "mes", 5000, 7500.5))
        self.assertEqual(self.v("De R$ 5 mil a R$ 7 mil"), (5000, 7000, "BRL", "mes", 5000, 7000))
        self.assertEqual(self.v("R$ 60.000 por ano"), (60000, 60000, "BRL", "ano", 5000, 5000))
        self.assertEqual(self.v("R$ 50/hora"), (50, 50, "BRL", "hora", 11000, 11000))
        self.assertEqual(self.v("4500", "brl"), (4500, 4500, "BRL", "mes", 4500, 4500))

    def test_formatos_de_fora(self):
        self.assertEqual(self.v("US$ 80k - 100k/yr"), (80000, 100000, "USD", "ano", 6666.67, 8333.33))
        self.assertEqual(self.v("$90,000 - $120,000"), (90000, 120000, "USD", "ano", 7500, 10000))
        self.assertEqual(self.v("€ 4.200 per month"), (4200, 4200, "EUR", "mes", 4200, 4200))

    def test_beneficio_e_sem_numero_nao_contam(self):
        for t in ("VR R$ 30,00 por dia", "Vale refeição R$ 600/mês", "A combinar", "", None, "Remuneração compatível"):
            self.assertIsNone(salarios.ler_valor(t), t)


class TestParecidas(Base):
    def test_cargo_senioridade_e_moeda(self):
        alvo = vaga("a", "Analista de Dados Pleno", senioridade=["pleno"])
        outras = [
            vaga("b", "Analista de Dados", "R$ 6.000 a R$ 8.000", senioridade=["pleno"]),
            vaga("c", "Analista de Dados Sênior (Remoto)", "R$ 10.000", senioridade=["senior"]),  # outro nível
            vaga("d", "Analista de Dados - Híbrido", "R$ 5.500"),
            vaga("e", "Analista Financeiro", "R$ 7.000"),  # cargo diferente
            vaga("f", "Data Analyst", "US$ 4,000 per month"),  # outra moeda (e outro idioma)
            vaga("g", "Analista de Dados", "VR R$ 35 por dia"),  # benefício
            vaga("h", "Analista de Dados", None),
        ]
        ids = [p["id"] for p in salarios.parecidas(alvo, outras + [dict(alvo, salario="R$ 1")])]
        self.assertEqual(sorted(ids), ["b", "d"])
        r = salarios.resumo(salarios.parecidas(alvo, outras))
        self.assertEqual((r["n"], r["minimo"], r["maximo"], r["mediana"]), (2, 5500, 8000, None))

    def test_mediana_so_com_tres(self):
        itens = [{"mensal_min": a, "mensal_max": b, "moeda": "BRL"} for a, b in ((4000, 6000), (5000, 7000), (8000, 8000))]
        self.assertEqual(salarios.resumo(itens)["mediana"], 6000)
        self.assertIsNone(salarios.resumo([]))


class TestLinks(unittest.TestCase):
    def test_links_so_para_abrir(self):
        ls = salarios.links(vaga("a", "Analista de Dados Pleno (Remoto) - Vaga PCD", empresa="Acme"))
        self.assertTrue(all(l["url"].startswith("https://") for l in ls))
        texto = unquote_plus(" ".join(l["url"] for l in ls))
        self.assertIn("site:glassdoor.com.br", texto)
        self.assertIn('"Analista de Dados Pleno"', texto)
        self.assertIn('"Acme"', texto)
        self.assertNotIn("Remoto", texto)
        fora = salarios.links(vaga("b", "Data Analyst", "US$ 90,000", empresa="Acme", pais_vaga="Estados Unidos", area="internacional"))
        self.assertIn("site:glassdoor.com ", unquote_plus(fora[0]["url"]))
        confidencial = salarios.links(vaga("c", "Analista", empresa="Empresa confidencial"))
        self.assertTrue(all("confidencial" not in unquote_plus(l["url"]).lower() for l in confidencial))

    def test_nada_vai_para_a_internet(self):
        fonte = (RAIZ / "salarios.py").read_text(encoding="utf-8")
        for proibido in ("urlopen", "urllib.request", "http.client", "import ia", "requests"):
            self.assertNotIn(proibido, fonte)


class TestAnotacoes(Base):
    def test_anotar_remover_e_entrevista(self):
        gravar(vaga("a", "Analista de Dados"))
        lista = salarios.anotar("a", "  R$ 6 mil a  R$ 9 mil ", "Glassdoor")
        self.assertEqual(lista[0]["texto"], "R$ 6 mil a R$ 9 mil")
        self.assertEqual(lista[0]["fonte"], "Glassdoor")
        self.assertEqual(salarios.faixa("a")["pesquisas"], lista)
        prep = entrevista.salario(banco.obter("a"), "")
        self.assertEqual(prep["pesquisas"][0]["texto"], "R$ 6 mil a R$ 9 mil")
        self.assertEqual(salarios.remover("a", 0), [])
        for texto, fonte in (("", "Glassdoor"), ("R$ 1", "")):
            with self.assertRaises(salarios.SalarioErro):
                salarios.anotar("a", texto, fonte)
        with self.assertRaises(salarios.SalarioErro):
            salarios.remover("a", 3)
        with self.assertRaises(KeyError):
            salarios.anotar("x", "R$ 1", "eu")


class TestRotas(Base):
    def setUp(self):
        super().setUp()
        import servidor
        p = mock.patch.object(servidor.Handler, "hosts_permitidos", {"127.0.0.1", "localhost"})
        p.start()
        self.addCleanup(p.stop)
        self.srv = servidor.ThreadingHTTPServer(("127.0.0.1", 0), servidor.Handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        gravar(vaga("a", "Analista de Dados", "R$ 7.000"), vaga("b", "Analista de Dados", "R$ 5.000 a R$ 6.000"))

    def pedir(self, metodo, caminho, corpo=None):
        con = http.client.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=10)
        self.addCleanup(con.close)
        dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
        con.request(metodo, caminho, dados, {"Content-Type": "application/json"} if dados else {})
        r = con.getresponse()
        return r.status, json.loads(r.read())

    def test_rotas(self):
        st, j = self.pedir("GET", "/api/vagas/a/salario")
        self.assertEqual((st, j["vaga"]["valor"]["min"], [p["id"] for p in j["parecidas"]]), (200, 7000, ["b"]))
        self.assertTrue(j["links"])
        st, j = self.pedir("POST", "/api/vagas/a/salario", {"texto": "R$ 8 mil", "fonte": "Recrutador"})
        self.assertEqual((st, j["pesquisas"][0]["fonte"]), (200, "Recrutador"))
        self.assertEqual(self.pedir("POST", "/api/vagas/a/salario", {"texto": "", "fonte": "x"})[0], 400)
        st, j = self.pedir("DELETE", "/api/vagas/a/salario/0", {})
        self.assertEqual((st, j["pesquisas"]), (200, []))
        self.assertEqual(self.pedir("GET", "/api/vagas/zz/salario")[0], 404)
        self.assertEqual(self.pedir("GET", "/api/vagas/a%2Fb/salario")[0], 404)


if __name__ == "__main__":
    unittest.main()
