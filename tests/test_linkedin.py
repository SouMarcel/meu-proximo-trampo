"""LinkedIn na busca (fontes/linkedin.py), com HTML fictício e sem rede: leitura dos cards, parâmetros de cada grupo
(SC-001), sem repetir (SC-002), bloqueio sem nova tentativa (SC-004), sem cookies e descrição só das candidatas
(SC-005), portais na configuração e o contrato com GLOBAL."""
import json
import shutil
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import banco  # noqa: E402
import filtros  # noqa: E402
import vagas  # noqa: E402
from fontes import FONTES, _comum, linkedin as li  # noqa: E402

DADOS = Path(__file__).resolve().parent / "dados" / "linkedin"
LISTA = (DADOS / "lista.html").read_text(encoding="utf-8")
VAGA = (DADOS / "vaga.html").read_text(encoding="utf-8")
CFG = {"termos": ["analista"], "localidade": {"pais": "Brasil", "estado": "PR", "cidade": "Curitiba", "raio_km": 25},
       "modelos": {"remoto": True, "hibrido": True, "presencial": False}, "tipos_emprego": ["tempo_integral", "pj"],
       "fontes": ["indeed", "linkedin"], "janela_horas": 168,
       "internacional": {"ativo": True, "paises": ["Portugal"], "aceita_mudar": True, "paises_mudanca": ["Alemanha"]}}


def grupos(cfg):
    return {c["grupo"]: c for c in filtros.consultas(filtros.efetivos(cfg))}


class SemRede(unittest.TestCase):
    def setUp(self):
        _comum.esquecer()
        li._estado["ultimo"] = None
        for p in (mock.patch.object(li, "PAUSA", (0, 0)), mock.patch.object(li.time, "sleep")):
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(_comum.esquecer)

    def respostas(self, fn):
        """Substitui o pedido de rede: fn(url) devolve o HTML."""
        self.urls = []

        def baixar(url):
            self.urls.append(url)
            return fn(url)
        p = mock.patch.object(li, "_baixar", side_effect=baixar)
        p.start()
        self.addCleanup(p.stop)


class TestLeitura(SemRede):
    def test_tres_cards(self):
        vs = li.ler_lista(LISTA)
        self.assertEqual([v["id"] for v in vs], ["li-4000000001", "li-4000000002", "li-4000000003"])
        a, b, c = vs
        self.assertEqual((a["titulo"], a["empresa"], a["local"], a["publicada_em"]),
                         ("Analista de Dados", "Empresa Alfa", "São Paulo, São Paulo, Brasil", "2026-10-10"))
        self.assertEqual(a["url"], "https://www.linkedin.com/jobs/view/4000000001/")
        self.assertEqual((b["titulo"], b["empresa"], b["publicada_em"]), ("Data Analyst & BI", "Empresa não informada", "2026-10-11"))
        self.assertEqual((c["titulo"], c["empresa"], c["publicada_em"]), ("Analista de BI (Remoto)", "Empresa Beta", None))
        self.assertEqual(li.ler_lista(""), [])

    def test_mesmo_id_do_link(self):
        import fontes.link as link
        self.assertEqual(link.vaga_linkedin("4000000001", VAGA)["id"], li.ler_lista(LISTA)[0]["id"])

    def test_tipo_emprego(self):
        self.assertEqual(li.tipo_emprego("Contrato"), ["pj"])
        self.assertEqual(li.tipo_emprego("Full-time"), ["tempo_integral"])
        self.assertEqual(li.tipo_emprego("Internship"), ["estagio"])
        self.assertEqual(li.tipo_emprego("Volunteer"), [])


