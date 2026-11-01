"""Área comum dos portais com login (fontes/_sessao.py, spec 041), sem navegador e sem rede: o contexto da busca da
página, a aba, a leitura só no portal, a espera do login olhando só o endereço, a conexão local, o Desconectar (que só
apaga o perfil inteiro sem nenhuma outra sessão) e as rotas /api/portais-login."""
import http.client
import json
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash"), str(Path(__file__).resolve().parent)]
import banco  # noqa: E402
import contas  # noqa: E402
import filtros  # noqa: E402
import navegador  # noqa: E402
from aba_login_falsa import AbaFalsa  # noqa: E402
from fontes import _sessao, mygreenhouse  # noqa: E402

BUSCA = "https://my.greenhouse.io/jobs/search"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for p in (mock.patch.object(_sessao, "ESTADO", self.tmp / ".cache" / "portais-login.json"),
                  mock.patch.object(contas, "ESTADO", self.tmp / ".cache" / "contas" / "estado.json"),
                  mock.patch.object(contas, "PASTA", self.tmp / ".cache" / "contas")):
            p.start()
            self.addCleanup(p.stop)


class TestContexto(Base):
    def test_so_dentro_do_with_e_na_mesma_thread(self):
        self.assertFalse(_sessao.dentro_da_pagina())
        visto = []
        with _sessao.na_pagina(lambda m, a: False):
            self.assertTrue(_sessao.dentro_da_pagina())
            t = threading.Thread(target=lambda: visto.append(_sessao.dentro_da_pagina()))
            t.start()
            t.join()
            with self.assertRaises(RuntimeError), _sessao.na_pagina(lambda m, a: False):
                pass
        self.assertEqual(visto, [False])  # outra thread do servidor não usa a sessão
        self.assertFalse(_sessao.dentro_da_pagina())

    def test_aba_uma_por_busca_e_fechada_no_fim(self):
        aba = AbaFalsa()
        with mock.patch.object(navegador, "abrir_para_leitura", return_value=aba) as abrir:
            with _sessao.na_pagina(lambda m, a: False):
                self.assertIs(_sessao.aba(mygreenhouse), aba)
                self.assertIs(_sessao.aba(mygreenhouse), aba)
            abrir.assert_called_once_with(BUSCA)
        self.assertTrue(aba.fechada)

    def test_fora_da_pagina_nao_abre_a_janela(self):
        with mock.patch.object(navegador, "abrir_para_leitura") as abrir:
            with self.assertRaises(_sessao.PortalComLoginErro) as erro:
                _sessao.aba(mygreenhouse)
        abrir.assert_not_called()
        self.assertEqual(erro.exception.tipo, "janela")
        self.assertIn("só pelo botão Buscar da página", str(erro.exception))

    def test_erro_do_navegador_vira_janela(self):
        with mock.patch.object(navegador, "abrir_para_leitura", side_effect=navegador.NavegadorErro("sem navegador")):
            with _sessao.na_pagina(lambda m, a: False), self.assertRaises(_sessao.PortalComLoginErro) as erro:
                _sessao.aba(mygreenhouse)
        self.assertEqual(erro.exception.tipo, "janela")


