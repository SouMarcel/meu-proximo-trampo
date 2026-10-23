"""Vagas.com na busca (fontes/vagascom.py), com HTML fictício e sem rede (spec 028): leitura dos cards, datas
relativas, filtro por cargo, janela, grupo e cidade, paginação sem repetir, uma leitura por cargo, descrição pela
página da vaga, bloqueio com espera de 24 horas, link no Adicionar Vaga e o portal ligado por padrão."""
import shutil
import sys
import tempfile
import unittest
import urllib.error
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import banco  # noqa: E402
import filtros  # noqa: E402
import vagas  # noqa: E402
from fontes import FONTES, _comum, link, vagascom  # noqa: E402

DADOS = Path(__file__).resolve().parent / "dados" / "vagascom"
LISTA = (DADOS / "lista.html").read_text(encoding="utf-8")
LISTA_2 = (DADOS / "lista-2.html").read_text(encoding="utf-8")
VAGA = (DADOS / "vaga.html").read_text(encoding="utf-8")
HOJE = datetime(2026, 10, 23, 15, tzinfo=timezone.utc)
CFG = {"termos": ["analista de dados"], "localidade": {"pais": "Brasil", "estado": "SP", "cidade": "São Paulo",
                                                      "raio_km": 25},
       "modelos": {"remoto": True, "hibrido": True, "presencial": True}, "tipos_emprego": [],
       "fontes": ["vagascom"], "janela_horas": 168, "internacional": {"ativo": False}}


def grupos(cfg):
    return {c["grupo"]: c for c in filtros.consultas(filtros.efetivos(cfg))}


def numeros(lista):
    return [int(v["id"].removeprefix("vagascom-")) for v in lista]


def paginas(url):
    return LISTA_2 if "pagina=2" in url else LISTA


class SemRede(unittest.TestCase):
    def setUp(self):
        _comum.esquecer()
        vagascom._estado["ultimo"] = None
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for p in (mock.patch.object(vagascom, "PAUSA", (0, 0)), mock.patch.object(vagascom.time, "sleep"),
                  mock.patch.object(vagascom, "_agora", return_value=HOJE),
                  mock.patch.object(vagascom, "POR_PAGINA", 4),
                  mock.patch.object(vagascom, "ARQ_ESPERA", self.tmp / ".cache" / "vagascom-espera.json")):
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(_comum.esquecer)

    def respostas(self, fn=paginas):
        self.urls = []

        def baixar(url):
            self.urls.append(url)
            return fn(url)
        p = mock.patch.object(vagascom, "_baixar", side_effect=baixar)
        p.start()
        self.addCleanup(p.stop)

    def abridor(self, respostas):
        self.pedidos = []
        fila = list(respostas)

        def abrir(req, timeout=None):
            self.pedidos.append(req)
            r = fila.pop(0)
            if isinstance(r, int):
                raise urllib.error.HTTPError(req.full_url, r, "x", {}, None)
            resp = mock.MagicMock()
            resp.__enter__.return_value = resp
            resp.read.return_value = r.encode()
            resp.headers.get_content_charset.return_value = "utf-8"
            resp.geturl.return_value = "https://www.vagas.com.br/vagas-de-analista-de-dados"
            return resp
        p = mock.patch.object(_comum.urllib.request, "urlopen", side_effect=abrir)
        p.start()
        self.addCleanup(p.stop)


