"""Testes das fontes do exterior (fontes/*.py), das consultas globais e do Adicionar Vaga com Greenhouse, Lever
e Ashby, com as respostas reais gravadas em tests/dados/ (a rede é substituída)."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import filtros  # noqa: E402
import vagas  # noqa: E402
from fontes import FONTES, _comum, ats, link  # noqa: E402

DADOS = Path(__file__).resolve().parent / "dados"
ARQUIVOS = {"remotive.com": "remotive.json", "himalayas.app": "himalayas.json", "remoteok.com": "remoteok.json",
            "jobicy.com": "jobicy.json", "weworkremotely.com": "weworkremotely.rss", "getonbrd.com": "getonboard.json",
            "greenhouse.io": "greenhouse.json", "lever.co": "lever.json", "ashbyhq.com": "ashby.json"}
EMPRESAS = [{"sistema": "greenhouse", "id": "gitlab", "nome": "GitLab", "url": "https://job-boards.greenhouse.io/gitlab"},
            {"sistema": "lever", "id": "spotify", "nome": "Spotify", "url": "https://jobs.lever.co/spotify"},
            {"sistema": "ashby", "id": "openai", "nome": "OpenAI", "url": "https://jobs.ashbyhq.com/openai"}]
JANELA = 24 * 365 * 5  # as amostras têm vagas antigas


def gravada(url, params=None, aceitar=None):
    for site, arq in ARQUIVOS.items():
        if site in url:
            return (DADOS / arq).read_bytes()
    raise AssertionError(f"consulta inesperada: {url}")


class ComRede(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.pasta, True)
        for alvo, valor in (("PASTA", self.pasta), ("INTERVALO", 0)):
            p = mock.patch.object(_comum, alvo, valor)
            p.start()
            self.addCleanup(p.stop)
        self.chamadas = []

        def baixar(url, params=None, aceitar="application/json"):
            self.chamadas.append(url)
            return gravada(url)
        p = mock.patch.object(_comum, "baixar", side_effect=baixar)
        p.start()
        self.addCleanup(p.stop)
        _comum.esquecer()
        self.addCleanup(_comum.esquecer)

    def buscar(self, nome, termo, remoto=True, por_termo=50):
        c = {"termo": termo, "remoto": remoto, "global": True, "area": "internacional", "empresas": EMPRESAS}
        return FONTES[nome].buscar(c, JANELA, por_termo)


class TestComum(unittest.TestCase):
    def test_bate_cargo(self):
        self.assertTrue(_comum.bate_cargo("Senior Data Engineer (Remote)", "data engineer"))
        self.assertTrue(_comum.bate_cargo("Engineer, Data Platform", "data engineer"))  # palavras em qualquer ordem
        self.assertFalse(_comum.bate_cargo("Engineer, Data Platform", '"data engineer"'))  # frase exata
        self.assertTrue(_comum.bate_cargo("Lead Data Engineer", '"data engineer"'))
        self.assertFalse(_comum.bate_cargo("Data Analyst", "data engineer"))
        self.assertTrue(_comum.bate_cargo("Analista de Dados Sênior", "analista de dados senior"))
        self.assertFalse(_comum.bate_cargo("Dataengineer", "data engineer"))
        self.assertFalse(_comum.bate_cargo("Qualquer", ""))

    def test_datas_salario_id(self):
        self.assertEqual(_comum.data_iso(1791579860), "2026-10-09")
        self.assertEqual(_comum.data_iso(1782214185805), "2026-06-23")  # milissegundos
        self.assertEqual(_comum.data_iso("2026-10-02T11:31:50-04:00"), "2026-10-02")
        self.assertEqual(_comum.data_iso("Fri, 09 Oct 2026 17:46:45 +0000"), "2026-10-09")
        self.assertIsNone(_comum.data_iso("ontem"))
        self.assertEqual(_comum.salario(100000, 150000, "usd", "per-year-salary"), "US$ 100.000–150.000/ano")
        self.assertEqual(_comum.salario(2000, None, "USD", "month"), "US$ 2.000/mês")
        self.assertEqual(_comum.salario(50, 70, "EUR", "1 HOUR"), "€ 50–70/hora")
        self.assertIsNone(_comum.salario(0, 0, "USD", "year"))
        longo = _comum.ident("getonboard", "senior-java-developer-odbc-jdbc-bi-connectors-improving-remote")
        self.assertLessEqual(len(longo), 64)
        self.assertEqual(longo, _comum.ident("getonboard", "senior-java-developer-odbc-jdbc-bi-connectors-improving-remote"))
        self.assertEqual(_comum.ident("remotive", 123), "remotive-123")
        self.assertEqual(_comum.consertar("Telefondienst fÃ¼r"), "Telefondienst für")
        self.assertEqual(_comum.consertar("São Paulo"), "São Paulo")

    def test_salario_com_travessao(self):
        self.assertEqual(filtros.salario_anual_usd({"salario": "US$ 100.000–150.000/ano"}), 150000)
        self.assertEqual(filtros.salario_anual_usd({"salario": "US$ 50–70/hora"}), 70 * 2080)


class TestConsultas(unittest.TestCase):
    BASE = {"termos": ["analista"], "localidade": {"pais": "Brasil"}, "modelos": {"remoto": True}}

    def efet(self, **inter):
        return filtros.efetivos({**self.BASE, "internacional": {"ativo": True, "termos": ["data engineer", "analyst"],
                                                                 **inter}})

    def test_globais_so_com_fonte_ou_empresa(self):
        self.assertFalse([c for c in filtros.consultas(self.efet(paises=["Portugal"])) if c.get("global")])
        f = self.efet(fontes=["remotive", "inexistente"], empresas=EMPRESAS[:1])
        self.assertEqual(f["internacional"]["fontes"], ["remotive"])
        globais = [c for c in filtros.consultas(f) if c.get("global")]
        self.assertEqual([c["termo"] for c in globais], ["data engineer", "analyst"])
        self.assertTrue(all(c["grupo"] == filtros.GLOBAL and c["remoto"] and c["empresas"] == EMPRESAS[:1]
                            for c in globais))
        self.assertIn("fontes do exterior: Remotive", filtros.resumo(f))
        self.assertIn("1 empresa acompanhada", filtros.resumo(f))
        # quem aceita morar fora recebe também as presenciais e híbridas das fontes do exterior
        self.assertFalse(filtros.consultas(self.efet(fontes=["remotive"], aceita_mudar=True))[-1]["remoto"])
        # busca internacional desligada: nada do exterior
        f = filtros.efetivos({**self.BASE, "internacional": {"ativo": False, "fontes": ["remotive"]}})
        self.assertFalse([c for c in filtros.consultas(f) if c["area"] == "internacional"])

    def test_fontes_da_busca_e_por_pais(self):
        f = self.efet(fontes=["remotive", "jobicy"], empresas=EMPRESAS)
        self.assertEqual(vagas.fontes_da_busca({"fontes": ["indeed"]}, f), ["indeed", "remotive", "jobicy", "ats"])
        self.assertEqual(vagas.fontes_da_busca({"fontes": ["indeed"]}, self.efet(paises=["Portugal"])), ["indeed"])
        por_pais = SimpleNamespace(AREAS=("nacional", "internacional"))
        global_ = SimpleNamespace(AREAS=("internacional",), POR_PAIS=False)
        pais = {"area": "internacional", "grupo": "internacional:Portugal"}
        glob = {"area": "internacional", "grupo": filtros.GLOBAL, "global": True}
        nac = {"area": "nacional", "grupo": "remoto"}
        self.assertEqual([vagas.atende(por_pais, c) for c in (pais, glob, nac)], [True, False, True])
        self.assertEqual([vagas.atende(global_, c) for c in (pais, glob, nac)], [False, True, False])

    def test_config_valida_fontes_empresas_frases(self):
        base = {**self.BASE, "localidade": {"pais": "Brasil"}, "modelos": {"remoto": True}}
        cfg = filtros.validar({**base, "internacional": {
            "ativo": True, "termos": ["data engineer"], "fontes": ["jobicy", "remotive"],
            "empresas": ["https://jobs.lever.co/spotify/2193db3f-77c5-43b8-b030-8f92c9882bf1",
                         {"url": "boards.greenhouse.io/gitlab", "nome": "GitLab"}, "https://jobs.lever.co/spotify"],
            "frases_restricao": ["Must be in the office", " "], "frases_positivas": ["Brazil welcome"]}})
        inter = cfg["internacional"]
        self.assertEqual(inter["fontes"], ["remotive", "jobicy"])  # na ordem do catálogo
        self.assertEqual([(e["sistema"], e["id"], e["nome"]) for e in inter["empresas"]],
                         [("lever", "spotify", "Spotify"), ("greenhouse", "gitlab", "GitLab")])
        self.assertEqual(inter["frases_restricao"], ["Must be in the office"])
        with self.assertRaisesRegex(ValueError, "Greenhouse, do Lever nem do Ashby"):
            filtros.validar({**base, "internacional": {"ativo": True, "termos": ["x"], "empresas": ["https://empresa.com/vagas"]}})
        with self.assertRaisesRegex(ValueError, "fonte internacional"):
            filtros.validar({**base, "internacional": {"ativo": True, "termos": ["x"], "fontes": ["linkedin"]}})
        with self.assertRaisesRegex(ValueError, "no máximo 30"):
            filtros.validar({**base, "internacional": {"frases_positivas": [f"frase {i}" for i in range(31)]}})
        with self.assertRaisesRegex(ValueError, "uma fonte do exterior"):
            filtros.validar({**base, "internacional": {"ativo": True, "termos": ["x"]}})
        nomes = [x["nome"] for x in filtros.opcoes()["fontes_int"]]
        self.assertEqual(nomes, list(filtros.FONTES_INT))
        self.assertTrue(all(x["termos"] for x in filtros.opcoes()["fontes_int"]))

    def test_area_da_vaga_global(self):
        f = self.efet(fontes=["remotive"])
        g = [filtros.GLOBAL]
        self.assertEqual(filtros.area_da_vaga({"grupos": g, "restricao_local": "USA"}, f), ("internacional", "Estados Unidos"))
        self.assertEqual(filtros.area_da_vaga({"grupos": g, "restricao_local": "Worldwide"}, f), ("internacional", "mundo todo"))
        self.assertEqual(filtros.area_da_vaga({"grupos": g, "local": "Remoto"}, f), ("internacional", "mundo todo"))
        self.assertEqual(filtros.area_da_vaga({"grupos": [*g, "internacional:Portugal"]}, f), ("internacional", "Portugal"))


class TestFontes(ComRede):
    def test_remotive(self):
        vs, erros = self.buscar("remotive", "engineer")
        self.assertEqual(erros, [])
        self.assertEqual([v["id"] for v in vs], ["remotive-2091045", "remotive-2091149"])
        v = vs[1]
        self.assertEqual(v["plataforma"], "Remotive")
        self.assertTrue(v["restricao_local"].startswith("USA, UK, India"))
        self.assertEqual(v["salario"], "$45-$120/Hour")
        self.assertTrue(v["url"].startswith("https://remotive.com/remote-jobs/"))
        self.assertNotIn("<", v["descricao"])
        # a lista fica guardada em disco: outra busca no mesmo dia não consulta a Remotive de novo
        _comum.esquecer()
        self.buscar("remotive", "engineer")
        self.assertEqual(len([u for u in self.chamadas if "remotive" in u]), 1)

    def test_himalayas(self):
        vs, _ = self.buscar("himalayas", "administrator")
        v = vs[0]
        self.assertEqual((v["titulo"], v["empresa"]), ("CMMS System Administrator", vs[0]["empresa"]))
        self.assertEqual((v["restricao_local"], v["moeda"], v["salario"]), ("United States", "USD", "US$ 55.250–65.000/ano"))
        self.assertLessEqual(len(v["id"]), 64)
        self.assertEqual(len({x["id"] for x in self.buscar("himalayas", "a")[0]}), len(self.buscar("himalayas", "a")[0]))

    def test_remoteok(self):
        vs, _ = self.buscar("remoteok", "telefondienst")
        self.assertEqual(vs[0]["titulo"][:18], "Telefondienst für ")  # texto com acentuação quebrada consertado
        self.assertEqual(self.buscar("remoteok", "project manager")[0][0]["restricao_local"], "Worldwide")
        self.assertFalse(any(v["id"] == "remoteok-None" for v in self.buscar("remoteok", "a")[0]))  # pula o aviso legal

    def test_jobicy(self):
        vs, _ = self.buscar("jobicy", "product manager")
        self.assertEqual(vs[0]["empresa"], "Juniper Square")
        self.assertEqual((vs[0]["restricao_local"], vs[0]["moeda"]), ("Canada, USA", "USD"))
        self.assertEqual(vs[0]["salario"], "US$ 230.000–300.000/ano")
        self.assertEqual(filtros.salario_anual_usd(vs[0]), 300000)

    def test_weworkremotely(self):
        vs, _ = self.buscar("weworkremotely", "customer success manager")
        self.assertEqual((vs[0]["titulo"], vs[0]["empresa"]), ("Customer Success Manager", "RETR"))
        self.assertEqual(vs[0]["restricao_local"], "Anywhere in the World")
        self.assertEqual(vs[0]["publicada_em"], "2026-10-09")
        self.assertTrue(vs[0]["url"].startswith("https://weworkremotely.com/remote-jobs/"))

    def test_getonboard(self):
        vs, _ = self.buscar("getonboard", "java developer")
        self.assertEqual([v["empresa"] for v in vs], ["23people", "Improving"])
        self.assertEqual((vs[0]["salario"], vs[0]["moeda"]), ("US$ 2.000–2.200/mês", "USD"))
        self.assertTrue(all(len(v["id"]) <= 64 for v in vs))
        # o híbrido em Santiago só vem para quem aceita morar fora (consulta sem o filtro de remoto)
        self.assertEqual(self.buscar("getonboard", "actuario")[0], [])
        hibrida = self.buscar("getonboard", "actuario", remoto=False)[0][0]
        self.assertEqual((hibrida["remoto"], hibrida["restricao_local"], hibrida["modelo_trabalho"]), (False, "Chile", "hibrido"))
        self.assertIn("modelo híbrido", hibrida["descricao"])

    def test_empresas(self):
        vs, erros = self.buscar("ats", "engineer", remoto=False)
        self.assertEqual(erros, [])
        por = {v["ats"]: v for v in vs}
        self.assertEqual(set(por), {"lever", "ashby"})
        lever = por["lever"]
        self.assertEqual((lever["plataforma"], lever["empresa"], lever["remoto"]), ("Lever", "Spotify", False))
        self.assertEqual(lever["modelo_trabalho"], "hibrido")
        self.assertTrue(lever["url_candidatura"].endswith("/apply"))
        self.assertIn("What You'll Do", lever["descricao"])
        ashby = next(v for v in vs if v["titulo"] == "Research Engineer")
        self.assertEqual((ashby["salario"], ashby["moeda"]), ("US$ 250.000–445.000/ano", "USD"))
        gh, _ = self.buscar("ats", "account executive")
        self.assertEqual((gh[0]["restricao_local"], gh[0]["idioma"], gh[0]["empresa"]), ("Remote, France", "en", "GitLab"))
        self.assertTrue(gh[0]["remoto"])
        # uma consulta por empresa na busca, por mais cargos que haja
        self.assertEqual(len([u for u in self.chamadas if "lever" in u]), 1)

    def test_fonte_fora_do_ar_nao_derruba_as_outras(self):
        def baixar(url, params=None, aceitar=None):
            if "remotive" in url or "lever" in url:
                raise _comum.FonteErro("remotive.com respondeu 503")
            return gravada(url)
        with mock.patch.object(_comum, "baixar", side_effect=baixar):
            self.assertEqual(self.buscar("remotive", "engineer"), ([], ["remotive.com respondeu 503"]))
            self.assertEqual(self.buscar("remotive", "manager"), ([], []))  # o erro sai uma vez só na busca
            vs, erros = self.buscar("ats", "engineer", remoto=False)
            self.assertEqual(erros, ["Spotify (Lever): remotive.com respondeu 503"])
            self.assertTrue(vs)  # o Ashby seguiu
            self.assertTrue(self.buscar("jobicy", "manager")[0])


class TestReconhecer(unittest.TestCase):
    def test_tres_sistemas_e_outro(self):
        casos = {
            "https://boards.greenhouse.io/gitlab": ("greenhouse", "gitlab", "https://job-boards.greenhouse.io/gitlab"),
            "https://job-boards.greenhouse.io/gitlab/jobs/8860302002": ("greenhouse", "gitlab", "https://job-boards.greenhouse.io/gitlab"),
            "https://boards.greenhouse.io/embed/job_board?for=acme": ("greenhouse", "acme", "https://job-boards.greenhouse.io/acme"),
            "jobs.lever.co/spotify": ("lever", "spotify", "https://jobs.lever.co/spotify"),
            "https://jobs.eu.lever.co/empresa/": ("lever", "empresa", "https://jobs.eu.lever.co/empresa"),
            "https://jobs.ashbyhq.com/openai/8fb1615c-34bf-47c4-a1d1-b7b2f836bbd3": ("ashby", "openai", "https://jobs.ashbyhq.com/openai"),
        }
        for url, (sistema, slug, normal) in casos.items():
            e = ats.reconhecer(url)
            self.assertEqual((e["sistema"], e["id"], e["url"]), (sistema, slug, normal), url)
        for url in ("https://empresa.com/carreiras", "https://jobs.lever.co/", "ftp://jobs.lever.co/x", ""):
            with self.assertRaises(ValueError, msg=url):
                ats.reconhecer(url)
        self.assertEqual(ats.vaga_do_link("https://job-boards.greenhouse.io/gitlab/jobs/8860302002")[1], "8860302002")
        self.assertIsNone(ats.vaga_do_link("https://jobs.lever.co/spotify"))


class TestAdicionarVaga(ComRede):
    def ler(self, url, resposta):
        with mock.patch.object(_comum, "baixar", return_value=json.dumps(resposta).encode("utf-8")):
            return link.ler(url)

    def test_lever_greenhouse_ashby(self):
        lever = json.loads((DADOS / "lever.json").read_text(encoding="utf-8"))[0]
        v = self.ler(lever["hostedUrl"], lever)
        self.assertEqual((v["plataforma"], v["ats"], v["empresa"]), ("Lever", "lever", "Spotify"))
        self.assertEqual(v["id"], "lever-spotify-2193db3f-77c5-43b8-b030-8f92c9882bf1")
        self.assertTrue(v["url_candidatura"].endswith("/apply"))
        gh = json.loads((DADOS / "greenhouse.json").read_text(encoding="utf-8"))["jobs"][0]
        v = self.ler(gh["absolute_url"], gh)
        self.assertEqual((v["plataforma"], v["titulo"], v["restricao_local"]), ("Greenhouse", gh["title"], "Remote, France"))
        ashby = json.loads((DADOS / "ashby.json").read_text(encoding="utf-8"))
        v = self.ler(ashby["jobs"][0]["jobUrl"], ashby)
        self.assertEqual((v["plataforma"], v["titulo"]), ("Ashby", ashby["jobs"][0]["title"]))

    def test_plataformas_novas(self):
        for host, nome in (("remotive.com", "Remotive"), ("himalayas.app", "Himalayas"), ("remoteok.com", "RemoteOK"),
                           ("jobicy.com", "Jobicy"), ("weworkremotely.com", "We Work Remotely"),
                           ("www.getonbrd.com", "Get on Board"), ("job-boards.greenhouse.io", "Greenhouse"),
                           ("jobs.lever.co", "Lever"), ("jobs.ashbyhq.com", "Ashby")):
            self.assertEqual(link.plataforma(host), nome)
            import banco
            self.assertIn(nome, banco.PLATAFORMAS)


if __name__ == "__main__":
    unittest.main()
