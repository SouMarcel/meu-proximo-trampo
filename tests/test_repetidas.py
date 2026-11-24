"""A mesma vaga em vários portais (spec 058): nome-base da empresa e mesma_empresa, IndiceVistas e sincronia com a
empresa escrita de outro jeito, juntar, grupos de repetidas, o comando e as rotas (link original com leitor falso).
Empresas fictícias."""
import http.client
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import banco  # noqa: E402
import filtros  # noqa: E402
import sincronia  # noqa: E402

HOJE = date.today().isoformat()


def vaga(vid, empresa="Alfaweb", titulo="SCRUM MASTER PL", plataforma="Gupy", **campos):
    return {"id": vid, "origem": "busca", "plataforma": plataforma, "titulo": titulo, "empresa": empresa,
            "url": f"https://exemplo.invalid/{vid}", "triagem": "pendente", "descricao": "", "encontrada_em": HOJE,
            **campos}


def gravar(*docs):
    with banco.escrita() as con:
        for d in docs:
            banco._gravar(con, d["id"], d)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for p in (mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db"),
                  mock.patch.object(banco, "BACKUPS", self.tmp / "backup"),
                  mock.patch.object(filtros, "CONFIG", self.tmp / "config.json")):
            p.start()
            self.addCleanup(p.stop)


class TestEmpresa(unittest.TestCase):
    def test_empresa_base(self):
        for nome in ("Alfaweb", "Alfaweb Corp", "Seja Alfaweb", "Alfa Web Ltda.", "ALFAWEB S.A.", "Carreiras Alfaweb"):
            with self.subTest(nome=nome):
                self.assertEqual(banco.empresa_base(nome), "alfaweb")
        self.assertEqual(banco.empresa_base("Empresa confidencial"), "")
        self.assertEqual(banco.empresa_base("Web Alfa"), "webalfa")  # a ordem das palavras conta

    def test_mesma_empresa(self):
        self.assertTrue(banco.mesma_empresa("Alfaweb", "Alfaweb Tecnologia"))  # contida, com 7 letras
        self.assertTrue(banco.mesma_empresa("Seja Alfaweb", "Alfaweb Corp"))
        self.assertFalse(banco.mesma_empresa("Ita", "Itaú Unibanco"))  # contida com menos de 5 letras
        self.assertFalse(banco.mesma_empresa("Web Alfa", "Alfaweb"))
        self.assertFalse(banco.mesma_empresa("Empresa confidencial", "Empresa confidencial"))


class TestReconhecer(Base):
    def test_indice_pela_empresa_contida(self):  # US1
        gravar(vaga("gupy-1", "Alfaweb"))
        indice = banco.IndiceVistas()
        self.assertEqual(indice.achar(vaga("jobgether-x", "Alfaweb Corp", plataforma="JobGether")), "gupy-1")
        self.assertEqual(indice.achar(vaga("y", "Seja Alfaweb")), "gupy-1")
        self.assertIsNone(indice.achar(vaga("z", "Alfaweb", titulo="SCRUM MASTER SR")))  # outro cargo
        self.assertIsNone(indice.achar(vaga("w", "Betaweb")))

    def test_contida_so_entre_portais(self):  # regiões diferentes no mesmo portal são vagas diferentes
        gravar(vaga("li-1", "Omega Data North America", plataforma="LinkedIn"))
        indice = banco.IndiceVistas()
        self.assertIsNone(indice.achar(vaga("li-2", "Omega Data Europe", plataforma="LinkedIn")))
        self.assertIsNone(indice.achar(vaga("li-3", "Omega Data", plataforma="LinkedIn")))
        self.assertEqual(indice.achar(vaga("gupy-3", "Omega Data", plataforma="Gupy")), "li-1")
        gravar(vaga("li-2", "Omega Data Europe", plataforma="LinkedIn"))
        self.assertEqual(banco.grupos_repetidos(), [])

    def test_prazo_e_juntada(self):
        gravar(vaga("velha", "Alfaweb", encontrada_em=(date.today() - timedelta(days=90)).isoformat()),
               vaga("principal", "Gamaweb"), {**vaga("juntada", "Gamaweb"), "juntada_a": "principal",
                                               "arquivada_em": "2026-11-24T10:00:00"})
        indice = banco.IndiceVistas()
        self.assertIsNone(indice.achar(vaga("n", "Alfaweb Corp")))  # mais de 60 dias: conta como nova
        self.assertEqual(indice.achar({"id": "juntada"}), "principal")  # o id da juntada aponta para a principal

    def test_sincronia_casa_com_empresa_de_outro_jeito(self):
        v = vaga("gupy-1", "Alfaweb", triagem="seguir", etapa="aplicada", etapa_em=HOJE)
        lida = {"portal": "gupy", "id": "gupya-9", "titulo": "Scrum Master PL", "empresa": "Seja Alfaweb",
                "etapa": "entrevista", "resultado": None, "data": HOJE, "ativa": True, "plataforma": "Gupy",
                "status": "Entrevista", "nota": None, "avisos": [], "url": ""}
        r = sincronia.proposta([lida], [v])
        self.assertEqual(len(r["itens"]), 1)
        self.assertEqual(r["itens"][0]["vaga_id"], "gupy-1")


