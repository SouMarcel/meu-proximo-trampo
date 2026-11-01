"""MyGreenhouse Jobs na busca (fontes/mygreenhouse.py, spec 041), com respostas fictícias do Inertia, uma aba falsa e
sem rede: o endereço da busca, a leitura sem os dados da conta, o id igual ao das empresas acompanhadas, os filtros de
cargo, janela e país, a paginação, a descrição pela API pública, o login caído, as paradas (bloqueio com 24 horas de
espera, captcha, portal mudado, janela fechada), a pausa e o portal fora da busca da página e desligado por padrão."""
import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs, urlsplit

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash"), str(Path(__file__).resolve().parent)]
import filtros  # noqa: E402
import navegador  # noqa: E402
import segredos  # noqa: E402
import vagas  # noqa: E402
from aba_login_falsa import AbaFalsa  # noqa: E402
from fontes import FONTES, _comum, _sessao, ats, mygreenhouse  # noqa: E402

DADOS = Path(__file__).resolve().parent / "dados" / "mygreenhouse"
PAGINA = json.loads((DADOS / "data-page.json").read_text(encoding="utf-8"))
P1 = json.loads((DADOS / "pagina-1.json").read_text(encoding="utf-8"))
P2 = json.loads((DADOS / "pagina-2.json").read_text(encoding="utf-8"))
SEM_POSTS = json.loads((DADOS / "sem-jobposts.json").read_text(encoding="utf-8"))
HOJE = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
CFG = {"termos": ["scrum master"], "localidade": {"pais": "Brasil", "estado": "SP", "cidade": "São Paulo", "raio_km": 25},
       "modelos": {"remoto": True, "hibrido": True, "presencial": False}, "tipos_emprego": [],
       "fontes": ["mygreenhouse"], "janela_horas": 168, "internacional": {"ativo": False}}
CONTA = ("viewed", "appliedAt", "saved", "departmentId", "logoUrl", "summary", "payRanges")


def consultas(cfg=CFG):
    return {c["grupo"]: c for c in filtros.consultas(filtros.efetivos(cfg))}


def ok(dados):
    return {"status": 200, "dados": dados}


def empresas(lista):
    return [v["empresa"] for v in lista]


class SemRede(unittest.TestCase):
    def setUp(self):
        _comum.esquecer()
        mygreenhouse._estado["ultimo"] = None
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for p in (mock.patch.object(mygreenhouse, "PAUSA", (0, 0)), mock.patch.object(mygreenhouse.time, "sleep"),
                  mock.patch.object(mygreenhouse, "_agora", return_value=HOJE),
                  mock.patch.object(mygreenhouse, "ARQ_ESPERA", self.tmp / ".cache" / "mygreenhouse-espera.json"),
                  mock.patch.object(_sessao, "ESTADO", self.tmp / ".cache" / "portais-login.json"),
                  mock.patch.object(segredos, "ler", return_value="")):
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(_comum.esquecer)

    def aba(self, *respostas, **kw):
        aba = AbaFalsa(respostas=list(respostas), data_page=kw.pop("data_page", PAGINA), **kw)
        p = mock.patch.object(navegador, "abrir_para_leitura", return_value=aba)
        self.abrir = p.start()
        self.addCleanup(p.stop)
        return aba

    def buscar(self, consulta=None, horas=168, por_termo=40, esperar_login=lambda m, a: False):
        with _sessao.na_pagina(esperar_login):
            return mygreenhouse.buscar(consulta or consultas()["remoto"], horas, por_termo)


class TestEndereco(SemRede):
    def params(self, url):
        return parse_qs(urlsplit(url).query)

    def test_nacional(self):
        q = self.params(mygreenhouse.endereco('"scrum master"', consultas()["remoto"], 168))
        self.assertEqual(q["query"], ["scrum master"])  # sem aspas: a busca do portal é por palavras
        self.assertEqual(q["work_type[]"], ["remote"])
        self.assertEqual((q["location"], q["country_short_name"], q["location_type"]), (["Brazil"], ["BR"], ["country"]))
        self.assertNotIn("date_posted", q)
        self.assertNotIn("page", q)

    def test_janela_curta_e_pagina(self):
        q = self.params(mygreenhouse.endereco("scrum master", consultas()["remoto"], 120, pagina=2))
        self.assertEqual((q["date_posted"], q["page"]), (["past_five_days"], ["2"]))
        self.assertNotIn("date_posted", self.params(mygreenhouse.endereco("x", consultas()["remoto"], 121)))

    def test_global_sem_local(self):
        q = self.params(mygreenhouse.endereco("scrum master", {"global": True, "remoto": True}, 168))
        self.assertNotIn("location", q)
        self.assertEqual(q["work_type[]"], ["remote"])


