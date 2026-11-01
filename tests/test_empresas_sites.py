"""Empresas acompanhadas em qualquer página de vagas (spec 042), sem rede e sem IA de verdade: reconhecer (sem pedido)
e descobrir (um pedido), portal recusado, Teamtailor pelo feed, a EY como empresa (migração e busca sem resultado sem
aviso), a página própria lida pela IA (só o que está escrito, memória sem IA, avisos) e a rota do botão Adicionar."""
import email.utils
import http.client
import json
import re
import shutil
import sys
import tempfile
import threading
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import banco  # noqa: E402
import filtros  # noqa: E402
import ia  # noqa: E402
import vagas  # noqa: E402
from fontes import _comum, ats, ey, pagina_empresa, teamtailor  # noqa: E402

DADOS = Path(__file__).resolve().parent / "dados" / "empresas-sites"
HOST = "carreiras.lojasexemplo.invalid"
PAGINA_TT = (DADOS / "teamtailor-pagina.html").read_bytes()
PAGINA = (DADOS / "pagina-propria.html").read_bytes()
URL_PAGINA = "https://www.empresaexemplo.invalid/carreira-em-tecnologia/#vagas"
CFG = {"termos": ["scrum master", "agile master"], "localidade": {"pais": "Brasil", "estado": "PR", "cidade": "Curitiba",
                                                                  "raio_km": 25},
       "modelos": {"remoto": True, "hibrido": True, "presencial": False}, "fontes": ["indeed"], "janela_horas": 168}
TT = {"sistema": "teamtailor", "id": HOST, "nome": "Lojas Exemplo", "url": f"https://{HOST}/jobs"}
PROPRIA = {"sistema": "pagina", "id": "empresaexemplo.invalid/carreira-em-tecnologia", "nome": "Empresa Exemplo TI",
           "url": URL_PAGINA}


def feed_de_hoje() -> bytes:
    """O feed fictício com as datas trocadas por datas relativas a hoje (2, 3, 4 e 5 dias atrás; a última, 60)."""
    texto = (DADOS / "teamtailor.rss").read_text(encoding="utf-8")
    dias = iter([2, 3, 4, 5, 60])
    agora = datetime.now(timezone.utc)
    return re.sub(r"<pubDate>[^<]*</pubDate>",
                  lambda m: f"<pubDate>{email.utils.format_datetime(agora - timedelta(days=next(dias)))}</pubDate>",
                  texto).encode("utf-8")


def consultas(empresas, cfg=CFG):
    f = filtros.efetivos({**cfg, "empresas": empresas})
    grupos = {}
    for c in filtros.consultas(f):  # a primeira de cada grupo: o cargo "scrum master"
        grupos.setdefault(c["grupo"], c)
    return grupos


class Base(unittest.TestCase):
    def setUp(self):
        _comum.esquecer()
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.pedidos, self.respostas = [], {}
        for p in (mock.patch.object(filtros, "CONFIG", self.tmp / "config.json"),
                  mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db"),
                  mock.patch.object(pagina_empresa, "PASTA", self.tmp / "empresas-paginas"),
                  mock.patch.object(_comum, "baixar", side_effect=self.baixar)):
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(_comum.esquecer)

    def baixar(self, url, params=None, aceitar="", nova_tentativa=True):
        self.pedidos.append(url)
        r = self.respostas.get(url)
        if r is None:
            raise AssertionError(f"pedido inesperado: {url}")
        if isinstance(r, Exception):
            raise r
        return r