class TestJuntar(Base):
    def setUp(self):
        super().setUp()
        gravar(vaga("gupy-1", "Alfaweb", descricao="Texto da vaga.", aderencia=88, analise_status="feita",
                    triagem="seguir", etapa="aplicada", etapa_em="2026-11-01", anotacao="enviei o currículo",
                    encontrada_em="2026-11-01"),
               vaga("gupya-9", "Seja Alfaweb", triagem="seguir", etapa="entrevista", etapa_em="2026-11-20",
                    anotacao="entrevista marcada", curriculos=["cv-alfa"], encontrada_em="2026-11-20"),
               vaga("jobgether-x", "Alfaweb Corp", plataforma="JobGether", aderencia=72, analise_status="feita",
                    nota_sem_descricao=True, encontrada_em="2026-11-22"),
               vaga("outra", "Betaweb"))

    def test_grupos_e_principal(self):  # US3
        grupos = banco.grupos_repetidos()
        self.assertEqual(len(grupos), 1)
        g = grupos[0]
        self.assertEqual(g["ids"], ["gupy-1", "gupya-9", "jobgether-x"])
        self.assertEqual((g["principal"]["id"], g["etapa_final"]), ("gupy-1", "entrevista"))
        self.assertEqual(g["outras"][1]["aderencia"], None)  # nota provisória não conta como nota

    def test_juntar(self):  # FR-004, FR-005
        r = banco.juntar_repetidas()
        self.assertEqual((r["juntados"], r["vagas"]), (1, 2))
        self.assertTrue((self.tmp / "backup" / r["backup"]).exists())
        p = banco.obter("gupy-1")
        self.assertEqual(p["outras_plataformas"], ["JobGether"])
        self.assertEqual(set(p["ids_relacionados"]), {"gupya-9", "jobgether-x"})
        self.assertEqual((p["etapa"], p["etapa_em"], p["aderencia"]), ("entrevista", "2026-11-20", 88))
        self.assertEqual(p["anotacao"], "enviei o currículo\nentrevista marcada")
        self.assertEqual(p["curriculos"], ["cv-alfa"])
        for vid in ("gupya-9", "jobgether-x"):
            o = banco.obter(vid)
            self.assertEqual(o["juntada_a"], "gupy-1")
            self.assertTrue(o["arquivada_em"])
        self.assertEqual(banco.IndiceVistas().achar({"id": "jobgether-x"}), "gupy-1")
        self.assertEqual(banco.grupos_repetidos(), [])

    def test_grupo_que_mudou_e_ignorado(self):
        r = banco.juntar_repetidas([["gupy-1", "jobgether-x"]])  # a prévia tinha três: não bate mais
        self.assertEqual((r["juntados"], r["ignorados"]), (0, [["gupy-1", "jobgether-x"]]))
        self.assertIsNone(r["backup"])

    def test_descricao_vem_da_outra(self):
        gravar(vaga("a", "Deltaweb", plataforma="JobGether"), vaga("b", "Deltaweb Ltda", descricao="Texto lido."))
        banco.juntar("a", ["b"])
        a = banco.obter("a")
        self.assertEqual((a["descricao"], a["analise_status"]), ("Texto lido.", "pendente"))

    def test_comando(self):
        env = {**os.environ, "TRAMPO_BANCO": str(self.tmp / "banco.db"), "PYTHONIOENCODING": "utf-8"}
        rodar = lambda *a: subprocess.run([sys.executable, str(RAIZ / "dash" / "banco.py"), "repetidas", *a], env=env,
                                          capture_output=True, text=True, encoding="utf-8", timeout=60, cwd=self.tmp)
        r = rodar()
        self.assertIn("1 grupo(s)", r.stdout)
        self.assertIn("Nada foi gravado", r.stdout)
        self.assertNotIn("juntada_a", banco.obter("gupya-9"))
        r = rodar("--gravar")
        self.assertIn("Juntados: 1", r.stdout)


