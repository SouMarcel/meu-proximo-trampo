"""LinkedIn na busca (fontes/linkedin.py), com HTML fictício e sem rede: leitura dos cards, parâmetros de cada grupo
(SC-001), sem repetir (SC-002), bloqueio sem nova tentativa (SC-004), sem cookies e descrição só das candidatas
(SC-005), portais na configuração e o contrato com GLOBAL. Spec 015: motivo do bloqueio e espera de 6 horas."""
import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
import urllib.error
from datetime import datetime, timedelta
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
        self.dir_espera = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir_espera, True)
        for p in (mock.patch.object(li, "PAUSA", (0, 0)), mock.patch.object(li.time, "sleep"),
                  mock.patch.object(li, "ARQ_ESPERA", self.dir_espera / ".cache" / "linkedin-espera.json"),
                  mock.patch.object(li, "ARQ_PEDIDOS", self.dir_espera / ".cache" / "linkedin-pedidos.json")):
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
        vagas_, erros = li.buscar(c["local"], 168, 20)
        self.assertEqual(vagas_, [])
        self.assertTrue(erros[0].startswith(li.BLOQUEIO + " (excesso de pedidos); em espera até "), erros)
        self.assertEqual(li.buscar(c["internacional:Portugal"], 168, 20), ([], []))  # sem pedido e sem repetir o aviso
        self.assertEqual(li.descrever({"id": "li-1", "descricao": "da lista"}), "da lista")
        self.assertEqual(len(self.pedidos), 2)
        li.ARQ_ESPERA.unlink()  # passada a espera, a busca seguinte tenta de novo
        _comum.esquecer()
        self.abridor([LISTA])
        self.assertEqual(len(li.buscar(c["remoto"], 168, 20)[0]), 3)

    def test_login_e_999_contam_como_bloqueio(self):  # 015: cada tipo de bloqueio com o seu motivo
        motivos = {302: "pediu login", 999: "costuma ser a rede", 403: "acesso negado (código 403)",
                   401: "acesso negado (código 401)"}
        for codigo, motivo in motivos.items():
            _comum.esquecer()
            li.ARQ_ESPERA.unlink(missing_ok=True)
            self.abridor([codigo])
            vagas_, erros = li.buscar(grupos(CFG)["remoto"], 168, 20)
            self.assertEqual(vagas_, [])
            self.assertTrue(erros[0].startswith(li.BLOQUEIO + " ("), erros)
            self.assertIn(motivo, erros[0])
            self.assertIn("em espera até", erros[0])

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