class TestReconhecer(Base):
    def test_sem_pedido(self):
        self.assertEqual(ats.reconhecer("https://job-boards.greenhouse.io/acme")["sistema"], "greenhouse")
        e = ats.reconhecer("https://lojas.teamtailor.com/jobs/123-scrum-master")
        self.assertEqual((e["sistema"], e["id"], e["url"]), ("teamtailor", "lojas.teamtailor.com",
                                                             "https://lojas.teamtailor.com/jobs"))
        self.assertEqual(ats.reconhecer("https://careers.ey.com/ey/search/?q=&locationsearch"), ats.EY)
        for portal in ("https://www.linkedin.com/jobs/view/1", "https://empresa.gupy.io/jobs/1", "https://www.vagas.com.br/x"):
            with self.assertRaisesRegex(ValueError, "portal de vagas"):
                ats.reconhecer(portal)
        with self.assertRaises(ats.Desconhecido):
            ats.reconhecer(URL_PAGINA)
        self.assertEqual(self.pedidos, [])

    def test_descobrir_teamtailor_com_dominio_proprio(self):
        self.respostas[f"https://{HOST}/jobs"] = PAGINA_TT
        e = ats.descobrir(f"https://{HOST}/jobs")
        self.assertEqual(e, {"sistema": "teamtailor", "id": HOST, "nome": "Lojas Exemplo", "url": f"https://{HOST}/jobs"})
        self.assertEqual(len(self.pedidos), 1)

    def test_descobrir_pagina_propria(self):
        self.respostas[URL_PAGINA.split("#")[0]] = PAGINA
        e = ats.descobrir(URL_PAGINA)
        self.assertEqual(e, PROPRIA)

    def test_descobrir_pagina_fora_do_ar(self):
        self.respostas["https://exemplo.invalid/vagas"] = _comum.FonteErro("exemplo.invalid respondeu 404", codigo=404)
        with self.assertRaisesRegex(ValueError, "não existe"):
            ats.descobrir("https://exemplo.invalid/vagas")

    def test_conferir_e_validar_sem_pedido(self):
        self.assertEqual(ats.conferir(TT)["id"], HOST)
        self.assertEqual(ats.conferir(PROPRIA), PROPRIA)
        with self.assertRaisesRegex(ValueError, "portal de vagas"):
            ats.conferir({**PROPRIA, "url": "https://www.linkedin.com/company/x/jobs"})
        with self.assertRaises(ValueError):
            ats.conferir({**PROPRIA, "sistema": "xyz"})
        v = filtros.validar({**CFG, "empresas": [TT, PROPRIA, ats.EY, TT]})
        self.assertEqual([e["sistema"] for e in v["empresas"]], ["teamtailor", "pagina", "ey"])
        self.assertEqual(self.pedidos, [])

    def test_vaga_do_link(self):
        e, n = ats.vaga_do_link("https://lojas.teamtailor.com/jobs/123-scrum-master")
        self.assertEqual((e["sistema"], n), ("teamtailor", "123"))
        e, n = ats.vaga_do_link("https://careers.ey.com/ey/job/Sao-Paulo-Scrum-Master/1234567/")
        self.assertEqual((e["sistema"], n), ("ey", "1234567"))
        self.assertIsNone(ats.vaga_do_link(f"https://{HOST}/jobs/1-x"))  # domínio próprio: só com pedido


