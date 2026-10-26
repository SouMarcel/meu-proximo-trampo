"""Empresas acompanhadas (Greenhouse, Lever e Ashby) na busca nacional, com respostas fictícias e sem rede (spec
031): vagas abertas ao país, cidade, uma lista por empresa para as duas áreas, a lista no nível de cima do
config.json, parada no primeiro bloqueio de cada sistema e "Acompanhar"."""
import json
import shutil
import sys
import tempfile
import time
import unittest
import urllib.error
from datetime import date
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import filtros  # noqa: E402
import vagas  # noqa: E402
from fontes import _comum, ats  # noqa: E402

HOJE = date.today().isoformat()
ACME = {"sistema": "greenhouse", "id": "acme", "nome": "Acme", "url": "https://job-boards.greenhouse.io/acme"}
BETA = {"sistema": "greenhouse", "id": "beta", "nome": "Beta", "url": "https://job-boards.greenhouse.io/beta"}
GAMA = {"sistema": "greenhouse", "id": "gama", "nome": "Gama", "url": "https://job-boards.greenhouse.io/gama"}
DELTA = {"sistema": "lever", "id": "delta", "nome": "Delta", "url": "https://jobs.lever.co/delta"}
CFG = {"termos": ["data engineer"], "localidade": {"pais": "Brasil", "estado": "SP", "cidade": "São Paulo",
                                                   "raio_km": 25},
       "modelos": {"remoto": True, "hibrido": True, "presencial": False}, "fontes": ["indeed"],
       "internacional": {"ativo": False}, "empresas": [ACME]}


def greenhouse(*locais, titulo="Data Engineer", empresa="Acme"):
    """A lista de uma empresa no Greenhouse, uma vaga por local."""
    return {"jobs": [{"id": 100 + i, "title": titulo, "company_name": empresa, "location": {"name": local},
                      "first_published": f"{HOJE}T10:00:00-03:00",
                      "absolute_url": f"https://job-boards.greenhouse.io/acme/jobs/{100 + i}",
                      "content": "&lt;p&gt;Texto da vaga.&lt;/p&gt;", "language": "en"}
                     for i, local in enumerate(locais)], "meta": {"total": len(locais)}}


def lever(*locais, titulo="Data Engineer"):
    return [{"id": f"{i:08d}-0000-0000-0000-000000000000", "text": titulo,
             "categories": {"location": local, "allLocations": [local]},
             "workplaceType": "remote" if "remote" in local.lower() else "onsite",
             "createdAt": int(time.time() * 1000),
             "hostedUrl": f"https://jobs.lever.co/delta/{i:08d}-0000-0000-0000-000000000000",
             "descriptionPlain": "Texto da vaga."} for i, local in enumerate(locais)]


def grupos(cfg):
    return {c["grupo"]: c for c in filtros.consultas(filtros.efetivos(cfg))}


def titulos_locais(vagas_):
    return [v["local"] for v in vagas_]


class Resposta:
    def __init__(self, dados):
        self.corpo = json.dumps(dados).encode()

    def read(self, n):
        return self.corpo

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class SemRede(unittest.TestCase):
    def setUp(self):
        _comum.esquecer()
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.dormiu = []
        for p in (mock.patch.object(_comum, "INTERVALO", 0),
                  mock.patch.object(_comum.time, "sleep", side_effect=self.dormiu.append),
                  mock.patch.object(filtros, "CONFIG", self.tmp / "config.json")):
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(_comum.esquecer)
        self.rede({})

    def rede(self, respostas):
        """urlopen falso: respostas[trecho da URL] = JSON, código HTTP ou uma tupla deles (um por pedido)."""
        self.pedidos = []
        filas = {k: list(v) for k, v in respostas.items() if isinstance(v, tuple)}

        def abrir(req, timeout=None):
            url = req.full_url
            self.pedidos.append(url)
            chave = next((k for k in respostas if k in url), None)
            if chave is None:
                raise AssertionError(f"pedido inesperado: {url}")
            r = filas[chave].pop(0) if chave in filas else respostas[chave]
            if isinstance(r, int):
                raise urllib.error.HTTPError(url, r, "x", {}, None)
            return Resposta(r)
        p = mock.patch.object(_comum.urllib.request, "urlopen", side_effect=abrir)
        p.start()
        self.addCleanup(p.stop)