class TestEspera(TestBloqueio):  # spec 015, US3
    def gravar(self, desde, motivo="excesso de pedidos"):
        li.ARQ_ESPERA.parent.mkdir(parents=True, exist_ok=True)
        dados = {"desde": desde.isoformat(timespec="seconds"), "motivo": motivo}
        li.ARQ_ESPERA.write_text(json.dumps(dados), encoding="utf-8")

    def test_bloqueio_grava_a_espera(self):
        self.abridor([429])
        li.buscar(grupos(CFG)["remoto"], 168, 20)
        dados = json.loads(li.ARQ_ESPERA.read_text(encoding="utf-8"))
        self.assertEqual(dados["motivo"], "excesso de pedidos")
        self.assertLess(abs(datetime.fromisoformat(dados["desde"]) - datetime.now()), timedelta(minutes=1))
        self.assertIsNotNone(li.espera())

    def test_espera_vale_6_horas(self):
        agora = datetime(2026, 10, 15, 12, 0)
        self.gravar(agora - timedelta(hours=1))
        self.assertEqual(li.espera(agora), {"ate": "2026-10-15T17:00", "motivo": "excesso de pedidos"})
        self.gravar(agora - timedelta(hours=6, minutes=1))
        self.assertIsNone(li.espera(agora))

    def test_hora_no_futuro_vale_como_agora(self):
        agora = datetime(2026, 10, 15, 12, 0)
        self.gravar(agora + timedelta(days=3))
        self.assertEqual(li.espera(agora)["ate"], "2026-10-15T18:00")

    def test_arquivo_ilegivel_ou_ausente_sem_espera(self):
        self.assertIsNone(li.espera())
        li.ARQ_ESPERA.parent.mkdir(parents=True, exist_ok=True)
        li.ARQ_ESPERA.write_text("{quebrado", encoding="utf-8")
        self.assertIsNone(li.espera())
        self.assertFalse(li.parada())

    def test_na_espera_nenhum_pedido_e_aviso_uma_vez(self):
        self.gravar(datetime.now() - timedelta(minutes=30), "pediu login")
        self.abridor([])
        c = grupos(CFG)
        vagas_, erros = li.buscar(c["remoto"], 168, 20)
        self.assertEqual(vagas_, [])
        self.assertTrue(erros[0].startswith("LinkedIn em espera até "), erros)
        self.assertIn("(pediu login); ficou de fora desta busca", erros[0])
        self.assertEqual(li.buscar(c["local"], 168, 20), ([], []))
        self.assertEqual(li.descrever({"id": "li-1", "descricao": ""}), "")
        self.assertTrue(li.parada())
        self.assertEqual(self.pedidos, [])
        _comum.esquecer()  # outra busca na espera: o aviso volta uma vez
        self.assertEqual(len(li.buscar(c["remoto"], 168, 20)[1]), 1)

    def test_espera_na_busca_e_no_terminal(self):
        self.gravar(datetime.now() - timedelta(minutes=30))
        for p in (contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO())):
            p.__enter__()
            self.addCleanup(p.__exit__, None, None, None)
        esp = vagas.fontes_em_espera(["linkedin", "indeed"])
        self.assertEqual([(e["nome"], e["portal"], e["motivo"]) for e in esp],
                         [("linkedin", "LinkedIn", "excesso de pedidos")])
        with mock.patch.object(vagas.sys.stdin, "isatty", return_value=False):
            self.assertFalse(vagas.confirmar_espera(["linkedin", "indeed"], False))
            self.assertTrue(vagas.confirmar_espera(["linkedin", "indeed"], True))
            self.assertFalse(vagas.confirmar_espera(["linkedin"], True))  # só ele: não há o que buscar
        with mock.patch.object(vagas.sys.stdin, "isatty", return_value=True):
            with mock.patch("builtins.input", return_value="s"):
                self.assertTrue(vagas.confirmar_espera(["linkedin", "indeed"], False))
            with mock.patch("builtins.input", return_value=""):
                self.assertFalse(vagas.confirmar_espera(["linkedin", "indeed"], False))
            with mock.patch("builtins.input", side_effect=EOFError):  # NUL no Windows: sem ninguém digitando
                self.assertFalse(vagas.confirmar_espera(["linkedin", "indeed"], False))
        li.ARQ_ESPERA.unlink()
        self.assertTrue(vagas.confirmar_espera(["linkedin"], False))


def pagina(inicio, n):
    """Uma página fictícia com n cards (ids a partir de inicio)."""
    card = ('<li><div class="base-card base-search-card" data-entity-urn="urn:li:jobPosting:{n}">'
            '<h3 class="base-search-card__title">Analista de Dados {n}</h3>'
            '<h4 class="base-search-card__subtitle">Empresa {n}</h4>'
            '<span class="job-search-card__location">Brasil</span><time datetime="2026-10-10"></time></div></li>')
    return "".join(card.format(n=inicio + i) for i in range(n))


