"""Forçar verificar (spec 021): a nota de uma vaga pedida pela pessoa, sem rede e sem IA de verdade. Fila com a vaga
forçada (sem duplicar, falhas), descrição lida uma vez fora da espera e da busca, nota sem a descrição com a marca,
marca que sai quando o texto chega, e a rota do servidor."""
import http.client
import json
import re
import shutil
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import analise  # noqa: E402
import banco  # noqa: E402
import filtros  # noqa: E402
import ia  # noqa: E402
import vagas  # noqa: E402

CFG = {"fontes": ["indeed"], "termos": ["analista"], "localidade": {"pais": "Brasil"},
       "modelos": {"remoto": True, "hibrido": True, "presencial": True}, "janela_horas": 168}


def vaga(vid, **campos):
    return {"id": vid, "origem": "busca", "plataforma": "Falsa", "titulo": f"Analista {vid}", "empresa": "Empresa Alfa",
            "local": "Remoto", "remoto": True, "url": f"https://exemplo.invalid/{vid}", "triagem": "pendente",
            "descricao": f"Texto da vaga {vid}.", "analise_status": "sem_analise", "encontrada_em": "2026-10-19",
            **campos}


def gravar(*docs):
    with banco.escrita() as con:
        for d in docs:
            banco._gravar(con, d["id"], d)


def fonte_falsa(espera=None, erro=None, parada=False, texto="Descrição completa lida do portal."):
    f = types.SimpleNamespace(NOME="falsa", PLATAFORMA="Falsa", MAX_DESCRICOES=20, lidas=[])

    def descrever(v):
        f.lidas.append(v["id"])
        if erro:
            raise erro
        return texto
    f.descrever = descrever
    f.espera = lambda: espera
    f.parada = lambda: parada
    return f


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "config.json").write_text(json.dumps(CFG), encoding="utf-8")
        for p in (mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db"),
                  mock.patch.object(filtros, "CONFIG", self.tmp / "config.json"),
                  mock.patch.object(vagas, "CACHE", self.tmp / ".cache"),
                  mock.patch.object(analise, "pausa_ia", return_value=0.0)):  # sem esperar nos testes (spec 056)
            p.start()
            self.addCleanup(p.stop)
        self.fonte = fonte_falsa()
        self.usar_fonte(self.fonte)

    def usar_fonte(self, f):
        p = mock.patch.dict(vagas.FONTES, {"falsa": f})
        p.start()
        self.addCleanup(p.stop)

    def ia_falsa(self, responder=None):
        """IA ligada; por padrão dá nota 70 a todas as vagas do pedido. Guarda os pedidos."""
        self.pedidos_ia = []

        def padrao(pedido, **_):
            ids = re.findall(r"^### id: (\S+)$", pedido, re.M)
            return json.dumps([{"id": i, "aderencia": 70, "resumo": "Bate.", "modelo_trabalho": "remoto"} for i in ids])

        def chamar(pedido, **kw):
            self.pedidos_ia.append(pedido)
            return (responder or padrao)(pedido, **kw)
        for p in (mock.patch.object(ia, "responder", side_effect=chamar),
                  mock.patch.object(ia, "disponivel", return_value=True),
                  mock.patch.object(ia, "escolha_efetiva", return_value={"provedor": "openrouter", "modelo": "m:free"}),
                  mock.patch.object(ia, "modelo_efetivo", return_value="m:free")):
            p.start()
            self.addCleanup(p.stop)

    def forcar(self, fila, *ids):
        for vid in ids:
            self.assertTrue(fila.forcar(vid))
        t = fila._thread
        if t is not None:
            t.join(20)
        self.assertEqual(fila.verificando(), [])