class TestParametros(SemRede):
    def test_seis_grupos(self):  # SC-001
        g = grupos(CFG)
        self.assertEqual(set(g), {"remoto", "local", "internacional:Portugal", "mudanca:Alemanha", "internacional:global"})
        p = {k: li.parametros(c, 168) for k, c in g.items()}
        self.assertEqual((p["remoto"]["location"], p["remoto"]["f_WT"]), ("Brazil", "2"))
        self.assertEqual((p["local"]["location"], p["local"]["f_WT"], p["local"]["distance"]), ("Curitiba, PR, Brazil", "3", 16))
        self.assertEqual((p["internacional:Portugal"]["location"], p["internacional:Portugal"]["f_WT"]), ("Portugal", "2"))
        self.assertEqual((p["mudanca:Alemanha"]["location"], p["mudanca:Alemanha"]["f_WT"]), ("Germany", "1,3"))
        self.assertEqual((p["internacional:global"]["location"], p["internacional:global"]["f_WT"]), ("Worldwide", "1,2,3"))
        for x in p.values():
            self.assertEqual((x["keywords"], x["f_JT"], x["f_TPR"]), ("analista", "F,C", "r604800"))
        self.assertNotIn("distance", p["remoto"])

    def test_remoto_no_pais_e_paises_em_ingles(self):
        cfg = {**CFG, "localidade": {"pais": "Brasil"}, "modelos": {"remoto": True}, "tipos_emprego": [],
               "internacional": {"ativo": True, "paises": ["Estados Unidos", "Reino Unido"]}}
        g = grupos(cfg)
        self.assertEqual((li.parametros(g["remoto"], None)["location"], li.parametros(g["remoto"], None)["f_WT"]), ("Brazil", "2"))
        self.assertNotIn("f_JT", li.parametros(g["remoto"], None))
        self.assertNotIn("f_TPR", li.parametros(g["remoto"], None))
        self.assertEqual(li.parametros(g["internacional:Estados Unidos"], 24)["location"], "United States")
        self.assertEqual(li.parametros(g["internacional:Reino Unido"], 24)["location"], "United Kingdom")
        self.assertEqual(li.parametros(g["internacional:global"], 24)["f_WT"], "2")
        sem_cidade = grupos({**cfg, "modelos": {"remoto": True, "hibrido": True}})  # país inteiro, sem filtro de remoto
        self.assertEqual((li.parametros(sem_cidade["pais"], 24)["location"], li.parametros(sem_cidade["pais"], 24)["f_WT"]),
                         ("Brazil", "2,3"))

    def test_criterios_de_sempre(self):
        f = filtros.efetivos(CFG)
        base = {"plataforma": "LinkedIn", "titulo": "Data Analyst", "empresa": "Empresa Gama", "descricao": "We need SQL.",
                "remoto": False}
        franca = {**base, "id": "li-1", "local": "Paris, Île-de-France, France", "modelo_trabalho": "presencial",
                  "grupos": ["internacional:global"]}
        self.assertTrue(filtros.criterios(franca, f), "presencial fora dos países de mudança")
        alemanha = {**franca, "local": "Berlin, Berlin, Germany", "grupos": ["mudanca:Alemanha"]}
        self.assertEqual(filtros.criterios(alemanha, f), [])
        estagio = {**base, "id": "li-2", "local": "Curitiba, PR, Brasil", "modelo_trabalho": "hibrido", "grupos": ["local"],
                   "tipo_emprego": ["estagio"]}
        self.assertTrue(any(m.startswith("Estágio; você busca") for m in filtros.criterios(estagio, f)))

    def test_grupo_global_so_com_o_linkedin(self):
        sem = {**CFG, "fontes": ["indeed", "gupy"]}
        self.assertNotIn("internacional:global", grupos(sem))
        self.assertIn("internacional:global", grupos(CFG))

    def test_atende_global(self):
        glob = {"area": "internacional", "global": True}
        pais = {"area": "nacional"}
        self.assertTrue(vagas.atende(FONTES["linkedin"], glob) and vagas.atende(FONTES["linkedin"], pais))
        self.assertFalse(vagas.atende(FONTES["indeed"], glob))
        self.assertTrue(vagas.atende(FONTES["indeed"], pais))
        self.assertTrue(vagas.atende(FONTES["remotive"], glob))
        self.assertFalse(vagas.atende(FONTES["remotive"], {"area": "internacional"}))
        self.assertFalse(vagas.atende(FONTES["gupy"], glob))


class TestBuscar(SemRede):
    def test_buscar_e_modelo(self):
        self.respostas(lambda url: LISTA)
        c = grupos(CFG)["internacional:Portugal"]
        vs, erros = li.buscar(c, 168, 20)
        self.assertEqual((len(vs), erros, len(self.urls)), (3, [], 1))  # menos de 25: uma página só
        self.assertTrue(all(v["modelo_trabalho"] == "remoto" and v["remoto"] for v in vs))
        self.assertIn("location=Portugal", self.urls[0])
        vs, _ = li.buscar(grupos(CFG)["mudanca:Alemanha"], 168, 20)
        self.assertNotIn("modelo_trabalho", vs[0])  # dois modelos: fica para o texto e a análise

    def test_pagina_ilegivel(self):
        self.respostas(lambda url: "<li><div class='outra-coisa'>nada</div></li>")
        self.assertEqual(li.buscar(grupos(CFG)["remoto"], 168, 20), ([], [li.ILEGIVEL]))

    def test_descrever(self):
        self.respostas(lambda url: VAGA)
        v = {"id": "li-4000000001", "descricao": ""}
        d = li.descrever(v)
        self.assertIn("SQL avançado", d)
        self.assertIn("Tipo de emprego: Contrato", d)
        self.assertEqual(v["tipo_emprego"], ["pj"])
        self.assertTrue(self.urls[0].endswith("/jobPosting/4000000001"))