class TestBuscaNacional(SemRede):  # US1
    def test_aberta_ao_pais(self):
        for local in ("Remote, Brazil", "Latin America", "Anywhere", "Worldwide", "Remote - LATAM",
                      "Remote, Brazil; Remote, Mexico", "Brasil"):
            self.assertTrue(filtros.aberta_ao_pais(local, "Brasil"), local)
        for local in ("Remote, United States", "Remote", "", None, "Europe", "Remote, Portugal"):
            self.assertFalse(filtros.aberta_ao_pais(local, "Brasil"), local)

    def test_remotas_abertas_ao_pais(self):
        self.rede({"boards/acme": greenhouse("Remote, Brazil", "Remote, United States", "Remote", "Anywhere",
                                             "Latin America", "São Paulo, Brazil")})
        achadas, erros = ats.buscar(grupos(CFG)["remoto"], 168, 50)
        self.assertEqual(erros, [])
        self.assertEqual(titulos_locais(achadas), ["Remote, Brazil", "Anywhere", "Latin America"])

    def test_presencial_e_hibrida_na_cidade(self):
        self.rede({"boards/acme": greenhouse("São Paulo, Brazil", "Sao Paulo, State of Sao Paulo, Brazil",
                                             "Campinas, SP", "Rio de Janeiro, Brazil", "São Paulo, Portugal",
                                             "Remote, Brazil")})
        achadas, _ = ats.buscar(grupos(CFG)["local"], 168, 50)
        self.assertEqual(titulos_locais(achadas), ["São Paulo, Brazil", "Sao Paulo, State of Sao Paulo, Brazil"])

    def test_pais_sem_cidade(self):
        cfg = {**CFG, "localidade": {"pais": "Brasil", "estado": "", "cidade": "", "raio_km": None}}
        self.rede({"boards/acme": greenhouse("Remote, Brazil", "Rio de Janeiro, Brazil", "Lisbon, Portugal")})
        achadas, _ = ats.buscar(grupos(cfg)["pais"], 168, 50)
        self.assertEqual(titulos_locais(achadas), ["Remote, Brazil", "Rio de Janeiro, Brazil"])

    def test_sem_a_internacional(self):
        f = filtros.efetivos(CFG)
        self.assertFalse(f["internacional"]["ativo"])
        self.assertEqual(vagas.fontes_da_busca(CFG, f), ["indeed", "ats"])
        nacionais = [c for c in filtros.consultas(f) if c["area"] == "nacional"]
        self.assertTrue(nacionais)
        self.assertTrue(all(c["empresas"] == [ACME] for c in nacionais))
        self.assertFalse([c for c in filtros.consultas(f) if c["area"] == "internacional"])
        self.assertEqual(vagas.fontes_da_busca({**CFG, "empresas": []}, filtros.efetivos({**CFG, "empresas": []})),
                         ["indeed"])

    def test_uma_lista_para_as_duas_areas(self):
        cfg = {**CFG, "internacional": {"ativo": True, "termos": ["data engineer"]}}
        g = grupos(cfg)
        self.assertEqual(g[filtros.GLOBAL]["empresas"], [ACME])
        self.rede({"boards/acme": greenhouse("Remote, Brazil", "Remote, Portugal")})
        nacional, _ = ats.buscar(g["remoto"], 168, 50)
        exterior, _ = ats.buscar(g[filtros.GLOBAL], 168, 50)
        self.assertEqual(titulos_locais(nacional), ["Remote, Brazil"])
        self.assertEqual(titulos_locais(exterior), ["Remote, Brazil", "Remote, Portugal"])
        self.assertEqual(len(self.pedidos), 1)

    def test_por_pais_e_mudanca_sem_pedido(self):
        cfg = {**CFG, "internacional": {"ativo": True, "termos": ["data engineer"], "paises": ["Portugal"],
                                        "aceita_mudar": True}}
        g = grupos(cfg)
        self.assertEqual(ats.buscar(g["internacional:Portugal"], 168, 50), ([], []))
        self.assertEqual(ats.buscar(g["mudanca:Portugal"], 168, 50), ([], []))
        self.assertEqual(self.pedidos, [])
        atendidas = {c["grupo"] for c in filtros.consultas(filtros.efetivos(cfg)) if vagas.atende(ats, c)}
        self.assertTrue({"remoto", "local", filtros.GLOBAL} <= atendidas)

    def test_vaga_achada_na_nacional_e_nacional(self):  # SC-001
        self.assertEqual(filtros.area_da_vaga({"grupos": ["remoto"], "local": "Remote, Brazil"},
                                              filtros.efetivos(CFG)), ("nacional", None))
        self.assertEqual(filtros.area_da_vaga({"grupos": ["remoto", filtros.GLOBAL], "local": "Anywhere"},
                                              filtros.efetivos(CFG))[0], "nacional")


