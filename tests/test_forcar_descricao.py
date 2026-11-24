"""Spec 057: o Forçar verificar só pede a nota com a descrição no computador (aguardando a busca ou a espera do portal,
falha sem IA quando não dá para ler), LINKEDIN_FORCAR_PAUSA, nova tentativa da IA, leitura tolerante da análise,
Colar a descrição e os dados do portal do JobGether. Vagas fictícias e IA falsa."""
import http.client
import json
import re
import sys
import threading
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash"), str(Path(__file__).resolve().parent)]
import analise  # noqa: E402
import banco  # noqa: E402
import ia  # noqa: E402
import vagas  # noqa: E402
from fontes import jobgether  # noqa: E402
from test_forcar import Base, fonte_falsa, gravar, vaga  # noqa: E402


class BaseFila(Base):
    def setUp(self):
        super().setUp()
        self.t, self.sonos = 0.0, []

        def dormir(s):
            self.sonos.append(round(s, 3))
            self.t += s
        self.fila = analise.Fila(dormir=dormir, relogio=lambda: self.t)
        p = mock.patch.object(analise, "pausa_ia", return_value=0.0)
        p.start()
        self.addCleanup(p.stop)

    def uma(self, vid):
        """Põe a vaga na fila sem acordar a thread e verifica aqui mesmo."""
        with mock.patch.object(analise, "ligada", return_value=True), mock.patch.object(self.fila, "_acordar"):
            self.fila.forcar(vid)
        self.assertEqual(self.fila._proxima_forcada(), vid)
        self.fila._verificar_uma(vid)
        with self.fila._trava:
            self.fila._atual = None


class TestDescricaoObrigatoria(BaseFila):
    def test_busca_rodando_aguarda_e_volta(self):  # FR-002
        self.ia_falsa()
        gravar(vaga("a", descricao="", descricao_pendente=True))
        with mock.patch.object(vagas, "ocupada", return_value={"origem": "pagina"}):
            self.uma("a")
            self.assertEqual(self.fila.aguardando(), {"a": {"motivo": "busca"}})
            self.assertEqual(self.fila._retomar_aguardando(), [])  # a busca continua
        self.assertEqual((self.fonte.lidas, self.pedidos_ia), ([], []))
        self.assertEqual(self.fila._retomar_aguardando(), ["a"])  # a busca terminou
        self.fila._proxima_forcada()
        self.fila._verificar_uma("a")
        self.assertEqual(banco.obter("a")["aderencia"], 70)

    def test_bloqueio_na_leitura_aguarda(self):
        self.ia_falsa()
        f = fonte_falsa(erro=RuntimeError("429"), parada=True)
        espera = {"ate": "2026-11-24T04:07", "motivo": "excesso de pedidos"}
        lidas = []

        def descrever(v):  # o portal bloqueia nesta leitura e a espera começa
            lidas.append(v["id"])
            f.espera = lambda: espera
            raise RuntimeError("429")
        f.descrever = descrever
        self.usar_fonte(f)
        gravar(vaga("a", descricao="", descricao_pendente=True))
        self.uma("a")
        self.assertEqual(lidas, ["a"])
        self.assertEqual(self.fila.aguardando()["a"], {"motivo": "espera", "portal": "Falsa", "ate": "2026-11-24T04:07"})
        self.assertEqual(self.pedidos_ia, [])

    def test_erro_e_vazia_falham_sem_ia(self):
        self.ia_falsa()
        self.usar_fonte(fonte_falsa(erro=RuntimeError("falhou")))
        gravar(vaga("a", descricao="", descricao_pendente=True), vaga("b", descricao="", descricao_pendente=True))
        self.uma("a")
        self.assertIn("não deu para ler a descrição no Falsa", self.fila.falhas_atuais()["a"]["motivo"])
        self.usar_fonte(fonte_falsa(texto=""))
        self.uma("b")
        self.assertIn("não está mais no Falsa", self.fila.falhas_atuais()["b"]["motivo"])
        self.assertEqual(self.pedidos_ia, [])

    def test_forcar_tira_de_aguardando(self):
        with mock.patch.object(analise, "ligada", return_value=True), mock.patch.object(self.fila, "_acordar"):
            self.fila._aguardar("a", "busca", "Falsa")
            self.fila.forcar("a")
        self.assertEqual((self.fila.aguardando(), self.fila.verificando()), ({}, ["a"]))

    def test_nota_chegou_enquanto_aguardava(self):
        gravar(vaga("a", aderencia=80, analise_status="feita"))
        self.fila._aguardar("a", "busca", "Falsa")
        self.assertEqual(self.fila._retomar_aguardando(), [])
        self.assertEqual(self.fila.aguardando(), {})