class TestRotas(Base):
    def setUp(self):
        super().setUp()
        import servidor
        self.servidor = servidor
        p = mock.patch.object(servidor.Handler, "hosts_permitidos", {"127.0.0.1", "localhost"})
        p.start()
        self.addCleanup(p.stop)
        self.srv = servidor.ThreadingHTTPServer(("127.0.0.1", 0), servidor.Handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)

    def pedir(self, metodo, caminho, corpo=None):
        con = http.client.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=10)
        self.addCleanup(con.close)
        dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
        con.request(metodo, caminho, dados, {"Content-Type": "application/json"} if dados else {})
        r = con.getresponse()
        return r.status, json.loads(r.read())

    def test_repetidas(self):
        gravar(vaga("gupy-1", "Alfaweb", descricao="x", triagem="seguir", etapa="aplicada"),
               vaga("jobgether-x", "Alfaweb Corp", plataforma="JobGether"))
        st, r = self.pedir("GET", "/api/repetidas")
        self.assertEqual((st, r["grupos"][0]["ids"]), (200, ["gupy-1", "jobgether-x"]))
        self.assertEqual(self.pedir("POST", "/api/repetidas/juntar", {"grupos": [["x"]]})[0], 400)
        st, r = self.pedir("POST", "/api/repetidas/juntar", {"grupos": [["gupy-1", "jobgether-x"]]})
        self.assertEqual((st, r["juntados"]), (200, 1))

    def test_link_original_junta_com_a_existente(self):  # US2
        gravar(vaga("gupy-12345", "Alfaweb", descricao="x", triagem="seguir", etapa="aplicada"),
               vaga("jobgether-x", "Alfaweb Corp", titulo="Outro cargo", plataforma="JobGether"))
        lido = {"id": "gupy-12345", "plataforma": "Gupy", "titulo": "SCRUM MASTER PL", "empresa": "Alfaweb",
                "descricao": "Texto da Gupy.", "url": "https://alfa.gupy.io/jobs/12345"}
        with mock.patch.object(self.servidor.link, "ler", return_value=lido):
            st, r = self.pedir("PUT", "/api/vagas/jobgether-x/link-original", {"url": "https://alfa.gupy.io/jobs/12345"})
        self.assertEqual((st, r["juntada"]), (200, "gupy-12345"))
        self.assertEqual(banco.obter("jobgether-x")["juntada_a"], "gupy-12345")
        self.assertIn("JobGether", banco.obter("gupy-12345")["outras_plataformas"])

    def test_link_original_completa_a_vaga(self):
        gravar(vaga("jobgether-x", "Alfaweb Corp", plataforma="JobGether", analise_status="sem_dados"))
        lido = {"id": "gupy-777", "plataforma": "Gupy", "titulo": "Scrum", "empresa": "Outra",
                "descricao": "Texto da Gupy com o que a vaga pede.", "url": "https://x.gupy.io/jobs/777"}
        with mock.patch.object(self.servidor.link, "ler", return_value=lido), \
                mock.patch.object(self.servidor.analise.FILA, "forcar", return_value=True) as forcar:
            st, r = self.pedir("PUT", "/api/vagas/jobgether-x/link-original", {"url": "https://x.gupy.io/jobs/777"})
        self.assertEqual((st, r["juntada"]), (200, None))
        v = banco.obter("jobgether-x")
        self.assertEqual((v["descricao"], v["analise_status"], v["url_candidatura"]),
                         ("Texto da Gupy com o que a vaga pede.", "pendente", "https://x.gupy.io/jobs/777"))
        self.assertEqual((v["outras_plataformas"], v["ids_relacionados"]), (["Gupy"], ["gupy-777"]))
        forcar.assert_called_once_with("jobgether-x")

    def test_link_de_vaga_ja_no_dashboard_junta_sem_ler(self):  # a vaga saiu do ar na Gupy, mas já está aqui
        gravar(vaga("gupy-12803631", "Alfaweb", descricao="x", triagem="seguir", etapa="aplicada"),
               vaga("jobgether-x", "Alfaweb Corp", titulo="Outro cargo", plataforma="JobGether"))
        url = ("https://sejaalfaweb.gupy.io/jobs/12803631?utm_source=Jobgether&utm_content=x-scrum-master-pl"
               "&utm_campaign=search&utm_medium=website")
        with mock.patch.object(self.servidor.link, "ler", side_effect=AssertionError("não devia ler o link")):
            st, r = self.pedir("PUT", "/api/vagas/jobgether-x/link-original", {"url": url})
        self.assertEqual((st, r["juntada"]), (200, "gupy-12803631"))
        self.assertEqual(banco.obter("jobgether-x")["juntada_a"], "gupy-12803631")

    def test_gupy_banco_de_talentos_pela_pagina(self):  # a API não devolve a vaga de Banco de Talentos
        from fontes import gupy, link
        job = {"id": 1, "name": "SCRUM MASTER PL", "jobType": "vacancy_type_talent_pool", "workplaceType": "remote",
               "publishedAt": "2026-10-29T12:46:57.875Z", "description": "<p>Nosso time é ágil.</p>",
               "responsibilities": "<ul><li>Facilitar cerimônias</li></ul>", "prerequisites": "<p>Graduação em TI</p>",
               "relevantExperiences": "", "careerPage": {"name": "Seja Alfaweb"}}
        pagina = ('<html><script id="__NEXT_DATA__" type="application/json">'
                  + json.dumps({"props": {"pageProps": {"job": job}}}) + "</script></html>")
        erro = gupy.GupyErro('a Gupy recusou a consulta ({"details":"Job with ID 1 not found"})')
        with mock.patch.object(gupy, "ler", side_effect=erro), mock.patch.object(link, "_baixar", return_value=pagina):
            v = link.ler("https://sejaalfaweb.gupy.io/jobs/1")
        self.assertEqual((v["id"], v["titulo"], v["empresa"], v["remoto"], v["publicada_em"], v["tipo"]),
                         ("gupy-1", "SCRUM MASTER PL", "Seja Alfaweb", True, "2026-10-29", "Banco de talentos"))
        for trecho in ("Nosso time é ágil.", "Responsabilidades e atribuições", "Facilitar cerimônias", "Graduação em TI",
                       "Na Gupy: modelo remoto · Banco de talentos"):
            self.assertIn(trecho, v["descricao"])
        with mock.patch.object(gupy, "ler", side_effect=erro), \
                mock.patch.object(link, "_baixar", return_value="<html>nada</html>"):
            with self.assertRaises(link.LinkErro) as c:
                link.ler("https://sejaalfaweb.gupy.io/jobs/1")
        self.assertIn("nem pela API nem pela página", str(c.exception))

    def test_link_ilegivel(self):
        gravar(vaga("jobgether-x"))
        with mock.patch.object(self.servidor.link, "ler", side_effect=self.servidor.link.LinkErro("não deu", {})):
            st, r = self.pedir("PUT", "/api/vagas/jobgether-x/link-original", {"url": "https://exemplo.invalid/v"})
        self.assertEqual(st, 422)
        self.assertNotIn("url_candidatura", {k: v for k, v in banco.obter("jobgether-x").items() if v})


if __name__ == "__main__":
    unittest.main()