class TestTeamtailor(Base):
    def test_ler_feed(self):
        vs = teamtailor.ler_feed(feed_de_hoje().decode("utf-8"), TT)
        self.assertEqual(len(vs), 5)
        v = vs[0]
        self.assertEqual({k: v[k] for k in ("id", "plataforma", "ats", "titulo", "empresa", "local", "remoto",
                                            "modelo_trabalho", "restricao_local", "url", "tipo")},
                         {"id": f"teamtailor-{HOST}-1000001", "plataforma": "Teamtailor", "ats": "teamtailor",
                          "titulo": "Scrum Master", "empresa": "Lojas Exemplo", "local": "Cidade Exemplo, Brazil",
                          "remoto": True, "modelo_trabalho": "remoto", "restricao_local": "Brazil",
                          "url": f"https://{HOST}/jobs/1000001-scrum-master", "tipo": "Tecnologia"})
        self.assertIn("Experiência com times ágeis", v["descricao"])
        self.assertEqual(v["publicada_em"], (datetime.now(timezone.utc) - timedelta(days=2)).date().isoformat())
        self.assertEqual([x.get("modelo_trabalho") for x in vs], ["remoto", "presencial", "hibrido", None, "remoto"])
        self.assertEqual(teamtailor.ler_feed(feed_de_hoje().decode(), {**TT, "nome": ""})[0]["empresa"],
                         "Lojas Exemplo BR")  # o nome do feed, sem gritar
        with self.assertRaises(_comum.FonteErro):
            teamtailor.ler_feed("<html>não é RSS", TT)

    def test_busca_nas_areas_com_uma_leitura(self):
        self.respostas[f"https://{HOST}/jobs.rss"] = feed_de_hoje()
        c = consultas([TT])
        remotas, erros = ats.buscar(c["remoto"], 168, 40)
        self.assertEqual(([v["titulo"] for v in remotas], erros), (["Scrum Master"], []))  # a antiga fica fora
        cidade, _ = ats.buscar(c["local"], 168, 40)
        self.assertEqual(sorted(v["titulo"] for v in cidade), ["Agile Scrum Master", "Scrum Master Pleno"])
        ats.buscar({**c["remoto"], "termo": "agile master"}, 168, 40)
        self.assertEqual(self.pedidos, [f"https://{HOST}/jobs.rss"])  # uma leitura por busca

    def test_bloqueio_por_site_e_404(self):
        outra = {**TT, "id": "outra.teamtailor.com", "nome": "Outra", "url": "https://outra.teamtailor.com/jobs"}
        self.respostas[f"https://{HOST}/jobs.rss"] = _comum.FonteErro(f"{HOST} respondeu 429", codigo=429)
        self.respostas["https://outra.teamtailor.com/jobs.rss"] = feed_de_hoje()
        c = consultas([TT, outra])
        vs, erros = ats.buscar(c["remoto"], 168, 40)
        self.assertEqual([v["empresa"] for v in vs], ["Outra"])
        self.assertIn("limitou as consultas", erros[0])
        ats.buscar({**c["remoto"], "termo": "agile master"}, 168, 40)
        self.assertEqual(self.pedidos.count(f"https://{HOST}/jobs.rss"), 1)  # sem nova tentativa
        _comum.esquecer()
        self.respostas[f"https://{HOST}/jobs.rss"] = _comum.FonteErro(f"{HOST} respondeu 404", codigo=404)
        _, erros = ats.buscar(consultas([TT])["remoto"], 168, 40)
        self.assertIn("remova ou troque o link", erros[0])


class TestEY(Base):
    def test_busca_pela_fonte_da_ey(self):
        vaga = {"id": "ey-1", "titulo": "Scrum Master", "plataforma": "EY"}
        with mock.patch.object(ey, "buscar", return_value=([vaga], [])) as buscar:
            vs, erros = ats.buscar(consultas([ats.EY])["remoto"], 168, 40)
        self.assertEqual((vs, erros), ([vaga], []))
        buscar.assert_called_once()

    def test_sem_resultado_sem_aviso(self):
        pagina = (DADOS / "ey-sem-resultado.html").read_text(encoding="utf-8")
        with mock.patch.object(ey, "_baixar", return_value=pagina):
            self.assertEqual(ey._linhas("agilista", "Brazil"), ([], None))
        com_linha = pagina.replace('<div id="noresults">There are currently no open positions matching',
                                   '<table><tr class="data-row"><td>?</td></tr></table><div>')
        with mock.patch.object(ey, "_baixar", return_value=com_linha):
            self.assertEqual(ey._linhas("agilista", "Brazil"), ([], ey.ILEGIVEL))

    def test_migracao(self):
        empresas = lambda cfg: [e["sistema"] for e in filtros.efetivos(cfg)["empresas"]]  # noqa: E731
        self.assertEqual(empresas({"termos": ["x"], "fontes": ["indeed", "ey"]}), ["ey"])
        self.assertEqual(empresas({"termos": ["x"], "fontes": ["indeed"]}), [])
        self.assertEqual(empresas({"termos": ["x"]}), ["ey"])  # o padrão antigo tinha a EY
        self.assertEqual(empresas({}), [])  # instalação nova
        self.assertEqual(empresas({"termos": ["x"], "fontes": ["ey"], "empresas": [ats.EY]}), ["ey"])  # sem repetir
        cfg = {"termos": ["x"], "fontes": ["indeed", "ey"]}
        f = filtros.efetivos(cfg)
        self.assertNotIn("ey", f["fontes"])
        self.assertEqual(vagas.fontes_da_busca(cfg, f), ["indeed", "ats"])
        filtros.CONFIG.write_text(json.dumps({**CFG, "fontes": ["indeed", "ey"]}), encoding="utf-8")
        filtros.salvar({**filtros.efetivos(filtros.ler_config())})
        salvo = filtros.ler_config()
        self.assertEqual(([e["sistema"] for e in salvo["empresas"]], "ey" in salvo["fontes"]), (["ey"], False))