class TestLeitura(SemRede):
    def test_campos_sem_os_dados_da_conta(self):
        vagas_lidas, mais = mygreenhouse.ler_resposta(P1)
        self.assertTrue(mais)
        self.assertEqual(len(vagas_lidas), 12)
        v = vagas_lidas[0]
        self.assertEqual({k: v[k] for k in ("id", "plataforma", "ats", "titulo", "empresa", "local", "remoto",
                                            "modelo_trabalho", "publicada_em", "url", "restricao_local")},
                         {"id": "greenhouse-empresaalfa-5001", "plataforma": "MyGreenhouse", "ats": "greenhouse",
                          "titulo": "Scrum Master", "empresa": "Empresa Alfa", "local": "Remote - Brazil",
                          "remoto": True, "modelo_trabalho": "remoto", "publicada_em": "2026-10-31",
                          "url": "https://job-boards.greenhouse.io/empresaalfa/jobs/5001",
                          "restricao_local": "Remote - Brazil"})
        for vaga in vagas_lidas:
            self.assertFalse(set(CONTA) & set(vaga))
        delta = next(x for x in vagas_lidas if x["empresa"] == "Empresa Delta")
        self.assertEqual((delta["remoto"], delta["modelo_trabalho"], "restricao_local" in delta), (False, "hibrido", False))

    def test_id_igual_ao_das_empresas_acompanhadas(self):
        v = mygreenhouse.ler_resposta(P1)[0][0]
        e = ats.reconhecer("https://job-boards.greenhouse.io/empresaalfa")
        self.assertEqual(ats.normalizar({"id": 5001, "title": "Scrum Master"}, e)["id"], v["id"])
        self.assertEqual(ats.vaga_do_link(v["url"])[1], "5001")  # o "Acompanhar empresa" reconhece o link (US5)

    def test_sem_jobposts_o_portal_mudou(self):
        with self.assertRaises(_sessao.PortalComLoginErro) as erro:
            mygreenhouse.ler_resposta(SEM_POSTS)
        self.assertEqual(erro.exception.tipo, "mudou")


class TestBusca(SemRede):
    def test_duas_paginas_filtradas(self):
        aba = self.aba(ok(P1), ok(P2))
        achadas, erros = self.buscar()
        self.assertEqual(erros, [])
        # Alfa (Brasil), Gama (América Latina), Zeta (Brasil, link no site da empresa) e Ni (página 2); fora: Beta (só
        # EUA), Delta (híbrida), Csi (fora da janela) e os títulos de outro cargo
        self.assertEqual(empresas(achadas), ["Empresa Alfa", "Empresa Gama", "Empresa Zeta", "Empresa Ni"])
        self.assertEqual(len(aba.pedidos), 2)
        self.assertEqual(parse_qs(urlsplit(aba.pedidos[1]).query)["page"], ["2"])
        self.abrir.assert_called_once_with(mygreenhouse.URL_BUSCA)
        fetch = next(js for js in aba.scripts if "fetch(" in js)
        for cab in ('"X-Inertia": "true"', '"X-Inertia-Version": "versao-ficticia-1"',
                    '"X-Inertia-Partial-Data": "browsing,page,moreResultsAvailable,jobPosts"'):
            self.assertIn(cab, fetch)
        for js in aba.scripts:
            self.assertNotIn("click", js)

    def test_para_no_limite_de_paginas(self):
        aba = self.aba(ok(P1), ok(P1), ok(P1), ok(P1))
        self.buscar()
        self.assertEqual(len(aba.pedidos), mygreenhouse.MAX_PAGINAS)

    def test_por_termo(self):
        self.aba(ok(P1), ok(P2))
        self.assertEqual(len(self.buscar(por_termo=1)[0]), 1)

    def test_consultas_sem_pedido(self):
        aba = self.aba(ok(P1))
        c = consultas()
        cidade = c["local"]
        outro_pais = {**c["remoto"], "pais": "argentina", "pais_nome": "Argentina"}
        for consulta in (cidade, outro_pais, {**c["remoto"], "grupo": "pais", "remoto": False}):
            self.assertEqual(self.buscar(consulta), ([], []))
        self.assertEqual(aba.pedidos, [])
        self.abrir.assert_not_called()

    def test_internacional_global(self):
        aba = self.aba(ok(P1), ok(P2))
        achadas, _ = self.buscar({"global": True, "remoto": True, "termo": "scrum master", "grupo": "internacional:global",
                                  "area": "internacional"})
        self.assertIn("Empresa Beta", empresas(achadas))  # sem o filtro do Brasil
        self.assertNotIn("location", parse_qs(urlsplit(aba.pedidos[0]).query))

    def test_descrever_pela_api_publica(self):
        v = mygreenhouse.ler_resposta(P1)[0]
        alfa, zeta = v[0], next(x for x in v if x["empresa"] == "Empresa Zeta")
        with mock.patch.object(ats, "ler", return_value={"descricao": "Texto da vaga"}) as ler:
            self.assertEqual(mygreenhouse.descrever(alfa), "Texto da vaga")
            self.assertEqual(mygreenhouse.descrever(zeta), "Texto da vaga")
        self.assertEqual([c.args[0] for c in ler.call_args_list],
                         ["https://job-boards.greenhouse.io/empresaalfa/jobs/5001",
                          "https://job-boards.greenhouse.io/empresazeta/jobs/5006"])  # link da empresa: pelo id
        with mock.patch.object(ats, "ler", side_effect=_comum.FonteErro("saiu do ar")):
            self.assertEqual(mygreenhouse.descrever({**alfa, "descricao": "antes"}), "antes")