class TestBanco(Base):
    def test_marca_da_nota_sem_descricao(self):
        gravar(vaga("a"))
        ok, _ = banco.aplicar_analises([{"id": "a", "aderencia": 60, "nota_sem_descricao": True}])
        self.assertEqual(ok, ["a"])
        self.assertTrue(banco.obter("a")["nota_sem_descricao"])
        banco.aplicar_analises([{"id": "a", "aderencia": 75}])  # nota normal: a marca sai
        self.assertNotIn("nota_sem_descricao", banco.obter("a"))
        self.assertNotIn("nota_sem_descricao",
                         banco.validar_analise({"analise_status": "sem_dados", "nota_sem_descricao": True}))

    def test_descricao_que_chega_refaz_a_nota(self):  # FR-007
        gravar(vaga("a", descricao="", descricao_pendente=True, aderencia=55, analise_status="feita",
                    nota_sem_descricao=True),
               vaga("b", descricao="", descricao_pendente=True))
        banco.completar_descricao("a", "Texto completo.")
        a = banco.obter("a")
        self.assertEqual((a["analise_status"], a["descricao"], a["aderencia"]), ("pendente", "Texto completo.", 55))
        self.assertNotIn("nota_sem_descricao", a)
        self.assertTrue(analise.precisa(a))
        banco.completar_descricao("b", "Outro texto.")
        self.assertEqual(banco.obter("b")["analise_status"], "sem_analise")  # sem a marca, o status não muda


class TestDescreverUma(Base):
    def test_le_uma_vez_e_grava(self):
        gravar(vaga("a", descricao="", descricao_pendente=True))
        r = vagas.descrever_uma("a")
        self.assertEqual((r["motivo"], self.fonte.lidas), (None, ["a"]))
        a = banco.obter("a")
        self.assertEqual(a["descricao"], "Descrição completa lida do portal.")
        self.assertNotIn("descricao_pendente", a)

    def test_sem_pedido_na_espera_na_busca_e_sem_fonte(self):
        gravar(vaga("a", descricao="", descricao_pendente=True), vaga("o", plataforma="Outra", descricao=""))
        self.assertEqual(vagas.descrever_uma("o")["motivo"], "sem_fonte")
        with mock.patch.object(vagas, "ocupada", return_value={"origem": "pagina"}):
            self.assertEqual(vagas.descrever_uma("a")["motivo"], "busca")
        with vagas._LEITURA:  # Completar descrições lendo
            self.assertEqual(vagas.descrever_uma("a")["motivo"], "busca")
        self.fonte.espera = lambda: {"ate": "2026-10-19T20:00", "motivo": "excesso de pedidos"}
        self.assertEqual(vagas.descrever_uma("a")["motivo"], "espera")
        self.assertEqual(self.fonte.lidas, [])
        self.assertTrue(banco.obter("a")["descricao_pendente"])

    def test_erro_e_bloqueio(self):
        gravar(vaga("a", descricao="", descricao_pendente=True))
        self.usar_fonte(fonte_falsa(erro=RuntimeError("falhou")))
        self.assertEqual(vagas.descrever_uma("a")["motivo"], "erro")
        f = fonte_falsa(erro=RuntimeError("limitou"), parada=True)
        self.usar_fonte(f)
        self.assertEqual(vagas.descrever_uma("a")["motivo"], "bloqueio")
        self.assertEqual(f.lidas, ["a"])  # um pedido só
        self.usar_fonte(fonte_falsa(texto=""))
        self.assertEqual(vagas.descrever_uma("a")["motivo"], "vazia")
        self.assertEqual(vagas.descrever_uma("nao-existe")["motivo"], "sem_vaga")