class TestConexao(Base):
    def test_conectados_e_marcar(self):
        self.assertEqual(_sessao.conectados(), [])
        _sessao.ESTADO.parent.mkdir(parents=True)
        _sessao.ESTADO.write_text("{quebrado", encoding="utf-8")
        self.assertEqual(_sessao.conectados(), [])
        _sessao.marcar("mygreenhouse", True)
        self.assertEqual(_sessao.conectados(), ["mygreenhouse"])
        self.assertIn("desde", json.loads(_sessao.ESTADO.read_text(encoding="utf-8"))["conectados"]["mygreenhouse"])
        _sessao.marcar("mygreenhouse", False)
        self.assertEqual(_sessao.conectados(), [])

    def test_algum_conectado_soma_as_contas(self):
        self.assertFalse(_sessao.algum_conectado())
        contas.marcar("gupy", True)
        self.assertTrue(_sessao.algum_conectado())

    def test_desconectar_sem_outra_sessao_apaga_o_perfil(self):
        _sessao.marcar("mygreenhouse", True)
        with mock.patch.object(navegador, "desconectar") as apagar, \
                mock.patch.object(navegador, "abrir_para_leitura") as abrir:
            _sessao.desconectar(mygreenhouse)
        apagar.assert_called_once()
        abrir.assert_not_called()
        self.assertEqual(_sessao.conectados(), [])

    def test_desconectar_com_conta_conectada_apaga_so_as_origens(self):
        _sessao.marcar("mygreenhouse", True)
        contas.marcar("gupy", True)
        aba = AbaFalsa(url="about:blank")
        with mock.patch.object(navegador, "desconectar") as apagar, \
                mock.patch.object(navegador, "abrir_para_leitura", return_value=aba) as abrir:
            _sessao.desconectar(mygreenhouse)
        apagar.assert_not_called()
        abrir.assert_called_once_with("about:blank")
        origens = [p["origin"] for m, p in aba.sessao.pedidos if m == "Storage.clearDataForOrigin"]
        self.assertEqual(origens, ["https://my.greenhouse.io", "https://www.linkedin.com", "https://linkedin.com"])
        self.assertTrue(aba.fechada)
        self.assertEqual(_sessao.conectados(), [])


class TestLeitura(Base):
    def test_no_portal_so_nos_dominios(self):
        self.assertTrue(_sessao.no_portal(mygreenhouse, AbaFalsa()))
        for url in ("https://www.linkedin.com/login", "https://my.greenhouse.io.exemplo.com/x", "about:blank"):
            self.assertFalse(_sessao.no_portal(mygreenhouse, AbaFalsa(url=url)))

    def test_fora_do_portal_nada_roda_na_pagina(self):
        aba = AbaFalsa(url="https://www.linkedin.com/checkpoint", data_page={"version": "x"}, captcha=True)
        self.assertIsNone(_sessao.data_page(mygreenhouse, aba))
        self.assertFalse(_sessao.captcha_na_aba(mygreenhouse, aba))
        with self.assertRaises(_sessao.PortalComLoginErro) as erro:
            _sessao.pedir_json(mygreenhouse, aba, BUSCA + "?query=x", {})
        self.assertEqual(erro.exception.tipo, "login")
        self.assertEqual(aba.scripts, [])

    def test_pedido_so_ao_portal(self):
        with self.assertRaises(ValueError):
            _sessao.pedir_json(mygreenhouse, AbaFalsa(), "https://exemplo.com/api", {})

    def test_pedir_json(self):
        aba = AbaFalsa(respostas=[{"status": 200, "dados": {"props": {}}}])
        status, dados, final = _sessao.pedir_json(mygreenhouse, aba, BUSCA + "?query=x", {"X-Inertia": "true"})
        self.assertEqual((status, dados, final), (200, {"props": {}}, BUSCA + "?query=x"))
        self.assertIn('credentials: "include"', aba.scripts[0])
        self.assertIn('"X-Inertia": "true"', aba.scripts[0])

    def test_scripts_so_leem(self):
        for js in (_sessao.JS_PAGINA, _sessao.JS_CAPTCHA, _sessao.JS_PEDIDO):
            for proibido in ("click", ".value =", "submit", "password", "method: \"POST\""):
                self.assertNotIn(proibido, js)


class Relogio:
    """Relógio e sleep trocados: cada dormir avança o relógio."""

    def __init__(self, aba=None, logar_em=None):
        self.agora, self.sonos, self.aba, self.logar_em = 0.0, 0, aba, logar_em

    def __call__(self):
        return self.agora

    def dormir(self, s):
        self.agora += s
        self.sonos += 1
        if self.logar_em is not None and self.sonos == self.logar_em:
            self.aba.historico.append("https://my.greenhouse.io/dashboard")