def antigo(*empresas):
    """config.json de antes da spec 031: a lista dentro de "internacional"."""
    cfg = {k: v for k, v in CFG.items() if k != "empresas"}
    return {**cfg, "internacional": {"ativo": False, "empresas": list(empresas)}}


class TestListaNoNivelDeCima(SemRede):  # US2
    def gravar(self, cfg):
        filtros.CONFIG.write_text(json.dumps(cfg), encoding="utf-8")

    def lido(self):
        return json.loads(filtros.CONFIG.read_text(encoding="utf-8"))

    def test_config_antigo_continua_valendo(self):  # SC-003
        f = filtros.efetivos(antigo(ACME, BETA))
        self.assertEqual(f["empresas"], [ACME, BETA])
        self.assertNotIn("empresas", f["internacional"])
        self.assertIn("2 empresas acompanhadas", filtros.resumo(f))
        self.assertEqual(filtros.efetivos({**antigo(ACME), "empresas": [BETA]})["empresas"], [BETA])  # a de cima vale

    def test_salvar_pelo_front_antigo(self):
        self.gravar(antigo(ACME))
        pedido = {**antigo(), "internacional": {"ativo": False, "empresas": [{"url": ACME["url"]}, BETA["url"]]}}
        filtros.salvar(pedido)
        cfg = self.lido()
        self.assertEqual([e["id"] for e in cfg["empresas"]], ["acme", "beta"])
        self.assertNotIn("empresas", cfg["internacional"])

    def test_salvar_pelo_front_novo(self):
        self.gravar(antigo(ACME))
        filtros.salvar({**antigo(ACME), "empresas": [GAMA["url"]]})  # a lista de cima vale sobre a antiga
        self.assertEqual([e["id"] for e in self.lido()["empresas"]], ["gama"])

    def test_maximo_e_repetida(self):
        lista = filtros.validar({**CFG, "empresas": ["https://job-boards.greenhouse.io/Acme", ACME["url"]]})["empresas"]
        self.assertEqual([e["id"] for e in lista], ["Acme"])
        with self.assertRaisesRegex(ValueError, "no máximo 50"):
            filtros.validar({**CFG, "empresas": [f"https://jobs.lever.co/empresa{i}" for i in range(51)]})

    def test_internacional_ligada_conta_a_lista_de_cima(self):
        inter = {"ativo": True, "termos": ["data engineer"]}
        self.assertEqual(filtros.validar({**CFG, "internacional": inter})["empresas"][0]["id"], "acme")
        with self.assertRaisesRegex(ValueError, "uma empresa para a busca internacional"):
            filtros.validar({**CFG, "empresas": [], "internacional": inter})