class Resposta:
    def __init__(self, corpo):
        self.corpo, self.headers = corpo.encode(), mock.Mock(get_content_charset=lambda: "utf-8")

    def read(self, n):
        return self.corpo

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestBloqueio(SemRede):
    def abridor(self, respostas):
        """build_opener falso: cada pedido devolve o próximo da lista (texto ou código de erro HTTP)."""
        self.pedidos = []
        fila = list(respostas)

        def abrir(req, timeout=None):
            self.pedidos.append(req)
            r = fila.pop(0)
            if isinstance(r, int):
                raise urllib.error.HTTPError(req.full_url, r, "x", {}, None)
            return Resposta(r)
        p = mock.patch.object(li.urllib.request, "build_opener", return_value=mock.Mock(open=abrir))
        p.start()
        self.addCleanup(p.stop)

    def test_429_para_o_resto_da_busca(self):  # SC-004
        self.abridor([LISTA, 429])
        c = grupos(CFG)
        self.assertEqual(len(li.buscar(c["remoto"], 168, 20)[0]), 3)
        self.assertEqual(li.buscar(c["local"], 168, 20), ([], [li.BLOQUEIO]))
        self.assertEqual(li.buscar(c["internacional:Portugal"], 168, 20), ([], []))  # sem pedido e sem repetir o aviso
        self.assertEqual(li.descrever({"id": "li-1", "descricao": "da lista"}), "da lista")
        self.assertEqual(len(self.pedidos), 2)
        _comum.esquecer()  # a busca seguinte tenta de novo
        self.abridor([LISTA])
        self.assertEqual(len(li.buscar(c["remoto"], 168, 20)[0]), 3)

    def test_login_e_999_contam_como_bloqueio(self):
        for codigo in (302, 999):
            _comum.esquecer()
            self.abridor([codigo])
            self.assertEqual(li.buscar(grupos(CFG)["remoto"], 168, 20), ([], [li.BLOQUEIO]))

    def test_outro_erro_nao_bloqueia(self):
        self.abridor([500, LISTA])
        c = grupos(CFG)["remoto"]
        self.assertEqual(li.buscar(c, 168, 20), ([], ["o LinkedIn respondeu 500"]))
        self.assertEqual(len(li.buscar(c, 168, 20)[0]), 3)

    def test_sem_cookies(self):  # SC-005
        self.abridor([LISTA])
        li.buscar(grupos(CFG)["remoto"], 168, 20)
        cab = {k.lower() for k in self.pedidos[0].headers}
        self.assertNotIn("cookie", cab)
        self.assertNotIn("authorization", cab)


class TestNaBusca(SemRede):
    def setUp(self):
        super().setUp()
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for p in (mock.patch.object(vagas, "CACHE", self.tmp / ".cache"), mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db")):
            p.start()
            self.addCleanup(p.stop)

    def test_sem_repetir_e_descricao_so_das_candidatas(self):  # SC-002, SC-005
        banco.criar_de_link({"id": "li-4000000001", "plataforma": "LinkedIn", "titulo": "Analista de Dados", "empresa": "Empresa Alfa",
                             "local": "São Paulo", "url": "https://www.linkedin.com/jobs/view/4000000001/", "descricao": "x"})
        self.respostas(lambda url: VAGA if "jobPosting" in url else LISTA)
        cfg = {**CFG, "fontes": ["linkedin"], "internacional": {"ativo": False}, "modelos": {"remoto": True}, "localidade": {"pais": "Brasil"},
               "tipos_emprego": []}
        r = vagas.executar(cfg, filtros.efetivos(cfg), ["linkedin"], 20, pausa=0)
        ids = [v["id"] for v in r["candidatas"] + r["fora"]]
        self.assertEqual(sorted(ids), ["li-4000000002", "li-4000000003"])  # a do link não volta
        lidas = [u for u in self.urls if "jobPosting" in u]
        self.assertEqual(sorted(u.rsplit("/", 1)[1] for u in lidas), ["4000000002", "4000000003"])

    def test_desligado_nenhum_pedido(self):  # SC-003
        self.respostas(lambda url: LISTA)
        cfg = {**CFG, "fontes": ["indeed"]}
        self.assertNotIn("linkedin", vagas.fontes_da_busca(cfg, filtros.efetivos(cfg)))
        self.assertEqual(self.urls, [])


class TestConfig(unittest.TestCase):
    BASE = {"termos": ["analista"], "localidade": {"pais": "Brasil"}, "modelos": {"remoto": True}}

    def test_validar_portais(self):
        self.assertEqual(filtros.validar({**self.BASE, "fontes": ["linkedin", "indeed"]})["fontes"], ["indeed", "linkedin"])
        self.assertNotIn("fontes", filtros.validar(self.BASE))  # sem a chave, o config mantém a lista dele
        with self.assertRaises(ValueError):
            filtros.validar({**self.BASE, "fontes": []})
        with self.assertRaises(ValueError):
            filtros.validar({**self.BASE, "fontes": ["orkut"]})
        self.assertEqual(filtros.validar({**self.BASE, "fontes": ["linkedin", "orkut"]})["fontes"], ["linkedin"])

    def test_padrao_e_opcoes(self):
        self.assertEqual(filtros.efetivos({})["fontes"], ["indeed", "gupy"])
        nomes = {o["nome"]: o for o in filtros.opcoes()["fontes_nac"]}
        self.assertEqual(list(nomes), ["indeed", "gupy", "linkedin", "startupjobs"])
        self.assertTrue(nomes["linkedin"]["termos"])
        self.assertIn("MCP_STARTUP_JOBS", nomes["startupjobs"]["precisa"])


if __name__ == "__main__":
    unittest.main()
