"""InfoJobs na busca (fontes/infojobs.py), com HTML fictício e sem rede (spec 026): leitura dos cards, filtro de data
pela URL, cargo, grupo e cidade, uma leitura por lista, descrição pela página da vaga, bloqueio com espera de 24 horas
(SC-005), link no Adicionar Vaga e o portal ligado por padrão (SC-001)."""
import shutil
import sys
import tempfile
import unittest
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import banco  # noqa: E402
import filtros  # noqa: E402
import vagas  # noqa: E402
from fontes import FONTES, _comum, infojobs, link  # noqa: E402

DADOS = Path(__file__).resolve().parent / "dados" / "infojobs"
LISTA = (DADOS / "lista.html").read_text(encoding="utf-8")
VAGA = (DADOS / "vaga.html").read_text(encoding="utf-8")
HOME_OFFICE = (DADOS / "home-office.html").read_text(encoding="utf-8")  # a lista de home office: cards sem o modelo
SEM_JSONLD = (DADOS / "vaga-sem-jsonld.html").read_text(encoding="utf-8")  # página de vaga sem o JobPosting
HOJE = datetime(2026, 10, 23, 12, tzinfo=timezone.utc)
CFG = {"termos": ["analista de dados"], "localidade": {"pais": "Brasil", "estado": "SP", "cidade": "São Paulo",
                                                      "raio_km": 25},
       "modelos": {"remoto": True, "hibrido": True, "presencial": True}, "tipos_emprego": [],
       "fontes": ["infojobs"], "janela_horas": 168, "internacional": {"ativo": False}}


def grupos(cfg):
    return {c["grupo"]: c for c in filtros.consultas(filtros.efetivos(cfg))}


def numeros(lista):
    return [int(v["id"].removeprefix("infojobs-")) for v in lista]


class Resposta:
    def __init__(self, corpo, final="https://www.infojobs.com.br/empregos.aspx"):
        self.corpo, self.final = corpo.encode(), final
        self.headers = mock.Mock(get_content_charset=lambda: "utf-8")

    def read(self, n):
        return self.corpo

    def geturl(self):
        return self.final

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class SemRede(unittest.TestCase):
    def setUp(self):
        _comum.esquecer()
        infojobs._estado["ultimo"] = None
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for p in (mock.patch.object(infojobs, "PAUSA", (0, 0)), mock.patch.object(infojobs.time, "sleep"),
                  mock.patch.object(infojobs, "_agora", return_value=HOJE),
                  mock.patch.object(infojobs, "ARQ_ESPERA", self.tmp / ".cache" / "infojobs-espera.json")):
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(_comum.esquecer)

    def respostas(self, fn=lambda url: HOME_OFFICE if "home-office" in url else LISTA):
        """Substitui o pedido de rede: fn(url) devolve o HTML."""
        self.urls = []

        def baixar(url):
            self.urls.append(url)
            return fn(url)
        p = mock.patch.object(infojobs, "_baixar", side_effect=baixar)
        p.start()
        self.addCleanup(p.stop)

    def abridor(self, respostas):
        """urlopen falso: cada pedido devolve o próximo da lista (Resposta, texto ou código de erro HTTP)."""
        self.pedidos = []
        fila = list(respostas)

        def abrir(req, timeout=None):
            self.pedidos.append(req)
            r = fila.pop(0)
            if isinstance(r, int):
                raise urllib.error.HTTPError(req.full_url, r, "x", {}, None)
            return r if isinstance(r, Resposta) else Resposta(r)
        p = mock.patch.object(_comum.urllib.request, "urlopen", side_effect=abrir)
        p.start()
        self.addCleanup(p.stop)