class TestLogin(SemRede):
    def test_login_caido_espera_e_segue(self):
        aba = self.aba(ok(P2), url="https://my.greenhouse.io/users/sign_in")
        aba.ao_ir = lambda url: url

        def esperar(modulo, a):
            a.historico.append("https://my.greenhouse.io/dashboard")
            return True
        achadas, erros = self.buscar(esperar_login=esperar)
        self.assertEqual((empresas(achadas), erros), (["Empresa Ni"], []))
        self.assertEqual(aba.idas, [mygreenhouse.URL_BUSCA])

    def test_sem_login_o_portal_sai_da_busca(self):
        aba = self.aba(ok(P1), url="https://my.greenhouse.io/users/sign_in")
        achadas, erros = self.buscar()
        self.assertEqual(achadas, [])
        self.assertIn("login não foi feito", erros[0])
        self.assertEqual(aba.pedidos, [])
        with _sessao.na_pagina(lambda m, a: False):  # outra consulta da mesma busca: sem pedido e sem novo aviso
            self.assertEqual(mygreenhouse.buscar({**consultas()["remoto"], "termo": "agile coach"}, 168, 40), ([], []))

    def test_401_no_meio_espera_uma_vez(self):
        aba = self.aba({"status": 401, "dados": None}, ok(P2))
        quedas = []

        def ao_ir(url):
            if not quedas:
                quedas.append(url)
                return "https://my.greenhouse.io/users/sign_in"
            return url
        aba.ao_ir = ao_ir

        def esperar(modulo, a):
            a.historico.append("https://my.greenhouse.io/dashboard")
            return True
        achadas, erros = self.buscar(esperar_login=esperar)
        self.assertEqual((empresas(achadas), erros), (["Empresa Ni"], []))
        self.assertEqual(len(aba.pedidos), 2)

    def test_redirecionado_ao_login_conta_como_401(self):
        aba = self.aba({"status": 200, "dados": None, "url": mygreenhouse.URL_LOGIN},
                       {"status": 200, "dados": None, "url": mygreenhouse.URL_LOGIN})
        achadas, erros = self.buscar()
        self.assertEqual(achadas, [])
        self.assertIn("sessão caiu de novo", erros[0])
        self.assertEqual(len(aba.pedidos), 2)