class TestLogin(Base):
    def test_esperar_logou(self):
        aba = AbaFalsa(url="https://my.greenhouse.io/users/sign_in")
        r = Relogio(aba, logar_em=3)
        self.assertTrue(_sessao.esperar(mygreenhouse, aba, relogio=r, dormir=r.dormir))
        self.assertEqual(aba.scripts, [])  # só o endereço, nenhum script na página

    def test_esperar_passa_pelo_linkedin_sem_ler(self):
        aba = AbaFalsa(url="https://www.linkedin.com/oauth/v2/authorization")
        r = Relogio(aba, logar_em=5)
        self.assertTrue(_sessao.esperar(mygreenhouse, aba, relogio=r, dormir=r.dormir))
        self.assertEqual(aba.scripts, [])

    def test_esperar_tempo_acabou(self):
        aba = AbaFalsa(url="https://my.greenhouse.io/users/sign_in")
        r = Relogio()
        self.assertFalse(_sessao.esperar(mygreenhouse, aba, relogio=r, dormir=r.dormir))
        self.assertEqual(r.agora, 180)

    def test_esperar_cancelado_e_janela_fechada(self):
        aba = AbaFalsa(url="https://my.greenhouse.io/users/sign_in")
        r = Relogio()
        self.assertFalse(_sessao.esperar(mygreenhouse, aba, cancelado=lambda: True, relogio=r, dormir=r.dormir))
        self.assertEqual(r.sonos, 0)
        aba.erro = navegador.NavegadorErro("fechada")
        self.assertFalse(_sessao.esperar(mygreenhouse, aba, relogio=r, dormir=r.dormir))

    def test_garantir_login(self):
        logada = AbaFalsa()
        chamado = mock.Mock(return_value=True)
        with _sessao.na_pagina(chamado):
            _sessao.garantir_login(mygreenhouse, logada)
        chamado.assert_not_called()

        caida = AbaFalsa(url="https://my.greenhouse.io/users/sign_in")
        with _sessao.na_pagina(lambda m, a: False), self.assertRaises(_sessao.PortalComLoginErro) as erro:
            _sessao.garantir_login(mygreenhouse, caida)
        self.assertEqual(erro.exception.tipo, "login")

        caida.ao_ir = lambda url: url
        with _sessao.na_pagina(lambda m, a: True):
            _sessao.garantir_login(mygreenhouse, caida)
        self.assertEqual(caida.idas, [BUSCA])

        with self.assertRaises(_sessao.PortalComLoginErro):  # fora da página não há quem espere
            _sessao.garantir_login(mygreenhouse, AbaFalsa(url="https://my.greenhouse.io/users/sign_in"))