class TestFila(Base):
    def setUp(self):
        super().setUp()
        self.fila = analise.Fila()

    def test_so_a_forcada_ganha_nota(self):  # FR-002, SC-002
        self.ia_falsa()
        gravar(vaga("a"), vaga("b"))
        self.forcar(self.fila, "a")
        a, b = banco.obter("a"), banco.obter("b")
        self.assertEqual((a["aderencia"], a["analise_status"], a["triagem"]), (70, "feita", "pendente"))
        self.assertNotIn("aderencia", b)
        self.assertEqual(len(self.pedidos_ia), 1)
        self.assertNotIn("### id: b", self.pedidos_ia[0])
        self.assertEqual(self.fila.falhas_atuais(), {})

    def test_sem_duplicar(self):  # FR-010
        with mock.patch.object(analise, "ligada", return_value=True), mock.patch.object(self.fila, "_acordar"):
            self.fila.forcar("a")
            self.fila.forcar("a")
        self.assertEqual(self.fila.verificando(), ["a"])

    def test_sem_ia_nada_muda(self):  # FR-009, SC-005
        with mock.patch.object(analise, "ligada", return_value=False):
            self.assertFalse(self.fila.forcar("a"))
        self.assertEqual((self.fila.verificando(), self.fila._thread), ([], None))

    def test_falha_volta_o_botao(self):  # FR-004
        self.ia_falsa(lambda pedido, **_: (_ for _ in ()).throw(ia.IAErro("a IA demorou demais")))
        gravar(vaga("a"))
        self.forcar(self.fila, "a")
        self.assertIn("demorou demais", self.fila.falhas_atuais()["a"]["motivo"])
        self.assertNotIn("aderencia", banco.obter("a"))
        with mock.patch.object(self.fila, "_acordar"):
            self.fila.forcar("a")  # tentar de novo limpa a falha
        self.assertEqual(self.fila.falhas_atuais(), {})

    def test_vaga_nao_devolvida(self):
        self.ia_falsa(lambda pedido, **_: "[]")
        gravar(vaga("a"))
        self.forcar(self.fila, "a")
        self.assertEqual(self.fila.falhas_atuais()["a"]["motivo"], "a IA não devolveu a nota desta vaga")

    def test_vaga_com_nota_sai_sem_ia(self):
        self.ia_falsa()
        gravar(vaga("a", aderencia=80, analise_status="feita"))
        self.forcar(self.fila, "a")
        self.assertEqual(self.pedidos_ia, [])
        self.assertEqual(self.fila.falhas_atuais(), {})

    def test_descricao_lida_antes_da_nota(self):  # FR-005
        self.ia_falsa()
        gravar(vaga("a", descricao="", descricao_pendente=True))
        self.forcar(self.fila, "a")
        self.assertEqual(self.fonte.lidas, ["a"])
        self.assertIn("Descrição completa lida do portal.", self.pedidos_ia[0])
        self.assertNotIn("NOTA SEM A DESCRIÇÃO", self.pedidos_ia[0])  # nem o bloco nem a regra
        a = banco.obter("a")
        self.assertEqual(a["aderencia"], 70)
        self.assertNotIn("nota_sem_descricao", a)

    def test_na_espera_aguarda_sem_ia(self):  # spec 057, FR-001, FR-002 (antes: nota provisória, spec 021)
        self.ia_falsa()
        self.fonte.espera = lambda: {"ate": "2026-10-19T20:00", "motivo": "excesso de pedidos"}
        gravar(vaga("a", descricao="", descricao_pendente=True))
        with mock.patch.object(analise, "ligada", return_value=True), mock.patch.object(self.fila, "_acordar"):
            self.fila.forcar("a")
        self.fila._proxima_forcada()
        self.fila._verificar_uma("a")
        self.assertEqual((self.fonte.lidas, self.pedidos_ia), ([], []))  # nenhum pedido ao portal nem à IA
        self.assertEqual(self.fila.aguardando(), {"a": {"motivo": "espera", "portal": "Falsa", "ate": "2026-10-19T20:00"}})
        self.assertNotIn("aderencia", banco.obter("a"))
        self.assertEqual(self.fila._retomar_aguardando(), [])  # a espera continua
        self.fonte.espera = lambda: None  # a espera acabou: volta para a fila e ganha a nota com o texto
        self.assertEqual(self.fila._retomar_aguardando(), ["a"])
        self.assertEqual((self.fila.verificando(), self.fila.aguardando()), (["a"], {}))
        self.fila._proxima_forcada()
        self.fila._verificar_uma("a")
        a = banco.obter("a")
        self.assertEqual((self.fonte.lidas, a["aderencia"]), (["a"], 70))
        self.assertNotIn("nota_sem_descricao", a)

    def test_portal_sem_leitura_falha_sem_ia(self):  # spec 057, FR-009 (sem os dados do portal)
        self.ia_falsa()
        gravar(vaga("a", plataforma="Outra", descricao="", analise_status="sem_dados"))
        self.forcar(self.fila, "a")
        self.assertEqual(self.pedidos_ia, [])
        self.assertIn("cole o texto", self.fila.falhas_atuais()["a"]["motivo"])

    def test_decisao_da_pessoa_nao_muda(self):  # FR-011, SC-004
        self.ia_falsa()
        gravar(vaga("f", triagem="fora", motivo_fora=["local"]))
        self.forcar(self.fila, "f")
        f = banco.obter("f")
        self.assertEqual((f["aderencia"], f["triagem"]), (70, "fora"))