class TestPausaLinkedIn(unittest.TestCase):
    def test_linkedin_forcar_pausa(self):  # FR-003
        import segredos
        for bruto, esperado in ((None, 60.0), ("", 60.0), ("10", 30.0), ("900", 600.0), ("120", 120.0),
                                ("1,5e2", 150.0), ("x", 60.0), ("nan", 60.0)):
            with self.subTest(bruto=bruto), mock.patch.object(segredos, "ler", return_value=bruto):
                self.assertEqual(vagas.pausa_leitura("LinkedIn"), esperado)

    def test_fila_espera_60s_entre_leituras_do_linkedin(self):
        class Rel:
            t = 0.0
        sonos = []

        def dormir(s):
            sonos.append(s)
            Rel.t += s
        fila = analise.Fila(dormir=dormir, relogio=lambda: Rel.t)
        with mock.patch.object(vagas, "pausa_leitura", side_effect=lambda p: 60.0 if p == "LinkedIn" else 3.0):
            fila._pausar_portal("LinkedIn")
            fila._pausar_portal("LinkedIn")
            fila._pausar_portal("Gupy")
        self.assertEqual(sonos, [60.0])


class TestNovaTentativa(BaseFila):
    def test_falha_uma_vez_e_acerta(self):  # FR-004, SC-003
        chamadas = []

        def responder(pedido, **_):
            chamadas.append(1)
            if len(chamadas) == 1:
                raise ia.IAErro("nenhuma IA respondeu: erro 503")
            vid = re.findall(r"^### id: (\S+)$", pedido, re.M)[0]
            return json.dumps([{"id": vid, "aderencia": 65, "resumo": "Bate."}])
        self.ia_falsa(responder)
        gravar(vaga("a"))
        self.uma("a")
        self.assertEqual((len(chamadas), banco.obter("a")["aderencia"]), (2, 65))
        self.assertEqual(self.fila.falhas_atuais(), {})

    def test_falha_duas_vezes(self):
        self.ia_falsa(lambda pedido, **_: "sem json nenhum")
        gravar(vaga("a"))
        self.uma("a")
        self.assertEqual(len(self.pedidos_ia), 2)
        self.assertIn("não trouxe o JSON", self.fila.falhas_atuais()["a"]["motivo"])


class TestLeituraTolerante(unittest.TestCase):  # FR-005
    def test_campos_secundarios(self):
        a = banco.validar_analise({"aderencia": 72, "senioridade": ["Sênior", "especialista"], "senioridade_origem": "x",
                                   "tipo_emprego": ["PJ", "freela"], "modelo_trabalho": "Híbrido", "idioma": "inglês",
                                   "moeda": "reais", "resumo": ["Bate com o perfil.", "Falta inglês."],
                                   "fora_dos_criterios": True, "analise_provedor": "gemini", "analise_modelo": 3})
        self.assertEqual(a["senioridade"], ["senior"])
        self.assertEqual(a["senioridade_origem"], "sugerida")
        self.assertEqual(a["tipo_emprego"], ["pj"])
        self.assertEqual(a["modelo_trabalho"], "hibrido")
        self.assertNotIn("idioma", a)
        self.assertNotIn("moeda", a)
        self.assertEqual(a["resumo"], "Bate com o perfil.; Falta inglês.")
        self.assertEqual(a["fora_dos_criterios"], "a IA marcou a vaga fora dos seus critérios")
        self.assertEqual(a["analise_modelo"], "3")
        self.assertEqual(banco.validar_analise({"aderencia": 50, "senioridade": {"x": 1}})["senioridade"], [])

    def test_nota_e_situacao_continuam_estritas(self):
        for ruim in ({"resumo": "sem nota"}, {"aderencia": "alta"}, {"aderencia": 70, "analise_status": "talvez"}):
            with self.subTest(ruim=ruim), self.assertRaises(ValueError):
                banco.validar_analise(ruim)