class TestBloqueio(SemRede):  # US3, SC-002
    EMPRESAS = {**CFG, "empresas": [ACME, BETA, GAMA, DELTA]}

    def test_429_para_o_sistema_e_os_outros_seguem(self):
        for codigo in (429, 403):
            with self.subTest(codigo=codigo):
                _comum.esquecer()
                self.rede({"boards/acme": codigo, "postings/delta": lever("Remote, Brazil")})
                c = grupos(self.EMPRESAS)["remoto"]
                achadas, erros = ats.buscar(c, 168, 50)
                self.assertEqual(erros, [f"o Greenhouse limitou as consultas (código {codigo}); as outras empresas "
                                         "dele ficam para a próxima busca"])
                self.assertEqual([v["empresa"] for v in achadas], ["Delta"])
                self.assertEqual(ats.buscar({**c, "termo": "senior data engineer"}, 168, 50)[1], [])  # sem novo aviso
                self.assertEqual(len([u for u in self.pedidos if "greenhouse" in u]), 1)  # sem nova tentativa
                self.assertEqual(len([u for u in self.pedidos if "lever" in u]), 1)
                self.assertEqual(self.dormiu, [])

    def test_404_avisa_a_empresa(self):
        self.rede({"boards/acme": 404, "boards/beta": greenhouse("Remote, Brazil"), "boards/gama": greenhouse(),
                   "postings/delta": lever()})
        achadas, erros = ats.buscar(grupos(self.EMPRESAS)["remoto"], 168, 50)
        self.assertEqual(erros, ["a página de vagas de Acme no Greenhouse não existe mais (a empresa pode ter mudado de "
                                 "sistema ou de nome); remova ou troque o link"])
        self.assertEqual(len(achadas), 1)

    def test_outro_erro_nao_para_o_sistema(self):
        self.rede({"boards/acme": 500, "boards/beta": greenhouse("Remote, Brazil"), "boards/gama": greenhouse(),
                   "postings/delta": lever()})
        achadas, erros = ats.buscar(grupos(self.EMPRESAS)["remoto"], 168, 50)
        self.assertEqual(erros, ["Acme (Greenhouse): boards-api.greenhouse.io respondeu 500"])
        self.assertEqual(len(achadas), 1)
        self.assertEqual(len(self.pedidos), 4)

    def test_download_comum_com_e_sem_nova_tentativa(self):
        self.rede({"exemplo.com/a": (429, {"ok": 1}), "exemplo.com/b": (429,)})
        self.assertEqual(_comum.baixar_json("https://exemplo.com/a"), {"ok": 1})
        self.assertEqual(len(self.dormiu), 1)
        with self.assertRaises(_comum.FonteErro) as ctx:
            _comum.baixar_json("https://exemplo.com/b", nova_tentativa=False)
        self.assertEqual(ctx.exception.codigo, 429)
        self.assertEqual(len(self.dormiu), 1)