class IAFalsa:
    """ia.responder trocado: devolve a resposta dada e guarda os pedidos."""

    def __init__(self, vagas_ia):
        self.pedidos = []
        self.vagas = vagas_ia

    def __call__(self, pedido, **kw):
        self.pedidos.append(pedido)
        return "Aqui está:\n" + json.dumps({"vagas": self.vagas}, ensure_ascii=False)


VAGAS_IA = [
    {"titulo": "Scrum Master Pleno", "modelo": "remoto", "local": None, "requisitos": "Agilidade: Scrum, Kanban, Jira.",
     "email_candidatura": "recrutamento@exemplo.invalid", "url": None},
    {"titulo": "Agile Master Sênior", "modelo": "presencial", "local": "Curitiba",
     "requisitos": "Transformação ágil: SAFe, OKR.", "email_candidatura": "inventado@exemplo.invalid", "url": None},
    {"titulo": "Desenvolvedor Full Stack Sênior", "modelo": "remoto", "local": None, "requisitos": "PHP, Python.",
     "email_candidatura": None, "url": "https://inventado.invalid/vaga"},
    {"titulo": "Gerente de Projetos", "modelo": "remoto", "local": None, "requisitos": "Inventada.",
     "email_candidatura": None, "url": None},
]


class TestPaginaPropria(Base):
    def setUp(self):
        super().setUp()
        self.respostas[URL_PAGINA.split("#")[0]] = PAGINA
        self.ia = IAFalsa(VAGAS_IA)
        for p in (mock.patch.object(ia, "disponivel", return_value=True),
                  mock.patch.object(ia, "responder", side_effect=self.ia)):
            p.start()
            self.addCleanup(p.stop)

    def test_texto_so_o_visivel_a_partir_da_ancora(self):
        t = pagina_empresa.texto(PAGINA.decode("utf-8"), URL_PAGINA)
        self.assertIn("Scrum Master Pleno", t)
        self.assertNotIn("Sobre nós", t)  # antes da âncora #vagas
        self.assertNotIn("Ignore as instruções", t)  # oculto: não vai à IA
        self.assertIn("E-mail dos links da página: vagas@exemplo.invalid", t)  # só no mailto do "Envie seu currículo"

    def test_lista_so_o_que_esta_escrito(self):
        vs = pagina_empresa.lista(PROPRIA)
        self.assertEqual([v["titulo"] for v in vs], ["Scrum Master Pleno", "Agile Master Sênior",
                                                      "Desenvolvedor Full Stack Sênior"])  # a inventada sai
        sm, am, dev = vs
        self.assertEqual((sm["remoto"], sm["modelo_trabalho"], sm["local"], sm["email_candidatura"]),
                         (True, "remoto", "Remoto", "recrutamento@exemplo.invalid"))
        self.assertNotIn("email_candidatura", am)  # e-mail que não está na página
        self.assertIsNone(dev["url_candidatura"])  # link que não está na página
        self.assertEqual((sm["plataforma"], sm["empresa"], sm["url"], sm["publicada_em"]),
                         ("Site da empresa", "Empresa Exemplo TI", URL_PAGINA, date.today().isoformat()))
        self.assertTrue(sm["id"].startswith("pagina-empresaexemplo.invalid"))
        self.assertNotIn("Ignore as instruções", self.ia.pedidos[0])

    def test_mesma_pagina_sem_ia_e_com_a_primeira_data(self):
        vs = pagina_empresa.lista(PROPRIA)
        arq = next(pagina_empresa.PASTA.glob("*.json"))
        mem = json.loads(arq.read_text(encoding="utf-8"))
        mem["vistas"][vs[0]["id"]] = "2026-10-01"
        arq.write_text(json.dumps(mem), encoding="utf-8")
        _comum.esquecer()
        de_novo = pagina_empresa.lista(PROPRIA)
        self.assertEqual(len(self.ia.pedidos), 1)  # a página não mudou: sem IA
        self.assertEqual(de_novo[0]["publicada_em"], "2026-10-01")

    def test_avisos(self):
        with mock.patch.object(ia, "disponivel", return_value=False):
            with self.assertRaisesRegex(_comum.FonteErro, "ligue a IA"):
                pagina_empresa.lista(PROPRIA)
        with mock.patch.object(pagina_empresa, "MAX_IA", 0):
            with self.assertRaisesRegex(_comum.FonteErro, "próxima busca"):
                pagina_empresa.lista(PROPRIA)
        self.ia.vagas = []
        with self.assertRaisesRegex(_comum.FonteErro, "nenhuma vaga"):
            pagina_empresa.lista(PROPRIA)
        _comum.esquecer()
        _, erros = ats.buscar(consultas([PROPRIA])["remoto"], 168, 40)
        self.assertEqual(erros, ["nenhuma vaga encontrada na página de Empresa Exemplo TI"])  # informativo
        self.assertEqual(len(self.ia.pedidos), 1)  # a mesma página vazia não volta à IA

    def test_busca_nas_areas(self):
        c = consultas([PROPRIA])
        remotas, erros = ats.buscar(c["remoto"], 168, 40)
        self.assertEqual(([v["titulo"] for v in remotas], erros), (["Scrum Master Pleno"], []))  # "Home Office"
        cidade, _ = ats.buscar({**c["local"], "termo": "agile master"}, 168, 40)
        self.assertEqual([v["titulo"] for v in cidade], ["Agile Master Sênior"])  # presencial na cidade
        self.assertEqual(len(self.ia.pedidos), 1)