class TestColarDescricao(BaseFila):
    TEXTO = "Responsabilidades: conduzir cerimônias ágeis, apoiar o time e acompanhar métricas de entrega. " * 2

    def test_colar(self):  # FR-007
        gravar(vaga("a", descricao="", analise_status="sem_dados", aderencia=40, nota_sem_descricao=True,
                    nota_dados_portal=True, descricao_pendente=True))
        doc = banco.colar_descricao("a", "  " + self.TEXTO + "  ")
        self.assertEqual(doc["descricao"], self.TEXTO.strip())
        self.assertEqual(doc["analise_status"], "pendente")
        self.assertTrue(doc["descricao_colada"])
        for saiu in ("descricao_pendente", "nota_sem_descricao", "nota_dados_portal"):
            self.assertNotIn(saiu, doc)
        for ruim in ("curto", "x" * 30001, None):
            with self.subTest(ruim=str(ruim)[:10]), self.assertRaises(ValueError):
                banco.colar_descricao("a", ruim)
        with self.assertRaises(KeyError):
            banco.colar_descricao("nao-existe", self.TEXTO)

    def test_nota_definitiva_continua(self):
        gravar(vaga("a", descricao="", aderencia=80, analise_status="feita"))
        doc = banco.colar_descricao("a", self.TEXTO)
        self.assertEqual((doc["aderencia"], doc["analise_status"]), (80, "feita"))

    def test_rota(self):
        import servidor
        p = mock.patch.object(servidor.Handler, "hosts_permitidos", {"127.0.0.1", "localhost"})
        p.start()
        self.addCleanup(p.stop)
        srv = servidor.ThreadingHTTPServer(("127.0.0.1", 0), servidor.Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        gravar(vaga("a", descricao="", analise_status="sem_dados"))

        def pedir(corpo):
            con = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=10)
            self.addCleanup(con.close)
            con.request("PUT", "/api/vagas/a/descricao", json.dumps(corpo).encode(), {"Content-Type": "application/json"})
            r = con.getresponse()
            return r.status, json.loads(r.read())
        with mock.patch.object(analise.FILA, "forcar", return_value=True) as forcar:
            st, r = pedir({"descricao": self.TEXTO})
            self.assertEqual((st, r["vaga"]["analise_status"]), (200, "pendente"))
            forcar.assert_called_once_with("a")
            self.assertEqual(pedir({"descricao": "curto"})[0], 400)
            with mock.patch.object(servidor.Handler, "_local", return_value=False):
                self.assertEqual(pedir({"descricao": self.TEXTO})[0], 403)


class TestDadosPortal(BaseFila):
    def test_normalizar_guarda_os_dados(self):  # FR-008
        v = jobgether.normalizar({"id": "65f1a2b3c4d5e6f7a8b9c0d1", "title": "Agile Master",
                                  "company": "Empresa Alfa", "url": "https://jobgether.com/offer/65f1a2b3c4d5e6f7a8b9c0d1-agile",
                                  "remote": "Full Remote", "contractType": "Full time", "experience": "Senior (5-10 years)",
                                  "jobFunctions": ["Scrum Master", " Agile Coach ", 3], "postedAt": "2026-11-20T00:00:00Z"})
        self.assertEqual(v["funcoes"], ["Scrum Master", "Agile Coach"])
        self.assertEqual((v["experiencia"], v["contrato_portal"]), ("Senior (5-10 years)", "Full time"))

    def test_pedido_traz_os_dados_do_portal(self):
        v = vaga("a", funcoes=["Scrum Master"], experiencia="Senior (5-10 years)", contrato_portal="Full time")
        pedido = analise.montar_pedido([v])
        for linha in ("Funções (do portal): Scrum Master", "Experiência pedida (do portal): Senior (5-10 years)",
                      "Contrato (do portal): Full time"):
            self.assertIn(linha, pedido)
        self.assertNotIn("NOTA PELOS DADOS DO PORTAL", pedido)  # com descrição, só as linhas

    def test_forcar_sem_leitura_com_dados_da_nota_provisoria(self):  # FR-009
        self.ia_falsa()
        gravar(vaga("a", plataforma="Outra", descricao="", funcoes=["Scrum Master"], experiencia="Senior"))
        self.uma("a")
        self.assertEqual(len(self.pedidos_ia), 1)
        self.assertIn("NOTA PELOS DADOS DO PORTAL", self.pedidos_ia[0])
        a = banco.obter("a")
        self.assertEqual((a["aderencia"], a["nota_sem_descricao"], a["nota_dados_portal"]), (70, True, True))
        banco.completar_descricao("a", "O texto chegou depois.")
        self.assertNotIn("nota_dados_portal", banco.obter("a"))

    def test_vaga_repetida_ganha_os_dados(self):
        gravar(vaga("a", plataforma="JobGether", experiencia="Mid"))
        banco.registrar_outros_portais("a", ["JobGether"], ["a"],
                                       {"funcoes": ["Scrum Master"], "experiencia": "Senior", "contrato_portal": "Full time"})
        a = banco.obter("a")
        self.assertEqual((a["funcoes"], a["experiencia"], a["contrato_portal"]), (["Scrum Master"], "Mid", "Full time"))


if __name__ == "__main__":
    unittest.main()