class TestRotas(Base):
    def setUp(self):
        super().setUp()
        import servidor
        import sincronia
        self.servidor, self.nav = servidor, sincronia.navegador
        for p in (mock.patch.object(filtros, "CONFIG", self.tmp / "config.json"),
                  mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db"),
                  mock.patch.object(mygreenhouse, "ARQ_ESPERA", self.tmp / ".cache" / "mygreenhouse-espera.json"),
                  mock.patch.object(servidor.Handler, "hosts_permitidos", {"127.0.0.1", "localhost"})):
            p.start()
            self.addCleanup(p.stop)
        self.srv = servidor.ThreadingHTTPServer(("127.0.0.1", 0), servidor.Handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)

    def pedir(self, metodo, caminho):
        con = http.client.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=10)
        self.addCleanup(con.close)
        con.request(metodo, caminho, b"{}" if metodo == "POST" else None,
                    {"Content-Type": "application/json"} if metodo == "POST" else {})
        r = con.getresponse()
        return r.status, json.loads(r.read().decode("utf-8"))

    def situacao(self):
        st, j = self.pedir("GET", "/api/portais-login")
        self.assertEqual(st, 200)
        return j["portais"][0]

    def test_situacoes_e_fluxo(self):
        p = self.situacao()
        self.assertEqual((p["nome"], p["situacao"], p["ligado"]), ("mygreenhouse", "desligado", False))
        self.assertTrue(p["aviso_risco"] and p["aviso_login"] and p["termos"])
        filtros.CONFIG.write_text(json.dumps({"fontes": ["gupy", "mygreenhouse"]}), encoding="utf-8")
        self.assertEqual(self.situacao()["situacao"], "desconectado")

        login = AbaFalsa(url="https://my.greenhouse.io/users/sign_in")
        with mock.patch.object(self.nav, "abrir_para_leitura", return_value=login) as abrir:
            self.assertEqual(self.pedir("POST", "/api/portais-login/mygreenhouse/conectar"), (200, {"ok": True}))
        abrir.assert_called_once_with(mygreenhouse.URL_LOGIN)
        self.assertEqual(login.frentes, 1)

        with mock.patch.object(self.nav, "abrir_para_leitura", return_value=AbaFalsa(url=mygreenhouse.URL_LOGIN)):
            self.assertEqual(self.pedir("POST", "/api/portais-login/mygreenhouse/pronto"), (200, {"conectado": False}))
        self.assertEqual(self.situacao()["situacao"], "desconectado")
        logada = AbaFalsa(url="https://my.greenhouse.io/dashboard")
        with mock.patch.object(self.nav, "abrir_para_leitura", return_value=logada):
            self.assertEqual(self.pedir("POST", "/api/portais-login/mygreenhouse/pronto"), (200, {"conectado": True}))
        self.assertEqual((logada.minimizacoes, logada.fechada, logada.scripts), (1, True, []))
        self.assertEqual(self.situacao()["situacao"], "conectado")

        mygreenhouse._comum.gravar_espera(mygreenhouse.ARQ_ESPERA, "código 429")
        p = self.situacao()
        self.assertEqual((p["situacao"], p["espera"]["motivo"]), ("em_espera", "código 429"))
        mygreenhouse.ARQ_ESPERA.unlink()

        with mock.patch.object(self.nav, "desconectar") as apagar:
            self.assertEqual(self.pedir("POST", "/api/portais-login/mygreenhouse/desconectar"), (200, {"ok": True}))
        apagar.assert_called_once()
        self.assertEqual(self.situacao()["situacao"], "desconectado")

    def test_portal_desconhecido_e_pedido_de_fora(self):
        self.assertEqual(self.pedir("POST", "/api/portais-login/linkedin/conectar")[0], 404)
        self.assertEqual(self.pedir("POST", "/api/portais-login/gupy/pronto")[0], 404)
        with mock.patch.object(self.servidor.Handler, "_local", return_value=False):
            self.assertEqual(self.pedir("GET", "/api/portais-login")[0], 403)
            self.assertEqual(self.pedir("POST", "/api/portais-login/mygreenhouse/conectar")[0], 403)

    def test_erro_do_navegador_e_409(self):
        with mock.patch.object(self.nav, "abrir_para_leitura", side_effect=navegador.NavegadorErro("sem navegador")):
            st, j = self.pedir("POST", "/api/portais-login/mygreenhouse/conectar")
        self.assertEqual((st, j.get("erro")), (409, "sem navegador"))

    def test_desconectar_conta_mantem_o_perfil_com_portal_conectado(self):
        _sessao.marcar("mygreenhouse", True)
        contas.marcar("gupy", True)
        aba = AbaFalsa(url="about:blank")
        with mock.patch.object(self.nav, "desconectar") as apagar, \
                mock.patch.object(self.nav, "abrir", return_value=aba):
            self.assertEqual(self.pedir("POST", "/api/contas/gupy/desconectar"), (200, {"ok": True}))
        apagar.assert_not_called()
        self.assertEqual(_sessao.conectados(), ["mygreenhouse"])


if __name__ == "__main__":
    unittest.main()