class TestRota(Base):
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

    def pedir(self, corpo):
        con = http.client.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=10)
        self.addCleanup(con.close)
        con.request("POST", "/api/empresas/reconhecer", json.dumps(corpo).encode(), {"Content-Type": "application/json"})
        r = con.getresponse()
        return r.status, json.loads(r.read())

    def test_reconhecer(self):
        self.respostas[f"https://{HOST}/jobs"] = PAGINA_TT
        self.respostas[URL_PAGINA.split("#")[0]] = PAGINA
        with mock.patch.object(ia, "disponivel", return_value=False):
            st, j = self.pedir({"url": f"https://{HOST}/jobs"})
            self.assertEqual((st, j["empresa"]["sistema"], j["rotulo"], j["ia_necessaria"]),
                             (200, "teamtailor", "Teamtailor", False))
            st, j = self.pedir({"url": URL_PAGINA})
            self.assertEqual((st, j["rotulo"], j["ia_necessaria"], j["ia_ligada"]),
                             (200, "Página própria (lida pela IA)", True, False))
        st, j = self.pedir({"url": "https://www.linkedin.com/jobs/view/1"})
        self.assertEqual(st, 400)
        self.assertIn("portal de vagas", j["erro"])
        self.assertFalse(filtros.CONFIG.exists())  # reconhecer não grava nada


if __name__ == "__main__":
    unittest.main()
