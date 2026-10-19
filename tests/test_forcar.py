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
                  mock.patch.object(vagas, "CACHE", self.tmp / ".cache")):
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

    def test_na_espera_nota_sem_a_descricao(self):  # FR-006, FR-007
        self.ia_falsa()
        self.fonte.espera = lambda: {"ate": "2026-10-19T20:00", "motivo": "excesso de pedidos"}
        gravar(vaga("a", descricao="", descricao_pendente=True))
        self.forcar(self.fila, "a")
        self.assertEqual(self.fonte.lidas, [])  # nenhum pedido na espera
        self.assertIn(analise.SEM_DESCRICAO, self.pedidos_ia[0])
        a = banco.obter("a")
        self.assertEqual((a["aderencia"], a["nota_sem_descricao"], a["descricao_pendente"]), (70, True, True))
        banco.completar_descricao("a", "Texto que chegou depois.")  # Completar descrições
        a = banco.obter("a")
        self.assertEqual(a["analise_status"], "pendente")
        self.assertNotIn("nota_sem_descricao", a)

    def test_sem_dados_sem_a_descricao_e_falha(self):
        self.ia_falsa(lambda pedido, **_: json.dumps([{"id": "a", "analise_status": "sem_dados", "resumo": "x"}]))
        gravar(vaga("a", plataforma="Outra", descricao="", analise_status="sem_dados"))
        self.forcar(self.fila, "a")
        self.assertEqual(self.fila.falhas_atuais()["a"]["motivo"], "a IA não conseguiu dar nota sem a descrição")

    def test_decisao_da_pessoa_nao_muda(self):  # FR-011, SC-004
        self.ia_falsa()
        gravar(vaga("f", triagem="fora", motivo_fora=["local"]))
        self.forcar(self.fila, "f")
        f = banco.obter("f")
        self.assertEqual((f["aderencia"], f["triagem"]), (70, "fora"))


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
            self.assertEqual(self.pedir("POST", "/api/vagas/a/analisar", {}), (202, {"verificando": ["a"]}))
            self.assertEqual(self.pedir("POST", "/api/vagas/a/analisar", {}), (202, {"verificando": ["a"]}))
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