class TestParadas(SemRede):
    def test_bloqueio_grava_24_horas_sem_nova_tentativa(self):
        for codigo in mygreenhouse.BLOQUEIOS:
            with self.subTest(codigo=codigo):
                _comum.esquecer()
                mygreenhouse.ARQ_ESPERA.unlink(missing_ok=True)
                aba = self.aba({"status": codigo, "dados": None}, ok(P1))
                achadas, erros = self.buscar()
                self.assertEqual((achadas, len(aba.pedidos)), ([], 1))
                self.assertIn("limitou as consultas", erros[0])
                self.assertIsNotNone(mygreenhouse.espera())
                self.assertTrue(mygreenhouse.parada())

    def test_na_espera_nenhum_pedido_e_um_aviso(self):
        _comum.gravar_espera(mygreenhouse.ARQ_ESPERA, "código 429")
        aba = self.aba(ok(P1))
        r1 = self.buscar()
        r2 = self.buscar({**consultas()["remoto"], "termo": "agile coach"})
        self.assertIn("em espera até", r1[1][0])
        self.assertEqual(r2, ([], []))
        self.assertEqual(aba.pedidos, [])
        self.abrir.assert_not_called()
        with mock.patch.object(ats, "ler") as ler:
            self.assertEqual(mygreenhouse.descrever({"id": "greenhouse-x-1", "url": "", "descricao": "d"}), "d")
        ler.assert_not_called()
        self.assertEqual(vagas.fontes_em_espera(["mygreenhouse"], pagina=True), [])  # desconectado: não pergunta
        _sessao.marcar("mygreenhouse", True)
        self.assertEqual([e["nome"] for e in vagas.fontes_em_espera(["mygreenhouse"], pagina=True)], ["mygreenhouse"])
        self.assertEqual(vagas.fontes_em_espera(["mygreenhouse"]), [])  # terminal: o portal nem roda

    def test_captcha_traz_a_janela_sem_espera(self):
        aba = self.aba(ok(P1), captcha=True)
        achadas, erros = self.buscar()
        self.assertEqual((achadas, aba.pedidos, aba.frentes), ([], [], 1))
        self.assertIn("captcha", erros[0])
        self.assertIsNone(mygreenhouse.espera())

    def test_portal_mudou(self):
        self.aba(ok(SEM_POSTS))
        self.assertIn("mudou", self.buscar()[1][0])
        _comum.esquecer()
        self.aba(ok(P1), data_page=None)
        self.assertIn("mudou", self.buscar()[1][0])
        _comum.esquecer()
        self.aba({"status": 200, "dados": None})  # HTML no lugar do JSON, sem captcha
        self.assertIn("mudou", self.buscar()[1][0])

    def test_409_recarrega_uma_vez(self):
        aba = self.aba({"status": 409, "dados": None}, ok(P2))
        self.assertEqual(empresas(self.buscar()[0]), ["Empresa Ni"])
        self.assertEqual(aba.idas, [mygreenhouse.URL_BUSCA])
        _comum.esquecer()
        aba = self.aba({"status": 409, "dados": None}, {"status": 409, "dados": None}, ok(P2))
        achadas, erros = self.buscar()
        self.assertEqual((achadas, len(aba.pedidos)), ([], 2))
        self.assertIn("mudou", erros[0])

    def test_janela_fechada(self):
        aba = self.aba(navegador.NavegadorErro("a janela foi fechada"))
        achadas, erros = self.buscar()
        self.assertEqual(achadas, [])
        self.assertIn("janela da ferramenta", erros[0])
        self.assertEqual(len(aba.pedidos), 1)  # sem nova tentativa

    @mock.patch.object(mygreenhouse, "PAUSA", (3.0, 7.0))  # o padrão (o setUp zera a pausa)
    def test_pausa(self):
        self.assertEqual(mygreenhouse.pausa(), {"faixa": (3.0, 7.0), "definida": False, "ajuste": ""})
        with mock.patch.object(segredos, "ler", return_value="10"):
            self.assertEqual(mygreenhouse.pausa()["faixa"], (10.0, 14.0))
            self.assertIn("MYGREENHOUSE_PAUSA", mygreenhouse.aviso_pausa(2))
        with mock.patch.object(segredos, "ler", return_value="1"):
            self.assertEqual(mygreenhouse.pausa()["faixa"], (3.0, 7.0))
        with mock.patch.object(segredos, "ler", return_value="abc"):
            self.assertEqual(mygreenhouse.pausa()["faixa"], (3.0, 7.0))


class TestForaDaPagina(SemRede):
    def test_terminal_nao_abre_a_janela(self):
        with mock.patch.object(navegador, "abrir_para_leitura") as abrir, \
                mock.patch.object(navegador, "abrir") as abrir2:
            r = mygreenhouse.buscar(consultas()["remoto"], 168, 40)
            fora = vagas.fontes_com_login_fora(["gupy", "mygreenhouse"])
        self.assertEqual(r, ([], ["MyGreenhouse Jobs: só pelo botão Buscar da página (portal com login)"]))
        self.assertEqual(list(fora), ["mygreenhouse"])
        abrir.assert_not_called()
        abrir2.assert_not_called()

    def test_desligado_por_padrao(self):
        self.assertNotIn("mygreenhouse", filtros.FONTES_PADRAO)
        self.assertNotIn("mygreenhouse", filtros.efetivos({})["fontes"])
        self.assertIs(FONTES["mygreenhouse"], mygreenhouse)
        self.assertIn("proíbem", mygreenhouse.TERMOS)
        self.assertIn("suspender", mygreenhouse.AVISO_RISCO)

    def test_painel_aceita_o_portal_com_login(self):
        e = {"termos": ["scrum master"], "localidade": {"pais": "Brasil", "estado": "", "cidade": "", "raio_km": 25},
             "modelos": {"remoto": True, "hibrido": False, "presencial": False}, "janela_horas": 168}
        self.assertEqual(filtros.validar({**e, "fontes": ["gupy", "mygreenhouse", "xyz"]})["fontes"],
                         ["gupy", "mygreenhouse"])
        with self.assertRaises(ValueError):  # sozinho não basta: ele não roda no terminal
            filtros.validar({**e, "fontes": ["mygreenhouse"]})
        self.assertEqual([p["nome"] for p in filtros.opcoes()["fontes_login"]], ["mygreenhouse"])


if __name__ == "__main__":
    unittest.main()