class TestLeitura(SemRede):
    def test_cards(self):
        vs = infojobs.ler_lista(LISTA)
        self.assertEqual(numeros(vs), [70001, 70002, 70003, 70004, 70005, 70006])  # a repetida sai uma vez
        v = vs[0]
        self.assertEqual((v["titulo"], v["empresa"], v["local"], v["modelo_trabalho"], v["remoto"]),
                         ("Analista de Dados Pleno", "Confidencial", "São Paulo, SP", "presencial", False))
        self.assertEqual((v["salario"], v["publicada_em"], v["tipo"], v["plataforma"]),
                         ("R$ 5.000,00 a R$ 6.000,00", "2026-10-22", "Entre 3 e 5 anos • Ensino Superior", "InfoJobs"))
        self.assertEqual(v["url"], "https://www.infojobs.com.br/vaga-de-analista-de-dados-pleno-em-sao-paulo__70001.aspx")
        self.assertEqual(v["descricao"], "")
        self.assertEqual((vs[1]["empresa"], vs[1]["titulo"], vs[1]["modelo_trabalho"]),
                         ("Exemplo Tecnologia Ltda", "Analista de Dados Sênior", "hibrido"))
        self.assertEqual((vs[2]["remoto"], vs[2]["modelo_trabalho"], vs[2]["salario"]), (True, "remoto", None))
        self.assertNotIn("Km", " ".join(x["local"] for x in vs))  # o texto oculto fica de fora

    def test_filtro_de_data_pela_url(self):
        self.assertEqual([infojobs.antiguidade(h) for h in (24, 72, 168, 360, 720)], [2, 2, 3, 4, 5])
        self.assertEqual(infojobs.url_lista("analista de dados", 168),
                         "https://www.infojobs.com.br/empregos.aspx?palabra=analista+de+dados&Antiguedad=3")
        self.assertEqual(infojobs.url_lista("Analista de Dados", 24, "São Paulo"),
                         "https://www.infojobs.com.br/vagas-de-emprego-analista+de+dados-em-sao-paulo.aspx?Antiguedad=2")
        self.assertEqual(infojobs.url_lista("analista de dados", 72, remoto=True),  # o endereço que o próprio site monta
                         "https://www.infojobs.com.br/vagas-de-emprego-analista+de+dados-trabalho-home-office.aspx?Antiguedad=2")
        # filtro de modelo (idw) com os modelos marcados; todos ou nenhum = sem filtro
        casos = {("presencial",): "&idw=1", ("hibrido",): "&idw=3", ("presencial", "hibrido"): "&idw=1,3",
                 ("remoto", "hibrido", "presencial"): "", (): ""}
        for modelos, esperado in casos.items():
            url = infojobs.url_lista("analista de dados", 168, "São Paulo", modelos=list(modelos))
            self.assertTrue(url.endswith("?Antiguedad=3" + esperado), (modelos, url))
        self.assertTrue(infojobs.url_lista("analista de dados", 168, modelos=["presencial"]).endswith("&Antiguedad=3&idw=1"))

    def test_remoto_pela_lista_de_home_office(self):
        self.respostas()
        c = grupos(CFG)
        remoto, erros = infojobs.buscar(c["remoto"], 168, 20)
        self.assertEqual((numeros(remoto), erros), ([70001, 70002, 70003, 70004, 70006], []))  # 70005: antes da janela
        self.assertTrue(all(v["remoto"] and v["modelo_trabalho"] == "remoto" for v in remoto))  # o card não diz
        self.assertEqual(remoto[3]["local"], "Remoto")  # "Todo Brasil"
        self.assertEqual(remoto[0]["local"], "São Paulo, SP")  # a cidade da empresa fica
        local, _ = infojobs.buscar(c["local"], 168, 20)
        self.assertEqual(numeros(local), [70001, 70002])  # SP (cidade e estado), da lista da cidade
        self.assertEqual(len(self.urls), 2)  # a lista de home office e a da cidade
        self.assertIn("-trabalho-home-office.aspx?Antiguedad=3", self.urls[0])
        self.assertIn("-em-sao-paulo.aspx", self.urls[1])
        infojobs.buscar(c["remoto"], 168, 20)
        self.assertEqual(len(self.urls), 2)  # a mesma lista não é pedida de novo na busca

    def test_todo_brasil_e_remoto(self):
        vs = {v["id"]: v for v in infojobs.ler_lista(LISTA.replace("Rio de Janeiro - RJ", "Todo Brasil"))}
        self.assertEqual((vs["infojobs-70006"]["local"], vs["infojobs-70006"]["remoto"]), ("Remoto", True))

    def test_pagina_sem_jsonld(self):  # vagas "Todo Brasil" costumam vir sem o JobPosting
        v = infojobs.ler_pagina(SEM_JSONLD)
        self.assertEqual((v["titulo"], v["empresa"], v["local"], v["remoto"], v["salario"]),
                         ("Analista de Dados Remoto", "Empresa Exemplo Remota Ltda", "Remoto", True,
                          "R$ 7.000,00 a R$ 8.000,00"))
        self.assertIn("SQL avançado", v["descricao"])
        self.respostas(lambda url: SEM_JSONLD)
        self.assertIn("100% remota", infojobs.descrever({"url": "https://www.infojobs.com.br/vaga-de-x-em-__70004.aspx"}))
        url = "https://www.infojobs.com.br/vaga-de-analista-de-dados-remoto-em-__70004.aspx"
        with mock.patch.object(link, "_baixar", return_value=SEM_JSONLD):
            lida = link.ler(url)  # o Adicionar Vaga também lê a página
        self.assertEqual((lida["id"], lida["titulo"], lida["empresa"], lida["remoto"]),
                         ("infojobs-70004", "Analista de Dados Remoto", "Empresa Exemplo Remota Ltda", True))

    def test_pais_inteiro_nos_modelos_marcados(self):
        self.respostas()
        cfg = {**CFG, "localidade": {"pais": "Brasil"}, "modelos": {"remoto": False, "hibrido": True,
                                                                     "presencial": True}}
        (consulta,) = grupos(cfg).values()
        self.assertEqual(numeros(infojobs.buscar(consulta, 168, 20)[0]), [70001, 70002, 70006])

    def test_fora_do_brasil_sem_pedido(self):
        self.respostas()
        consulta = {**grupos(CFG)["remoto"], "pais": "portugal"}
        self.assertEqual(infojobs.buscar(consulta, 168, 20), ([], []))
        self.assertEqual(self.urls, [])

    def test_pagina_ilegivel_avisa_uma_vez(self):
        self.respostas(lambda url: '<div class="js_vacancyLoad">mudou</div>')
        c = grupos(CFG)
        self.assertEqual(infojobs.buscar(c["remoto"], 168, 20), ([], [infojobs.ILEGIVEL]))
        self.assertEqual(infojobs.buscar(c["remoto"], 168, 20), ([], []))

    def test_descrever_e_id_do_link(self):
        self.respostas(lambda url: VAGA)
        v = infojobs.ler_lista(LISTA)[0]
        texto = infojobs.descrever(v)
        self.assertIn("SQL avançado", texto)
        self.assertIn("Efetivo – CLT", texto)
        self.assertEqual(infojobs.id_do_link(v["url"]), "infojobs-70001")
        self.assertIsNone(infojobs.id_do_link("https://www.infojobs.com.br/empregos.aspx?palabra=x"))
        self.assertIsNone(infojobs.id_do_link("/vaga-de-x__1.aspx"))
        with self.assertRaises(_comum.FonteErro):
            infojobs.descrever({"url": "https://example.com/x"})

    def test_adicionar_pelo_link(self):  # mesmo id da busca: a vaga não volta como nova
        url = "https://www.infojobs.com.br/vaga-de-analista-de-dados-pleno-em-sao-paulo__70001.aspx"
        self.assertEqual(link.plataforma("www.infojobs.com.br"), "InfoJobs")
        with mock.patch.object(link, "_baixar", return_value=VAGA):
            v = link.ler(url)
        self.assertEqual((v["id"], v["plataforma"], v["titulo"], v["url"]),
                         ("infojobs-70001", "InfoJobs", "Analista de Dados Pleno", url))
        self.assertIn("InfoJobs", banco.PLATAFORMAS)