class TestLeitura(SemRede):
    def test_cards(self):
        vs = vagascom.ler_lista(LISTA)
        self.assertEqual(numeros(vs), [80001, 80002, 80003, 80004])
        v = vs[0]
        self.assertEqual(v["titulo"], "Analista de Dados Pleno — Vaga Exclusiva para Pessoas com Deficiência")
        self.assertEqual((v["empresa"], v["local"], v["remoto"], v["publicada_em"], v["tipo"]),
                         ("Empresa Alfa", "São Paulo, SP", False, "2026-10-23", "Pleno • Exclusiva para PCD"))
        self.assertEqual(v["url"], "https://www.vagas.com.br/vagas/v80001/analista-de-dados-pleno")
        self.assertNotIn("modelo_trabalho", v)  # a lista só diz quando é 100% home office
        self.assertEqual((vs[1]["local"], vs[1]["remoto"], vs[1]["modelo_trabalho"], vs[1]["publicada_em"]),
                         ("Remoto", True, "remoto", "2026-10-22"))
        antiga = vagascom.ler_lista(LISTA_2)[-1]
        self.assertEqual((antiga["local"], antiga["publicada_em"]), ("", "2026-09-01"))

    def test_datas_relativas(self):
        hoje = date(2026, 10, 23)
        casos = {"Hoje": "2026-10-23", "Ontem": "2026-10-22", "Há 3 dias": "2026-10-20", "Há 1 dia": "2026-10-22",
                 "24/09/2026": "2026-09-24", "algum dia": None, "": None}
        for texto, esperado in casos.items():
            self.assertEqual(vagascom.data_relativa(texto, hoje), esperado, texto)

    def test_remoto_e_cidade_com_uma_leitura(self):
        self.respostas()
        c = grupos(CFG)
        remoto, erros = vagascom.buscar(c["remoto"], 168, 20)
        self.assertEqual((numeros(remoto), erros), ([80002], []))
        local, _ = vagascom.buscar(c["local"], 168, 20)
        self.assertEqual(numeros(local), [80001, 80004])  # SP e Campinas/SP; 80003 é de suporte; 80005 é do RJ
        self.assertEqual(len(self.urls), 2)  # as duas páginas, uma vez para as duas consultas
        self.assertEqual(self.urls[0], "https://www.vagas.com.br/vagas-de-analista-de-dados?ordenar_por=mais_recentes")
        self.assertIn("pagina=2", self.urls[1])

    def test_janela_para_a_paginacao(self):
        self.respostas()
        vagascom.buscar(grupos(CFG)["remoto"], 24, 20)  # a página 1 já chega a vagas de antes da janela
        self.assertEqual(len(self.urls), 1)

    def test_fora_do_brasil_sem_pedido(self):
        self.respostas()
        self.assertEqual(vagascom.buscar({**grupos(CFG)["remoto"], "pais": "usa"}, 168, 20), ([], []))
        self.assertEqual(self.urls, [])

    def test_descrever_e_link(self):
        self.respostas(lambda url: VAGA)
        self.assertIn("SQL avançado", vagascom.descrever(vagascom.ler_lista(LISTA)[1]))
        url = "https://www.vagas.com.br/vagas/v80002/analista-de-dados-remoto"
        self.assertEqual(vagascom.id_do_link(url), "vagascom-80002")
        self.assertIsNone(vagascom.id_do_link("https://www.vagas.com.br/vagas-de-analista-de-dados"))
        self.assertEqual(link.plataforma("www.vagas.com.br"), "Vagas.com")
        with mock.patch.object(link, "_baixar", return_value=VAGA):
            v = link.ler(url)
        self.assertEqual((v["id"], v["plataforma"], v["empresa"]), ("vagascom-80002", "Vagas.com", "Empresa Beta"))
        self.assertIn("Vagas.com", banco.PLATAFORMAS)


class TestBloqueio(SemRede):
    def test_429_poe_em_espera(self):
        self.abridor([LISTA, 429])
        c = grupos(CFG)
        remoto, erros = vagascom.buscar(c["remoto"], 168, 20)
        self.assertEqual(numeros(remoto), [80002])  # a página 1 já lida vale
        self.assertTrue(erros[0].startswith(vagascom.BLOQUEIO + " (código 429); em espera até "), erros)
        self.assertEqual(vagascom.buscar({**c["remoto"], "termo": "cientista"}, 168, 20), ([], []))
        self.assertEqual(len(self.pedidos), 2)
        self.assertIsNotNone(vagascom.espera())
        _comum.esquecer()
        self.abridor([])
        vs, erros = vagascom.buscar(c["remoto"], 168, 20)
        self.assertTrue(erros[0].startswith("Vagas.com em espera até "), erros)
        self.assertEqual(self.pedidos, [])


class TestPadrao(unittest.TestCase):
    def test_ligado_por_padrao(self):
        self.assertIn("vagascom", FONTES)
        self.assertIn("vagascom", filtros.efetivos({})["fontes"])
        nomes = {o["nome"]: o for o in filtros.opcoes()["fontes_nac"]}
        self.assertEqual((nomes["vagascom"]["rotulo"], nomes["vagascom"]["precisa"]), ("Vagas.com", ""))
        self.assertIn("24 horas", nomes["vagascom"]["termos"])


if __name__ == "__main__":
    unittest.main()