class TestFilaSequencial(Base):
    """Spec 056: as forçadas uma por vez, na ordem dos cliques, com a pausa do portal entre leituras do mesmo portal e
    FORCAR_PAUSA entre pedidos à IA. Relógio falso: só anda quando a fila dorme."""

    def setUp(self):
        super().setUp()
        self.t, self.sonos = 0.0, []

        def dormir(s):
            self.sonos.append(round(s, 3))
            self.t += s
        self.fila = analise.Fila(dormir=dormir, relogio=lambda: self.t)
        p = mock.patch.object(analise, "pausa_ia", return_value=5.0)
        p.start()
        self.addCleanup(p.stop)

    def rodar(self, *ids):
        """Põe as vagas na fila (sem acordar a thread) e roda a fila aqui mesmo, até o fim."""
        with mock.patch.object(analise, "ligada", return_value=True), mock.patch.object(self.fila, "_acordar"):
            for vid in ids:
                self.assertTrue(self.fila.forcar(vid))
        self.assertEqual(self.fila.verificando(), list(dict.fromkeys(ids)))
        self.fila._pedido = True
        self.fila._rodar()
        self.assertEqual((self.fila.verificando(), self.fila.agora()), ([], None))

    def ids_dos_pedidos(self):
        return [re.findall(r"^### id: (\S+)$", p, re.M) for p in self.pedidos_ia]

    def test_uma_por_vez_na_ordem_com_a_pausa_da_ia(self):  # FR-001, FR-002, FR-004, SC-001
        self.ia_falsa()
        gravar(vaga("c"), vaga("a"), vaga("b"))
        self.rodar("c", "a", "b", "a")
        self.assertEqual(self.ids_dos_pedidos(), [["c"], ["a"], ["b"]])
        self.assertEqual(self.sonos, [5.0, 5.0])  # nenhuma pausa antes do primeiro pedido
        self.assertTrue(all(banco.obter(v)["analise_status"] == "feita" for v in "abc"))

    def test_pausa_do_portal_entre_leituras_do_mesmo_portal(self):  # FR-003, SC-002
        self.ia_falsa()
        self.fonte.pausa = lambda: {"faixa": (8.0, 12.0)}
        outra = fonte_falsa()
        outra.PLATAFORMA = "Outra Falsa"
        p = mock.patch.dict(vagas.FONTES, {"outra": outra})
        p.start()
        self.addCleanup(p.stop)
        with mock.patch.object(analise, "pausa_ia", return_value=0.0):
            gravar(vaga("a", descricao="", descricao_pendente=True),
                   vaga("x", descricao="", descricao_pendente=True, plataforma="Outra Falsa"),
                   vaga("b", descricao="", descricao_pendente=True))
            self.rodar("a", "x", "b")
        self.assertEqual((self.fonte.lidas, outra.lidas), (["a", "b"], ["x"]))
        self.assertEqual(self.sonos, [8.0])  # só entre a e b (mesmo portal); x é de outro portal

    def test_falha_de_uma_nao_afeta_as_outras(self):  # FR-005, SC-003
        padrao = None

        def responder(pedido, **_):
            if "### id: b" in pedido:
                raise ia.IAErro("limite de pedidos da IA")
            return padrao(pedido)
        self.ia_falsa()
        padrao = ia.responder.side_effect
        ia.responder.side_effect = responder
        gravar(vaga("a"), vaga("b"), vaga("c"))
        self.rodar("a", "b", "c")
        self.assertEqual(list(self.fila.falhas_atuais()), ["b"])
        self.assertIn("limite de pedidos", self.fila.falhas_atuais()["b"]["motivo"])
        self.assertEqual((banco.obter("a")["aderencia"], banco.obter("c")["aderencia"]), (70, 70))

    def test_atual_e_fila_durante_a_rodada(self):  # FR-006
        vistos = []

        def responder(pedido, **_):
            vistos.append((self.fila.agora(), self.fila.verificando()))
            vid = re.findall(r"^### id: (\S+)$", pedido, re.M)[0]
            return json.dumps([{"id": vid, "aderencia": 70, "resumo": "Bate.", "modelo_trabalho": "remoto"}])
        self.ia_falsa(responder)
        gravar(vaga("a"), vaga("b"))
        self.rodar("a", "b")
        self.assertEqual(vistos, [("a", ["a", "b"]), ("b", ["b"])])

    def test_forcar_a_atual_nao_duplica(self):
        with mock.patch.object(analise, "ligada", return_value=True), mock.patch.object(self.fila, "_acordar"):
            self.fila.forcar("a")
            self.fila._proxima_forcada()  # "a" virou a atual
            self.fila.forcar("a")
            self.fila.forcar("b")
        self.assertEqual((self.fila.agora(), self.fila.verificando()), ("a", ["a", "b"]))