class TestBloqueio(SemRede):
    def test_429_poe_em_espera_de_24_horas(self):  # SC-005
        self.abridor([HOME_OFFICE, 429])
        c = grupos(CFG)
        self.assertEqual(numeros(infojobs.buscar(c["remoto"], 168, 20)[0]), [70001, 70002, 70003, 70004, 70006])
        local, erros = infojobs.buscar(c["local"], 168, 20)
        self.assertEqual(local, [])
        self.assertTrue(erros[0].startswith(infojobs.BLOQUEIO + " (código 429); em espera até "), erros)
        self.assertTrue(infojobs.parada())
        outro = {**c["remoto"], "termo": "cientista de dados"}
        self.assertEqual(infojobs.buscar(outro, 168, 20), ([], []))  # nenhum pedido a mais
        self.assertEqual(infojobs.descrever({"url": "x", "descricao": "da lista"}), "da lista")
        self.assertEqual(len(self.pedidos), 2)
        for req in self.pedidos:  # sem cookies e com o nome da ferramenta
            self.assertIsNone(req.get_header("Cookie"))
            self.assertEqual(req.get_header("User-agent"), _comum.AGENTE)
        e = infojobs.espera()
        self.assertEqual(e["motivo"], "código 429")
        self.assertAlmostEqual((datetime.fromisoformat(e["ate"]) - datetime.now()).total_seconds() / 3600, 24, delta=0.1)
        self.assertEqual([x["nome"] for x in vagas.fontes_em_espera(["indeed", "infojobs"])], ["infojobs"])

    def test_na_espera_nenhum_pedido(self):
        infojobs._bloquear("código 429")
        _comum.esquecer()  # a busca seguinte, ainda na espera
        self.abridor([])
        c = grupos(CFG)
        vagas_, erros = infojobs.buscar(c["remoto"], 168, 20)
        self.assertEqual(vagas_, [])
        self.assertTrue(erros[0].startswith("InfoJobs em espera até "), erros)
        self.assertEqual(infojobs.buscar(c["local"], 168, 20), ([], []))  # o aviso sai uma vez por busca
        self.assertEqual(infojobs.descrever({"url": "x", "descricao": ""}), "")
        with self.assertRaises(link.LinkErro) as ctx:
            link.ler("https://www.infojobs.com.br/vaga-de-analista__70001.aspx")
        self.assertIn("em espera", str(ctx.exception))
        self.assertEqual(self.pedidos, [])

    def test_a_espera_acaba(self):
        infojobs._bloquear("código 503")
        self.assertIsNotNone(infojobs.espera())
        self.assertIsNone(infojobs.espera(datetime.now() + timedelta(hours=24, minutes=1)))
        infojobs.ARQ_ESPERA.write_text("{quebrado", encoding="utf-8")
        self.assertIsNone(infojobs.espera())  # arquivo ilegível: segue como se não houvesse espera

    def test_403_503_e_login_contam_como_bloqueio(self):
        for resposta, motivo in ((403, "código 403"), (503, "código 503"),
                                 (Resposta(LISTA, "https://www.infojobs.com.br/candidate/login.aspx"), "pediu login")):
            _comum.esquecer()
            infojobs.ARQ_ESPERA.unlink(missing_ok=True)
            self.abridor([resposta])
            vs, erros = infojobs.buscar(grupos(CFG)["remoto"], 168, 20)
            self.assertEqual(vs, [])
            self.assertIn(f"({motivo}); em espera até", erros[0])
            self.assertTrue(infojobs.parada())

    def test_outro_erro_nao_para_a_fonte(self):
        self.abridor([500, LISTA])
        c = grupos(CFG)
        self.assertEqual(infojobs.buscar(c["remoto"], 168, 20), ([], ["o InfoJobs respondeu 500"]))
        self.assertFalse(infojobs.parada())
        self.assertIsNone(infojobs.espera())
        self.assertTrue(infojobs.buscar(c["local"], 168, 20)[0])


class TestPadrao(unittest.TestCase):
    def test_ligado_por_padrao(self):  # SC-001
        self.assertIn("infojobs", FONTES)
        self.assertIn("infojobs", filtros.efetivos({})["fontes"])
        cfg = {"termos": ["analista"], "fontes": ["indeed", "gupy"]}  # a lista escolhida pela pessoa não muda
        self.assertEqual(vagas.fontes_da_busca(cfg, filtros.efetivos(cfg)), ["indeed", "gupy"])
        nomes = {o["nome"]: o for o in filtros.opcoes()["fontes_nac"]}
        self.assertIn("não autorizam robôs", nomes["infojobs"]["termos"])
        self.assertEqual(nomes["infojobs"]["precisa"], "")


if __name__ == "__main__":
    unittest.main()