class TestConsultaCombinada(SemRede):  # spec 015, US1
    def test_expressao_or(self):
        termos = ['"analista de dados"', "designer", "product owner", '"engenheiro de dados', '""']
        [(ts, expr)] = filtros.expressao_or(termos)
        self.assertEqual(expr, '"analista de dados" OR designer OR (product owner) OR (engenheiro de dados)')
        self.assertEqual(ts, termos[:4])  # o vazio sai
        self.assertEqual(filtros.expressao_or(['"analista de dados"']), [(['"analista de dados"'], '"analista de dados"')])
        partes = filtros.expressao_or([f'"cargo numero {i}"' for i in range(10)], maximo=60)
        self.assertGreater(len(partes), 1)
        self.assertTrue(all(len(e) <= 60 for _, e in partes))
        self.assertEqual(sum(len(ts) for ts, _ in partes), 10)

    def test_termos_no_titulo(self):
        termos = ['"analista de dados"', "product owner", "designer"]
        self.assertEqual(filtros.termos_no_titulo("Analista de Dados Sênior", termos), ['"analista de dados"'])
        self.assertEqual(filtros.termos_no_titulo("Owner, Product (remoto)", termos), ["product owner"])
        self.assertEqual(filtros.termos_no_titulo("Dados de Analista", termos), [])  # entre aspas: em sequência
        self.assertEqual(filtros.termos_no_titulo("Designer", termos), ["designer"])

    def test_uma_consulta_por_grupo_so_no_linkedin(self):
        cfg = {**CFG, "termos": ['"analista de dados"', "designer", "product owner"], "internacional": {"ativo": False}}
        plano = filtros.consultas(filtros.efetivos(cfg))
        li_c = vagas.consultas_da_fonte(plano, FONTES["linkedin"])
        self.assertEqual([c["grupo"] for c in li_c], ["remoto", "local"])
        self.assertTrue(all(c["agrupada"] and len(c["termos"]) == 3 for c in li_c))
        self.assertEqual(len(vagas.consultas_da_fonte(plano, FONTES["indeed"])), 6)  # outras: uma por cargo
        self.assertEqual(vagas.contar_consultas(plano, ["linkedin", "indeed"]), 8)
        p = li.parametros(li_c[0], 168)
        self.assertEqual(p["keywords"], '"analista de dados" OR designer OR (product owner)')
        um = vagas.consultas_da_fonte(filtros.consultas(filtros.efetivos({**cfg, "termos": ['"analista de dados"']})),
                                      FONTES["linkedin"])
        self.assertFalse(um[0].get("agrupada"))
        self.assertEqual(li.parametros(um[0], 168)["keywords"], "analista de dados")  # um cargo só: como antes

    def test_ate_3_paginas_na_combinada(self):
        c = {**grupos(CFG)["remoto"], "termos": ["a", "b"], "termo": "a OR b", "agrupada": True}
        self.respostas(lambda url: pagina(int(url.split("start=")[1].split("&")[0]) + 5000000000, 10))
        vs, _ = li.buscar(c, 168, 40)
        self.assertEqual((len(vs), len(self.urls)), (30, 3))
        self.urls.clear()
        self.respostas(lambda url: pagina(6000000000, 10) if "start=0" in url else pagina(6000000100, 4))
        vs, _ = li.buscar(c, 168, 40)
        self.assertEqual((len(vs), len(self.urls)), (14, 2))  # página incompleta: para
        self.urls.clear()
        self.respostas(lambda url: pagina(7000000000, 10))
        li.buscar({**c, "agrupada": False, "termo": "a"}, 168, 40)
        self.assertEqual(len(self.urls), 1)  # um cargo: uma página, como antes

    def test_cargos_da_vaga_na_busca(self):
        self.respostas(lambda url: VAGA if "jobPosting" in url else pagina(8000000000, 3))
        cfg = {**CFG, "fontes": ["linkedin"], "termos": ['"analista de dados"', "designer"],
               "internacional": {"ativo": False},
               "modelos": {"remoto": True}, "localidade": {"pais": "Brasil"}, "tipos_emprego": []}
        with mock.patch.object(vagas, "CACHE", self.dir_espera), \
                mock.patch.object(banco, "ARQUIVO", self.dir_espera / "banco.db"):
            r = vagas.executar(cfg, filtros.efetivos(cfg), ["linkedin"], 40, pausa=0)
        self.assertEqual(r["parametros"]["consultas"], 2)
        buscas = [u for u in self.urls if "jobPosting" not in u]
        self.assertEqual(len(buscas), 1)
        self.assertTrue(all(v["termos"] == ['"analista de dados"'] for v in r["candidatas"]))


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
               "tipos_emprego": [], "janela_horas": 24 * 3650}  # as vagas de exemplo são de 10/2026: a janela não depende do dia
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
        self.assertEqual(filtros.efetivos({})["fontes"], ["indeed", "gupy", "nerdin", "infojobs", "vagascom"])
        nomes = {o["nome"]: o for o in filtros.opcoes()["fontes_nac"]}
        self.assertEqual(list(nomes), ["indeed", "gupy", "nerdin", "infojobs", "vagascom", "linkedin",
                                       "startupjobs"])
        self.assertTrue(nomes["linkedin"]["termos"])
        self.assertIn("MCP_STARTUP_JOBS", nomes["startupjobs"]["precisa"])