class TestAcompanhar(SemRede):  # US4 e US5 (lado do servidor)
    LINK_LEVER = "https://jobs.lever.co/delta/00000000-0000-0000-0000-000000000000"

    def setUp(self):
        super().setUp()
        filtros.CONFIG.write_text(json.dumps(CFG), encoding="utf-8")

    def lido(self):
        return json.loads(filtros.CONFIG.read_text(encoding="utf-8"))

    def test_acompanhar(self):
        e, nova, lista = filtros.acompanhar(self.LINK_LEVER)
        self.assertEqual((e["sistema"], e["id"], e["nome"], nova), ("lever", "delta", "Delta", True))
        self.assertEqual([x["id"] for x in self.lido()["empresas"]], ["acme", "delta"])
        e, nova, lista = filtros.acompanhar("https://job-boards.greenhouse.io/ACME/jobs/123")
        self.assertEqual((e["id"], nova, len(lista)), ("acme", False, 2))
        with self.assertRaisesRegex(ValueError, "Greenhouse, do Lever nem do Ashby"):
            filtros.acompanhar("https://exemplo.com/vagas")
        self.assertEqual(self.pedidos, [])  # sem pedido ao sistema

    def test_link_de_candidatura_embutida(self):  # comum no link de candidatura de vagas que vêm do Indeed
        e, nova, _ = filtros.acompanhar("https://boards.greenhouse.io/embed/job_app?for=gama&token=123")
        self.assertEqual((e["sistema"], e["id"], e["url"], nova),
                         ("greenhouse", "gama", "https://job-boards.greenhouse.io/gama", True))

    def test_lista_cheia(self):
        cheia = [{"sistema": "lever", "id": f"e{i}", "nome": f"E{i}", "url": f"https://jobs.lever.co/e{i}"}
                 for i in range(50)]
        filtros.CONFIG.write_text(json.dumps({**CFG, "empresas": cheia}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "lista de empresas está cheia"):
            filtros.acompanhar(self.LINK_LEVER)

    def test_migra_o_config_antigo(self):
        filtros.CONFIG.write_text(json.dumps(antigo(ACME)), encoding="utf-8")
        filtros.acompanhar(BETA["url"])
        cfg = self.lido()
        self.assertEqual([x["id"] for x in cfg["empresas"]], ["acme", "beta"])
        self.assertNotIn("empresas", cfg["internacional"])
        self.assertEqual(cfg["termos"], CFG["termos"])  # os outros filtros ficam como estavam


class TestServidor(SemRede):  # US4
    def setUp(self):
        super().setUp()
        import http.client
        import threading

        import analise
        import banco
        import servidor
        self.http, self.servidor = http.client, servidor
        filtros.CONFIG.write_text(json.dumps(CFG), encoding="utf-8")
        for p in (mock.patch.object(servidor.Handler, "hosts_permitidos", {"127.0.0.1", "localhost"}),
                  mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db"),
                  mock.patch.object(analise, "precisa", return_value=False)):
            p.start()
            self.addCleanup(p.stop)
        self.srv = servidor.ThreadingHTTPServer(("127.0.0.1", 0), servidor.Handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)

    def pedir(self, metodo, caminho, corpo=None):
        con = self.http.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=10)
        self.addCleanup(con.close)
        dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
        con.request(metodo, caminho, dados, {"Content-Type": "application/json"} if dados else {})
        r = con.getresponse()
        return r.status, json.loads(r.read())

    def test_rotas_de_empresas(self):
        status, j = self.pedir("GET", "/api/empresas")
        self.assertEqual((status, [e["id"] for e in j["empresas"]], j["maximo"]), (200, ["acme"], 50))
        status, j = self.pedir("POST", "/api/empresas", {"url": TestAcompanhar.LINK_LEVER})
        self.assertEqual((status, j["nova"], j["empresa"]["id"], len(j["empresas"])), (201, True, "delta", 2))
        self.assertEqual(self.pedir("POST", "/api/empresas", {"url": DELTA["url"]})[0], 200)
        status, j = self.pedir("POST", "/api/empresas", {"url": "https://exemplo.com/vagas"})
        self.assertEqual(status, 400)
        self.assertIn("Greenhouse, do Lever nem do Ashby", j["erro"])

    def test_link_traz_a_empresa(self):
        url = TestAcompanhar.LINK_LEVER
        vaga = ats.normalizar(lever("Remote, Brazil")[0], DELTA)
        with mock.patch.object(self.servidor.link, "ler", return_value=vaga):
            status, j = self.pedir("POST", "/api/vagas/link", {"url": url})
            self.assertEqual(status, 201)
            self.assertEqual({k: j["empresa"][k] for k in ("sistema", "id", "acompanhada")},
                             {"sistema": "lever", "id": "delta", "acompanhada": False})
            self.pedir("POST", "/api/empresas", {"url": url})
            self.assertTrue(self.pedir("POST", "/api/vagas/link", {"url": url})[1]["empresa"]["acompanhada"])
            with mock.patch.object(self.servidor.link, "ler", return_value={**vaga, "id": "web-1"}):
                self.assertNotIn("empresa", self.pedir("POST", "/api/vagas/link",
                                                       {"url": "https://exemplo.com/vaga/1"})[1])


if __name__ == "__main__":
    unittest.main()