class TestPausas(unittest.TestCase):
    def test_pausa_ia(self):  # FR-004, US3
        import segredos
        for bruto, esperado in (("0", 0.0), ("90", 60.0), ("-3", 0.0), ("2,5", 2.5), ("abc", 5.0), ("nan", 5.0),
                                ("", 5.0), (None, 5.0)):
            with self.subTest(bruto=bruto), mock.patch.object(segredos, "ler", return_value=bruto):
                self.assertEqual(analise.pausa_ia(), esperado)

    def test_pausa_lote(self):  # spec 062, FR-005
        import segredos
        for bruto, esperado in (("0", 5.0), ("200", 120.0), ("7,5", 7.5), ("30", 30.0), ("abc", 20.0),
                                ("inf", 20.0), ("", 20.0), (None, 20.0)):
            with self.subTest(bruto=bruto), mock.patch.object(segredos, "ler", return_value=bruto):
                self.assertEqual(analise.pausa_lote(), esperado)

    def test_pausa_leitura(self):  # FR-003
        f = fonte_falsa()
        with mock.patch.dict(vagas.FONTES, {"falsa": f}):
            self.assertEqual(vagas.pausa_leitura("Falsa"), 3.0)  # sem pausa própria: o piso
            f.pausa = lambda: {"faixa": (1.0, 2.0)}
            self.assertEqual(vagas.pausa_leitura("Falsa"), 3.0)  # abaixo do piso
            f.pausa = lambda: {"faixa": (7.5, 9.0)}
            self.assertEqual(vagas.pausa_leitura("Falsa"), 7.5)
        self.assertEqual(vagas.pausa_leitura("Portal que não existe"), 3.0)


class TestServidor(Base):
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
        self.addCleanup(analise.FILA._forcadas.clear)
        self.addCleanup(analise.FILA.falhas.clear)

    def pedir(self, metodo, caminho, corpo=None):
        con = http.client.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=10)
        self.addCleanup(con.close)
        dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
        con.request(metodo, caminho, dados, {"Content-Type": "application/json"} if dados else {})
        r = con.getresponse()
        return r.status, json.loads(r.read())

    def test_rota(self):
        gravar(vaga("a"), vaga("n", aderencia=80, analise_status="feita"))
        with mock.patch.object(analise, "ligada", return_value=True), \
                mock.patch.object(analise.FILA, "_acordar"):
            self.assertEqual(self.pedir("POST", "/api/vagas/a/analisar", {}), (202, {"verificando": ["a"], "verificando_agora": None}))
            self.assertEqual(self.pedir("POST", "/api/vagas/a/analisar", {}), (202, {"verificando": ["a"], "verificando_agora": None}))
            status, j = self.pedir("GET", "/api/versao")
            self.assertEqual((status, j["verificando"], j["falhas"]), (200, ["a"], {}))
            self.assertEqual(self.pedir("POST", "/api/vagas/n/analisar", {}), (409, {"erro": "a vaga já tem nota"}))
            self.assertEqual(self.pedir("POST", "/api/vagas/x/analisar", {})[0], 404)
            self.assertEqual(self.pedir("POST", "/api/vagas/a%2Fb/analisar", {})[0], 404)
            with mock.patch.object(self.servidor.Handler, "_local", return_value=False):
                self.assertEqual(self.pedir("POST", "/api/vagas/a/analisar", {})[0], 403)

    def test_sem_ia(self):  # FR-009
        gravar(vaga("a"))
        with mock.patch.object(analise, "ligada", return_value=False):
            status, j = self.pedir("POST", "/api/vagas/a/analisar", {})
        self.assertEqual((status, j), (409, {"erro": "Para dar nota, ligue uma IA", "sem_ia": True}))
        self.assertEqual(analise.FILA.verificando(), [])
        self.assertEqual(banco.obter("a")["analise_status"], "sem_analise")


if __name__ == "__main__":
    unittest.main()