class TestPausa(SemRede):  # spec 017: LINKEDIN_PAUSA no .env
    def env(self, valor):
        p = mock.patch.object(li.segredos, "ler", side_effect=lambda nome: valor if nome == li.VAR_PAUSA else "")
        p.start()
        self.addCleanup(p.stop)

    def test_sem_a_variavel_fica_como_antes(self):  # SC-002
        self.env("")
        self.assertEqual(li.pausa(), {"faixa": li.PAUSA, "definida": False, "ajuste": ""})
        self.assertIsNone(li.aviso_pausa(2))

    def test_valores(self):  # SC-003, SC-004
        casos = {"10": ((10, 14), ""), "7,5": ((7.5, 11.5), ""), "7.5": ((7.5, 11.5), ""), "3": ((3, 7), ""),
                 "1": ((3, 7), "mínimo"), "0": ((3, 7), "mínimo"), "-5": ((3, 7), "mínimo"),
                 "500": ((60, 64), "máximo"), "abc": (li.PAUSA, "não é um número"), "nan": (li.PAUSA, "não é um número")}
        for valor, (faixa, ajuste) in casos.items():
            self.env(valor)
            p = li.pausa()
            self.assertEqual(p["faixa"], faixa, valor)
            self.assertTrue(p["definida"])
            self.assertIn(ajuste, p["ajuste"]) if ajuste else self.assertEqual(p["ajuste"], "", valor)
            if p["faixa"] != li.PAUSA:  # o padrão está zerado nestes testes (SemRede); o valor da variável não
                self.assertGreaterEqual(p["faixa"][0], 3)
                self.assertLessEqual(p["faixa"][1], 64)

    def test_aviso(self):
        self.env("10")
        self.assertEqual(li.aviso_pausa(2), "LinkedIn: pausa de 10 a 14 s entre os pedidos (LINKEDIN_PAUSA), "
                                            "até cerca de 5 min só de pausa no LinkedIn.")  # (2 × 3 + 20) × 12 s
        self.env("1")
        self.assertIn("Atenção: LINKEDIN_PAUSA abaixo do mínimo de 3 segundos", li.aviso_pausa(2))
        self.assertIsNone(li.aviso_pausa(0))

    def test_pausa_usada_entre_os_pedidos(self):  # SC-001
        self.env("10")
        _comum.esquecer()
        with mock.patch.object(li.random, "uniform", return_value=12.0) as sorteio:
            li._pausar()
            li._pausar()
        sorteio.assert_called_with(10.0, 14.0)
        self.env("")  # muda o .env: vale na busca seguinte (esquecer), não no meio desta
        with mock.patch.object(li.random, "uniform", return_value=5.0) as sorteio:
            li._pausar()
            self.assertEqual(sorteio.call_args.args, (10.0, 14.0))
            _comum.esquecer()
            li._pausar()
            self.assertEqual(sorteio.call_args.args, li.PAUSA)

    def test_aviso_na_busca(self):
        self.env("10")
        cfg = {**CFG, "fontes": ["linkedin"]}
        f = filtros.efetivos(cfg)
        self.assertIn("pausa de 10 a 14 s", vagas.aviso_pausa(f, ["linkedin"]))
        self.assertIsNone(vagas.aviso_pausa(f, ["indeed"]))  # sem o LinkedIn, sem aviso
        li._bloquear("excesso de pedidos")  # em espera: não há pedidos ao LinkedIn
        self.assertIsNone(vagas.aviso_pausa(f, ["linkedin"]))


if __name__ == "__main__":
    unittest.main()
